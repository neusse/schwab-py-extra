"""
Risk Metrics Dashboard - Standalone Application
Comprehensive risk analysis including VaR, correlation, volatility, and other metrics
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
import argparse
import sys

# Import from the existing portfolio analyzer
try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, 
        fetch_market_data, 
        calculate_portfolio_metrics,
        calculate_benchmark_comparison,
        SP500_TICKER,
        CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    print("Make sure portfolio_analyzer_update_3.py is in the same directory")
    sys.exit(1)

def create_risk_dashboard(metrics, benchmark_data, data, positions, days_back, save_chart=False):
    """Create comprehensive risk metrics dashboard."""
    plt.style.use('default')
    
    # Create a 3x3 grid for comprehensive risk analysis
    fig = plt.figure(figsize=(CHART_FIGSIZE[0] * 2.2, CHART_FIGSIZE[1] * 2.2))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)
    
    daily_changes = metrics['total_daily_change'].dropna()
    portfolio_returns = daily_changes / metrics['initial_value'] * 100  # Convert to percentage
    
    # 1. Value at Risk (VaR) Analysis - Top Left
    ax1 = fig.add_subplot(gs[0, 0])
    create_var_analysis(ax1, daily_changes, portfolio_returns)
    
    # 2. Return Distribution - Top Center
    ax2 = fig.add_subplot(gs[0, 1])
    create_return_distribution(ax2, portfolio_returns)
    
    # 3. Rolling Volatility - Top Right
    ax3 = fig.add_subplot(gs[0, 2])
    create_rolling_volatility(ax3, portfolio_returns)
    
    # 4. Correlation Matrix - Middle Left
    ax4 = fig.add_subplot(gs[1, 0])
    create_correlation_heatmap(ax4, data, positions)
    
    # 5. Beta Analysis - Middle Center
    ax5 = fig.add_subplot(gs[1, 1])
    create_beta_analysis(ax5, benchmark_data, portfolio_returns)
    
    # 6. Risk-Return Scatter - Middle Right
    ax6 = fig.add_subplot(gs[1, 2])
    create_risk_return_scatter(ax6, data, positions)
    
    # 7. Maximum Drawdown Timeline - Bottom Left
    ax7 = fig.add_subplot(gs[2, 0])
    create_drawdown_timeline(ax7, metrics)
    
    # 8. Tail Risk Analysis - Bottom Center
    ax8 = fig.add_subplot(gs[2, 1])
    create_tail_risk_analysis(ax8, portfolio_returns)
    
    # 9. Risk Metrics Summary - Bottom Right
    ax9 = fig.add_subplot(gs[2, 2])
    create_risk_metrics_table(ax9, metrics, portfolio_returns, benchmark_data)
    
    plt.suptitle(f'Risk Metrics Dashboard ({days_back} Days)', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    if save_chart:
        filename = f'risk_dashboard_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print comprehensive risk analysis
    print_risk_analysis(metrics, portfolio_returns, benchmark_data, data, positions, days_back)

def create_var_analysis(ax, daily_changes, portfolio_returns):
    """Create Value at Risk analysis chart"""
    # Calculate VaR at different confidence levels
    var_95 = np.percentile(daily_changes, 5)
    var_99 = np.percentile(daily_changes, 1)
    var_99_5 = np.percentile(daily_changes, 0.5)
    
    # Create histogram
    ax.hist(daily_changes, bins=30, alpha=0.7, color='skyblue', 
            edgecolor='black', density=True, label='Daily Changes')
    
    # Add VaR lines
    ax.axvline(var_95, color='orange', linestyle='--', linewidth=2, 
               label=f'95% VaR: ${var_95:.0f}')
    ax.axvline(var_99, color='red', linestyle='--', linewidth=2, 
               label=f'99% VaR: ${var_99:.0f}')
    ax.axvline(var_99_5, color='darkred', linestyle='--', linewidth=2, 
               label=f'99.5% VaR: ${var_99_5:.0f}')
    
    ax.set_title('Value at Risk Distribution', fontweight='bold', fontsize=11)
    ax.set_xlabel('Daily Change ($)')
    ax.set_ylabel('Density')
    ax.legend(fontsize='small')
    ax.grid(True, alpha=0.3)

def create_return_distribution(ax, portfolio_returns):
    """Create return distribution with normality test"""
    # Histogram of returns
    ax.hist(portfolio_returns, bins=25, alpha=0.7, color='lightgreen', 
            edgecolor='black', density=True, label='Actual Returns')
    
    # Fit normal distribution
    mu, std = stats.norm.fit(portfolio_returns)
    xmin, xmax = ax.get_xlim()
    x = np.linspace(xmin, xmax, 100)
    normal_dist = stats.norm.pdf(x, mu, std)
    
    ax.plot(x, normal_dist, 'r-', linewidth=2, 
            label=f'Normal Fit (μ={mu:.2f}%, σ={std:.2f}%)')
    
    # Shapiro-Wilk test for normality
    shapiro_stat, shapiro_p = stats.shapiro(portfolio_returns[:5000])  # Limit for shapiro test
    
    ax.set_title(f'Return Distribution\n(Shapiro p-value: {shapiro_p:.4f})', 
                fontweight='bold', fontsize=11)
    ax.set_xlabel('Daily Return (%)')
    ax.set_ylabel('Density')
    ax.legend(fontsize='small')
    ax.grid(True, alpha=0.3)

def create_rolling_volatility(ax, portfolio_returns):
    """Create rolling volatility chart"""
    # Calculate rolling volatility (annualized)
    rolling_vol_30 = portfolio_returns.rolling(window=30).std() * np.sqrt(252)
    rolling_vol_60 = portfolio_returns.rolling(window=60).std() * np.sqrt(252)
    
    ax.plot(rolling_vol_30.index, rolling_vol_30, color='blue', 
            linewidth=2, label='30-Day Rolling Vol', alpha=0.8)
    ax.plot(rolling_vol_60.index, rolling_vol_60, color='red', 
            linewidth=2, label='60-Day Rolling Vol', alpha=0.8)
    
    # Add current volatility level
    current_vol = portfolio_returns.std() * np.sqrt(252)
    ax.axhline(y=current_vol, color='black', linestyle=':', 
               label=f'Current Vol: {current_vol:.1f}%')
    
    ax.set_title('Rolling Volatility (Annualized)', fontweight='bold', fontsize=11)
    ax.set_xlabel('Date')
    ax.set_ylabel('Volatility (%)')
    ax.legend(fontsize='small')
    ax.grid(True, alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

def create_correlation_heatmap(ax, data, positions):
    """Create correlation heatmap for top holdings"""
    # Select top 8 holdings by position size
    top_positions = dict(sorted(positions.items(), key=lambda x: abs(x[1]), reverse=True)[:8])
    top_tickers = list(top_positions.keys())
    
    if len(top_tickers) > 1:
        # Calculate correlation matrix
        returns_data = data[top_tickers].pct_change().dropna()
        corr_matrix = returns_data.corr()
        
        # Create heatmap
        im = ax.imshow(corr_matrix, cmap='RdYlBu_r', aspect='auto', vmin=-1, vmax=1)
        
        # Add correlation values as text
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix.columns)):
                text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=8)
        
        ax.set_xticks(range(len(corr_matrix.columns)))
        ax.set_yticks(range(len(corr_matrix)))
        ax.set_xticklabels(corr_matrix.columns, rotation=45)
        ax.set_yticklabels(corr_matrix.index)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Correlation', fontsize=9)
    else:
        ax.text(0.5, 0.5, 'Insufficient positions\nfor correlation analysis', 
                ha='center', va='center', transform=ax.transAxes, fontsize=10)
    
    ax.set_title('Top Holdings Correlation', fontweight='bold', fontsize=11)

def create_beta_analysis(ax, benchmark_data, portfolio_returns):
    """Create beta analysis vs benchmark"""
    if benchmark_data is None:
        ax.text(0.5, 0.5, 'Benchmark data\nnot available', 
                ha='center', va='center', transform=ax.transAxes, fontsize=10)
        ax.set_title('Beta Analysis', fontweight='bold', fontsize=11)
        return
    
    # Calculate benchmark returns
    benchmark_values = benchmark_data['benchmark_normalized']
    benchmark_returns = benchmark_values.pct_change() * 100
    
    # Align data
    aligned_data = pd.DataFrame({
        'portfolio': portfolio_returns,
        'benchmark': benchmark_returns
    }).dropna()
    
    if len(aligned_data) > 10:
        # Scatter plot
        ax.scatter(aligned_data['benchmark'], aligned_data['portfolio'], 
                  alpha=0.6, s=20, color='blue')
        
        # Calculate and plot regression line
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            aligned_data['benchmark'], aligned_data['portfolio'])
        
        x_line = np.linspace(aligned_data['benchmark'].min(), 
                           aligned_data['benchmark'].max(), 100)
        y_line = slope * x_line + intercept
        
        ax.plot(x_line, y_line, 'r-', linewidth=2, 
                label=f'Beta: {slope:.3f}\nR²: {r_value**2:.3f}')
        
        ax.set_xlabel('S&P 500 Return (%)')
        ax.set_ylabel('Portfolio Return (%)')
        ax.legend(fontsize='small')
        ax.grid(True, alpha=0.3)
    
    ax.set_title('Beta Analysis vs S&P 500', fontweight='bold', fontsize=11)

def create_risk_return_scatter(ax, data, positions):
    """Create risk-return scatter plot for individual holdings"""
    returns = []
    volatilities = []
    labels = []
    sizes = []
    
    for ticker, shares in positions.items():
        if ticker in data.columns:
            ticker_data = data[ticker]
            ticker_returns = ticker_data.pct_change().dropna()
            
            if len(ticker_returns) > 10:
                total_return = (ticker_data.iloc[-1] / ticker_data.iloc[0] - 1) * 100
                volatility = ticker_returns.std() * np.sqrt(252) * 100  # Annualized
                
                returns.append(total_return)
                volatilities.append(volatility)
                labels.append(ticker)
                sizes.append(abs(shares) / 10)  # Scale for visualization
    
    if returns:
        # Create scatter plot
        scatter = ax.scatter(volatilities, returns, s=sizes, alpha=0.7, 
                           c=returns, cmap='RdYlGn', edgecolors='black')
        
        # Add labels for top/bottom performers
        combined_data = list(zip(volatilities, returns, labels))
        combined_data.sort(key=lambda x: x[1])  # Sort by returns
        
        # Label best and worst performers
        for i, (vol, ret, label) in enumerate([combined_data[0], combined_data[-1]]):
            ax.annotate(label, (vol, ret), xytext=(5, 5), 
                       textcoords='offset points', fontsize=8)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
        ax.set_xlabel('Volatility (% Annualized)')
        ax.set_ylabel('Total Return (%)')
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
        cbar.set_label('Return (%)', fontsize=9)
    
    ax.set_title('Risk vs Return (Holdings)', fontweight='bold', fontsize=11)
    ax.grid(True, alpha=0.3)

def create_drawdown_timeline(ax, metrics):
    """Create maximum drawdown timeline"""
    daily_drawdown = metrics['daily_drawdown'] * 100
    
    ax.fill_between(daily_drawdown.index, 0, daily_drawdown, 
                   color='red', alpha=0.4, label='Drawdown')
    ax.plot(daily_drawdown.index, daily_drawdown, color='darkred', linewidth=1.5)
    
    # Mark maximum drawdown
    max_dd_date = metrics['max_drawdown_date']
    max_dd_value = metrics['max_drawdown_pct'] * 100
    
    ax.plot(max_dd_date, max_dd_value, 'ro', markersize=8, 
            label=f'Max DD: {max_dd_value:.1f}%')
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.set_title('Drawdown Timeline', fontweight='bold', fontsize=11)
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown (%)')
    ax.legend(fontsize='small')
    ax.grid(True, alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

def create_tail_risk_analysis(ax, portfolio_returns):
    """Create tail risk analysis"""
    # Calculate tail statistics
    left_tail = portfolio_returns[portfolio_returns < np.percentile(portfolio_returns, 5)]
    right_tail = portfolio_returns[portfolio_returns > np.percentile(portfolio_returns, 95)]
    
    # Expected Shortfall (Conditional VaR)
    es_95 = left_tail.mean() if len(left_tail) > 0 else 0
    es_99 = portfolio_returns[portfolio_returns < np.percentile(portfolio_returns, 1)].mean()
    
    # Plot tail distribution
    ax.hist(portfolio_returns, bins=50, alpha=0.5, color='lightblue', 
           density=True, label='All Returns')
    
    if len(left_tail) > 0:
        ax.hist(left_tail, bins=20, alpha=0.8, color='red', 
               density=True, label=f'Left Tail (5%)\nES 95%: {es_95:.2f}%')
    
    if len(right_tail) > 0:
        ax.hist(right_tail, bins=20, alpha=0.8, color='green', 
               density=True, label=f'Right Tail (5%)')
    
    ax.set_title('Tail Risk Analysis', fontweight='bold', fontsize=11)
    ax.set_xlabel('Daily Return (%)')
    ax.set_ylabel('Density')
    ax.legend(fontsize='small')
    ax.grid(True, alpha=0.3)

def create_risk_metrics_table(ax, metrics, portfolio_returns, benchmark_data):
    """Create risk metrics summary table"""
    ax.axis('off')
    
    # Calculate key risk metrics
    volatility = portfolio_returns.std() * np.sqrt(252)
    var_95 = np.percentile(portfolio_returns, 5)
    var_99 = np.percentile(portfolio_returns, 1)
    max_drawdown = metrics['max_drawdown_pct'] * 100
    
    # Sharpe ratio (assuming risk-free rate ≈ 0)
    sharpe_ratio = (portfolio_returns.mean() * 252) / volatility if volatility > 0 else 0
    
    # Skewness and Kurtosis
    skewness = stats.skew(portfolio_returns)
    kurtosis = stats.kurtosis(portfolio_returns)
    
    # Beta vs benchmark
    beta = 'N/A'
    if benchmark_data:
        benchmark_returns = benchmark_data['benchmark_normalized'].pct_change() * 100
        aligned_data = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) > 10:
            beta = np.cov(aligned_data['portfolio'], aligned_data['benchmark'])[0][1] / np.var(aligned_data['benchmark'])
            beta = f'{beta:.3f}'
    
    # Create table data
    table_data = [
        ['Metric', 'Value'],
        ['Volatility (Ann.)', f'{volatility:.1f}%'],
        ['95% VaR', f'{var_95:.2f}%'],
        ['99% VaR', f'{var_99:.2f}%'],
        ['Max Drawdown', f'{max_drawdown:.1f}%'],
        ['Sharpe Ratio', f'{sharpe_ratio:.3f}'],
        ['Beta vs S&P 500', str(beta)],
        ['Skewness', f'{skewness:.3f}'],
        ['Kurtosis', f'{kurtosis:.3f}']
    ]
    
    # Create table
    table = ax.table(cellText=table_data[1:], colLabels=table_data[0],
                    cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style the table
    for i in range(len(table_data)):
        table[(i, 0)].set_facecolor('#E6E6FA')
        table[(i, 1)].set_facecolor('#F0F8FF')
    
    ax.set_title('Risk Metrics Summary', fontweight='bold', fontsize=11, pad=20)

def print_risk_analysis(metrics, portfolio_returns, benchmark_data, data, positions, days_back):
    """Print comprehensive risk analysis"""
    print("\n" + "="*80)
    print("COMPREHENSIVE RISK ANALYSIS")
    print("="*80)
    print(f"Analysis Period:                  {days_back} days")
    print(f"Total Observations:               {len(portfolio_returns)}")
    print()
    
    # Basic risk metrics
    volatility = portfolio_returns.std() * np.sqrt(252)
    var_95 = np.percentile(portfolio_returns, 5)
    var_99 = np.percentile(portfolio_returns, 1)
    max_drawdown = metrics['max_drawdown_pct'] * 100
    
    print("Volatility Metrics:")
    print(f"  Daily Volatility:               {portfolio_returns.std():.3f}%")
    print(f"  Annualized Volatility:          {volatility:.2f}%")
    print(f"  Downside Deviation:             {portfolio_returns[portfolio_returns < 0].std() * np.sqrt(252):.2f}%")
    print()
    
    print("Value at Risk (VaR):")
    print(f"  95% VaR (Daily):                {var_95:.2f}%")
    print(f"  99% VaR (Daily):                {var_99:.2f}%")
    print(f"  Expected Shortfall (95%):       {portfolio_returns[portfolio_returns < var_95].mean():.2f}%")
    print()
    
    print("Drawdown Analysis:")
    print(f"  Maximum Drawdown:               {max_drawdown:.2f}%")
    print(f"  Current Drawdown:               {metrics['daily_drawdown'].iloc[-1] * 100:.2f}%")
    print()
    
    # Distribution analysis
    skewness = stats.skew(portfolio_returns)
    kurtosis = stats.kurtosis(portfolio_returns)
    
    print("Distribution Analysis:")
    print(f"  Skewness:                       {skewness:.3f}")
    print(f"  Kurtosis:                       {kurtosis:.3f}")
    print(f"  Jarque-Bera p-value:            {stats.jarque_bera(portfolio_returns)[1]:.6f}")
    print()
    
    # Risk-adjusted returns
    mean_return = portfolio_returns.mean() * 252
    sharpe_ratio = mean_return / volatility if volatility > 0 else 0
    
    print("Risk-Adjusted Returns:")
    print(f"  Annualized Return:              {mean_return:.2f}%")
    print(f"  Sharpe Ratio:                   {sharpe_ratio:.3f}")
    
    if portfolio_returns[portfolio_returns < 0].std() > 0:
        sortino_ratio = mean_return / (portfolio_returns[portfolio_returns < 0].std() * np.sqrt(252))
        print(f"  Sortino Ratio:                  {sortino_ratio:.3f}")
    
    print()
    
    # Concentration risk
    total_position_value = sum(abs(v) for v in positions.values())
    concentration_hhi = sum((abs(v) / total_position_value) ** 2 for v in positions.values())
    
    print("Concentration Risk:")
    print(f"  Number of Positions:            {len(positions)}")
    print(f"  HHI Concentration Index:        {concentration_hhi:.3f}")
    
    if concentration_hhi > 0.25:
        print("  ⚠ High concentration risk")
    elif concentration_hhi > 0.15:
        print("  ⚠ Moderate concentration risk")
    else:
        print("  ✓ Well diversified")
    
    # Risk assessment
    print()
    print("Risk Assessment:")
    
    if volatility < 15:
        print("  ✓ Low volatility portfolio")
    elif volatility < 25:
        print("  ⚠ Moderate volatility portfolio")
    else:
        print("  ⚠ High volatility portfolio")
    
    if max_drawdown < 10:
        print("  ✓ Low maximum drawdown")
    elif max_drawdown < 20:
        print("  ⚠ Moderate maximum drawdown")
    else:
        print("  ⚠ High maximum drawdown")
    
    if sharpe_ratio > 1.0:
        print("  ✓ Good risk-adjusted returns")
    elif sharpe_ratio > 0.5:
        print("  ⚠ Moderate risk-adjusted returns")
    else:
        print("  ⚠ Poor risk-adjusted returns")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Risk Metrics Dashboard')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Risk Metrics Dashboard ({days_back} days)...")
    
    try:
        # Get portfolio positions
        positions = get_portfolio_positions()
        if not positions:
            print("Error: No positions found")
            return
        
        # Remove problematic tickers
        if 'SNSXX' in positions:
            del positions['SNSXX']
        
        print(f"Analyzing {len(positions)} positions...")
        
        # Fetch market data (include S&P 500 for benchmark)
        tickers = list(positions.keys()) + [SP500_TICKER]
        data = fetch_market_data(tickers, days_back)
        
        if data.empty:
            print("Error: Unable to fetch market data")
            return
        
        # Calculate portfolio metrics
        portfolio_data = data[list(positions.keys())]
        metrics = calculate_portfolio_metrics(portfolio_data, positions)
        
        # Calculate benchmark comparison
        benchmark_data = calculate_benchmark_comparison(data, positions)
        
        # Create the dashboard
        create_risk_dashboard(metrics, benchmark_data, data, positions, days_back, save_chart)
        
        print("\nRisk dashboard generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
