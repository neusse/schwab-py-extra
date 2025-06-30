"""
Portfolio Value & Trend Chart - Standalone Application
Can be launched independently or from the main chart manager
"""

import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from scipy.stats import linregress
import argparse
import sys

# Import from the existing portfolio analyzer
try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, 
        fetch_market_data, 
        calculate_portfolio_metrics,
        CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    print("Make sure portfolio_analyzer_update_3.py is in the same directory")
    sys.exit(1)

def create_portfolio_value_chart(metrics, days_back, save_chart=False):
    """Create portfolio value chart with trend line."""
    plt.style.use('default')  # Ensure consistent styling
    
    fig, ax1 = plt.subplots(figsize=CHART_FIGSIZE)
    
    daily_total = metrics['daily_portfolio_total']
    
    # Calculate trend line
    x_vals = range(len(daily_total))
    slope, intercept, r_value, p_value, std_err = linregress(x_vals, daily_total.values)
    trend_line = slope * pd.Series(x_vals, index=daily_total.index) + intercept
    
    # Plot portfolio value
    ax1.plot(daily_total.index, daily_total, label='Portfolio Value', 
             color='darkgreen', linewidth=2.5, alpha=0.8)
    
    # Plot trend line
    ax1.plot(daily_total.index, trend_line, label=f'Trend Line (R²={r_value**2:.3f})', 
             color='blue', linestyle='--', linewidth=2)
    
    # Formatting
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Portfolio Value ($)', fontsize=12, color='darkgreen')
    ax1.tick_params(axis='y', labelcolor='darkgreen')
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Title with key metrics
    initial_value = daily_total.iloc[0]
    final_value = daily_total.iloc[-1]
    total_return = (final_value - initial_value) / initial_value * 100
    
    plt.title(f"Portfolio Value & Trend Analysis ({days_back} Days)\n"
              f"Return: {total_return:+.2f}% | Current Value: ${final_value:,.0f}", 
              fontsize=14, fontweight='bold', pad=20)
    
    # Legend
    ax1.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
    
    # Add annotations for key points
    ax1.annotate(f'Start: ${initial_value:,.0f}', 
                xy=(daily_total.index[0], initial_value),
                xytext=(10, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7),
                fontsize=10)
    
    ax1.annotate(f'End: ${final_value:,.0f}', 
                xy=(daily_total.index[-1], final_value),
                xytext=(-60, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7),
                fontsize=10)
    
    # Format y-axis as currency
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Rotate x-axis labels for better readability
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    if save_chart:
        filename = f'portfolio_value_trend_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*50)
    print("PORTFOLIO VALUE ANALYSIS SUMMARY")
    print("="*50)
    print(f"Analysis Period:        {days_back} days")
    print(f"Initial Value:          ${initial_value:,.2f}")
    print(f"Final Value:            ${final_value:,.2f}")
    print(f"Total Change:           ${final_value - initial_value:+,.2f}")
    print(f"Total Return:           {total_return:+.2f}%")
    print(f"Trend R-squared:        {r_value**2:.4f}")
    
    if slope > 0:
        print(f"Trend Direction:        ↗ Upward (${slope:.2f}/day)")
    else:
        print(f"Trend Direction:        ↘ Downward (${slope:.2f}/day)")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Portfolio Value & Trend Chart')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Portfolio Value Chart ({days_back} days)...")
    
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
        
        # Calculate portfolio metrics
        portfolio_data = data[tickers]
        metrics = calculate_portfolio_metrics(portfolio_data, positions)
        
        # Create the chart
        create_portfolio_value_chart(metrics, days_back, save_chart)
        
        print("\nChart generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
