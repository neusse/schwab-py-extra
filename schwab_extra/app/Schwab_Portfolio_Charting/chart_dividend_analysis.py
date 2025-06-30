"""
Dividend Analysis Chart - Standalone Application
Comprehensive dividend income analysis and yield calculations
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import argparse
import sys

# Import from the existing portfolio analyzer
try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, 
        fetch_market_data,
        fetch_dividends,
        CHART_FIGSIZE
    )
except ImportError:
    print("Error: Could not import portfolio analyzer functions")
    print("Make sure portfolio_analyzer_update_3.py is in the same directory")
    sys.exit(1)

def create_dividend_chart(dividends, positions, days_back, save_chart=False):
    """Create comprehensive dividend analysis chart."""
    plt.style.use('default')
    
    # Filter out zero dividends
    non_zero_dividends = {k: v for k, v in dividends.items() if v > 0}
    
    if not non_zero_dividends:
        print("No dividends found for the analysis period")
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE)
        ax.text(0.5, 0.5, f'No dividends received\nin the last {days_back} days', 
                ha='center', va='center', transform=ax.transAxes, 
                fontsize=16, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        ax.set_title(f'Dividend Analysis ({days_back} Days)', fontweight='bold', fontsize=14)
        ax.axis('off')
        
        if save_chart:
            filename = f'dividend_analysis_{days_back}days.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Chart saved as: {filename}")
        
        plt.show()
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_FIGSIZE[0] * 1.8, CHART_FIGSIZE[1] * 1.5))
    
    # Top Left: Dividend amounts by ticker
    tickers = list(non_zero_dividends.keys())
    amounts = list(non_zero_dividends.values())
    
    # Sort by amount for better visualization
    sorted_data = sorted(zip(tickers, amounts), key=lambda x: x[1], reverse=True)
    tickers_sorted, amounts_sorted = zip(*sorted_data)
    
    bars1 = ax1.bar(range(len(tickers_sorted)), amounts_sorted, color='green', alpha=0.7)
    ax1.set_title('Dividend Income by Ticker', fontweight='bold')
    ax1.set_ylabel('Dividend Amount ($)')
    ax1.set_xticks(range(len(tickers_sorted)))
    ax1.set_xticklabels(tickers_sorted, rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, amount in zip(bars1, amounts_sorted):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'${amount:.2f}', ha='center', va='bottom', fontsize=9)
    
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
    
    # Top Right: Dividend yield estimates and detailed analysis
    create_yield_analysis(ax2, non_zero_dividends, positions, days_back)
    
    # Bottom Left: Monthly dividend projection
    create_monthly_projection(ax3, non_zero_dividends, days_back)
    
    # Bottom Right: Dividend growth analysis
    create_dividend_growth_analysis(ax4, tickers, days_back)
    
    plt.suptitle(f'Dividend Analysis ({days_back} Days)', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    if save_chart:
        filename = f'dividend_analysis_{days_back}days.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as: {filename}")
    
    plt.show()
    
    # Print detailed dividend analysis
    print_dividend_analysis(non_zero_dividends, positions, tickers, days_back)

def create_yield_analysis(ax, dividends, positions, days_back):
    """Create dividend yield analysis"""
    tickers = list(dividends.keys())
    yields = []
    position_values = []
    
    # Get current prices for yield calculation
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            shares = positions.get(ticker, 0)
            position_value = shares * current_price
            
            # Annualize dividend and calculate yield
            annual_dividend = dividends[ticker] * (365 / days_back)
            dividend_yield = (annual_dividend / position_value) * 100 if position_value > 0 else 0
            
            yields.append(dividend_yield)
            position_values.append(position_value)
            
        except Exception as e:
            print(f"Error calculating yield for {ticker}: {e}")
            yields.append(0)
            position_values.append(0)
    
    # Create bubble chart - size represents position value
    if yields and any(y > 0 for y in yields):
        # Normalize bubble sizes
        max_position = max(position_values) if position_values else 1
        bubble_sizes = [(pv / max_position * 300) + 50 for pv in position_values]
        
        colors = ['green' if y > 3 else 'orange' if y > 1 else 'red' for y in yields]
        
        scatter = ax.scatter(range(len(tickers)), yields, s=bubble_sizes, 
                           c=colors, alpha=0.7, edgecolors='black')
        
        # Add ticker labels
        for i, (ticker, yield_val) in enumerate(zip(tickers, yields)):
            ax.annotate(ticker, (i, yield_val), xytext=(0, 10), 
                       textcoords='offset points', ha='center', fontsize=8)
        
        ax.set_title('Estimated Dividend Yields', fontweight='bold')
        ax.set_ylabel('Yield (%)')
        ax.set_xlabel('Holdings (Bubble size = Position value)')
        ax.grid(True, alpha=0.3)
        ax.set_xticks([])
        
        # Add yield benchmarks
        ax.axhline(y=3, color='green', linestyle=':', alpha=0.7, label='3% yield')
        ax.axhline(y=1, color='orange', linestyle=':', alpha=0.7, label='1% yield')
        ax.legend(fontsize='small')
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    else:
        ax.text(0.5, 0.5, 'Unable to calculate\nyield estimates', 
                ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Estimated Dividend Yields', fontweight='bold')

def create_monthly_projection(ax, dividends, days_back):
    """Create monthly dividend projection"""
    total_dividends = sum(dividends.values())
    
    # Project annualized dividends
    annual_projection = total_dividends * (365 / days_back)
    monthly_projection = annual_projection / 12
    quarterly_projection = annual_projection / 4
    
    # Create projection chart
    periods = ['Current\nPeriod', 'Monthly\nProjection', 'Quarterly\nProjection', 'Annual\nProjection']
    amounts = [total_dividends, monthly_projection, quarterly_projection, annual_projection]
    colors = ['blue', 'green', 'orange', 'red']
    
    bars = ax.bar(periods, amounts, color=colors, alpha=0.7)
    
    # Add value labels
    for bar, amount in zip(bars, amounts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.02,
                f'${amount:.2f}', ha='center', va='bottom', fontweight='bold')
    
    ax.set_title('Dividend Income Projections', fontweight='bold')
    ax.set_ylabel('Dividend Amount ($)')
    ax.grid(True, alpha=0.3, axis='y')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
    
    # Add annotation
    ax.text(0.02, 0.98, f'Based on {days_back}-day period', 
            transform=ax.transAxes, fontsize=9, va='top', 
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

def create_dividend_growth_analysis(ax, tickers, days_back):
    """Create dividend growth analysis"""
    growth_data = []
    
    # Get dividend history for growth analysis
    for ticker in tickers[:8]:  # Limit to avoid clutter
        try:
            stock = yf.Ticker(ticker)
            dividends_hist = stock.dividends
            
            if len(dividends_hist) >= 8:  # Need sufficient history
                # Get last 2 years of dividends
                recent_dividends = dividends_hist.tail(8)
                
                # Calculate year-over-year growth
                if len(recent_dividends) >= 4:
                    current_year = recent_dividends.tail(4).sum()
                    previous_year = recent_dividends.head(4).sum()
                    
                    if previous_year > 0:
                        growth_rate = ((current_year / previous_year) - 1) * 100
                        growth_data.append((ticker, growth_rate))
                        
        except Exception as e:
            continue
    
    if growth_data:
        # Sort by growth rate
        growth_data.sort(key=lambda x: x[1], reverse=True)
        tickers_growth, growth_rates = zip(*growth_data)
        
        colors = ['green' if gr > 0 else 'red' for gr in growth_rates]
        bars = ax.barh(range(len(tickers_growth)), growth_rates, color=colors, alpha=0.7)
        
        ax.set_yticks(range(len(tickers_growth)))
        ax.set_yticklabels(tickers_growth)
        ax.set_xlabel('Dividend Growth Rate (%)')
        ax.set_title('Dividend Growth Analysis\n(YoY Comparison)', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        
        # Add value labels
        for bar, rate in zip(bars, growth_rates):
            width = bar.get_width()
            ax.text(width + (abs(width) * 0.02 if width >= 0 else -abs(width) * 0.02), 
                   bar.get_y() + bar.get_height()/2.,
                   f'{rate:+.1f}%', ha='left' if width >= 0 else 'right', 
                   va='center', fontsize=9)
        
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:+.0f}%'))
    else:
        ax.text(0.5, 0.5, 'Insufficient dividend\nhistory for growth analysis', 
                ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Dividend Growth Analysis', fontweight='bold')

def print_dividend_analysis(dividends, positions, tickers, days_back):
    """Print comprehensive dividend analysis"""
    
    total_dividends = sum(dividends.values())
    annual_projection = total_dividends * (365 / days_back)
    
    print("\n" + "="*70)
    print("COMPREHENSIVE DIVIDEND ANALYSIS")
    print("="*70)
    print(f"Analysis Period:                  {days_back} days")
    print(f"Dividend-Paying Holdings:         {len(dividends)}")
    print()
    
    print("Dividend Income Summary:")
    print(f"  Total Dividends Received:       ${total_dividends:.2f}")
    print(f"  Monthly Projection:             ${annual_projection/12:.2f}")
    print(f"  Quarterly Projection:           ${annual_projection/4:.2f}")
    print(f"  Annual Projection:              ${annual_projection:.2f}")
    print()
    
    # Detailed breakdown by ticker
    print("Dividend Breakdown by Ticker:")
    print(f"{'Ticker':<8} {'Amount':<12} {'% of Total':<12} {'Shares':<10} {'Est. Yield':<10}")
    print("-" * 60)
    
    sorted_dividends = sorted(dividends.items(), key=lambda x: x[1], reverse=True)
    
    for ticker, amount in sorted_dividends:
        percentage = (amount / total_dividends) * 100
        shares = positions.get(ticker, 0)
        
        # Calculate estimated yield
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            position_value = shares * current_price
            annual_dividend = amount * (365 / days_back)
            est_yield = (annual_dividend / position_value) * 100 if position_value > 0 else 0
            yield_str = f"{est_yield:.2f}%"
        except:
            yield_str = "N/A"
        
        print(f"{ticker:<8} ${amount:<11.2f} {percentage:<11.1f}% {shares:<9.1f} {yield_str:<10}")
    
    # Portfolio dividend analysis
    print()
    print("Portfolio Dividend Metrics:")
    
    # Calculate portfolio dividend yield
    try:
        total_portfolio_value = 0
        for ticker, shares in positions.items():
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
                total_portfolio_value += shares * current_price
            except:
                continue
        
        if total_portfolio_value > 0:
            portfolio_yield = (annual_projection / total_portfolio_value) * 100
            print(f"  Portfolio Dividend Yield:       {portfolio_yield:.2f}%")
            
            # Dividend coverage (rough estimate)
            dividend_portion = (annual_projection / total_portfolio_value) * 100
            if dividend_portion > 0:
                print(f"  Dividend as % of Portfolio:     {dividend_portion:.2f}%")
        
    except Exception as e:
        print(f"  Portfolio Yield:                Unable to calculate")
    
    # Dividend frequency analysis
    print()
    print("Dividend Frequency Analysis:")
    
    monthly_payers = 0
    quarterly_payers = 0
    annual_payers = 0
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            div_history = stock.dividends.tail(12)  # Last year
            
            if len(div_history) >= 12:
                monthly_payers += 1
            elif len(div_history) >= 4:
                quarterly_payers += 1
            elif len(div_history) >= 1:
                annual_payers += 1
                
        except:
            continue
    
    print(f"  Monthly Payers:                 {monthly_payers}")
    print(f"  Quarterly Payers:               {quarterly_payers}")
    print(f"  Annual Payers:                  {annual_payers}")
    
    # Dividend sustainability assessment
    print()
    print("Dividend Assessment:")
    
    avg_yield = 0
    yield_count = 0
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            shares = positions.get(ticker, 0)
            position_value = shares * current_price
            annual_dividend = dividends[ticker] * (365 / days_back)
            est_yield = (annual_dividend / position_value) * 100 if position_value > 0 else 0
            
            if est_yield > 0:
                avg_yield += est_yield
                yield_count += 1
                
        except:
            continue
    
    if yield_count > 0:
        avg_yield = avg_yield / yield_count
        print(f"  Average Dividend Yield:         {avg_yield:.2f}%")
        
        if avg_yield > 4:
            print("  ✓ High dividend yield portfolio")
        elif avg_yield > 2:
            print("  ✓ Moderate dividend yield portfolio")
        else:
            print("  ⚠ Low dividend yield portfolio")
    
    if annual_projection > 1000:
        print("  ✓ Significant dividend income stream")
    elif annual_projection > 100:
        print("  ✓ Moderate dividend income stream")
    else:
        print("  ⚠ Minimal dividend income stream")

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Dividend Analysis Chart')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', type=str, default='0', help='Save chart (1 for yes, 0 for no)')
    
    args = parser.parse_args()
    days_back = args.days
    save_chart = args.save == '1'
    
    print(f"Loading Dividend Analysis Chart ({days_back} days)...")
    
    try:
        # Get portfolio positions
        positions = get_portfolio_positions()
        if not positions:
            print("Error: No positions found")
            return
        
        # Remove problematic tickers
        if 'SNSXX' in positions:
            del positions['SNSXX']
        
        print(f"Analyzing {len(positions)} positions for dividend income...")
        
        # Fetch dividends
        dividends = fetch_dividends(positions, days_back)
        
        # Create the chart
        create_dividend_chart(dividends, positions, days_back, save_chart)
        
        print("\nDividend analysis complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
