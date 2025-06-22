#!/usr/bin/env python3
"""
Daily Driver Dividend Income Screener
Production-ready dividend screening with multiple strategies
Max 250 candidates per yfinance screener - combines multiple sources
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, date
import argparse
import sys
import time
import os

def correct_dividend_format(raw_yield):
    """Fix yfinance dividend yield format issues"""
    if not raw_yield or raw_yield == 0:
        return 0
    
    if raw_yield > 50:  # Likely basis points or wrong format
        return raw_yield / 100
    elif raw_yield > 1:  # Already percentage
        return raw_yield  
    else:  # Decimal format
        return raw_yield * 100

def multi_source_dividend_discovery(strategy='balanced'):
    """
    Discover dividend candidates from multiple yfinance screeners
    Maximizes the 250 candidate limit by using different sources
    """
    print(f"🔍 MULTI-SOURCE DIVIDEND DISCOVERY - {strategy.upper()} STRATEGY")
    print("=" * 70)
    
    all_candidates = []
    screener_configs = get_strategy_config(strategy)
    
    for screener_name, config in screener_configs.items():
        print(f"\n📊 Fetching from {screener_name}...")
        try:
            response = yf.screen(screener_name, count=config['count'])
            
            if response and 'quotes' in response:
                quotes = response['quotes']
                print(f"✅ Retrieved {len(quotes)} candidates")
                
                batch_candidates = []
                for quote in quotes:
                    symbol = quote.get('symbol', '')
                    raw_dividend_yield = quote.get('dividendYield', 0)
                    
                    if raw_dividend_yield and raw_dividend_yield > 0:
                        corrected_yield = correct_dividend_format(raw_dividend_yield)
                        
                        # Apply strategy-specific yield filters
                        if config['min_yield'] <= corrected_yield <= config['max_yield']:
                            candidate = {
                                'symbol': symbol,
                                'dividend_yield': corrected_yield,
                                'price': quote.get('regularMarketPrice', 0),
                                'market_cap': quote.get('marketCap', 0),
                                'market_cap_billions': quote.get('marketCap', 0) / 1e9 if quote.get('marketCap') else 0,
                                'pe_ratio': quote.get('trailingPE', 0),
                                'source': screener_name,
                                'strategy': strategy
                            }
                            batch_candidates.append(candidate)
                
                print(f"🎯 Found {len(batch_candidates)} dividend candidates from {screener_name}")
                all_candidates.extend(batch_candidates)
                
            else:
                print(f"❌ No data from {screener_name}")
                
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error with {screener_name}: {e}")
            continue
    
    # Remove duplicates, keeping best yield for each symbol
    unique_candidates = {}
    for candidate in all_candidates:
        symbol = candidate['symbol']
        if symbol not in unique_candidates or candidate['dividend_yield'] > unique_candidates[symbol]['dividend_yield']:
            unique_candidates[symbol] = candidate
    
    final_candidates = list(unique_candidates.values())
    
    print(f"\n🎯 DISCOVERY SUMMARY:")
    print(f"   Total candidates found: {len(all_candidates)}")
    print(f"   Unique symbols: {len(final_candidates)}")
    print(f"   Average yield: {sum(c['dividend_yield'] for c in final_candidates) / len(final_candidates):.1f}%")
    
    # Show source breakdown
    sources = {}
    for candidate in final_candidates:
        source = candidate['source']
        sources[source] = sources.get(source, 0) + 1
    
    print(f"   Source breakdown:")
    for source, count in sources.items():
        print(f"     {source}: {count} stocks")
    
    return final_candidates

def get_strategy_config(strategy):
    """Get screener configurations for different strategies"""
    
    if strategy == 'conservative':
        return {
            'undervalued_large_caps': {'count': 250, 'min_yield': 1.5, 'max_yield': 6.0},
        }
    
    elif strategy == 'high_yield':
        return {
            'undervalued_large_caps': {'count': 150, 'min_yield': 3.0, 'max_yield': 20.0},
            'undervalued_growth_stocks': {'count': 100, 'min_yield': 3.0, 'max_yield': 20.0},
        }
    
    elif strategy == 'growth_dividend':
        return {
            'undervalued_growth_stocks': {'count': 200, 'min_yield': 1.0, 'max_yield': 8.0},
            'growth_technology_stocks': {'count': 50, 'min_yield': 0.5, 'max_yield': 5.0},
        }
    
    else:  # balanced (default)
        return {
            'undervalued_large_caps': {'count': 150, 'min_yield': 1.5, 'max_yield': 12.0},
            'undervalued_growth_stocks': {'count': 100, 'min_yield': 1.0, 'max_yield': 10.0},
        }

def enhanced_dividend_analysis(candidates, max_analyze=50):
    """Get detailed dividend data for top candidates"""
    print(f"\n📊 ENHANCED DIVIDEND ANALYSIS")
    print("=" * 70)
    
    # Sort by yield and take top candidates
    sorted_candidates = sorted(candidates, key=lambda x: x['dividend_yield'], reverse=True)
    top_candidates = sorted_candidates[:max_analyze]
    
    print(f"Analyzing top {len(top_candidates)} candidates for detailed dividend data...")
    
    analyzed_stocks = []
    
    for i, candidate in enumerate(top_candidates):
        symbol = candidate['symbol']
        
        if i % 10 == 0:  # Progress indicator
            print(f"  Progress: {i+1}/{len(top_candidates)} ({symbol})")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Comprehensive dividend analysis
            enhanced_stock = {
                **candidate,  # Include original candidate data
                
                # Company info
                'company_name': info.get('longName', symbol)[:40],
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown')[:30],
                'country': info.get('country', 'Unknown'),
                
                # Dividend details
                'dividend_rate': info.get('dividendRate', 0),
                'payout_ratio': info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0,
                'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield', 0) * 100 if info.get('fiveYearAvgDividendYield') else 0,
                'ex_dividend_date': info.get('exDividendDate', ''),
                'dividend_date': info.get('dividendDate', ''),
                
                # Financial health
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'quick_ratio': info.get('quickRatio', 0),
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                
                # Valuation
                'forward_pe': info.get('forwardPE', 0),
                'price_to_book': info.get('priceToBook', 0),
                'price_to_sales': info.get('priceToSalesTrailing12Months', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                
                # Market data
                'beta': info.get('beta', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'current_price': info.get('currentPrice', candidate.get('price', 0)),
                
                # Analysis metadata
                'analysis_date': datetime.now().isoformat(),
                'data_quality_score': calculate_data_quality_score(info)
            }
            
            analyzed_stocks.append(enhanced_stock)
            
        except Exception as e:
            print(f"    ❌ Error analyzing {symbol}: {e}")
            continue
    
    print(f"✅ Successfully analyzed {len(analyzed_stocks)} dividend stocks")
    return analyzed_stocks

def calculate_data_quality_score(info):
    """Calculate a data quality score based on available information"""
    score = 0
    key_fields = [
        'dividendYield', 'payoutRatio', 'debtToEquity', 'returnOnEquity',
        'currentRatio', 'priceToBook', 'forwardPE', 'sector'
    ]
    
    for field in key_fields:
        if info.get(field) is not None:
            score += 1
    
    return score

def apply_quality_filters(stocks, criteria):
    """Apply quality filters based on criteria"""
    print(f"\n🔍 APPLYING QUALITY FILTERS")
    print("=" * 70)
    
    print(f"Filter criteria:")
    for key, value in criteria.items():
        print(f"  {key}: {value}")
    print()
    
    filtered_stocks = []
    rejection_stats = {}
    
    for stock in stocks:
        symbol = stock['symbol']
        rejections = []
        
        # Yield range
        if not (criteria['min_yield'] <= stock['dividend_yield'] <= criteria['max_yield']):
            rejections.append('yield_range')
        
        # Market cap
        if stock['market_cap_billions'] < criteria['min_market_cap_billions']:
            rejections.append('market_cap')
        
        # Debt to equity
        debt_ratio = stock.get('debt_to_equity', 0)
        if debt_ratio > criteria['max_debt_equity'] and debt_ratio > 0:
            rejections.append('debt_equity')
        
        # Payout ratio
        payout = stock.get('payout_ratio', 0)
        if payout > criteria['max_payout_ratio'] and payout > 0:
            rejections.append('payout_ratio')
        
        # Data quality
        if stock.get('data_quality_score', 0) < criteria['min_data_quality']:
            rejections.append('data_quality')
        
        # Track rejections
        for rejection in rejections:
            rejection_stats[rejection] = rejection_stats.get(rejection, 0) + 1
        
        # Accept if no rejections
        if not rejections:
            # Calculate dividend quality score
            quality_score = calculate_dividend_quality_score(stock)
            stock['dividend_quality_score'] = quality_score
            filtered_stocks.append(stock)
            print(f"  ✅ {symbol}: {stock['dividend_yield']:.1f}% yield, Quality: {quality_score:.0f}/100")
        else:
            if len(filtered_stocks) < 5:  # Show first few rejections
                print(f"  ✗ {symbol}: {', '.join(rejections)}")
    
    print(f"\n📊 FILTERING RESULTS:")
    print(f"   Analyzed: {len(stocks)} stocks")
    print(f"   Passed filters: {len(filtered_stocks)} stocks")
    print(f"   Rejection breakdown:")
    for reason, count in rejection_stats.items():
        print(f"     {reason}: {count} stocks")
    
    return filtered_stocks

def calculate_dividend_quality_score(stock):
    """Calculate comprehensive dividend quality score (0-100)"""
    score = 0
    
    # Dividend yield (25 points)
    yield_val = stock.get('dividend_yield', 0)
    if 2.0 <= yield_val <= 5.0:  # Sweet spot
        score += 25
    elif 1.5 <= yield_val < 2.0 or 5.0 < yield_val <= 7.0:
        score += 20
    elif 1.0 <= yield_val < 1.5 or 7.0 < yield_val <= 10.0:
        score += 15
    elif yield_val > 0:
        score += 10
    
    # Payout sustainability (25 points)
    payout = stock.get('payout_ratio', 0)
    if 0 < payout <= 50:
        score += 25
    elif 50 < payout <= 70:
        score += 20
    elif 70 < payout <= 85:
        score += 15
    elif 85 < payout <= 100:
        score += 10
    
    # Financial health (25 points)
    roe = stock.get('roe', 0)
    debt_equity = stock.get('debt_to_equity', 0)
    
    if roe >= 15:
        score += 15
    elif roe >= 10:
        score += 12
    elif roe >= 5:
        score += 8
    
    if 0 <= debt_equity <= 1.0:
        score += 10
    elif 1.0 < debt_equity <= 2.0:
        score += 8
    elif 2.0 < debt_equity <= 3.0:
        score += 5
    
    # Company stability (25 points)
    market_cap = stock.get('market_cap_billions', 0)
    current_ratio = stock.get('current_ratio', 0)
    
    if market_cap >= 50:  # Large cap
        score += 15
    elif market_cap >= 10:  # Mid-large cap
        score += 12
    elif market_cap >= 2:  # Mid cap
        score += 8
    elif market_cap >= 1:  # Small-mid cap
        score += 5
    
    if current_ratio >= 1.5:
        score += 10
    elif current_ratio >= 1.0:
        score += 7
    elif current_ratio >= 0.8:
        score += 4
    
    return min(score, 100)

def display_dividend_results(stocks, max_display=25):
    """Display comprehensive dividend results"""
    if not stocks:
        print("❌ No dividend stocks found!")
        return
    
    # Sort by quality score
    sorted_stocks = sorted(stocks, key=lambda x: x.get('dividend_quality_score', 0), reverse=True)
    
    print(f"\n🏆 TOP DIVIDEND INCOME OPPORTUNITIES")
    print("=" * 130)
    print(f"Found {len(sorted_stocks)} quality dividend stocks\n")
    
    # Enhanced table
    headers = ['Rank', 'Symbol', 'Company', 'Yield%', 'Quality', 'Payout%', 'P/E', 'Market Cap', 'Sector']
    print(f"{headers[0]:<5} {headers[1]:<8} {headers[2]:<25} {headers[3]:<7} {headers[4]:<8} {headers[5]:<8} {headers[6]:<6} {headers[7]:<11} {headers[8]:<15}")
    print("-" * 130)
    
    for i, stock in enumerate(sorted_stocks[:max_display], 1):
        symbol = stock.get('symbol', 'N/A')
        company = stock.get('company_name', 'N/A')[:23]
        yield_val = stock.get('dividend_yield', 0)
        quality = stock.get('dividend_quality_score', 0)
        payout = stock.get('payout_ratio', 0)
        pe_ratio = stock.get('pe_ratio', 0)
        market_cap = stock.get('market_cap_billions', 0)
        sector = stock.get('sector', 'Unknown')[:13]
        
        payout_str = f"{payout:.0f}%" if payout > 0 else "N/A"
        pe_str = f"{pe_ratio:.1f}" if pe_ratio > 0 else "N/A"
        
        print(f"{i:<5} {symbol:<8} {company:<25} {yield_val:<6.1f}% {quality:<7.0f} {payout_str:<8} {pe_str:<6} ${market_cap:<10.1f}B {sector:<15}")
    
    # Portfolio analysis
    yields = [s.get('dividend_yield', 0) for s in sorted_stocks]
    quality_scores = [s.get('dividend_quality_score', 0) for s in sorted_stocks]
    market_caps = [s.get('market_cap_billions', 0) for s in sorted_stocks if s.get('market_cap_billions', 0) > 0]
    
    print(f"\n📊 PORTFOLIO ANALYSIS:")
    print(f"   🎯 Total quality dividend stocks: {len(sorted_stocks)}")
    print(f"   📈 Average dividend yield: {sum(yields) / len(yields):.1f}%")
    print(f"   🏆 Average quality score: {sum(quality_scores) / len(quality_scores):.1f}/100")
    print(f"   💰 Yield range: {min(yields):.1f}% - {max(yields):.1f}%")
    print(f"   🏢 Average market cap: ${sum(market_caps) / len(market_caps):.1f}B")
    
    # Sector and country diversification
    sectors = {}
    countries = {}
    for stock in sorted_stocks:
        sector = stock.get('sector', 'Unknown')
        country = stock.get('country', 'Unknown')
        sectors[sector] = sectors.get(sector, 0) + 1
        countries[country] = countries.get(country, 0) + 1
    
    print(f"\n📋 Sector Diversification:")
    for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:8]:
        print(f"   {sector}: {count} stocks")
    
    if len(countries) > 1:
        print(f"\n🌍 Geographic Diversification:")
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {country}: {count} stocks")
    
    return sorted_stocks

def save_comprehensive_results(stocks, strategy, criteria):
    """Save comprehensive results with metadata"""
    if not stocks:
        return None
    
    # Create results with metadata
    results_data = {
        'metadata': {
            'strategy': strategy,
            'criteria': criteria,
            'screening_date': datetime.now().isoformat(),
            'total_stocks_found': len(stocks),
            'script_version': '1.0',
        },
        'stocks': stocks
    }
    
    # Save main CSV
    df = pd.DataFrame(stocks)
    df = df.sort_values('dividend_quality_score', ascending=False)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"dividend_income_{strategy}_{timestamp}.csv"
    df.to_csv(filename, index=False)
    
    # Save metadata
    metadata_filename = f"dividend_metadata_{strategy}_{timestamp}.json"
    import json
    with open(metadata_filename, 'w') as f:
        json.dump(results_data['metadata'], f, indent=2)
    
    print(f"\n✅ Results saved:")
    print(f"   📄 Main data: {filename}")
    print(f"   📋 Metadata: {metadata_filename}")
    print(f"   📊 Contains {len(stocks)} dividend stocks with full analysis")
    
    return filename

def setup_daily_driver_cli():
    """Setup comprehensive CLI for daily driver"""
    parser = argparse.ArgumentParser(
        description="Daily Driver Dividend Income Screener - Production Ready",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Screening Strategies:
  conservative    - Large caps, stable dividends (1.5-6% yield)
  balanced        - Mix of large caps and growth (1.5-12% yield)  
  high_yield      - REITs, utilities, high payers (3-20% yield)
  growth_dividend - Growth stocks with dividends (1-8% yield)

Examples:
  # Daily conservative screening
  python dividend_daily_driver.py --strategy conservative

  # High-yield focus for income
  python dividend_daily_driver.py --strategy high_yield --max-analyze 75

  # Balanced approach with custom criteria
  python dividend_daily_driver.py --strategy balanced --min-yield 2.0 --max-debt-equity 4.0

  # Quick scan with top results only
  python dividend_daily_driver.py --strategy conservative --max-display 15 --max-analyze 30
        """
    )
    
    # Strategy selection
    parser.add_argument('--strategy', 
                       choices=['conservative', 'balanced', 'high_yield', 'growth_dividend'],
                       default='balanced',
                       help='Dividend screening strategy (default: balanced)')
    
    # Analysis limits
    parser.add_argument('--max-analyze', type=int, default=50,
                       help='Maximum candidates to analyze in detail (default: 50)')
    
    parser.add_argument('--max-display', type=int, default=25,
                       help='Maximum results to display (default: 25)')
    
    # Custom criteria overrides
    parser.add_argument('--min-yield', type=float,
                       help='Override minimum dividend yield %')
    
    parser.add_argument('--max-yield', type=float,
                       help='Override maximum dividend yield %')
    
    parser.add_argument('--min-market-cap', type=float, default=1.0,
                       help='Minimum market cap in billions (default: 1.0)')
    
    parser.add_argument('--max-debt-equity', type=float, default=5.0,
                       help='Maximum debt-to-equity ratio (default: 5.0)')
    
    parser.add_argument('--max-payout', type=float, default=100.0,
                       help='Maximum payout ratio % (default: 100.0)')
    
    parser.add_argument('--min-data-quality', type=int, default=5,
                       help='Minimum data quality score (default: 5)')
    
    # Output options
    parser.add_argument('--output-dir', type=str, default='.',
                       help='Output directory for results (default: current)')
    
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    return parser

def get_default_criteria(strategy):
    """Get default filtering criteria for each strategy"""
    
    base_criteria = {
        'min_market_cap_billions': 1.0,
        'max_debt_equity': 5.0,
        'max_payout_ratio': 100.0,
        'min_data_quality': 5
    }
    
    if strategy == 'conservative':
        return {**base_criteria, 'min_yield': 1.5, 'max_yield': 6.0, 'max_debt_equity': 3.0}
    elif strategy == 'high_yield':
        return {**base_criteria, 'min_yield': 3.0, 'max_yield': 20.0, 'max_debt_equity': 8.0}
    elif strategy == 'growth_dividend':
        return {**base_criteria, 'min_yield': 1.0, 'max_yield': 8.0, 'min_market_cap_billions': 2.0}
    else:  # balanced
        return {**base_criteria, 'min_yield': 1.5, 'max_yield': 12.0}

def main():
    parser = setup_daily_driver_cli()
    args = parser.parse_args()
    
    if not args.quiet:
        print("💰 DAILY DRIVER DIVIDEND INCOME SCREENER")
        print("Production-Ready Multi-Source Dividend Discovery")
        print("=" * 80)
        print(f"Strategy: {args.strategy.upper()}")
        print(f"Max candidates to analyze: {args.max_analyze}")
        print(f"Max results to display: {args.max_display}")
    
    try:
        # Create output directory
        if args.output_dir != '.' and not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        
        # Get default criteria and apply overrides
        criteria = get_default_criteria(args.strategy)
        if args.min_yield is not None:
            criteria['min_yield'] = args.min_yield
        if args.max_yield is not None:
            criteria['max_yield'] = args.max_yield
        criteria['min_market_cap_billions'] = args.min_market_cap
        criteria['max_debt_equity'] = args.max_debt_equity
        criteria['max_payout_ratio'] = args.max_payout
        criteria['min_data_quality'] = args.min_data_quality
        
        # Step 1: Multi-source discovery (maximizes 250 limit)
        candidates = multi_source_dividend_discovery(args.strategy)
        
        if not candidates:
            print("❌ No dividend candidates found")
            return
        
        # Step 2: Enhanced analysis
        analyzed_stocks = enhanced_dividend_analysis(candidates, args.max_analyze)
        
        if not analyzed_stocks:
            print("❌ No stocks successfully analyzed")
            return
        
        # Step 3: Quality filtering
        quality_stocks = apply_quality_filters(analyzed_stocks, criteria)
        
        if not quality_stocks:
            print("❌ No stocks passed quality filters")
            print("💡 Try relaxing criteria or using a different strategy")
            return
        
        # Step 4: Display results
        final_results = display_dividend_results(quality_stocks, args.max_display)
        
        # Step 5: Save results
        saved_file = save_comprehensive_results(final_results, args.strategy, criteria)
        
        if not args.quiet:
            print(f"\n🎯 DAILY SCREENING COMPLETE!")
            print(f"   Strategy: {args.strategy}")
            print(f"   Quality dividend stocks found: {len(final_results)}")
            print(f"   Ready for portfolio analysis and selection")
            
            if len(final_results) < 10:
                print(f"\n💡 For more results, try:")
                print(f"   --strategy high_yield (includes REITs)")
                print(f"   --max-debt-equity 8.0 (more lenient)")
                print(f"   --max-analyze 75 (analyze more candidates)")
        
    except KeyboardInterrupt:
        print("\n⏹️ Screening interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during screening: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
