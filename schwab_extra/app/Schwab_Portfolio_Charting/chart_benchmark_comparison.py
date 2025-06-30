"""
Portfolio vs S&P 500 Benchmark Comparison Chart - Standalone Application
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
        calculate_benchmark_comparison,
        SP500_TICKER,
        CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    print("Make sure portfolio_analyzer_update_3.py is in the same directory")
    sys.exit(1)

def create_benchmark_comparison_chart(benchmark_data, days_back, save_chart=False):
    """Create comprehensive benchmark comparison chart."""
    plt.style.use('default')
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_FIGSIZE[0] * 1.5, CHART_FIGSIZE[1] * 1.5))
    
    portfolio_values = benchmark_data['portfolio_values']
    benchmark_normalized = benchmark_data['benchmark_normalized']
    
    # Calculate normalized performance (percentage change from start)
    portfolio_pct = (portfolio_values / portfolio_values.iloc[0] - 1) * 100
    benchmark_pct = (benchmark_normalized / benchmark_normalized.iloc[0] - 1) * 100
    
    # Top Left: Absolute values
    ax1.plot(portfolio_values.index, portfolio_values, color='darkgreen', 
             label='Portfolio', linewidth=2.5, alpha=0.9)
    ax1.plot(benchmark_normalized.index, benchmark_normalized, color='blue', 
             linestyle='--', label='S&P 500 (Normalized)', linewidth=2.5, alpha=0.9)
    
    ax1.set_title('Absolute Value Comparison', fontweight='bold')
    ax1.set_ylabel('Value ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Top Right: Percentage returns
    ax2.plot(portfolio_pct.index, portfolio_pct, color='darkgreen', 
             label='Portfolio', linewidth=2.5, alpha=0.9)
    ax2.plot(benchmark_pct.index, benchmark_pct, color='blue', 
             linestyle='--', label='S&P 500', linewidth=2.5, alpha=0.9)
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax2.set_title('Percentage Returns', fontweight='bold')
    ax2.set_ylabel('Return (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # Bottom Left: Excess return (Portfolio - S&P 500)
    excess_return = portfolio_pct - benchmark_pct
    colors = ['green' if x >= 0 else 'red' for x in excess_return]
    
    ax3.bar(excess_return.index, excess_return, color=colors, alpha=0.6, width=1)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax3.set_title('Excess Return vs S&P 500', fontweight='bold')
    ax3.set_ylabel('Excess Return (%)')
    ax3.grid(True, alpha=0.3)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:+.1f}%'))
    
    # Bottom Right: Rolling correlation (30-day)
    portfolio_returns = portfolio_values.pct_change()
    benchmark_returns = (benchmark_normalized / benchmark_normalized.shift(1) - 1)
    
    rolling_corr = portfolio_returns.rolling(window=30).corr(benchmark_returns)
    
    ax4.plot(rolling_corr.index, rolling_corr, color='purple', linewidth=2)
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax4.axhline(y=0.5, color='red', linestyle=':', alpha=0.7)
    ax4.axhline(y=-0.5, color='red', linestyle=':', alpha=0.7)
    ax4.set_title('30-Day Rolling Correlation', fontweight='bold')
    ax4.set_ylabel('Correlation')
    ax4.set_ylim(-1, 1)
    ax4.grid(True, alpha=0.3)
    
    # Format x-axes
    for ax in [ax1, ax2, ax3, ax4]:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        ax.set_xlabel('Date')
    
    plt.suptitle(f'Portfolio vs S&P 500 Analysis ({days_back} Days)', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    if save_chart:
        filename = f'benchmark_comparison_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print detailed analysis
    print_benchmark_analysis(benchmark_data, portfolio_pct, benchmark_pct, excess_return, rolling_corr, days_back)

def print_benchmark_analysis(benchmark_data, portfolio_pct, benchmark_pct, excess_return, rolling_corr, days_back):
    """Print detailed benchmark comparison analysis"""
    
    portfolio_return = benchmark_data['portfolio_return']
    benchmark_return = benchmark_data['benchmark_return']
    excess_return_total = benchmark_data['excess_return']
    
    # Risk metrics
    portfolio_volatility = portfolio_pct.std() * np.sqrt(252)  # Annualized
    benchmark_volatility = benchmark_pct.std() * np.sqrt(252)  # Annualized
    
    # Sharpe ratio approximation (assuming risk-free rate ≈ 0 for simplicity)
    sharpe_portfolio = (portfolio_return * 252) / portfolio_volatility if portfolio_volatility > 0 else 0
    sharpe_benchmark = (benchmark_return * 252) / benchmark_volatility if benchmark_volatility > 0 else 0
    
    # Beta calculation
    portfolio_daily_returns = portfolio_pct.diff().dropna()
    benchmark_daily_returns = benchmark_pct.diff().dropna()
    
    covariance = np.cov(portfolio_daily_returns, benchmark_daily_returns)[0][1]
    benchmark_variance = np.var(benchmark_daily_returns)
    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
    
    # Up/Down capture ratios
    up_market_days = benchmark_daily_returns > 0
    down_market_days = benchmark_daily_returns < 0
    
    up_capture = (portfolio_daily_returns[up_market_days].mean() / 
                  benchmark_daily_returns[up_market_days].mean()) if up_market_days.any() else 0
    down_capture = (portfolio_daily_returns[down_market_days].mean() / 
                    benchmark_daily_returns[down_market_days].mean()) if down_market_days.any() else 0
    
    # Current correlation
    current_correlation = rolling_corr.dropna().iloc[-1] if len(rolling_corr.dropna()) > 0 else 0
    avg_correlation = rolling_corr.mean()
    
    print("\n" + "="*70)
    print("BENCHMARK COMPARISON ANALYSIS")
    print("="*70)
    print(f"Analysis Period:                  {days_back} days")
    print()
    print("Total Returns:")
    print(f"  Portfolio Return:               {portfolio_return*100:+.2f}%")
    print(f"  S&P 500 Return:                 {benchmark_return*100:+.2f}%")
    print(f"  Excess Return:                  {excess_return_total*100:+.2f}%")
    print()
    print("Risk Metrics (Annualized):")
    print(f"  Portfolio Volatility:           {portfolio_volatility:.2f}%")
    print(f"  S&P 500 Volatility:             {benchmark_volatility:.2f}%")
    print(f"  Portfolio Sharpe Ratio:         {sharpe_portfolio:.3f}")
    print(f"  S&P 500 Sharpe Ratio:           {sharpe_benchmark:.3f}")
    print()
    print("Risk-Adjusted Metrics:")
    print(f"  Beta vs S&P 500:                {beta:.3f}")
    print(f"  Up Market Capture:              {up_capture*100:.1f}%")
    print(f"  Down Market Capture:            {down_capture*100:.1f}%")
    print()
    print("Correlation Analysis:")
    print(f"  Current 30-Day Correlation:     {current_correlation:.3f}")
    print(f"  Average Correlation:            {avg_correlation:.3f}")
    
    # Performance assessment
    print()
    print("Performance Assessment:")
    if excess_return_total > 0:
        print("  ✓ Portfolio is OUTPERFORMING the S&P 500")
    else:
        print("  ✗ Portfolio is UNDERPERFORMING the S&P 500")
        
    if beta > 1.1:
        print("  ⚠ High Beta: Portfolio is more volatile than market")
    elif beta < 0.9:
        print("  ℹ Low Beta: Portfolio is less volatile than market")
    else:
        print("  ℹ Moderate Beta: Portfolio volatility similar to market")
        
    if up_capture > 1.1 and down_capture < 0.9:
        print("  ✓ Excellent: Captures more upside, less downside")
    elif up_capture > 1.0:
        print("  ✓ Good upside capture")
    elif down_capture < 1.0:
        print("  ✓ Good downside protection")
    
    # Excess return trend
    recent_excess = excess_return.tail(10).mean()
    if recent_excess > 0:
        print(f"  ✓ Recent trend: Outperforming by {recent_excess:.2f}% on average")
    else:
        print(f"  ⚠ Recent trend: Underperforming by {abs(recent_excess):.2f}% on average")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Portfolio vs S&P 500 Benchmark Comparison')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Benchmark Comparison Chart ({days_back} days)...")
    
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
        
        # Fetch market data (include S&P 500)
        tickers = list(positions.keys()) + [SP500_TICKER]
        data = fetch_market_data(tickers, days_back)
        
        if data.empty:
            print("Error: Unable to fetch market data")
            return
        
        # Calculate benchmark comparison
        benchmark_data = calculate_benchmark_comparison(data, positions)
        
        # Create the chart
        create_benchmark_comparison_chart(benchmark_data, days_back, save_chart)
        
        print("\nChart generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
