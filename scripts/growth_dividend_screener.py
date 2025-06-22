import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import warnings
import requests
from bs4 import BeautifulSoup
import json



warnings.filterwarnings('ignore')

def screen_growth_dividend_stocks(symbols: List[str], 
                                 min_dividend_yield: float = 2.0,
                                 min_revenue_growth: float = 8.0,
                                 min_earnings_growth: float = 10.0,
                                 max_payout_ratio: float = 60.0) -> pd.DataFrame:
    """
    Screen stocks for both growth and dividend characteristics.
    
    Args:
        symbols: List of stock symbols to screen
        min_dividend_yield: Minimum dividend yield % (default 2.0%)
        min_revenue_growth: Minimum revenue growth % (default 8.0%)
        min_earnings_growth: Minimum earnings growth % (default 10.0%)
        max_payout_ratio: Maximum payout ratio % (default 60.0%)
    
    Returns:
        DataFrame with stocks meeting criteria, sorted by combined score
    """
    
    results = []
    
    print(f"Screening {len(symbols)} stocks for growth + dividend characteristics...")
    print(f"Criteria: Div Yield ≥{min_dividend_yield}%, Revenue Growth ≥{min_revenue_growth}%, "
          f"Earnings Growth ≥{min_earnings_growth}%, Payout Ratio ≤{max_payout_ratio}%")
    print("-" * 80)
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get financial metrics
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
            earnings_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
            payout_ratio = info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0
            
            # Additional useful metrics
            pe_ratio = info.get('trailingPE', 0)
            forward_pe = info.get('forwardPE', 0)
            peg_ratio = info.get('pegRatio', 0)
            market_cap = info.get('marketCap', 0)
            company_name = info.get('longName', symbol)
            sector = info.get('sector', 'Unknown')
            
            # if payout_ratio and 0 < payout_ratio <= max_payout_ratio:
            #     payout_ratio_valid = True
            # else:
            #     payout_ratio_valid = False

            # Get payout ratio from earnings (default method)
            raw_payout_ratio = info.get('payoutRatio')
            payout_ratio = raw_payout_ratio * 100 if raw_payout_ratio else None

            # Alternative FCF payout ratio
            free_cashflow = info.get('freeCashflow')
            dividends_paid = info.get('dividendsPaid')

            fcf_payout_ratio = None
            if free_cashflow and dividends_paid and free_cashflow > 0:
                fcf_payout_ratio = abs(dividends_paid / free_cashflow) * 100

            # Use FCF payout if EPS payout is missing or zero
            final_payout_ratio = None
            if payout_ratio and payout_ratio > 0:
                final_payout_ratio = payout_ratio
            elif fcf_payout_ratio:
                final_payout_ratio = fcf_payout_ratio

            # Validate final payout ratio
            payout_ratio_valid = final_payout_ratio is not None and 0 < final_payout_ratio <= max_payout_ratio




            # Check if meets criteria
            meets_criteria = (
                dividend_yield >= min_dividend_yield and
                revenue_growth >= min_revenue_growth and
                earnings_growth >= min_earnings_growth and
                payout_ratio_valid #0 < payout_ratio <= max_payout_ratio
            )
            
            # Calculate a combined score (you can adjust weights)
            growth_score = (revenue_growth + earnings_growth) / 2
            dividend_score = dividend_yield * 2  # Give dividend some extra weight
            sustainability_score = max(0, 100 - payout_ratio)  # Lower payout ratio = more sustainable
            
            combined_score = (growth_score * 0.4 + dividend_score * 0.3 + sustainability_score * 0.3)
            
            results.append({
                'Symbol': symbol,
                'Company': company_name[:30],  # Truncate long names
                'Sector': sector,
                'Dividend_Yield_%': round(dividend_yield, 2),
                'Revenue_Growth_%': round(revenue_growth, 2),
                'Earnings_Growth_%': round(earnings_growth, 2),
                #'Payout_Ratio_%': round(payout_ratio, 2),
                'Payout_Ratio_%': round(final_payout_ratio, 2) if final_payout_ratio else None,

                'PE_Ratio': round(pe_ratio, 2) if pe_ratio else 0,
                'Forward_PE': round(forward_pe, 2) if forward_pe else 0,
                'PEG_Ratio': round(peg_ratio, 2) if peg_ratio else 0,
                'Market_Cap_B': round(market_cap / 1e9, 1) if market_cap else 0,
                'Meets_Criteria': meets_criteria,
                'Combined_Score': round(combined_score, 2),
                'Used_FCF_Payout': fcf_payout_ratio is not None and (not payout_ratio or payout_ratio <= 0),

            })
            
            status = "✓ PASS" if meets_criteria else "✗ fail"
            if meets_criteria:
                print(f"{symbol:6s} {status:8s} | Div: {dividend_yield:5.1f}% | Rev: {revenue_growth:6.1f}% | "
                    f"EPS: {earnings_growth:6.1f}% | Payout: {payout_ratio:5.1f}%")
            
        except Exception as e:
            print(f"{symbol:6s} ERROR   | Could not retrieve data: {str(e)[:50]}")
            continue
    
    # Convert to DataFrame and sort by combined score
    df = pd.DataFrame(results)
    
    if df.empty:
        print("\nNo stocks found!")
        return df
    
    # Sort by combined score (highest first)
    df = df.sort_values('Combined_Score', ascending=False)
    
    # Show summary
    passing_stocks = df[df['Meets_Criteria'] == True]
    print(f"\n{'='*80}")
    print(f"SUMMARY: {len(passing_stocks)} out of {len(symbols)} stocks meet all criteria")
    print(f"{'='*80}")
    
    return df

def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})
    tickers = [row.find("td").text.strip() for row in table.find_all("tr")[1:]]
    return tickers


def analyze_dividend_growth_trends(symbol: str, years: int = 5) -> Dict:
    """
    Analyze dividend growth trends for a specific stock.
    Handles partial year data properly.
    """
    try:
        ticker = yf.Ticker(symbol)
        dividends = ticker.dividends
        
        if dividends.empty:
            return {'error': 'No dividend history'}
        
        # Get annual dividend totals
        annual_dividends = dividends.groupby(dividends.index.year).sum()
        
        if len(annual_dividends) < 2:
            return {'error': 'Insufficient dividend history'}
        
        # Handle partial current year - exclude if less than 10 months of data
        current_year = annual_dividends.index[-1]
        current_month = pd.Timestamp.now().month
        
        # If we're not near year-end and current year looks incomplete, exclude it
        if current_month < 11:  # Before November
            # Check if current year dividend is significantly lower than previous year
            if len(annual_dividends) > 1:
                current_div = annual_dividends.iloc[-1]
                previous_div = annual_dividends.iloc[-2]
                
                # If current year is less than 70% of previous year, likely incomplete
                if current_div < (previous_div * 0.7):
                    annual_dividends = annual_dividends.iloc[:-1]  # Exclude partial year
                    print(f"Note: Excluding partial {current_year} data (${current_div:.2f} vs ${previous_div:.2f} in previous year)")
        
        if len(annual_dividends) < 2:
            return {'error': 'Insufficient complete year data'}
        
        # Calculate year-over-year growth rates
        growth_rates = annual_dividends.pct_change().dropna() * 100
        
        recent_years = annual_dividends.tail(min(years, len(annual_dividends)))
        avg_growth = growth_rates.tail(min(years-1, len(growth_rates))).mean()
        
        # Count consecutive increases (looking at complete years only)
        consecutive_increases = 0
        for i in range(len(growth_rates)-1, -1, -1):
            if growth_rates.iloc[i] > 0:
                consecutive_increases += 1
            else:
                break
        
        return {
            'symbol': symbol,
            'latest_annual_dividend': annual_dividends.iloc[-1],
            'dividend_growth_avg_%': round(avg_growth, 2),
            'years_of_positive_growth': len([x for x in growth_rates if x > 0]),
            'consecutive_increases': consecutive_increases,
            'recent_annual_dividends': recent_years.to_dict(),
            'annual_growth_rates_%': {year: round(rate, 2) for year, rate in growth_rates.items()}
        }
        
    except Exception as e:
        return {'error': str(e)}

"""
Re-run your screener with a payout ratio cap at ~80–100%.

Add a Free Cash Flow Payout Ratio if possible — much more reliable.

Look for forward EPS and whether the dividend is covered going forward.
"""



# Example usage
if __name__ == "__main__":
    # Screen a sample of large-cap stocks
    large_cap_stocks = get_sp500_symbols()
    
    # Run the screening
    results = screen_growth_dividend_stocks(
        symbols=large_cap_stocks,
        min_dividend_yield=1.5,      # Lower threshold to find more candidates
        min_revenue_growth=5.0,      # Reasonable growth expectation
        min_earnings_growth=8.0,     # Good earnings growth
        max_payout_ratio=70.0        # Sustainable payout
    )
    
    # Display top candidates
    if not results.empty:
        print("\nTOP GROWTH + DIVIDEND CANDIDATES:")
        print("-" * 100)
        top_candidates = results[results['Meets_Criteria'] == True].head(10)
        
        # Format the output nicely
        for idx, row in top_candidates.iterrows():
            print(f"{row['Symbol']:6s} | {row['Company']:25s} | "
                  f"Div: {row['Dividend_Yield_%']:4.1f}% | "
                  f"Growth: {row['Revenue_Growth_%']:5.1f}%/{row['Earnings_Growth_%']:5.1f}% | "
                  f"Score: {row['Combined_Score']:5.1f}")
        
        # Analyze dividend growth for top candidate
        if len(top_candidates) > 0:
            top_symbol = top_candidates.iloc[0]['Symbol']
            print(f"\nDIVIDEND GROWTH ANALYSIS FOR {top_symbol}:")
            div_analysis = analyze_dividend_growth_trends(top_symbol)
            print(json.dumps(div_analysis,indent=4))
