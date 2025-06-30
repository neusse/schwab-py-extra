# Portfolio Chart Manager

A comprehensive GUI-based portfolio analysis system that displays multiple chart types for Schwab portfolios using the schwab-py API wrapper. The system features a main management interface with a live portfolio vs S&P 500 chart and the ability to launch individual chart applications.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install schwab-py matplotlib pandas scipy numpy yfinance
   ```

2. **Setup Files**
   - Ensure `portfolio_analyzer_update_3.py` is in the same directory
   - Verify Schwab API credentials are configured
   - Run validation: `python chart_validator.py`

3. **Launch Application**
   ```bash
   python portfolio_chart_manager.py
   ```

## 📁 File Structure

```
portfolio_analyzer/
├── portfolio_analyzer_update_3.py      # Core portfolio analyzer (your existing file)
├── portfolio_chart_manager.py          # Main GUI application ⭐
├── chart_portfolio_value.py            # Portfolio value & trend analysis
├── chart_daily_changes.py              # Daily changes & moving averages
├── chart_benchmark_comparison.py       # Portfolio vs S&P 500 comparison
├── chart_drawdown.py                   # Drawdown risk analysis
├── chart_individual_tickers.py         # Individual ticker performance
├── chart_gainloss_analysis.py          # Win/loss trading patterns
├── chart_risk_dashboard.py             # Comprehensive risk metrics
├── chart_dividend_analysis.py          # Dividend income analysis
├── chart_validator.py                  # System validation utility
├── bulk_chart_generator.py             # Generate all charts at once
├── requirements.txt                    # Python dependencies
├── launch_all_charts.bat              # Windows launcher
├── launch_all_charts.sh               # Linux/Mac launcher
└── README.md                          # This file
```

## 🎯 Main Features

### Main GUI Application (`portfolio_chart_manager.py`)
- **Live Portfolio Chart**: Real-time portfolio vs S&P 500 comparison
- **Chart Selection**: Launch any chart type from a list
- **Settings Panel**: Configure analysis periods (30-365 days)
- **Auto-refresh**: Optional 5-minute data updates
- **Status Monitoring**: Real-time status updates and error handling

### Available Chart Types

| Chart Type | Description | Key Features |
|------------|-------------|--------------|
| **Portfolio Value & Trend** | Portfolio value over time with trend analysis | Linear regression, R-squared, start/end annotations |
| **Daily Changes & Moving Averages** | Daily gains/losses with moving averages | Bar chart, 1-week & 2-week MA, volatility analysis |
| **Portfolio vs S&P 500** | Comprehensive benchmark comparison | Returns, correlation, beta analysis, excess returns |
| **Drawdown Analysis** | Risk analysis with drawdown metrics | Max drawdown, underwater periods, recovery analysis |
| **Individual Tickers** | Performance of individual holdings | Normalized performance, top/bottom performers, risk/return scatter |
| **Gain/Loss Analysis** | Daily trading patterns and streaks | Win/loss distribution, streak analysis, monthly performance |
| **Risk Metrics Dashboard** | Comprehensive risk assessment | VaR, volatility, correlation matrix, tail risk |
| **Dividend Analysis** | Dividend income and yield analysis | Income breakdown, yield estimates, growth analysis |

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Schwab account with API access
- schwab-py library configured with credentials

### Step-by-Step Installation

1. **Clone or Download Files**
   ```bash
   # Create directory
   mkdir portfolio_analyzer
   cd portfolio_analyzer
   
   # Place all Python files in this directory
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install individually:
   ```bash
   pip install schwab-py matplotlib pandas scipy numpy yfinance
   ```

3. **Verify Schwab API Setup**
   - Ensure your existing `portfolio_analyzer_update_3.py` works
   - Test API authentication
   - Verify environment variables are set

4. **Validate Installation**
   ```bash
   python chart_validator.py
   ```

5. **Test Launch**
   ```bash
   python portfolio_chart_manager.py
   ```

## 🖥 Usage

### Main GUI Application

Launch the main application:
```bash
python portfolio_chart_manager.py
```

**Features:**
- **Left Panel**: Select chart type and configure settings
- **Right Panel**: Live portfolio vs S&P 500 chart
- **Settings**: Adjust days back (30-365), enable chart saving
- **Launch Button**: Open selected chart in new window
- **Refresh Button**: Update data and charts
- **Auto-refresh**: Enable 5-minute automatic updates

### Individual Chart Applications

Run any chart independently:
```bash
# Portfolio value analysis
python chart_portfolio_value.py --days 90 --save 0

# Daily changes with 60-day period
python chart_daily_changes.py --days 60 --save 1

# Risk dashboard with charts saved
python chart_risk_dashboard.py --days 120 --save 1
```

**Command Line Arguments:**
- `--days`: Analysis period (default: 90)
- `--save`: Save charts (1=yes, 0=no, default: 0)

### Batch Operations

**Windows:**
```batch
launch_all_charts.bat
```

**Linux/Mac:**
```bash
chmod +x launch_all_charts.sh
./launch_all_charts.sh
```

**Bulk Chart Generation:**
```bash
# Generate all charts for 90 days and save
python bulk_chart_generator.py --days 90 --save --output-dir reports

# Generate without saving
python bulk_chart_generator.py --days 180
```

## 📊 Chart Details

### Portfolio Value & Trend
- **Visual**: Line chart with trend line
- **Metrics**: Total return, trend R-squared, daily slope
- **Analysis**: Start/end values, trend direction assessment

### Daily Changes & Moving Averages  
- **Visual**: Bar chart + line chart (dual subplot)
- **Metrics**: Gain/loss days, average changes, volatility
- **Analysis**: Win/loss ratios, momentum indicators

### Portfolio vs S&P 500
- **Visual**: 4-panel comparison dashboard  
- **Metrics**: Excess returns, beta, correlation, capture ratios
- **Analysis**: Relative performance, risk-adjusted returns

### Drawdown Analysis
- **Visual**: 4-panel drawdown dashboard
- **Metrics**: Max drawdown, underwater periods, recovery time
- **Analysis**: Drawdown duration distribution, risk assessment

### Individual Tickers
- **Visual**: 4-panel ticker analysis
- **Metrics**: Normalized performance, volatility, Sharpe ratios
- **Analysis**: Top/bottom performers, risk vs return

### Gain/Loss Analysis
- **Visual**: 4-panel trading pattern analysis
- **Metrics**: Win/loss streaks, distribution analysis
- **Analysis**: Trading effectiveness, pattern recognition

### Risk Dashboard
- **Visual**: 9-panel comprehensive risk analysis
- **Metrics**: VaR, volatility, correlation, tail risk
- **Analysis**: Complete risk profile assessment

### Dividend Analysis
- **Visual**: 4-panel dividend income analysis
- **Metrics**: Income breakdown, yield estimates, growth rates
- **Analysis**: Dividend sustainability and projections

## ⚙️ Configuration

### Settings Panel (Main GUI)
- **Days Back**: 30-365 days (default: 90)
- **Save Charts**: Enable/disable chart saving
- **Auto-refresh**: 5-minute automatic updates

### Chart Customization
Each chart module can be customized by modifying:
- Color schemes and styling
- Figure sizes and DPI
- Analysis periods and calculations
- Output formats and file names

### API Configuration
- Rate limiting: 0.5 seconds between calls
- Error handling: Automatic retry logic
- Data validation: Quality checks included

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   Error: Could not import portfolio analyzer functions
   ```
   **Solution**: Ensure `portfolio_analyzer_update_3.py` is in the same directory

2. **API Authentication**
   ```
   Error: No positions found
   ```
   **Solution**: Check Schwab API credentials and environment variables

3. **Data Fetching**
   ```
   Error: Unable to fetch market data
   ```
   **Solution**: Verify network connection and API rate limits

4. **Chart Display Issues**
   ```
   Charts not displaying properly
   ```
   **Solution**: Check matplotlib backend configuration

### Data Quality Issues
- **Extreme moves**: Automatically detected (>10% daily changes)
- **Missing data**: Forward-filled where possible
- **Problematic tickers**: SNSXX and similar excluded automatically

### Performance Optimization
- **Large portfolios**: Consider shorter analysis periods
- **API limits**: Built-in rate limiting prevents issues
- **Memory usage**: Charts cleared after display

## 🔒 Security & Privacy

- **Local Processing**: All data processing happens locally
- **No Data Storage**: No persistent storage of sensitive data
- **API Security**: Uses your existing Schwab API credentials
- **Network**: Only connects to Schwab API and Yahoo Finance for dividends

## 📈 Advanced Usage

### Custom Chart Development
Create new chart types by:
1. Following the template pattern in existing charts
2. Implementing `main()` function with argument parsing
3. Adding entry to `chart_types` dictionary in main GUI
4. Including data fetching and visualization functions

### Integration with Other Systems
- **Export capabilities**: High-resolution PNG charts suitable for reports
- **Command line interface**: All charts support CLI usage
- **Batch processing**: Generate multiple charts programmatically
- **API integration**: Can be called from other Python applications

### Scheduled Analysis
Set up automated portfolio analysis:
```bash
# Daily analysis at market close
0 16 * * 1-5 cd /path/to/portfolio && python bulk_chart_generator.py --days 90 --save
```

## 📞 Support

### Getting Help
1. **Validation Tool**: Run `python chart_validator.py` to diagnose issues
2. **Verbose Output**: Charts include detailed console output for debugging
3. **Error Messages**: Descriptive error messages with suggested solutions

### Common Questions

**Q: Can I analyze different time periods?**
A: Yes, use `--days` parameter (30-365 days supported)

**Q: How do I save charts automatically?**
A: Enable "Save Charts" in GUI or use `--save 1` in CLI

**Q: Can I run this on a schedule?**
A: Yes, use `bulk_chart_generator.py` with cron/task scheduler

**Q: What if I have a large portfolio?**
A: System handles large portfolios; consider shorter periods for faster processing

## 🚀 Future Enhancements

### Planned Features
- **Web Interface**: Browser-based dashboard
- **Real-time Updates**: Live streaming data
- **Advanced Analytics**: Machine learning insights
- **Mobile App**: Smartphone companion
- **Report Generation**: Automated PDF reports
- **Alert System**: Email/SMS notifications for significant events

### Contributing
This system is designed to be modular and extensible. New chart types and features can be added by following the established patterns.

---

## 📋 Requirements Summary

```txt
schwab-py>=0.7.0
matplotlib>=3.5.0
pandas>=1.3.0
scipy>=1.7.0
numpy>=1.21.0
yfinance>=0.1.70
tkinter
requests>=2.25.0
python-dateutil>=2.8.0
```

**System Requirements:**
- Python 3.8+
- 4GB RAM recommended
- Network connection for API access
- Display capability for GUI (for headless operation, use CLI charts only)

---

*This portfolio chart manager provides a comprehensive solution for analyzing Schwab portfolios with professional-quality charts and detailed analytics. The modular design allows for easy customization and extension based on your specific needs.*
