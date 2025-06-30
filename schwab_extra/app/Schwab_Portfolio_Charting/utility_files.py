# ===============================================================================
# REQUIREMENTS.TXT
# ===============================================================================
"""
schwab-py>=0.7.0
matplotlib>=3.5.0
pandas>=1.3.0
scipy>=1.7.0
numpy>=1.21.0
yfinance>=0.1.70
tkinter
requests>=2.25.0
python-dateutil>=2.8.0
"""

# ===============================================================================
# LAUNCH_ALL_CHARTS.BAT (Windows Batch File)
# ===============================================================================
"""
@echo off
echo Portfolio Chart Manager - Launch All Charts
echo ==========================================
echo.

echo Starting Main GUI Application...
start "Portfolio Chart Manager" python portfolio_chart_manager.py

timeout /t 2 /nobreak >nul

echo Launching Portfolio Value Chart...
start "Portfolio Value" python chart_portfolio_value.py --days 90

timeout /t 1 /nobreak >nul

echo Launching Daily Changes Chart...
start "Daily Changes" python chart_daily_changes.py --days 90

timeout /t 1 /nobreak >nul

echo Launching Benchmark Comparison...
start "Benchmark" python chart_benchmark_comparison.py --days 90

timeout /t 1 /nobreak >nul

echo Launching Drawdown Analysis...
start "Drawdown" python chart_drawdown.py --days 90

timeout /t 1 /nobreak >nul

echo Launching Individual Tickers...
start "Tickers" python chart_individual_tickers.py --days 90

timeout /t 1 /nobreak >nul

echo Launching Gain/Loss Analysis...
start "Gain/Loss" python chart_gainloss_analysis.py --days 90

timeout /t 1 /nobreak >nul

echo Launching Risk Dashboard...
start "Risk Dashboard" python chart_risk_dashboard.py --days 90

timeout /t 1 /nobreak >nul

echo Launching Dividend Analysis...
start "Dividends" python chart_dividend_analysis.py --days 90

echo.
echo All charts launched!
echo Close this window when done.
pause
"""

# ===============================================================================
# LAUNCH_ALL_CHARTS.SH (Linux/Mac Shell Script)
# ===============================================================================
"""
#!/bin/bash

echo "Portfolio Chart Manager - Launch All Charts"
echo "==========================================="
echo

echo "Starting Main GUI Application..."
python portfolio_chart_manager.py &

sleep 2

echo "Launching Portfolio Value Chart..."
python chart_portfolio_value.py --days 90 &

sleep 1

echo "Launching Daily Changes Chart..."
python chart_daily_changes.py --days 90 &

sleep 1

echo "Launching Benchmark Comparison..."
python chart_benchmark_comparison.py --days 90 &

sleep 1

echo "Launching Drawdown Analysis..."
python chart_drawdown.py --days 90 &

sleep 1

echo "Launching Individual Tickers..."
python chart_individual_tickers.py --days 90 &

sleep 1

echo "Launching Gain/Loss Analysis..."
python chart_gainloss_analysis.py --days 90 &

sleep 1

echo "Launching Risk Dashboard..."
python chart_risk_dashboard.py --days 90 &

sleep 1

echo "Launching Dividend Analysis..."
python chart_dividend_analysis.py --days 90 &

echo
echo "All charts launched!"
echo "Press Ctrl+C to exit"

wait
"""

# ===============================================================================
# CHART_VALIDATOR.PY - Utility to check chart functionality
# ===============================================================================

import importlib.util
import sys
import os
from pathlib import Path

def validate_chart_files():
    """Validate that all chart files exist and can be imported"""
    
    chart_files = [
        'portfolio_chart_manager.py',
        'chart_portfolio_value.py',
        'chart_daily_changes.py',
        'chart_benchmark_comparison.py',
        'chart_drawdown.py',
        'chart_individual_tickers.py',
        'chart_gainloss_analysis.py',
        'chart_risk_dashboard.py',
        'chart_dividend_analysis.py'
    ]
    
    required_dependencies = [
        'portfolio_analyzer_update_3.py'
    ]
    
    print("Portfolio Chart Manager - File Validation")
    print("=" * 50)
    print()
    
    # Check if files exist
    missing_files = []
    for file in chart_files + required_dependencies:
        if not Path(file).exists():
            missing_files.append(file)
            print(f"❌ MISSING: {file}")
        else:
            print(f"✅ Found: {file}")
    
    print()
    
    if missing_files:
        print(f"⚠️  {len(missing_files)} file(s) missing!")
        print("Please ensure all files are in the same directory.")
        return False
    
    # Check Python imports
    print("Checking Python dependencies...")
    
    required_modules = [
        'matplotlib',
        'pandas', 
        'numpy',
        'scipy',
        'tkinter',
        'yfinance',
        'schwab'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ MISSING: {module}")
    
    print()
    
    if missing_modules:
        print(f"⚠️  {len(missing_modules)} Python module(s) missing!")
        print("Install with: pip install " + " ".join(missing_modules))
        return False
    
    print("✅ All files and dependencies found!")
    return True

def create_sample_config():
    """Create a sample configuration file"""
    
    config_content = """
# Portfolio Chart Manager Configuration
# Copy this to config.py and modify as needed

# Default settings
DEFAULT_DAYS_BACK = 90
DEFAULT_SAVE_CHARTS = False
AUTO_REFRESH_INTERVAL = 300000  # 5 minutes in milliseconds

# Chart display settings
CHART_FIGSIZE = (14, 7)
CHART_DPI = 300
CHART_STYLE = 'default'

# Colors
PORTFOLIO_COLOR = 'darkgreen'
BENCHMARK_COLOR = 'blue'
GAIN_COLOR = 'green'
LOSS_COLOR = 'red'

# Excluded tickers (problematic data)
EXCLUDED_TICKERS = ['SNSXX']

# API settings
API_RATE_LIMIT_DELAY = 0.5  # seconds between API calls

# GUI settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
REFRESH_INTERVAL_MINUTES = 5
"""
    
    with open('sample_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ Created sample_config.py")
    print("   Copy to config.py and customize as needed")

def main():
    """Main validation function"""
    print("Running Portfolio Chart Manager validation...")
    print()
    
    # Validate files
    files_ok = validate_chart_files()
    
    if files_ok:
        print()
        print("🎉 Validation complete! System ready to use.")
        print()
        print("Quick start:")
        print("1. Ensure Schwab API credentials are configured")
        print("2. Run: python portfolio_chart_manager.py")
        print("3. Or run individual charts: python chart_portfolio_value.py")
    else:
        print()
        print("❌ Validation failed. Please fix the issues above.")
    
    # Create sample config
    print()
    create_sample_config()

if __name__ == "__main__":
    main()

# ===============================================================================
# BULK_CHART_GENERATOR.PY - Generate all charts at once
# ===============================================================================

import subprocess
import sys
import os
from datetime import datetime
import argparse

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
    
    print(f"Generating {len(chart_scripts)} charts...")
    print(f"Days back: {days_back}")
    print(f"Save charts: {save_charts}")
    print(f"Output directory: {output_dir}")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    for chart_name, script_name in chart_scripts:
        print(f"\nGenerating {chart_name}...")
        
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
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Return to original directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                print(f"✅ {chart_name} - Success")
                successful += 1
            else:
                print(f"❌ {chart_name} - Failed")
                print(f"   Error: {result.stderr}")
                failed += 1
                
        except subprocess.TimeoutExpired:
            os.chdir(original_dir)
            print(f"❌ {chart_name} - Timeout")
            failed += 1
        except Exception as e:
            os.chdir(original_dir)
            print(f"❌ {chart_name} - Error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Chart generation complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if save_charts and successful > 0:
        print(f"Charts saved to: {os.path.abspath(output_dir)}")

def main():
    """Main entry point for bulk chart generation"""
    parser = argparse.ArgumentParser(description='Generate all portfolio charts at once')
    parser.add_argument('--days', type=int, default=90, help='Number of days back to analyze')
    parser.add_argument('--save', action='store_true', help='Save charts to files')
    parser.add_argument('--output-dir', default='charts', help='Output directory for saved charts')
    
    args = parser.parse_args()
    
    print("Portfolio Chart Manager - Bulk Chart Generator")
    print("=" * 50)
    
    generate_all_charts(
        days_back=args.days,
        save_charts=args.save,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()
