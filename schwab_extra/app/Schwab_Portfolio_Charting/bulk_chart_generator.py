"""
Bulk Chart Generator - Generate all portfolio charts at once
Can run all chart types in sequence and save to specified directory
"""

import subprocess
import sys
import os
from datetime import datetime
import argparse
import time

def generate_all_charts(days_back=90, save_charts=True, output_dir="charts"):
    """Generate all charts and save to specified directory"""
    
    # Create output directory
    if save_charts and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    chart_scripts = [
        ('Portfolio Value & Trend', 'chart_portfolio_value.py'),
        ('Daily Changes & Moving Averages', 'chart_daily_changes.py'),
        ('Portfolio vs S&P 500', 'chart_benchmark_comparison.py'),
        ('Drawdown Analysis', 'chart_drawdown.py'),
        ('Individual Tickers', 'chart_individual_tickers.py'),
        ('Gain/Loss Analysis', 'chart_gainloss_analysis.py'),
        ('Risk Metrics Dashboard', 'chart_risk_dashboard.py'),
        ('Dividend Analysis', 'chart_dividend_analysis.py')
    ]
    
    print(f"Portfolio Chart Manager - Bulk Generator")
    print(f"========================================")
    print(f"Generating {len(chart_scripts)} charts...")
    print(f"Days back: {days_back}")
    print(f"Save charts: {save_charts}")
    print(f"Output directory: {output_dir if save_charts else 'Not saving'}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, (chart_name, script_name) in enumerate(chart_scripts, 1):
        print(f"\n[{i}/{len(chart_scripts)}] Generating {chart_name}...")
        
        # Check if script file exists
        if not os.path.exists(script_name):
            print(f"❌ {chart_name} - Script not found: {script_name}")
            failed += 1
            continue
        
        try:
            # Change to output directory if saving
            original_dir = os.getcwd()
            if save_charts:
                os.chdir(output_dir)
            
            # Run chart script
            cmd = [
                sys.executable, 
                os.path.join(original_dir, script_name),
                '--days', str(days_back),
                '--save', '1' if save_charts else '0'
            ]
            
            print(f"   Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            # Return to original directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                print(f"✅ {chart_name} - Success")
                successful += 1
                
                # Show any important output
                if result.stdout:
                    # Extract key lines from output
                    lines = result.stdout.split('\n')
                    important_lines = [line for line in lines if 
                                     'saved as:' in line.lower() or 
                                     'complete!' in line.lower() or
                                     'error' in line.lower()]
                    for line in important_lines[:2]:  # Show first 2 important lines
                        if line.strip():
                            print(f"   {line.strip()}")
            else:
                print(f"❌ {chart_name} - Failed (Return code: {result.returncode})")
                if result.stderr:
                    error_lines = result.stderr.split('\n')[:3]  # First 3 error lines
                    for line in error_lines:
                        if line.strip():
                            print(f"   Error: {line.strip()}")
                failed += 1
                
        except subprocess.TimeoutExpired:
            os.chdir(original_dir)
            print(f"❌ {chart_name} - Timeout (>180 seconds)")
            failed += 1
        except Exception as e:
            os.chdir(original_dir)
            print(f"❌ {chart_name} - Error: {str(e)}")
            failed += 1
        
        # Small delay between charts to be nice to the API
        if i < len(chart_scripts):
            time.sleep(1)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"BULK CHART GENERATION COMPLETE")
    print("=" * 50)
    print(f"Total time: {duration:.1f} seconds")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/(successful+failed)*100:.1f}%" if (successful+failed) > 0 else "No charts processed")
    
    if save_charts and successful > 0:
        full_path = os.path.abspath(output_dir)
        print(f"Charts saved to: {full_path}")
        
        # List generated files
        if os.path.exists(output_dir):
            chart_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
            if chart_files:
                print(f"Generated files ({len(chart_files)}):")
                for file in sorted(chart_files):
                    file_size = os.path.getsize(os.path.join(output_dir, file)) / 1024  # KB
                    print(f"  - {file} ({file_size:.1f} KB)")
    
    if failed > 0:
        print(f"\n⚠️  {failed} chart(s) failed to generate.")
        print("Common issues:")
        print("  - Missing dependencies (run: pip install -r requirements.txt)")
        print("  - Schwab API authentication not configured")
        print("  - Network connectivity issues")
        print("  - Missing portfolio_analyzer_update_3.py file")
    else:
        print(f"\n🎉 All charts generated successfully!")
    
    return successful, failed

def list_available_charts():
    """List all available chart scripts"""
    chart_scripts = [
        'chart_portfolio_value.py',
        'chart_daily_changes.py',
        'chart_benchmark_comparison.py',
        'chart_drawdown.py',
        'chart_individual_tickers.py',
        'chart_gainloss_analysis.py',
        'chart_risk_dashboard.py',
        'chart_dividend_analysis.py'
    ]
    
    print("Available Chart Scripts:")
    print("=" * 30)
    
    for i, script in enumerate(chart_scripts, 1):
        exists = "✅" if os.path.exists(script) else "❌"
        print(f"{i}. {exists} {script}")
    
    missing = [s for s in chart_scripts if not os.path.exists(s)]
    if missing:
        print(f"\n⚠️  {len(missing)} script(s) missing:")
        for script in missing:
            print(f"   - {script}")
    else:
        print(f"\n✅ All {len(chart_scripts)} chart scripts found!")

def generate_single_chart(chart_name, days_back=90, save_chart=True, output_dir="charts"):
    """Generate a single specific chart"""
    
    chart_mapping = {
        'portfolio': 'chart_portfolio_value.py',
        'daily': 'chart_daily_changes.py',
        'benchmark': 'chart_benchmark_comparison.py',
        'drawdown': 'chart_drawdown.py',
        'tickers': 'chart_individual_tickers.py',
        'gainloss': 'chart_gainloss_analysis.py',
        'risk': 'chart_risk_dashboard.py',
        'dividend': 'chart_dividend_analysis.py'
    }
    
    script_name = chart_mapping.get(chart_name.lower())
    if not script_name:
        print(f"❌ Unknown chart type: {chart_name}")
        print(f"Available types: {', '.join(chart_mapping.keys())}")
        return False
    
    if not os.path.exists(script_name):
        print(f"❌ Script not found: {script_name}")
        return False
    
    print(f"Generating single chart: {chart_name}")
    successful, failed = generate_all_charts(days_back, save_chart, output_dir)
    
    return successful > 0

def main():
    """Main entry point for bulk chart generation"""
    parser = argparse.ArgumentParser(
        description='Generate portfolio charts in bulk',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bulk_chart_generator.py --days 90 --save --output-dir reports
  python bulk_chart_generator.py --days 180 --no-save
  python bulk_chart_generator.py --list
  python bulk_chart_generator.py --single risk --days 60
        """
    )
    
    parser.add_argument('--days', type=int, default=90, 
                       help='Number of days back to analyze (default: 90)')
    parser.add_argument('--save', action='store_true', 
                       help='Save charts to files')
    parser.add_argument('--no-save', action='store_true', 
                       help='Display charts without saving (default)')
    parser.add_argument('--output-dir', default='charts', 
                       help='Output directory for saved charts (default: charts)')
    parser.add_argument('--list', action='store_true',
                       help='List available chart scripts and exit')
    parser.add_argument('--single', type=str,
                       help='Generate single chart type (portfolio, daily, benchmark, etc.)')
    
    args = parser.parse_args()
    
    # Handle list option
    if args.list:
        list_available_charts()
        return
    
    # Determine save option
    save_charts = args.save and not args.no_save
    
    # Validate days parameter
    if args.days < 1 or args.days > 365:
        print("❌ Days parameter must be between 1 and 365")
        return
    
    print("Portfolio Chart Manager - Bulk Generator")
    print("=" * 40)
    
    # Handle single chart option
    if args.single:
        success = generate_single_chart(args.single, args.days, save_charts, args.output_dir)
        if not success:
            sys.exit(1)
        return
    
    # Check if any chart scripts exist
    chart_scripts = [
        'chart_portfolio_value.py',
        'chart_daily_changes.py', 
        'chart_benchmark_comparison.py',
        'chart_drawdown.py',
        'chart_individual_tickers.py',
        'chart_gainloss_analysis.py',
        'chart_risk_dashboard.py',
        'chart_dividend_analysis.py'
    ]
    
    existing_scripts = [s for s in chart_scripts if os.path.exists(s)]
    if not existing_scripts:
        print("❌ No chart scripts found in current directory!")
        print("Make sure you have the chart_*.py files in the same directory.")
        list_available_charts()
        sys.exit(1)
    
    # Generate all charts
    try:
        successful, failed = generate_all_charts(
            days_back=args.days,
            save_charts=save_charts,
            output_dir=args.output_dir
        )
        
        # Exit with error code if any charts failed
        if failed > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ Chart generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
