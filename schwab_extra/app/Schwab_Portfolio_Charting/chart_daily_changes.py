"""
Daily Changes & Moving Averages Chart - Standalone Application
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

def create_daily_change_chart(metrics, days_back, save_chart=False):
    """Create daily change chart with moving averages."""
    plt.style.use('default')
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(CHART_FIGSIZE[0], CHART_FIGSIZE[1] * 1.5))
    
    total_change = metrics['total_daily_change']
    ma_1week = metrics['ma_1week'] 
    ma_2week = metrics['ma_2week']
    
    # Top subplot - Daily changes as bars
    positive_changes = total_change[total_change >= 0]
    negative_changes = total_change[total_change < 0]
    
    ax1.bar(positive_changes.index, positive_changes, color='green', alpha=0.7, 
            label=f'Gains ({len(positive_changes)} days)', width=1)
    ax1.bar(negative_changes.index, negative_changes, color='red', alpha=0.7, 
            label=f'Losses ({len(negative_changes)} days)', width=1)
    
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax1.set_ylabel('Daily Change ($)', fontsize=12)
    ax1.set_title(f'Daily Portfolio Changes ({days_back} Days)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Format y-axis as currency
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Bottom subplot - Moving averages
    ax2.plot(ma_1week.index, ma_1week, color='blue', linewidth=2.5, 
             label='1 Week MA', alpha=0.8)
    ax2.plot(ma_2week.index, ma_2week, color='red', linewidth=2.5, 
             label='2 Week MA', alpha=0.8)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Moving Average ($)', fontsize=12)
    ax2.set_title('Moving Averages of Daily Changes', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Format y-axis as currency
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Rotate x-axis labels
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    if save_chart:
        filename = f'daily_changes_ma_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print analysis
    print_daily_change_analysis(metrics, days_back)

def print_daily_change_analysis(metrics, days_back):
    """Print detailed analysis of daily changes"""
    total_change = metrics['total_daily_change'].dropna()
    
    gain_days = (total_change > 0).sum()
    loss_days = (total_change < 0).sum()
    flat_days = (total_change == 0).sum()
    
    total_gains = total_change[total_change > 0].sum()
    total_losses = total_change[total_change < 0].sum()
    
    avg_daily_change = total_change.mean()
    avg_gain = total_change[total_change > 0].mean() if gain_days > 0 else 0
    avg_loss = total_change[total_change < 0].mean() if loss_days > 0 else 0
    
    # Volatility metrics
    daily_std = total_change.std()
    max_gain = total_change.max()
    max_loss = total_change.min()
    
    print("\n" + "="*60)
    print("DAILY CHANGES ANALYSIS")
    print("="*60)
    print(f"Analysis Period:              {days_back} days")
    print(f"Trading Days with Data:       {len(total_change)}")
    print()
    print("Day Distribution:")
    print(f"  Gain Days:                  {gain_days} ({gain_days/len(total_change)*100:.1f}%)")
    print(f"  Loss Days:                  {loss_days} ({loss_days/len(total_change)*100:.1f}%)")
    print(f"  Flat Days:                  {flat_days} ({flat_days/len(total_change)*100:.1f}%)")
    print()
    print("Financial Metrics:")
    print(f"  Total Gains:                ${total_gains:,.2f}")
    print(f"  Total Losses:               ${total_losses:,.2f}")
    print(f"  Net Change:                 ${total_gains + total_losses:+,.2f}")
    print()
    print("Average Daily Metrics:")
    print(f"  Average Daily Change:       ${avg_daily_change:+,.2f}")
    print(f"  Average Gain (gain days):   ${avg_gain:,.2f}")
    print(f"  Average Loss (loss days):   ${avg_loss:,.2f}")
    print()
    print("Volatility Metrics:")
    print(f"  Daily Standard Deviation:   ${daily_std:,.2f}")
    print(f"  Largest Single Gain:        ${max_gain:,.2f}")
    print(f"  Largest Single Loss:        ${max_loss:,.2f}")
    print()
    
    # Win/Loss ratios
    if loss_days > 0:
        win_loss_ratio = gain_days / loss_days
        print(f"Win/Loss Ratio:               {win_loss_ratio:.2f}")
        
    if avg_loss != 0:
        gain_loss_magnitude = abs(avg_gain / avg_loss)
        print(f"Avg Gain/Loss Magnitude:      {gain_loss_magnitude:.2f}")
        
    # Moving average analysis
    ma_1week = metrics['ma_1week'].dropna()
    ma_2week = metrics['ma_2week'].dropna()
    
    if len(ma_1week) > 0 and len(ma_2week) > 0:
        current_1w_ma = ma_1week.iloc[-1]
        current_2w_ma = ma_2week.iloc[-1]
        
        print()
        print("Current Moving Averages:")
        print(f"  1-Week MA:                  ${current_1w_ma:+,.2f}")
        print(f"  2-Week MA:                  ${current_2w_ma:+,.2f}")
        
        if current_1w_ma > current_2w_ma:
            print("  Trend Indication:           Short-term momentum is positive")
        elif current_1w_ma < current_2w_ma:
            print("  Trend Indication:           Short-term momentum is negative")
        else:
            print("  Trend Indication:           Neutral momentum")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Daily Changes & Moving Averages Chart')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Daily Changes Chart ({days_back} days)...")
    
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
        create_daily_change_chart(metrics, days_back, save_chart)
        
        print("\nChart generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
