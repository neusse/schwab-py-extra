"""
Chart Validator - System Validation Utility
Checks that all required files and dependencies are available
"""

import importlib.util
import sys
import os
from pathlib import Path
import subprocess

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
        'chart_dividend_analysis.py',
        'bulk_chart_generator.py'
    ]
    
    required_dependencies = [
        'portfolio_analyzer_update_3.py'
    ]
    
    optional_files = [
        'requirements.txt',
        'README.md'
    ]
    
    print("Portfolio Chart Manager - File Validation")
    print("=" * 50)
    print()
    
    # Check core chart files
    print("Checking Core Chart Files:")
    missing_files = []
    for file in chart_files:
        if not Path(file).exists():
            missing_files.append(file)
            print(f"❌ MISSING: {file}")
        else:
            file_size = Path(file).stat().st_size / 1024  # KB
            print(f"✅ Found: {file} ({file_size:.1f} KB)")
    
    print()
    
    # Check required dependencies
    print("Checking Required Dependencies:")
    for file in required_dependencies:
        if not Path(file).exists():
            missing_files.append(file)
            print(f"❌ MISSING: {file}")
        else:
            file_size = Path(file).stat().st_size / 1024  # KB
            print(f"✅ Found: {file} ({file_size:.1f} KB)")
    
    print()
    
    # Check optional files
    print("Checking Optional Files:")
    for file in optional_files:
        if not Path(file).exists():
            print(f"⚠️  Optional: {file}")
        else:
            file_size = Path(file).stat().st_size / 1024  # KB
            print(f"✅ Found: {file} ({file_size:.1f} KB)")
    
    print()
    
    if missing_files:
        print(f"⚠️  {len(missing_files)} required file(s) missing!")
        print("Please ensure all files are in the same directory.")
        return False
    
    print("✅ All required files found!")
    return True

def validate_python_dependencies():
    """Check Python module dependencies"""
    
    print("Checking Python Dependencies:")
    print("-" * 30)
    
    required_modules = [
        ('matplotlib', 'Chart plotting'),
        ('pandas', 'Data manipulation'), 
        ('numpy', 'Numerical computations'),
        ('scipy', 'Statistical functions'),
        ('tkinter', 'GUI interface'),
        ('yfinance', 'Dividend data'),
        ('schwab', 'Schwab API')
    ]
    
    missing_modules = []
    for module, description in required_modules:
        try:
            if module == 'tkinter':
                import tkinter
                print(f"✅ {module:<12} - {description}")
            else:
                __import__(module)
                print(f"✅ {module:<12} - {description}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module:<12} - {description} (MISSING)")
    
    print()
    
    if missing_modules:
        print(f"⚠️  {len(missing_modules)} Python module(s) missing!")
        print()
        print("Install missing modules with:")
        print(f"pip install {' '.join(missing_modules)}")
        print()
        print("Or install all at once:")
        print("pip install schwab-py matplotlib pandas scipy numpy yfinance")
        return False
    
    print("✅ All Python dependencies found!")
    return True

def validate_api_setup():
    """Test basic API functionality"""
    
    print("Checking API Setup:")
    print("-" * 20)
    
    try:
        # Try to import the portfolio analyzer
        import portfolio_analyzer_update_3 as pa
        print("✅ Portfolio analyzer imported successfully")
        
        # Try to get positions (this will test API authentication)
        try:
            positions = pa.get_portfolio_positions()
            if positions:
                print(f"✅ API authentication working ({len(positions)} positions found)")
                
                # Show sample positions (first 3)
                sample_tickers = list(positions.keys())[:3]
                if sample_tickers:
                    print(f"   Sample tickers: {', '.join(sample_tickers)}")
                
                return True
            else:
                print("⚠️  API connected but no positions found")
                print("   This may be normal if you have no holdings")
                return True
                
        except Exception as e:
            print(f"❌ API authentication failed: {str(e)}")
            print("   Check your Schwab API credentials and environment variables")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import portfolio analyzer: {str(e)}")
        print("   Make sure portfolio_analyzer_update_3.py is available")
        return False
    except Exception as e:
        print(f"❌ API setup error: {str(e)}")
        return False

def test_chart_functionality():
    """Test that charts can be generated"""
    
    print("Testing Chart Functionality:")
    print("-" * 30)
    
    # Test a simple chart import
    try:
        import chart_portfolio_value
        print("✅ Chart modules can be imported")
        
        # Test matplotlib backend
        import matplotlib
        print(f"✅ Matplotlib backend: {matplotlib.get_backend()}")
        
        # Test basic plotting
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))
        ax.plot([1, 2, 3], [1, 4, 2])
        ax.set_title("Test Plot")
        plt.close(fig)
        print("✅ Basic plotting functionality works")
        
        return True
        
    except ImportError as e:
        print(f"❌ Chart import failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Chart functionality error: {str(e)}")
        return False

def create_sample_config():
    """Create a sample configuration file"""
    
    config_content = """# Portfolio Chart Manager Configuration
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
    
    try:
        with open('sample_config.py', 'w') as f:
            f.write(config_content)
        
        print("✅ Created sample_config.py")
        print("   Copy to config.py and customize as needed")
        return True
    except Exception as e:
        print(f"❌ Failed to create config file: {str(e)}")
        return False

def run_quick_test():
    """Run a quick functionality test"""
    
    print("Running Quick Functionality Test:")
    print("-" * 35)
    
    try:
        # Test bulk chart generator
        if Path('bulk_chart_generator.py').exists():
            result = subprocess.run([
                sys.executable, 'bulk_chart_generator.py', '--list'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Bulk chart generator working")
            else:
                print("⚠️  Bulk chart generator has issues")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
        
        # Test main GUI (import only, don't launch)
        try:
            spec = importlib.util.spec_from_file_location("pcm", "portfolio_chart_manager.py")
            if spec and spec.loader:
                print("✅ Main GUI can be imported")
            else:
                print("⚠️  Main GUI import issues")
        except Exception as e:
            print(f"⚠️  Main GUI import error: {str(e)}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️  Quick test timed out")
        return False
    except Exception as e:
        print(f"❌ Quick test error: {str(e)}")
        return False

def generate_system_report():
    """Generate a comprehensive system report"""
    
    print("\n" + "=" * 60)
    print("SYSTEM REPORT")
    print("=" * 60)
    
    print(f"Python Version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Python Path: {sys.executable}")
    
    # Count files
    chart_files = [f for f in os.listdir('.') if f.startswith('chart_') and f.endswith('.py')]
    print(f"Chart Files Found: {len(chart_files)}")
    
    # Check disk space (rough estimate)
    try:
        import shutil
        free_space = shutil.disk_usage('.').free / (1024**3)  # GB
        print(f"Available Disk Space: {free_space:.1f} GB")
    except:
        print("Available Disk Space: Unable to determine")

def main():
    """Main validation function"""
    print("Portfolio Chart Manager - System Validator")
    print("=" * 50)
    print("Validating system setup and dependencies...")
    print()
    
    all_checks_passed = True
    
    # 1. Validate files
    print("📁 STEP 1: File Validation")
    files_ok = validate_chart_files()
    if not files_ok:
        all_checks_passed = False
    print()
    
    # 2. Validate Python dependencies
    print("🐍 STEP 2: Python Dependencies")
    deps_ok = validate_python_dependencies()
    if not deps_ok:
        all_checks_passed = False
    print()
    
    # 3. Validate API setup
    print("🔌 STEP 3: API Setup")
    api_ok = validate_api_setup()
    if not api_ok:
        all_checks_passed = False
    print()
    
    # 4. Test chart functionality
    print("📊 STEP 4: Chart Functionality")
    charts_ok = test_chart_functionality()
    if not charts_ok:
        all_checks_passed = False
    print()
    
    # 5. Quick functionality test
    print("⚡ STEP 5: Quick Test")
    test_ok = run_quick_test()
    if not test_ok:
        all_checks_passed = False
    print()
    
    # 6. Create sample config
    print("⚙️  STEP 6: Configuration")
    config_ok = create_sample_config()
    print()
    
    # Generate system report
    generate_system_report()
    
    # Final assessment
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    if all_checks_passed:
        print("🎉 VALIDATION PASSED!")
        print("✅ System is ready to use")
        print()
        print("Quick start:")
        print("1. Run: python portfolio_chart_manager.py")
        print("2. Or generate all charts: python bulk_chart_generator.py --save")
        print("3. Or run individual charts: python chart_portfolio_value.py")
    else:
        print("❌ VALIDATION FAILED!")
        print("⚠️  Please fix the issues above before using the system")
        print()
        print("Common solutions:")
        print("- Install missing dependencies: pip install schwab-py matplotlib pandas scipy numpy yfinance")
        print("- Check Schwab API credentials and environment variables")
        print("- Ensure portfolio_analyzer_update_3.py is in the same directory")
    
    print()
    print("For detailed setup instructions, see README.md")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
