"""
Daily Portfolio Gains and Losses Analysis - Refactored with Gain/Loss Days Analysis
"""
import schwab
import yfinance as yf  # Keep for dividend data
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import linregress
import time
import json
from schwab_extra.lib.schwab_lib import authenticate as client_auth
from schwab_extra.lib.schwab_lib import get_positions_shares as gps 
from collections import defaultdict
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONSTANTS
# =============================================================================
DAYS_BACK = 365
TRADING_DAYS_PER_YEAR = 252
TRADING_DAYS_PER_MONTH = 21
SP500_TICKER = "$SPX"
CHART_FIGSIZE = (14, 7)
SLEEP_DELAY = 0.5

# =============================================================================
# DATA FETCHING FUNCTIONS
# =============================================================================

def get_schwab_symbol(ticker: str) -> str:
    """Convert ticker symbols to Schwab format if needed."""
    symbol_mapping = {
        "^GSPC": "$SPX.X",  # S&P 500 Index
        "^DJI": "$DJI.X",   # Dow Jones
        "^IXIC": "$COMPX.X", # NASDAQ Composite
        "^TNX": "$TNX.X",   # 10-Year Treasury
        "^VIX": "$VIX.X",   # VIX
    }
    return symbol_mapping.get(ticker, ticker)

def fetch_positions() -> Dict[str, float]:
    """Fetch portfolio positions from Schwab API."""
    try:
        client = client_auth()
        resp = client.get_accounts(fields=client.Account.Fields)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return {}

def get_portfolio_positions() -> Dict[str, float]:
    """Get consolidated portfolio positions by symbol."""
    my_positions = gps()
    positions = defaultdict(float)
    for item in my_positions:
        positions[item["symbol"]] += item["shares"]
    return dict(positions)

def fetch_market_data(tickers: List[str], days_back: int) -> pd.DataFrame:
    """Fetch market data for given tickers using Schwab API."""
    try:
        client = client_auth()
    except Exception as e:
        print(f"Error authenticating with Schwab: {e}")
        return pd.DataFrame()
        
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)
    
    all_data = {}
    
    print(f"Fetching market data for {len(tickers)} symbols using Schwab API...")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    for i, ticker in enumerate(tickers):
        try:
            print(f"Fetching data for {ticker} ({i+1}/{len(tickers)})")
            
            # Convert ticker to Schwab format if needed
            symbol = get_schwab_symbol(ticker)
            
            # Get price history from Schwab
            # response = client.get_price_history(
            #     symbol=symbol,
            #     period_type=Client.PriceHistory.PeriodType.YEAR,
            #     period=Client.PriceHistory.Period.ONE_YEAR,
            #     frequency_type=Client.PriceHistory.FrequencyType.DAILY,
            #     frequency=Client.PriceHistory.Frequency.DAILY,
            #     start_datetime=start_date,
            #     end_datetime=end_date
            # )
            
            response = client.get_price_history_every_day(
            symbol,
            start_datetime=start_date, 
            end_datetime=end_date, 
            need_extended_hours_data=False, 
            need_previous_close=False
            )

            response.raise_for_status()
            data = response.json()
            
            if 'candles' in data and data['candles']:
                # Convert to DataFrame
                candles = data['candles']
                dates = [datetime.fromtimestamp(candle['datetime']/1000) for candle in candles]
                closes = [candle['close'] for candle in candles]
                
                # Create a series for this ticker
                ticker_series = pd.Series(closes, index=pd.DatetimeIndex(dates), name=ticker)
                all_data[ticker] = ticker_series
                
                print(f"  Retrieved {len(closes)} data points for {ticker}")
                
            else:
                print(f"Warning: No candle data returned for {ticker}")
                
            # Rate limiting - be nice to the API
            if i < len(tickers) - 1:
                time.sleep(SLEEP_DELAY)
                
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            # Create empty series to maintain structure
            all_data[ticker] = pd.Series(dtype=float, name=ticker)
    
    if not all_data:
        print("Error: No market data could be fetched from Schwab API")
        return pd.DataFrame()
    
    # Combine all series into a DataFrame
    combined_df = pd.DataFrame(all_data)
    
    # Handle missing data - forward fill and align dates
    if not combined_df.empty:
        # Sort by date index
        combined_df = combined_df.sort_index()
        
        # Forward fill missing data (weekends, holidays)
        combined_df = combined_df.fillna(method='ffill')
        
        # Drop any rows that are still NaN (beginning of series)
        combined_df = combined_df.dropna()
        
        print(f"Successfully fetched data: {len(combined_df)} trading days")
        print(f"Date range: {combined_df.index[0].strftime('%Y-%m-%d')} to {combined_df.index[-1].strftime('%Y-%m-%d')}")
    else:
        print("Warning: No valid data returned for any symbols")
    
    return combined_df

def fetch_dividends(positions: Dict[str, float], days_back: int) -> Dict[str, float]:
    """
    Fetch dividend data for portfolio positions using yfinance.
    
    Note: We use yfinance for dividends since Schwab doesn't provide 
    dividend data in a usable format via their API.
    """
    total_dividends_paid = {}
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    print("Fetching dividend data using yfinance...")
    
    for i, (symbol, shares) in enumerate(positions.items()):
        try:
            stock = yf.Ticker(symbol)
            stock_dividends = stock.dividends
            recent_dividends = stock_dividends[stock_dividends.index > cutoff_date.strftime('%Y-%m-%d')]
            total_dividends = recent_dividends.sum() * shares
            total_dividends_paid[symbol] = total_dividends
            
            if total_dividends > 0:
                print(f"  {symbol}: ${total_dividends:.2f} in dividends")
            
            if i < len(positions) - 1:  # Don't sleep after the last request
                time.sleep(SLEEP_DELAY)
                
        except Exception as e:
            print(f"Error fetching dividends for {symbol}: {e}")
            total_dividends_paid[symbol] = 0.0
    
    total_div_amount = sum(total_dividends_paid.values())
    print(f"Total dividends fetched: ${total_div_amount:.2f}")
    
    return total_dividends_paid

# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================

def calculate_portfolio_metrics(data: pd.DataFrame, positions: Dict[str, float]) -> Dict:
    """Calculate comprehensive portfolio metrics."""
    # Calculate daily portfolio values
    daily_portfolio_values = data.multiply([positions[ticker] for ticker in data.columns], axis='columns')
    daily_portfolio_total = daily_portfolio_values.sum(axis=1)
    
    # Calculate daily changes
    daily_dollar_change = data.diff().multiply([positions[ticker] for ticker in data.columns], axis='columns')
    total_daily_change = daily_dollar_change.sum(axis=1)
    
    # Portfolio values
    initial_portfolio_value = daily_portfolio_total.iloc[0]
    final_portfolio_value = daily_portfolio_total.iloc[-1]
    total_change = total_daily_change.sum()
    
    # Returns
    percent_return = (total_change / initial_portfolio_value) * 100
    trading_days_period = len(daily_portfolio_total)
    annualized_return = ((final_portfolio_value / initial_portfolio_value) ** (TRADING_DAYS_PER_YEAR / trading_days_period)) - 1
    
    # Moving averages
    ma_1week = total_daily_change.rolling(window=5).mean()
    ma_2week = total_daily_change.rolling(window=10).mean()
    
    # Drawdown calculations
    rolling_max = daily_portfolio_total.cummax()
    daily_drawdown = daily_portfolio_total / rolling_max - 1
    max_drawdown_pct = daily_drawdown.min()
    max_drawdown_dollars = (rolling_max - daily_portfolio_total).max()
    max_drawdown_date = daily_drawdown.idxmin()
    
    # Trend analysis
    slope, intercept, r_value, p_value, std_err = linregress(range(len(daily_portfolio_total)), daily_portfolio_total)
    trend_line = slope * pd.Series(range(len(daily_portfolio_total))) + intercept
    
    # Gain/Loss Days Analysis (NEW)
    # Remove NaN values (first day has no change)
    daily_changes_clean = total_daily_change.dropna()
    
    gain_days = (daily_changes_clean > 0).sum()
    loss_days = (daily_changes_clean < 0).sum()
    flat_days = (daily_changes_clean == 0).sum()
    
    total_gains = daily_changes_clean[daily_changes_clean > 0].sum()
    total_losses = daily_changes_clean[daily_changes_clean < 0].sum()
    
    average_daily_change = daily_changes_clean.mean()
    average_gain_on_gain_days = daily_changes_clean[daily_changes_clean > 0].mean() if gain_days > 0 else 0
    average_loss_on_loss_days = daily_changes_clean[daily_changes_clean < 0].mean() if loss_days > 0 else 0
    
    return {
        'daily_portfolio_total': daily_portfolio_total,
        'total_daily_change': total_daily_change,
        'initial_value': initial_portfolio_value,
        'final_value': final_portfolio_value,
        'total_change': total_change,
        'percent_return': percent_return,
        'annualized_return': annualized_return,
        'ma_1week': ma_1week,
        'ma_2week': ma_2week,
        'daily_drawdown': daily_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'max_drawdown_dollars': max_drawdown_dollars,
        'max_drawdown_date': max_drawdown_date,
        'trend_line': trend_line,
        'trading_days': trading_days_period,
        # New gain/loss metrics
        'gain_days': gain_days,
        'loss_days': loss_days,
        'flat_days': flat_days,
        'total_gains': total_gains,
        'total_losses': total_losses,
        'average_daily_change': average_daily_change,
        'average_gain_on_gain_days': average_gain_on_gain_days,
        'average_loss_on_loss_days': average_loss_on_loss_days,
        'trading_days_with_data': len(daily_changes_clean)
    }

def calculate_benchmark_comparison(data: pd.DataFrame, positions: Dict[str, float], 
                                 benchmark_ticker: str = SP500_TICKER) -> Dict:
    """Calculate benchmark comparison metrics."""
    portfolio_tickers = list(positions.keys())
    
    # Portfolio values
    daily_portfolio_values = data[portfolio_tickers].multiply(pd.Series(positions), axis='columns').sum(axis=1)
    initial_portfolio_value = daily_portfolio_values.iloc[0]
    
    # Normalize benchmark to initial portfolio value
    benchmark_normalized = (data[benchmark_ticker] / data[benchmark_ticker].iloc[0]) * initial_portfolio_value
    
    # Calculate returns
    portfolio_return = (daily_portfolio_values.iloc[-1] / daily_portfolio_values.iloc[0]) - 1
    benchmark_return = (benchmark_normalized.iloc[-1] / benchmark_normalized.iloc[0]) - 1
    excess_return = portfolio_return - benchmark_return
    
    return {
        'portfolio_values': daily_portfolio_values,
        'benchmark_normalized': benchmark_normalized,
        'portfolio_return': portfolio_return,
        'benchmark_return': benchmark_return,
        'excess_return': excess_return
    }

# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_portfolio_value_chart(metrics: Dict, days_back: int, save_chart: bool = False) -> None:
    """Create portfolio value chart with trend line."""
    fig, ax1 = plt.subplots(figsize=CHART_FIGSIZE)
    
    daily_total = metrics['daily_portfolio_total']
    trend_line = metrics['trend_line']
    
    ax1.plot(daily_total.index, daily_total, label='Portfolio Value', color='green', linewidth=2)
    ax1.plot(daily_total.index, trend_line, label='Trend Line', color='blue', linestyle='--')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Portfolio Value ($)', color='green')
    ax1.tick_params(axis='y', labelcolor='green')
    
    plt.title(f"Portfolio Value Over the Last {days_back} Days")
    plt.legend()
    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
    plt.tight_layout()
    
    if save_chart:
        plt.savefig('portfolio_value_trend.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_daily_change_chart(metrics: Dict, days_back: int, save_chart: bool = False) -> None:
    """Create daily change chart with moving averages."""
    fig, ax1 = plt.subplots(figsize=CHART_FIGSIZE)
    
    total_change = metrics['total_daily_change']
    ma_1week = metrics['ma_1week']
    ma_2week = metrics['ma_2week']
    
    # Bar chart for daily changes
    ax1.bar(total_change.index, total_change, color='green', alpha=0.3, label='Daily Change')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Daily Change ($)', color='green')
    ax1.tick_params(axis='y', labelcolor='green')
    
    # Moving averages on second axis
    ax2 = ax1.twinx()
    ax2.plot(ma_1week.index, ma_1week, color='blue', linewidth=2, label='1 Week MA')
    ax2.plot(ma_2week.index, ma_2week, color='red', linewidth=2, label='2 Week MA')
    ax2.set_ylabel('Moving Average ($)', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    plt.title(f"Daily Portfolio Changes and Moving Averages ({days_back} days)")
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
    plt.tight_layout()
    
    if save_chart:
        plt.savefig('daily_changes_ma.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_benchmark_comparison_chart(benchmark_data: Dict, days_back: int, save_chart: bool = False) -> None:
    """Create benchmark comparison chart."""
    fig, ax1 = plt.subplots(figsize=CHART_FIGSIZE)
    
    portfolio_values = benchmark_data['portfolio_values']
    benchmark_normalized = benchmark_data['benchmark_normalized']
    
    ax1.plot(portfolio_values.index, portfolio_values, color='green', label='Portfolio Value', linewidth=2)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Portfolio Value ($)', color='green')
    ax1.tick_params(axis='y', labelcolor='green')
    
    ax2 = ax1.twinx()
    ax2.plot(benchmark_normalized.index, benchmark_normalized, color='blue', 
             linestyle='--', label='S&P 500 (Normalized)', linewidth=2)
    ax2.set_ylabel('S&P 500 (Normalized)', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    plt.title(f'Portfolio vs S&P 500 Performance ({days_back} Days)')
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.tight_layout()
    
    if save_chart:
        plt.savefig('portfolio_vs_sp500.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_drawdown_chart(metrics: Dict, days_back: int, save_chart: bool = False) -> None:
    """Create drawdown analysis chart."""
    fig, ax1 = plt.subplots(figsize=CHART_FIGSIZE)
    
    daily_drawdown = metrics['daily_drawdown']
    max_dd_date = metrics['max_drawdown_date']
    max_dd_value = metrics['max_drawdown_pct']
    
    drawdown_values = daily_drawdown * 100
    
    ax1.fill_between(daily_drawdown.index, 0, drawdown_values,
                     color='red', alpha=0.3, label='Drawdown')
    ax1.plot(daily_drawdown.index, drawdown_values,
             color='darkred', linewidth=1.5, label='Drawdown %')
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Drawdown (%)', color='darkred')
    ax1.tick_params(axis='y', labelcolor='darkred')
    ax1.set_title(f'Portfolio Drawdown ({days_back} Days)')
    ax1.legend(loc='lower right')
    ax1.grid(True, linestyle='--', linewidth=0.5, color='gray')
    
    # Annotate maximum drawdown
    ax1.annotate(f'Max Drawdown: {max_dd_value * 100:.2f}%\n{max_dd_date.strftime("%Y-%m-%d")}',
                 xy=(max_dd_date, max_dd_value * 100),
                 xytext=(10, -10), textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    plt.tight_layout()
    if save_chart:
        plt.savefig('portfolio_drawdown.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_individual_tickers_chart(data: pd.DataFrame, positions: Dict[str, float], 
                                  days_back: int, save_chart: bool = False) -> None:
    """Create chart showing individual ticker performance to identify data anomalies."""
    fig, ax1 = plt.subplots(figsize=(16, 10))  # Larger chart for better visibility
    
    # Get portfolio tickers (exclude S&P 500)
    tickers = list(positions.keys())
    
    # Normalize each ticker to starting value for comparison (percentage change)
    normalized_data = data[tickers].div(data[tickers].iloc[0]) * 100
    
    # Color cycle for different tickers
    colors = plt.cm.tab20(range(len(tickers)))
    
    # Plot each ticker
    for i, ticker in enumerate(tickers):
        try:
            ax1.plot(normalized_data.index, normalized_data[ticker], 
                    label=ticker, color=colors[i], linewidth=1.5, alpha=0.8)
        except Exception as e:
            print(f"Error plotting {ticker}: {e}")
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Normalized Price (Starting Value = 100)')
    ax1.set_title(f'Individual Ticker Performance - Normalized ({days_back} Days)')
    ax1.grid(True, linestyle='--', linewidth=0.5, color='gray')
    
    # Handle legend - if too many tickers, put legend outside plot
    if len(tickers) <= 12:
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small', ncol=2)
    
    plt.tight_layout()
    
    if save_chart:
        plt.savefig('individual_tickers.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print data quality summary
    print_section_header("Data Quality Analysis")
    
    # Check for extreme daily moves (potential data errors)
    daily_changes = data[tickers].pct_change() * 100
    
    for ticker in tickers:
        extreme_moves = daily_changes[ticker].abs() > 10  # More than 10% daily move
        if extreme_moves.any():
            extreme_dates = daily_changes[ticker][extreme_moves]
            print(f"{ticker}: Found {len(extreme_dates)} extreme daily moves (>10%)")
            for date, change in extreme_dates.head(3).items():  # Show first 3
                print(f"  {date.strftime('%Y-%m-%d')}: {change:.2f}%")
            if len(extreme_dates) > 3:
                print(f"  ... and {len(extreme_dates) - 3} more")
        
        # Check for zero/missing data
        zero_prices = (data[ticker] == 0) | data[ticker].isna()
        if zero_prices.any():
            print(f"{ticker}: Found {zero_prices.sum()} days with zero/missing prices")
    
    print(f"\nTotal tickers analyzed: {len(tickers)}")
    
    # Identify potential mutual funds by ticker pattern
    potential_mutual_funds = [t for t in tickers if len(t) == 5 and t.endswith('X')]
    if potential_mutual_funds:
        print(f"Potential mutual funds (ending in X): {', '.join(potential_mutual_funds)}")
        print("Note: Mutual funds often have data quality issues with yfinance")

# =============================================================================
# REPORTING FUNCTIONS
# =============================================================================

def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2f}%"

def print_section_header(title: str) -> None:
    """Print formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title.upper()}")
    print("=" * 60)

def print_portfolio_summary(metrics: Dict, dividends: Dict[str, float], days_back = DAYS_BACK) -> None:
    """Print comprehensive portfolio summary."""
    print_section_header("Portfolio Performance Summary")
    
    print(f"Analysis Period:                {days_back} days")
    print(f"Trading Days in Period:         {metrics['trading_days']}")
    print()
    print(f"Initial Portfolio Value:        {format_currency(metrics['initial_value'])}")
    print(f"Final Portfolio Value:          {format_currency(metrics['final_value'])}")
    print(f"Total Change:                   {format_currency(metrics['total_change'])}")
    print()
    print(f"Period Return:                  {format_percentage(metrics['percent_return'])}")
    print(f"Annualized Return:              {format_percentage(metrics['annualized_return'] * 100)}")
    
    # Dividends summary
    total_dividends = sum(dividends.values())
    if total_dividends > 0:
        print()
        print(f"Total Dividends Received:       {format_currency(total_dividends)}")
        dividend_yield_annualized = (total_dividends / metrics['initial_value']) * (365 / days_back) * 100
        print(f"Annualized Dividend Yield:      {format_percentage(dividend_yield_annualized)}")

def print_gain_loss_analysis(metrics: Dict) -> None:
    """Print daily gain/loss analysis."""
    print_section_header("Daily Gain/Loss Analysis")
    
    total_trading_days = metrics['trading_days_with_data']
    gain_days = metrics['gain_days']
    loss_days = metrics['loss_days']
    flat_days = metrics['flat_days']
    
    print(f"Total Trading Days Analyzed:    {total_trading_days}")
    print(f"Gain Days:                      {gain_days} ({gain_days/total_trading_days*100:.1f}%)")
    print(f"Loss Days:                      {loss_days} ({loss_days/total_trading_days*100:.1f}%)")
    print(f"Flat Days (No Change):          {flat_days} ({flat_days/total_trading_days*100:.1f}%)")
    print()
    print(f"Total Gains:                    {format_currency(metrics['total_gains'])}")
    print(f"Total Losses:                   {format_currency(metrics['total_losses'])}")
    print(f"Net Change:                     {format_currency(metrics['total_gains'] + metrics['total_losses'])}")
    print()
    print(f"Average Daily Change:           {format_currency(metrics['average_daily_change'])}")
    print(f"Average Gain (on gain days):    {format_currency(metrics['average_gain_on_gain_days'])}")
    print(f"Average Loss (on loss days):    {format_currency(metrics['average_loss_on_loss_days'])}")
    
    # Win/Loss ratio
    if loss_days > 0:
        win_loss_ratio = gain_days / loss_days
        print(f"Win/Loss Ratio:                 {win_loss_ratio:.2f}")
    else:
        print(f"Win/Loss Ratio:                 ∞ (No loss days)")
    
    # Average gain vs average loss magnitude comparison
    if metrics['average_loss_on_loss_days'] != 0:
        gain_loss_magnitude_ratio = abs(metrics['average_gain_on_gain_days'] / metrics['average_loss_on_loss_days'])
        print(f"Avg Gain/Avg Loss Magnitude:    {gain_loss_magnitude_ratio:.2f}")

def print_risk_metrics(metrics: Dict) -> None:
    """Print risk and drawdown metrics."""
    print_section_header("Risk Metrics")
    
    print(f"Maximum Drawdown:               {format_percentage(metrics['max_drawdown_pct'] * 100)}")
    print(f"Maximum Drawdown ($):           {format_currency(metrics['max_drawdown_dollars'])}")
    print(f"Date of Maximum Drawdown:       {metrics['max_drawdown_date'].strftime('%Y-%m-%d')}")
    
    current_drawdown = metrics['daily_drawdown'].iloc[-1] * 100
    if current_drawdown < -0.01:
        print(f"Current Drawdown:               {format_percentage(current_drawdown)}")
    else:
        print("Current Status:                 At or near peak value")

def print_benchmark_comparison(benchmark_data: Dict) -> None:
    """Print benchmark comparison results."""
    print_section_header("Benchmark Comparison (vs S&P 500)")
    
    print(f"Portfolio Return:               {format_percentage(benchmark_data['portfolio_return'] * 100)}")
    print(f"S&P 500 Return:                 {format_percentage(benchmark_data['benchmark_return'] * 100)}")
    print(f"Excess Return:                  {format_percentage(benchmark_data['excess_return'] * 100)}")
    
    if benchmark_data['excess_return'] > 0:
        print("Performance:                    ✓ Outperforming S&P 500")
    else:
        print("Performance:                    ✗ Underperforming S&P 500")

def print_dividend_details(dividends: Dict[str, float], days_back=DAYS_BACK) -> None:
    """Print detailed dividend information."""
    if not any(dividends.values()):
        return
        
    print_section_header(f"Dividend Details ({days_back} Days)")
    
    for symbol, amount in sorted(dividends.items(), key=lambda x: x[1], reverse=True):
        if amount > 0:
            print(f"{symbol:10} {format_currency(amount)}")
    
    # Print total dividends
    total_dividends = sum(dividends.values())
    print("-" * 25)
    print(f"{'TOTAL':10} {format_currency(total_dividends)}")

# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def analyze_portfolio(save_charts: bool = False, show_dividend_details: bool = True, 
                     days_back: int = DAYS_BACK) -> None:
    """Main portfolio analysis function."""
    print(f"Starting Portfolio Analysis for {days_back} days...")
    
    # Get portfolio data
    positions = get_portfolio_positions()
    if not positions:
        print("Error: No positions found")
        return
    
    # need some kind of black list.  SNSXX is a fund and returns bad data affecting calculations.
    if 'SNSXX' in positions:
        del(positions['SNSXX'])
    
    tickers = list(positions.keys())
    print(f"Analyzing {len(tickers)} positions")
    
    # Fetch market data (include S&P 500 for benchmark)
    all_tickers = tickers + [SP500_TICKER]
    data = fetch_market_data(all_tickers, days_back)
    if data.empty:
        print("Error: Unable to fetch market data")
        return
    
    # Calculate portfolio metrics
    portfolio_data = data[tickers]
    metrics = calculate_portfolio_metrics(portfolio_data, positions)
    
    # Calculate benchmark comparison
    benchmark_data = calculate_benchmark_comparison(data, positions)
    
    # Fetch dividends
    dividends = fetch_dividends(positions, days_back)
    
    # Generate reports
    print_portfolio_summary(metrics, dividends, days_back)
    print_gain_loss_analysis(metrics)  # NEW: Add gain/loss analysis
    print_risk_metrics(metrics)
    print_benchmark_comparison(benchmark_data)
    
    if show_dividend_details:
        print_dividend_details(dividends, days_back)
    
    # Generate charts
    print("\nGenerating charts...")
    create_portfolio_value_chart(metrics, days_back, save_charts)
    create_daily_change_chart(metrics, days_back, save_charts)
    create_benchmark_comparison_chart(benchmark_data, days_back, save_charts)
    create_drawdown_chart(metrics, days_back, save_charts)
    create_individual_tickers_chart(data, positions, days_back, save_charts)
    
    if save_charts:
        print("Charts saved to current directory")
    
    print("\nAnalysis complete!")

def main():
    analyze_portfolio(save_charts=False, show_dividend_details=True)


# =============================================================================
# EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Run the analysis with default 90-day period
    #analyze_portfolio(save_charts=False, show_dividend_details=True, days_back=180)
    main()
    # Example: Run analysis for different periods
    # analyze_portfolio(days_back=30)   # 30-day analysis
    # analyze_portfolio(days_back=180)  # 6-month analysis
    # analyze_portfolio(days_back=365)  # 1-year analysis