"""
Gain/Loss Analysis Chart - Standalone Application
Analyzes daily trading patterns, streaks, and win/loss statistics
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

def create_gainloss_chart(metrics, days_back, save_chart=False):
    """Create comprehensive gain/loss analysis chart."""
    plt.style.use('default')
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_FIGSIZE[0] * 1.8, CHART_FIGSIZE[1] * 1.5))
    
    total_change = metrics['total_daily_change'].dropna()
    
    # Separate gains and losses
    gains = total_change[total_change > 0]
    losses = total_change[total_change < 0]
    flat_days = total_change[total_change == 0]
    
    # Top Left: Daily changes histogram with statistics
    bins = 25
    ax1.hist(losses, bins=bins//2, alpha=0.7, color='red', label=f'Losses ({len(losses)} days)', density=True)
    ax1.hist(gains, bins=bins//2, alpha=0.7, color='green', label=f'Gains ({len(gains)} days)', density=True)
    
    # Add statistical lines
    if len(gains) > 0:
        ax1.axvline(gains.mean(), color='darkgreen', linestyle='--', alpha=0.8, label=f'Avg Gain: ${gains.mean():.0f}')
    if len(losses) > 0:
        ax1.axvline(losses.mean(), color='darkred', linestyle='--', alpha=0.8, label=f'Avg Loss: ${losses.mean():.0f}')
    
    ax1.set_title('Distribution of Daily Changes', fontweight='bold')
    ax1.set_xlabel('Daily Change ($)')
    ax1.set_ylabel('Density')
    ax1.legend(fontsize='small')
    ax1.grid(True, alpha=0.3)
    
    # Top Right: Win/Loss streaks analysis
    streaks = calculate_streaks(total_change)
    gain_streaks = [s[1] for s in streaks if s[0] == 'gain']
    loss_streaks = [s[1] for s in streaks if s[0] == 'loss']
    
    # Create streak histogram
    max_streak_len = max(max(gain_streaks, default=0), max(loss_streaks, default=0))
    bins = range(1, max_streak_len + 2)
    
    ax2.hist([gain_streaks, loss_streaks], bins=bins, color=['green', 'red'], 
            alpha=0.7, label=[f'Win Streaks (max: {max(gain_streaks, default=0)})', 
                             f'Loss Streaks (max: {max(loss_streaks, default=0)})'])
    
    ax2.set_title('Win/Loss Streak Distribution', fontweight='bold')
    ax2.set_xlabel('Streak Length (Days)')
    ax2.set_ylabel('Frequency')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Bottom Left: Cumulative gain/loss over time
    cumulative_gains = gains.reindex(total_change.index, fill_value=0).cumsum()
    cumulative_losses = losses.reindex(total_change.index, fill_value=0).cumsum()
    net_cumulative = total_change.cumsum()
    
    ax3.plot(cumulative_gains.index, cumulative_gains, color='green', 
             label=f'Cumulative Gains: ${cumulative_gains.iloc[-1]:,.0f}', linewidth=2.5, alpha=0.8)
    ax3.plot(cumulative_losses.index, cumulative_losses, color='red', 
             label=f'Cumulative Losses: ${cumulative_losses.iloc[-1]:,.0f}', linewidth=2.5, alpha=0.8)
    ax3.plot(net_cumulative.index, net_cumulative, color='blue', 
             label=f'Net: ${net_cumulative.iloc[-1]:+,.0f}', linewidth=3, alpha=0.9)
    
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    ax3.set_title('Cumulative Gains vs Losses', fontweight='bold')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Cumulative Amount ($)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Bottom Right: Monthly performance summary
    monthly_data = total_change.resample('M').agg({
        'sum': lambda x: x.sum(),
        'count': lambda x: len(x),
        'positive': lambda x: (x > 0).sum(),
        'negative': lambda x: (x < 0).sum()
    })
    
    # Calculate win rate for each month
    monthly_data['win_rate'] = monthly_data['positive'] / monthly_data['count'] * 100
    
    months = monthly_data.index.strftime('%b %y')
    colors = ['green' if x > 0 else 'red' for x in monthly_data['sum']]
    
    bars = ax4.bar(range(len(monthly_data)), monthly_data['sum'], color=colors, alpha=0.7)
    
    # Add win rate as text on bars
    for i, (bar, win_rate) in enumerate(zip(bars, monthly_data['win_rate'])):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + (abs(height) * 0.02 if height >= 0 else -abs(height) * 0.1),
                f'{win_rate:.0f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
    
    ax4.set_title('Monthly Performance & Win Rate', fontweight='bold')
    ax4.set_xlabel('Month')
    ax4.set_ylabel('Monthly Change ($)')
    ax4.set_xticks(range(len(monthly_data)))
    ax4.set_xticklabels(months, rotation=45)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Format x-axes
    for ax in [ax1, ax3]:
        if hasattr(ax, 'xaxis'):
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.suptitle(f'Gain/Loss Analysis ({days_back} Days)', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    if save_chart:
        filename = f'gainloss_analysis_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print detailed analysis
    print_gainloss_analysis(total_change, streaks, monthly_data, days_back)

def calculate_streaks(daily_changes):
    """Calculate win/loss streaks from daily changes"""
    streaks = []
    current_streak = 0
    streak_type = None
    
    for change in daily_changes:
        if change > 0:  # Gain
            if streak_type == 'gain':
                current_streak += 1
            else:
                if current_streak > 0 and streak_type is not None:
                    streaks.append((streak_type, current_streak))
                current_streak = 1
                streak_type = 'gain'
        elif change < 0:  # Loss
            if streak_type == 'loss':
                current_streak += 1
            else:
                if current_streak > 0 and streak_type is not None:
                    streaks.append((streak_type, current_streak))
                current_streak = 1
                streak_type = 'loss'
        # Flat days (change == 0) end any current streak
        else:
            if current_streak > 0 and streak_type is not None:
                streaks.append((streak_type, current_streak))
            current_streak = 0
            streak_type = None
    
    # Add final streak if it exists
    if current_streak > 0 and streak_type is not None:
        streaks.append((streak_type, current_streak))
    
    return streaks

def print_gainloss_analysis(daily_changes, streaks, monthly_data, days_back):
    """Print detailed gain/loss analysis"""
    
    gains = daily_changes[daily_changes > 0]
    losses = daily_changes[daily_changes < 0]
    flat_days = daily_changes[daily_changes == 0]
    
    total_trading_days = len(daily_changes)
    gain_days = len(gains)
    loss_days = len(losses)
    flat_days_count = len(flat_days)
    
    # Basic statistics
    total_gains = gains.sum()
    total_losses = losses.sum()
    net_change = total_gains + total_losses
    
    avg_daily_change = daily_changes.mean()
    avg_gain = gains.mean() if len(gains) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0
    
    # Streak analysis
    gain_streaks = [s[1] for s in streaks if s[0] == 'gain']
    loss_streaks = [s[1] for s in streaks if s[0] == 'loss']
    
    max_gain_streak = max(gain_streaks) if gain_streaks else 0
    max_loss_streak = max(loss_streaks) if loss_streaks else 0
    avg_gain_streak = np.mean(gain_streaks) if gain_streaks else 0
    avg_loss_streak = np.mean(loss_streaks) if loss_streaks else 0
    
    # Risk metrics
    daily_volatility = daily_changes.std()
    downside_deviation = losses.std() if len(losses) > 0 else 0
    
    # Largest single moves
    largest_gain = gains.max() if len(gains) > 0 else 0
    largest_loss = losses.min() if len(losses) > 0 else 0
    
    print("\n" + "="*70)
    print("COMPREHENSIVE GAIN/LOSS ANALYSIS")
    print("="*70)
    print(f"Analysis Period:                  {days_back} days")
    print(f"Total Trading Days:               {total_trading_days}")
    print()
    
    print("Daily Distribution:")
    print(f"  Gain Days:                      {gain_days} ({gain_days/total_trading_days*100:.1f}%)")
    print(f"  Loss Days:                      {loss_days} ({loss_days/total_trading_days*100:.1f}%)")
    print(f"  Flat Days:                      {flat_days_count} ({flat_days_count/total_trading_days*100:.1f}%)")
    print()
    
    print("Financial Performance:")
    print(f"  Total Gains:                    ${total_gains:,.2f}")
    print(f"  Total Losses:                   ${total_losses:,.2f}")
    print(f"  Net Change:                     ${net_change:+,.2f}")
    print(f"  Average Daily Change:           ${avg_daily_change:+,.2f}")
    print()
    
    print("Average Performance:")
    print(f"  Average Gain (gain days):       ${avg_gain:,.2f}")
    print(f"  Average Loss (loss days):       ${avg_loss:,.2f}")
    
    if avg_loss != 0:
        gain_loss_ratio = abs(avg_gain / avg_loss)
        print(f"  Gain/Loss Ratio:                {gain_loss_ratio:.2f}")
    
    print()
    print("Extremes:")
    print(f"  Largest Single Gain:            ${largest_gain:,.2f}")
    print(f"  Largest Single Loss:            ${largest_loss:,.2f}")
    print()
    
    print("Streak Analysis:")
    print(f"  Total Streaks:                  {len(streaks)}")
    print(f"  Gain Streaks:                   {len(gain_streaks)}")
    print(f"  Loss Streaks:                   {len(loss_streaks)}")
    print(f"  Max Gain Streak:                {max_gain_streak} days")
    print(f"  Max Loss Streak:                {max_loss_streak} days")
    print(f"  Avg Gain Streak:                {avg_gain_streak:.1f} days")
    print(f"  Avg Loss Streak:                {avg_loss_streak:.1f} days")
    print()
    
    print("Risk Metrics:")
    print(f"  Daily Volatility:               ${daily_volatility:,.2f}")
    print(f"  Downside Deviation:             ${downside_deviation:,.2f}")
    
    if loss_days > 0:
        win_rate = gain_days / total_trading_days * 100
        print(f"  Win Rate:                       {win_rate:.1f}%")
        
        # Kelly Criterion approximation
        if avg_loss != 0:
            win_prob = gain_days / total_trading_days
            lose_prob = loss_days / total_trading_days
            kelly_pct = (win_prob * abs(avg_gain) - lose_prob * abs(avg_loss)) / abs(avg_gain) * 100
            print(f"  Kelly Criterion:                {kelly_pct:.1f}%")
    
    print()
    print("Monthly Performance Summary:")
    if len(monthly_data) > 0:
        winning_months = (monthly_data['sum'] > 0).sum()
        total_months = len(monthly_data)
        monthly_win_rate = winning_months / total_months * 100
        
        best_month = monthly_data['sum'].max()
        worst_month = monthly_data['sum'].min()
        avg_monthly_return = monthly_data['sum'].mean()
        
        print(f"  Winning Months:                 {winning_months}/{total_months} ({monthly_win_rate:.1f}%)")
        print(f"  Best Month:                     ${best_month:+,.2f}")
        print(f"  Worst Month:                    ${worst_month:+,.2f}")
        print(f"  Average Monthly Return:         ${avg_monthly_return:+,.2f}")
        
        # Recent trend (last 3 months)
        if len(monthly_data) >= 3:
            recent_performance = monthly_data['sum'].tail(3).sum()
            recent_win_rate = (monthly_data['sum'].tail(3) > 0).sum() / 3 * 100
            print(f"  Last 3 Months Performance:     ${recent_performance:+,.2f}")
            print(f"  Last 3 Months Win Rate:        {recent_win_rate:.1f}%")
    
    # Performance assessment
    print()
    print("Performance Assessment:")
    
    if gain_days > loss_days:
        print("  ✓ More gain days than loss days")
    else:
        print("  ⚠ More loss days than gain days")
    
    if abs(total_gains) > abs(total_losses):
        print("  ✓ Total gains exceed total losses")
    else:
        print("  ⚠ Total losses exceed total gains")
    
    if avg_gain > abs(avg_loss):
        print("  ✓ Average gains larger than average losses")
    else:
        print("  ⚠ Average losses larger than average gains")
    
    if max_gain_streak >= max_loss_streak:
        print("  ✓ Longest winning streak ≥ longest losing streak")
    else:
        print("  ⚠ Longest losing streak > longest winning streak")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Gain/Loss Analysis Chart')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Gain/Loss Analysis Chart ({days_back} days)...")
    
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
        create_gainloss_chart(metrics, days_back, save_chart)
        
        print("\nChart generation complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
