# ==============================================================================
# CHART_GAINLOSS_ANALYSIS.PY
# ==============================================================================
"""
Gain/Loss Analysis Chart - Standalone Application
Can be launched independently or from the main chart manager
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import argparse
import sys

try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, fetch_market_data, 
        calculate_portfolio_metrics, CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    sys.exit(1)

def create_gainloss_chart(metrics, days_back, save_chart=False):
    """Create gain/loss analysis chart."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_FIGSIZE[0] * 1.5, CHART_FIGSIZE[1] * 1.5))
    
    total_change = metrics['total_daily_change'].dropna()
    
    # Gain/Loss distribution
    gains = total_change[total_change > 0]
    losses = total_change[total_change < 0]
    
    # Top Left: Daily changes histogram
    ax1.hist([gains, losses], bins=20, color=['green', 'red'], alpha=0.7, label=['Gains', 'Losses'])
    ax1.set_title('Distribution of Daily Changes')
    ax1.set_xlabel('Daily Change ($)')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Top Right: Win/Loss streaks
    # Calculate streaks
    streaks = []
    current_streak = 0
    streak_type = None
    
    for change in total_change:
        if change > 0:  # Gain
            if streak_type == 'gain':
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(('loss', current_streak))
                current_streak = 1
                streak_type = 'gain'
        elif change < 0:  # Loss
            if streak_type == 'loss':
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(('gain', current_streak))
                current_streak = 1
                streak_type = 'loss'
    
    # Add final streak
    if current_streak > 0:
        streaks.append((streak_type, current_streak))
    
    gain_streaks = [s[1] for s in streaks if s[0] == 'gain']
    loss_streaks = [s[1] for s in streaks if s[0] == 'loss']
    
    ax2.hist([gain_streaks, loss_streaks], bins=10, color=['green', 'red'], 
            alpha=0.7, label=['Gain Streaks', 'Loss Streaks'])
    ax2.set_title('Win/Loss Streak Distribution')
    ax2.set_xlabel('Streak Length (Days)')
    ax2.set_ylabel('Frequency')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Bottom Left: Cumulative gain/loss
    cumulative_gains = gains.cumsum()
    cumulative_losses = losses.cumsum()
    
    ax3.plot(cumulative_gains.index, cumulative_gains, color='green', label='Cumulative Gains', linewidth=2)
    ax3.plot(cumulative_losses.index, cumulative_losses, color='red', label='Cumulative Losses', linewidth=2)
    ax3.set_title('Cumulative Gains vs Losses')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Cumulative Amount ($)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Bottom Right: Monthly gain/loss summary
    monthly_data = total_change.resample('M').agg({
        'sum': 'sum',
        'count': 'count',
        'mean': 'mean'
    })
    
    monthly_gains = monthly_data[monthly_data['sum'] > 0]['sum']
    monthly_losses = monthly_data[monthly_data['sum'] < 0]['sum']
    
    months = monthly_data.index.strftime('%b')
    ax4.bar(range(len(monthly_data)), monthly_data['sum'], 
           color=['green' if x > 0 else 'red' for x in monthly_data['sum']], alpha=0.7)
    ax4.set_title('Monthly Performance')
    ax4.set_xlabel('Month')
    ax4.set_ylabel('Monthly Change ($)')
    ax4.set_xticks(range(len(monthly_data)))
    ax4.set_xticklabels(months, rotation=45)
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(f'Gain/Loss Analysis ({days_back} Days)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    if save_chart:
        plt.savefig(f'gainloss_analysis_{days_back}days.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Gain/Loss Analysis Chart')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    
    try:
        positions = get_portfolio_positions()
        if 'SNSXX' in positions: del positions['SNSXX']
        
        data = fetch_market_data(list(positions.keys()), args.days)
        metrics = calculate_portfolio_metrics(data[list(positions.keys())], positions)
        
        create_gainloss_chart(metrics, args.days, args.save == '1')
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()


# ==============================================================================
# CHART_RISK_DASHBOARD.PY
# ==============================================================================
"""
Risk Metrics Dashboard - Standalone Application
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import argparse
import sys

try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, fetch_market_data, 
        calculate_portfolio_metrics, CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    sys.exit(1)

def create_risk_dashboard(metrics, days_back, save_chart=False):
    """Create comprehensive risk metrics dashboard."""
    fig = plt.figure(figsize=(CHART_FIGSIZE[0] * 2, CHART_FIGSIZE[1] * 2))
    
    # Create a 3x3 grid of subplots
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # VaR calculation (Value at Risk)
    daily_changes = metrics['total_daily_change'].dropna()
    var_95 = np.percentile(daily_changes, 5)  # 95% VaR
    var_99 = np.percentile(daily_changes, 1)  # 99% VaR
    
    # Subplot 1: VaR histogram
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(daily_changes, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.axvline(var_95, color='orange', linestyle='--', label=f'95% VaR: ${var_95:.0f}')
    ax1.axvline(var_99, color='red', linestyle='--', label=f'99% VaR: ${var_99:.0f}')
    ax1.set_title('Value at Risk Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add more risk metrics subplots here...
    # This is a template - expand with additional risk metrics
    
    plt.suptitle(f'Risk Metrics Dashboard ({days_back} Days)', fontsize=16, fontweight='bold')
    
    if save_chart:
        plt.savefig(f'risk_dashboard_{days_back}days.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Risk Metrics Dashboard')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    
    try:
        positions = get_portfolio_positions()
        if 'SNSXX' in positions: del positions['SNSXX']
        
        data = fetch_market_data(list(positions.keys()), args.days)
        metrics = calculate_portfolio_metrics(data[list(positions.keys())], positions)
        
        create_risk_dashboard(metrics, args.days, args.save == '1')
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()


# ==============================================================================
# CHART_DIVIDEND_ANALYSIS.PY
# ==============================================================================
"""
Dividend Analysis Chart - Standalone Application
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import argparse
import sys

try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, fetch_dividends, CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    sys.exit(1)

def create_dividend_chart(dividends, positions, days_back, save_chart=False):
    """Create dividend analysis chart."""
    
    # Filter out zero dividends
    non_zero_dividends = {k: v for k, v in dividends.items() if v > 0}
    
    if not non_zero_dividends:
        print("No dividends found for the analysis period")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_FIGSIZE[0] * 1.5, CHART_FIGSIZE[1] * 1.5))
    
    # Top Left: Dividend amounts by ticker
    tickers = list(non_zero_dividends.keys())
    amounts = list(non_zero_dividends.values())
    
    ax1.bar(tickers, amounts, color='green', alpha=0.7)
    ax1.set_title('Dividend Income by Ticker')
    ax1.set_ylabel('Dividend Amount ($)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Top Right: Dividend yield estimate
    yields = []
    for ticker in tickers:
        if ticker in positions:
            # Rough yield estimate (annual projection)
            annual_dividend = non_zero_dividends[ticker] * (365 / days_back)
            position_value = positions[ticker] * 100  # Rough estimate, need actual price
            estimated_yield = (annual_dividend / position_value) * 100 if position_value > 0 else 0
            yields.append(estimated_yield)
        else:
            yields.append(0)
    
    ax2.bar(tickers, yields, color='blue', alpha=0.7)
    ax2.set_title('Estimated Dividend Yield')
    ax2.set_ylabel('Yield (%)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # Add additional dividend analysis subplots...
    
    plt.suptitle(f'Dividend Analysis ({days_back} Days)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    if save_chart:
        plt.savefig(f'dividend_analysis_{days_back}days.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Dividend Analysis Chart')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    
    try:
        positions = get_portfolio_positions()
        if 'SNSXX' in positions: del positions['SNSXX']
        
        dividends = fetch_dividends(positions, args.days)
        
        create_dividend_chart(dividends, positions, args.days, args.save == '1')
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
