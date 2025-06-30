"""
Individual Tickers Performance Chart - Standalone Application
Can be launched independently or from the main chart manager
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import sys

# Import from the existing portfolio analyzer
try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, 
        fetch_market_data, 
        CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    print("Make sure portfolio_analyzer_update_3.py is in the same directory")
    sys.exit(1)

def create_individual_tickers_chart(data, positions, days_back, save_chart=False):
    """Create chart showing individual ticker performance."""
    plt.style.use('default')
    
    tickers = list(positions.keys())
    
    # Create subplots - normalize to show percentage change
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_FIGSIZE[0] * 1.8, CHART_FIGSIZE[1] * 1.5))
    
    # Normalize each ticker to starting value for comparison (percentage change)
    normalized_data = data[tickers].div(data[tickers].iloc[0]) * 100
    
    # Top Left: All tickers normalized
    colors = plt.cm.tab20(np.linspace(0, 1, len(tickers)))
    
    for i, ticker in enumerate(tickers):
        if ticker in normalized_data.columns:
            ax1.plot(normalized_data.index, normalized_data[ticker], 
                    label=ticker, color=colors[i], linewidth=1.5, alpha=0.8)
    
    ax1.axhline(y=100, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    ax1.set_title('All Tickers - Normalized Performance', fontweight='bold')
    ax1.set_ylabel('Normalized Price (Start = 100)')
    ax1.grid(True, alpha=0.3)
    
    # Handle legend - if too many tickers, put legend outside plot
    if len(tickers) <= 8:
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small', ncol=2)
    
    # Top Right: Best and Worst Performers
    final_performance = normalized_data.iloc[-1] - 100  # Percentage change
    best_performers = final_performance.nlargest(5)
    worst_performers = final_performance.nsmallest(5)
    
    best_colors = ['green'] * len(best_performers)
    worst_colors = ['red'] * len(worst_performers)
    
    # Plot best performers
    for ticker in best_performers.index:
        ax2.plot(normalized_data.index, normalized_data[ticker], 
                label=f'{ticker} ({best_performers[ticker]:+.1f}%)', 
                linewidth=2.5, alpha=0.9)
    
    ax2.axhline(y=100, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    ax2.set_title('Top 5 Performers', fontweight='bold')
    ax2.set_ylabel('Normalized Price')
    ax2.legend(fontsize='small')
    ax2.grid(True, alpha=0.3)
    
    # Bottom Left: Worst performers
    for ticker in worst_performers.index:
        ax3.plot(normalized_data.index, normalized_data[ticker], 
                label=f'{ticker} ({worst_performers[ticker]:+.1f}%)', 
                linewidth=2.5, alpha=0.9, color='red')
    
    ax3.axhline(y=100, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    ax3.set_title('Bottom 5 Performers', fontweight='bold')
    ax3.set_ylabel('Normalized Price')
    ax3.legend(fontsize='small')
    ax3.grid(True, alpha=0.3)
    
    # Bottom Right: Volatility vs Return scatter
    returns = final_performance
    volatilities = normalized_data.std()
    
    scatter = ax4.scatter(volatilities, returns, 
                         c=returns, cmap='RdYlGn', s=100, alpha=0.7, edgecolors='black')
    
    # Add ticker labels to points
    for ticker in tickers:
        if ticker in returns.index and ticker in volatilities.index:
            ax4.annotate(ticker, (volatilities[ticker], returns[ticker]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    ax4.set_xlabel('Volatility (Std Dev)')
    ax4.set_ylabel('Total Return (%)')
    ax4.set_title('Risk vs Return Analysis', fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Return (%)')
    
    # Format x-axes
    for ax in [ax1, ax2, ax3]:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        ax.set_xlabel('Date')
    
    plt.suptitle(f'Individual Ticker Analysis ({days_back} Days)', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    if save_chart:
        filename = f'individual_tickers_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print analysis
    print_ticker_analysis(data, positions, normalized_data, days_back)

def print_ticker_analysis(data, positions, normalized_data, days_back):
    """Print detailed ticker analysis"""
    
    tickers = list(positions.keys())
    
    # Calculate performance metrics
    final_performance = normalized_data.iloc[-1] - 100
    volatilities = normalized_data.std()
    
    # Calculate daily returns for additional metrics
    daily_returns = data[tickers].pct_change() * 100
    
    # Sharpe ratio approximation (assuming risk-free rate ≈ 0)
    sharpe_ratios = daily_returns.mean() / daily_returns.std() * np.sqrt(252)
    
    # Maximum drawdown for each ticker
    max_drawdowns = {}
    for ticker in tickers:
        if ticker in normalized_data.columns:
            cummax = normalized_data[ticker].cummax()
            drawdown = (normalized_data[ticker] / cummax - 1) * 100
            max_drawdowns[ticker] = drawdown.min()
    
    print("\n" + "="*80)
    print("INDIVIDUAL TICKER ANALYSIS")
    print("="*80)
    print(f"Analysis Period:              {days_back} days")
    print(f"Number of Positions:          {len(tickers)}")
    print()
    
    # Summary statistics
    avg_return = final_performance.mean()
    avg_volatility = volatilities.mean()
    
    print("Portfolio Summary:")
    print(f"  Average Return:             {avg_return:+.2f}%")
    print(f"  Average Volatility:         {avg_volatility:.2f}")
    print(f"  Best Performer:             {final_performance.idxmax()} ({final_performance.max():+.2f}%)")
    print(f"  Worst Performer:            {final_performance.idxmin()} ({final_performance.min():+.2f}%)")
    print()
    
    # Top performers table
    print("Top 5 Performers:")
    print(f"{'Ticker':<8} {'Return':<10} {'Volatility':<12} {'Sharpe':<8} {'Max DD':<8} {'Position':<12}")
    print("-" * 68)
    
    top_performers = final_performance.nlargest(5)
    for ticker in top_performers.index:
        return_val = final_performance[ticker]
        volatility = volatilities[ticker] if ticker in volatilities.index else 0
        sharpe = sharpe_ratios[ticker] if ticker in sharpe_ratios.index else 0
        max_dd = max_drawdowns.get(ticker, 0)
        position = positions.get(ticker, 0)
        
        print(f"{ticker:<8} {return_val:+7.2f}%   {volatility:8.2f}     {sharpe:6.2f}   {max_dd:6.2f}%  {position:8.1f}")
    
    print()
    print("Bottom 5 Performers:")
    print(f"{'Ticker':<8} {'Return':<10} {'Volatility':<12} {'Sharpe':<8} {'Max DD':<8} {'Position':<12}")
    print("-" * 68)
    
    bottom_performers = final_performance.nsmallest(5)
    for ticker in bottom_performers.index:
        return_val = final_performance[ticker]
        volatility = volatilities[ticker] if ticker in volatilities.index else 0
        sharpe = sharpe_ratios[ticker] if ticker in sharpe_ratios.index else 0
        max_dd = max_drawdowns.get(ticker, 0)
        position = positions.get(ticker, 0)
        
        print(f"{ticker:<8} {return_val:+7.2f}%   {volatility:8.2f}     {sharpe:6.2f}   {max_dd:6.2f}%  {position:8.1f}")
    
    # Data quality check
    print()
    print("Data Quality Analysis:")
    
    # Check for extreme moves
    extreme_moves_count = 0
    for ticker in tickers:
        if ticker in daily_returns.columns:
            extreme_moves = daily_returns[ticker].abs() > 10  # More than 10% daily move
            if extreme_moves.any():
                extreme_count = extreme_moves.sum()
                extreme_moves_count += extreme_count
                if extreme_count > 2:  # Only report if multiple extreme moves
                    print(f"  {ticker}: {extreme_count} extreme daily moves (>10%)")
    
    if extreme_moves_count == 0:
        print("  ✓ No extreme daily moves detected")
    else:
        print(f"  ⚠ Total extreme moves detected: {extreme_moves_count}")
    
    # Check for potential data issues
    zero_data_tickers = []
    for ticker in tickers:
        if ticker in data.columns:
            if (data[ticker] == 0).any() or data[ticker].isna().any():
                zero_data_tickers.append(ticker)
    
    if zero_data_tickers:
        print(f"  ⚠ Tickers with data issues: {', '.join(zero_data_tickers)}")
    else:
        print("  ✓ No data quality issues detected")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Individual Tickers Performance Analysis')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Individual Tickers Chart ({days_back} days)...")
    
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
        
        # Fetch market data
        tickers = list(positions.keys())
        data = fetch_market_data(tickers, days_back)
        
        if data.empty:
            print("Error: Unable to fetch market data")
            return
        
        # Create the chart
        create_individual_tickers_chart(data, positions, days_back, save_chart)
        
        print("\nChart generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
