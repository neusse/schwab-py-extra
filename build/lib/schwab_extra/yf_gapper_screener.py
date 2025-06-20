import yfinance as yf
import pandas as pd
import time
from datetime import datetime, date
import argparse
import sys

def get_predefined_screeners():
    """Get all available predefined screeners"""
    print("🔍 Available yfinance predefined screeners:")
    for key in yf.PREDEFINED_SCREENER_QUERIES.keys():
        print(f"  📊 {key}")
    return list(yf.PREDEFINED_SCREENER_QUERIES.keys())

def screen_day_gainers(min_gap_percent=3.0, count=100):
    """Use yfinance built-in day_gainers screener for gappers"""
    print(f"\n🚀 Screening for day gainers (built-in gappers)...")
    print(f"   Using yfinance 'day_gainers' screener")
    print(f"   Count: {count} stocks")
    
    try:
        # Use the built-in day_gainers screener
        response = yf.screen("day_gainers", count=count)
        
        if response and 'quotes' in response:
            quotes = response['quotes']
            print(f"✅ Retrieved {len(quotes)} day gainers from yfinance")
            
            gappers = []
            for quote in quotes:
                # Extract gapper data
                symbol = quote.get('symbol', '')
                price = quote.get('regularMarketPrice', 0)
                change = quote.get('regularMarketChange', 0)
                change_percent = quote.get('regularMarketChangePercent', 0)
                volume = quote.get('regularMarketVolume', 0)
                avg_volume = quote.get('averageDailyVolume3Month', 0)
                previous_close = quote.get('regularMarketPreviousClose', 0)
                market_cap = quote.get('marketCap', 0)
                
                # Filter by minimum gap percentage
                if change_percent >= min_gap_percent:
                    volume_ratio = volume / avg_volume if avg_volume > 0 else 0
                    
                    gapper_data = {
                        'symbol': symbol,
                        'current_price': price,
                        'previous_close': previous_close,
                        'gap_percent': change_percent,
                        'change_dollar': change,
                        'current_volume': volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': volume_ratio,
                        'market_cap': market_cap,
                        'pe_ratio': quote.get('trailingPE', 0),
                        'market_cap_billions': market_cap / 1e9 if market_cap else 0,
                        'collection_time': datetime.now().isoformat(),
                        'source': 'yfinance_day_gainers'
                    }
                    gappers.append(gapper_data)
                    
            print(f"🎯 Found {len(gappers)} gappers with gap >= {min_gap_percent}%")
            return gappers
        else:
            print("❌ No data returned from day_gainers screener")
            return []
            
    except Exception as e:
        print(f"❌ Error with day_gainers screener: {e}")
        return []

def screen_small_cap_gainers(count=100):
    """Screen small cap gainers for potential big movers"""
    print(f"\n📈 Screening small cap gainers...")
    
    try:
        response = yf.screen("small_cap_gainers", count=count)
        
        if response and 'quotes' in response:
            quotes = response['quotes']
            print(f"✅ Retrieved {len(quotes)} small cap gainers")
            
            small_cap_gappers = []
            for quote in quotes:
                symbol = quote.get('symbol', '')
                price = quote.get('regularMarketPrice', 0)
                change_percent = quote.get('regularMarketChangePercent', 0)
                volume = quote.get('regularMarketVolume', 0)
                market_cap = quote.get('marketCap', 0)
                
                if change_percent > 0:  # Any positive move
                    gapper_data = {
                        'symbol': symbol,
                        'current_price': price,
                        'gap_percent': change_percent,
                        'current_volume': volume,
                        'market_cap': market_cap,
                        'market_cap_billions': market_cap / 1e9 if market_cap else 0,
                        'source': 'yfinance_small_cap_gainers'
                    }
                    small_cap_gappers.append(gapper_data)
                    
            return small_cap_gappers
        else:
            print("❌ No small cap data returned")
            return []
            
    except Exception as e:
        print(f"❌ Error with small_cap_gainers: {e}")
        return []

def screen_most_actives(count=100):
    """Screen most active stocks for volume-based gappers"""
    print(f"\n📊 Screening most active stocks...")
    
    try:
        response = yf.screen("most_actives", count=count)
        
        if response and 'quotes' in response:
            quotes = response['quotes']
            print(f"✅ Retrieved {len(quotes)} most active stocks")
            
            active_movers = []
            for quote in quotes:
                symbol = quote.get('symbol', '')
                price = quote.get('regularMarketPrice', 0)
                change_percent = quote.get('regularMarketChangePercent', 0)
                volume = quote.get('regularMarketVolume', 0)
                avg_volume = quote.get('averageDailyVolume3Month', 0)
                
                # Focus on stocks with significant moves
                if abs(change_percent) >= 1.0:  # 1%+ move
                    volume_ratio = volume / avg_volume if avg_volume > 0 else 0
                    
                    active_data = {
                        'symbol': symbol,
                        'current_price': price,
                        'gap_percent': change_percent,
                        'current_volume': volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': volume_ratio,
                        'source': 'yfinance_most_actives'
                    }
                    active_movers.append(active_data)
                    
            return active_movers
        else:
            print("❌ No most actives data returned")
            return []
            
    except Exception as e:
        print(f"❌ Error with most_actives: {e}")
        return []

def create_custom_gapper_query(min_gap_percent=3.0, min_price=5.0, min_volume=15000):
    """Create custom EquityQuery for gappers"""
    print(f"\n🔧 Creating custom gapper query...")
    print(f"   Min gap: {min_gap_percent}%")
    print(f"   Min price: ${min_price}")
    print(f"   Min volume: {min_volume:,}")
    
    try:
        from yfinance import EquityQuery
        
        # Create custom query similar to day_gainers but with our parameters
        q = EquityQuery('and', [
            
            EquityQuery('gt', ['percentchange', min_gap_percent]), # type: ignore[arg-type]
            EquityQuery('eq', ['region', 'us']),                   # type: ignore[arg-type]
            EquityQuery('gte', ['intradayprice', min_price]),      # type: ignore[arg-type]
            EquityQuery('gt', ['dayvolume', min_volume])           # type: ignore[arg-type]
        ])
        
        response = yf.screen(q, sortField='percentchange', sortAsc=False, size=250)
        
        if response and 'quotes' in response:
            quotes = response['quotes']
            print(f"✅ Custom query returned {len(quotes)} stocks")
            
            custom_gappers = []
            for quote in quotes:
                symbol = quote.get('symbol', '')
                price = quote.get('regularMarketPrice', 0)
                change_percent = quote.get('regularMarketChangePercent', 0)
                volume = quote.get('regularMarketVolume', 0)
                
                gapper_data = {
                    'symbol': symbol,
                    'current_price': price,
                    'gap_percent': change_percent,
                    'current_volume': volume,
                    'source': 'yfinance_custom_query'
                }
                custom_gappers.append(gapper_data)
                
            return custom_gappers
        else:
            print("❌ No custom query data returned")
            return []
            
    except Exception as e:
        print(f"❌ Error with custom query: {e}")
        return []

def comprehensive_yfinance_screening(min_gap_percent=3.0, count=100):
    """Run comprehensive screening using multiple yfinance screeners"""
    print(f"🚀 COMPREHENSIVE YFINANCE GAPPER SCREENING")
    print("=" * 60)
    
    all_gappers = []
    
    # 1. Day gainers (main gappers)
    day_gainers = screen_day_gainers(min_gap_percent, count)
    all_gappers.extend(day_gainers)
    
    # 2. Small cap gainers (potential big movers)
    small_caps = screen_small_cap_gainers(count)
    all_gappers.extend(small_caps)
    
    # 3. Most actives (volume-based)
    actives = screen_most_actives(count)
    all_gappers.extend(actives)
    
    # 4. Custom query (if available)
    try:
        custom = create_custom_gapper_query(min_gap_percent)
        all_gappers.extend(custom)
    except:
        print("⚠️ Custom query not available (EquityQuery import failed)")
    
    # Remove duplicates by symbol
    seen_symbols = set()
    unique_gappers = []
    for gapper in all_gappers:
        symbol = gapper.get('symbol', '')
        if symbol and symbol not in seen_symbols:
            seen_symbols.add(symbol)
            unique_gappers.append(gapper)
    
    print(f"\n🎯 SCREENING SUMMARY:")
    print(f"   Total candidates found: {len(all_gappers)}")
    print(f"   Unique symbols: {len(unique_gappers)}")
    print(f"   Sources: day_gainers, small_cap_gainers, most_actives, custom_query")
    
    return unique_gappers

def filter_gappers(gappers, min_gap_percent=3.0, min_volume_multiplier=1.5, 
                  min_price=5.0, max_price=500.0):
    """Apply additional filtering to gappers"""
    print(f"\n🔍 Applying additional filters...")
    print(f"   Min gap: {min_gap_percent}%")
    print(f"   Volume multiplier: {min_volume_multiplier}x")
    print(f"   Price range: ${min_price} - ${max_price}")
    
    filtered = []
    for gapper in gappers:
        gap_percent = gapper.get('gap_percent', 0)
        price = gapper.get('current_price', 0)
        volume_ratio = gapper.get('volume_ratio', 0)
        
        # Apply filters
        if (gap_percent >= min_gap_percent and 
            min_price <= price <= max_price and
            (volume_ratio >= min_volume_multiplier or volume_ratio == 0)):  # Allow 0 if no avg volume data
            filtered.append(gapper)
    
    print(f"✅ {len(filtered)} gappers passed additional filters")
    return filtered

def display_yfinance_gappers(gappers, max_results=30):
    """Display yfinance gapper results"""
    if not gappers:
        print("❌ No gappers found!")
        return
    
    # Sort by gap percentage
    sorted_gappers = sorted(gappers, key=lambda x: x.get('gap_percent', 0), reverse=True)
    
    print(f"\n🏆 TOP YFINANCE GAPPERS")
    print("=" * 80)
    print(f"Found {len(sorted_gappers)} total gappers\n")
    
    # Display table header
    print(f"{'Symbol':<8} {'Price':<10} {'Gap %':<8} {'Volume':<12} {'Vol Ratio':<10} {'Source':<20}")
    print("-" * 80)
    
    # Display results
    for gapper in sorted_gappers[:max_results]:
        symbol = gapper.get('symbol', 'N/A')
        price = gapper.get('current_price', 0)
        gap = gapper.get('gap_percent', 0)
        volume = gapper.get('current_volume', 0)
        vol_ratio = gapper.get('volume_ratio', 0)
        source = gapper.get('source', 'unknown')[:18]
        
        vol_ratio_str = f"{vol_ratio:.1f}x" if vol_ratio > 0 else "N/A"
        
        print(f"{symbol:<8} ${price:<9.2f} {gap:<7.1f}% {volume:<11,.0f} {vol_ratio_str:<10} {source:<20}")
    
    # Summary statistics
    total_gaps = [g.get('gap_percent', 0) for g in sorted_gappers]
    avg_gap = sum(total_gaps) / len(total_gaps) if total_gaps else 0
    max_gap = max(total_gaps) if total_gaps else 0
    
    print(f"\n📊 GAPPER ANALYSIS:")
    print(f"   🎯 Total gappers: {len(sorted_gappers)}")
    print(f"   📈 Average gap: {avg_gap:.1f}%")
    print(f"   🚀 Largest gap: {max_gap:.1f}%")
    
    # Source breakdown
    sources = {}
    for gapper in sorted_gappers:
        source = gapper.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\n📋 Source breakdown:")
    for source, count in sources.items():
        print(f"   {source}: {count} stocks")
    
    return sorted_gappers

def save_yfinance_results(gappers, filename_prefix="yfinance_gappers"):
    """Save results to CSV"""
    if gappers:
        df = pd.DataFrame(gappers)
        df = df.sort_values('gap_percent', ascending=False)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{filename_prefix}_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Results saved to {filename}")
        return filename
    return None

def setup_yfinance_cli():
    """Setup CLI arguments"""
    parser = argparse.ArgumentParser(
        description="yfinance Gapper Screener using yf.screen() API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use day_gainers screener (fast, pre-filtered)
  python yfinance_screener.py --screener day_gainers --count 100

  # Comprehensive screening (all sources)
  python yfinance_screener.py --comprehensive --min-gap 2.0

  # Small cap focus
  python yfinance_screener.py --screener small_cap_gainers --count 200

  # Most actives with volume spikes
  python yfinance_screener.py --screener most_actives --min-volume-multiplier 2.0
        """
    )
    
    parser.add_argument('--screener', 
                       choices=['day_gainers', 'small_cap_gainers', 'most_actives', 'custom'], 
                       default='day_gainers',
                       help='Which yfinance screener to use')
    
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run all screeners and combine results')
    
    parser.add_argument('--count', type=int, default=100,
                       help='Number of results from each screener (max 250)')
    
    parser.add_argument('--min-gap', type=float, default=3.0,
                       help='Minimum gap percentage')
    
    parser.add_argument('--min-volume-multiplier', type=float, default=1.5,
                       help='Minimum volume vs average')
    
    parser.add_argument('--min-price', type=float, default=5.0,
                       help='Minimum stock price')
    
    parser.add_argument('--max-price', type=float, default=200.0,
                       help='Maximum stock price')
    
    parser.add_argument('--max-results', type=int, default=30,
                       help='Maximum results to display')
    
    parser.add_argument('--list-screeners', action='store_true',
                       help='List all available predefined screeners')
    
    return parser

def main():
    parser = setup_yfinance_cli()
    args = parser.parse_args()
    
    print("🚀 YFINANCE GAPPER SCREENER")
    print("=" * 50)
    #print("Using correct yf.screen() API")
    
    # List available screeners if requested
    if args.list_screeners:
        get_predefined_screeners()
        return
    
    try:
        gappers = []
        
        if args.comprehensive:
            # Run comprehensive screening
            gappers = comprehensive_yfinance_screening(args.min_gap, args.count)
        else:
            # Run single screener
            if args.screener == 'day_gainers':
                gappers = screen_day_gainers(args.min_gap, args.count)
            elif args.screener == 'small_cap_gainers':
                gappers = screen_small_cap_gainers(args.count)
            elif args.screener == 'most_actives':
                gappers = screen_most_actives(args.count)
            elif args.screener == 'custom':
                gappers = create_custom_gapper_query(args.min_gap, args.min_price)
        
        # Apply additional filtering
        if gappers:
            filtered_gappers = filter_gappers(
                gappers, 
                args.min_gap, 
                args.min_volume_multiplier,
                args.min_price, 
                args.max_price
            )
            
            # Display results
            display_yfinance_gappers(filtered_gappers, args.max_results)
            
            # Save results
            if filtered_gappers:
                save_yfinance_results(filtered_gappers)
            
        else:
            print("❌ No gappers found")
            
    except KeyboardInterrupt:
        print("\n⏹️ Screening interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
