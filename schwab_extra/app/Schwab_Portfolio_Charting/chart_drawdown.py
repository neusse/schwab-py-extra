"""
Portfolio Drawdown Analysis Chart - Standalone Application
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
        calculate_portfolio_metrics,
        CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    print("Make sure portfolio_analyzer_update_3.py is in the same directory")
    sys.exit(1)

def create_drawdown_chart(metrics, days_back, save_chart=False):
    """Create comprehensive drawdown analysis chart."""
    plt.style.use('default')
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_FIGSIZE[0] * 1.5, CHART_FIGSIZE[1] * 1.5))
    
    daily_portfolio_total = metrics['daily_portfolio_total']
    daily_drawdown = metrics['daily_drawdown']
    max_dd_date = metrics['max_drawdown_date']
    max_dd_value = metrics['max_drawdown_pct']
    
    # Top Left: Portfolio value with peaks
    rolling_max = daily_portfolio_total.cummax()
    
    ax1.plot(daily_portfolio_total.index, daily_portfolio_total, 
             color='darkgreen', label='Portfolio Value', linewidth=2)
    ax1.plot(rolling_max.index, rolling_max, 
             color='red', linestyle='--', alpha=0.7, label='Peak Values', linewidth=1.5)
    
    # Fill between portfolio and peaks to show drawdown areas
    ax1.fill_between(daily_portfolio_total.index, daily_portfolio_total, rolling_max,
                     alpha=0.3, color='red', label='Drawdown Areas')
    
    ax1.set_title('Portfolio Value & Peak Levels', fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Top Right: Drawdown percentage
    drawdown_pct = daily_drawdown * 100
    
    ax2.fill_between(daily_drawdown.index, 0, drawdown_pct,
                     color='red', alpha=0.4, label='Drawdown')
    ax2.plot(daily_drawdown.index, drawdown_pct,
             color='darkred', linewidth=1.5, label='Drawdown %')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    # Annotate maximum drawdown
    ax2.annotate(f'Max DD: {max_dd_value * 100:.2f}%\n{max_dd_date.strftime("%Y-%m-%d")}',
                 xy=(max_dd_date, max_dd_value * 100),
                 xytext=(10, -20), textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    ax2.set_title('Drawdown Analysis', fontweight='bold')
    ax2.set_ylabel('Drawdown (%)')
    ax2.legend(loc='lower right')
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # Bottom Left: Drawdown duration analysis
    # Calculate drawdown periods
    in_drawdown = daily_drawdown < -0.001  # More than 0.1% drawdown
    drawdown_periods = []
    start_date = None
    
    for date, is_dd in in_drawdown.items():
        if is_dd and start_date is None:
            start_date = date
        elif not is_dd and start_date is not None:
            drawdown_periods.append((start_date, date, (date - start_date).days))
            start_date = None
    
    # If still in drawdown at the end
    if start_date is not None:
        drawdown_periods.append((start_date, daily_drawdown.index[-1], 
                                (daily_drawdown.index[-1] - start_date).days))
    
    # Create histogram of drawdown durations
    if drawdown_periods:
        durations = [period[2] for period in drawdown_periods]
        ax3.hist(durations, bins=min(10, len(durations)), color='orange', alpha=0.7, edgecolor='black')
        ax3.set_title('Drawdown Duration Distribution', fontweight='bold')
        ax3.set_xlabel('Duration (Days)')
        ax3.set_ylabel('Frequency')
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No significant\ndrawdown periods', 
                ha='center', va='center', transform=ax3.transAxes, fontsize=12)
        ax3.set_title('Drawdown Duration Distribution', fontweight='bold')
    
    # Bottom Right: Underwater curve (time underwater)
    underwater_days = []
    days_underwater = 0
    
    for i, dd_value in enumerate(daily_drawdown):
        if dd_value < -0.001:  # In drawdown
            days_underwater += 1
        else:  # At new high
            days_underwater = 0
        underwater_days.append(days_underwater)
    
    underwater_series = pd.Series(underwater_days, index=daily_drawdown.index)
    
    ax4.plot(underwater_series.index, underwater_series, color='blue', linewidth=2)
    ax4.fill_between(underwater_series.index, 0, underwater_series, alpha=0.3, color='blue')
    ax4.set_title('Time Underwater (Days Since Peak)', fontweight='bold')
    ax4.set_ylabel('Days Underwater')
    ax4.grid(True, alpha=0.3)
    
    # Format x-axes
    for ax in [ax1, ax2, ax3, ax4]:
        if ax != ax3:  # ax3 doesn't have date x-axis
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            ax.set_xlabel('Date')
    
    plt.suptitle(f'Portfolio Drawdown Analysis ({days_back} Days)', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    if save_chart:
        filename = f'drawdown_analysis_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print detailed analysis
    print_drawdown_analysis(metrics, drawdown_periods, underwater_series, days_back)

def print_drawdown_analysis(metrics, drawdown_periods, underwater_series, days_back):
    """Print detailed drawdown analysis"""
    
    max_dd_pct = metrics['max_drawdown_pct']
    max_dd_dollars = metrics['max_drawdown_dollars']
    max_dd_date = metrics['max_drawdown_date']
    current_dd = metrics['daily_drawdown'].iloc[-1]
    
    print("\n" + "="*60)
    print("DRAWDOWN ANALYSIS")
    print("="*60)
    print(f"Analysis Period:              {days_back} days")
    print()
    print("Maximum Drawdown:")
    print(f"  Maximum Drawdown:           {max_dd_pct*100:.2f}%")
    print(f"  Maximum Drawdown ($):       ${max_dd_dollars:,.2f}")
    print(f"  Date of Max Drawdown:       {max_dd_date.strftime('%Y-%m-%d')}")
    print()
    
    # Current status
    if current_dd < -0.001:
        print(f"Current Drawdown:             {current_dd*100:.2f}%")
        days_underwater_current = underwater_series.iloc[-1]
        print(f"Days Since Peak:              {days_underwater_current} days")
    else:
        print("Current Status:               At or near peak value")
    
    print()
    
    # Drawdown periods analysis
    if drawdown_periods:
        durations = [period[2] for period in drawdown_periods]
        avg_duration = np.mean(durations)
        max_duration = max(durations)
        total_periods = len(drawdown_periods)
        
        # Calculate drawdown severity for each period
        severities = []
        for start_date, end_date, duration in drawdown_periods:
            period_dd = metrics['daily_drawdown'][start_date:end_date]
            min_dd = period_dd.min()
            severities.append(min_dd * 100)
        
        avg_severity = np.mean(severities)
        max_severity = min(severities)
        
        print("Drawdown Periods:")
        print(f"  Total Drawdown Periods:     {total_periods}")
        print(f"  Average Duration:           {avg_duration:.1f} days")
        print(f"  Longest Duration:           {max_duration} days")
        print(f"  Average Severity:           {avg_severity:.2f}%")
        print(f"  Most Severe:                {max_severity:.2f}%")
        
        # Recovery analysis
        total_underwater_days = underwater_series.sum()
        total_days = len(underwater_series)
        underwater_percentage = (total_underwater_days / total_days) * 100
        
        print()
        print("Recovery Analysis:")
        print(f"  Total Days Underwater:      {total_underwater_days} days")
        print(f"  Percentage Time Underwater: {underwater_percentage:.1f}%")
        
        # Recent drawdown periods (last 3)
        if len(drawdown_periods) > 0:
            print()
            print("Recent Drawdown Periods:")
            recent_periods = drawdown_periods[-3:] if len(drawdown_periods) >= 3 else drawdown_periods
            
            for i, (start_date, end_date, duration) in enumerate(recent_periods, 1):
                period_dd = metrics['daily_drawdown'][start_date:end_date]
                min_dd = period_dd.min() * 100
                print(f"  Period {i}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                print(f"            Duration: {duration} days, Max DD: {min_dd:.2f}%")
                
    else:
        print("Drawdown Periods:             No significant drawdown periods detected")
    
    # Risk assessment
    print()
    print("Risk Assessment:")
    if max_dd_pct < -0.05:  # Less than 5%
        print("  ✓ Low Risk: Maximum drawdown under 5%")
    elif max_dd_pct < -0.10:  # Less than 10%
        print("  ⚠ Moderate Risk: Maximum drawdown 5-10%")
    elif max_dd_pct < -0.20:  # Less than 20%
        print("  ⚠ High Risk: Maximum drawdown 10-20%")
    else:
        print("  ⚠ Very High Risk: Maximum drawdown over 20%")
    
    if drawdown_periods:
        if avg_duration < 10:
            print("  ✓ Quick Recovery: Average drawdown duration under 10 days")
        elif avg_duration < 30:
            print("  ⚠ Moderate Recovery: Average drawdown duration 10-30 days")
        else:
            print("  ⚠ Slow Recovery: Average drawdown duration over 30 days")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Portfolio Drawdown Analysis')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Drawdown Analysis Chart ({days_back} days)...")
    
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
        create_drawdown_chart(metrics, days_back, save_chart)
        
        print("\nChart generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
