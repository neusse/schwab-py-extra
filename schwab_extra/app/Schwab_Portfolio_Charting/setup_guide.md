# Portfolio Chart Manager - Setup Guide

This portfolio chart manager system provides a GUI application that displays portfolio charts and allows launching individual chart applications. It's designed to work with the Schwab API using the schwab-py library.

## System Architecture

The system consists of:
1. **Main GUI Application** (`portfolio_chart_manager.py`) - Displays a live portfolio vs S&P 500 chart and manages other charts
2. **Individual Chart Modules** - Standalone applications for specific chart types
3. **Base Portfolio Analyzer** (`portfolio_analyzer_update_3.py`) - Core data fetching and calculation functions

## Prerequisites

- Python 3.8 or higher
- Schwab account with API access configured
- Environment variables for Schwab API authentication
- Required Python packages (see requirements below)

## Installation

### 1. Required Python Packages

```bash
pip install schwab-py matplotlib pandas scipy numpy tkinter yfinance
```

### 2. File Structure

Create a directory for your portfolio analyzer and place these files:

```
portfolio_analyzer/
├── portfolio_analyzer_update_3.py      # Your existing analyzer
├── portfolio_chart_manager.py          # Main GUI application
├── chart_portfolio_value.py            # Portfolio value chart
├── chart_daily_changes.py              # Daily changes chart
├── chart_benchmark_comparison.py       # Benchmark comparison
├── chart_drawdown.py                   # Drawdown analysis
├── chart_individual_tickers.py         # Individual tickers
├── chart_gainloss_analysis.py          # Gain/loss analysis (template)
├── chart_risk_dashboard.py             # Risk dashboard (template)
└── chart_dividend_analysis.py          # Dividend analysis (template)
```

### 3. Schwab API Setup

Ensure you have:
- Schwab API credentials configured
- Environment variables set up
- `schwab_extra.lib.schwab_lib` module available (referenced in your existing code)

## Usage

### Running the Main Application

```bash
python portfolio_chart_manager.py
```

### Running Individual Charts Directly

Each chart can be run independently:

```bash
# Portfolio value chart
python chart_portfolio_value.py --days 90 --save 0

# Daily changes chart
python chart_daily_changes.py --days 60 --save 1

# Benchmark comparison
python chart_benchmark_comparison.py --days 180 --save 0

# Drawdown analysis
python chart_drawdown.py --days 120 --save 1

# Individual tickers analysis
python chart_individual_tickers.py --days 90 --save 0
```

### Command Line Arguments

All chart applications support:
- `--days`: Number of days back to analyze (default: 90)
- `--save`: Save chart to file (1 for yes, 0 for no, default: 0)

## Features

### Main GUI Application

- **Live Portfolio Chart**: Real-time portfolio vs S&P 500 comparison
- **Chart Selection**: Choose from multiple chart types
- **Settings Panel**: Configure analysis period and save options
- **Auto-refresh**: Optional automatic data refresh every 5 minutes

### Available Chart Types

1. **Portfolio Value & Trend**: Shows portfolio value over time with trend analysis
2. **Daily Changes & Moving Averages**: Daily gains/losses with moving averages
3. **Portfolio vs S&P 500**: Comprehensive benchmark comparison
4. **Drawdown Analysis**: Risk analysis with drawdown metrics
5. **Individual Tickers**: Performance analysis of individual holdings
6. **Gain/Loss Analysis**: Daily trading patterns and streaks
7. **Risk Metrics Dashboard**: Comprehensive risk assessment
8. **Dividend Analysis**: Dividend income and yield analysis

### Chart Features

- **High-quality graphics**: 300 DPI charts suitable for reports
- **Detailed analysis**: Each chart includes statistical summaries
- **Customizable periods**: Analyze different time ranges
- **Data quality checks**: Automatic detection of data anomalies
- **Professional formatting**: Clean, publication-ready charts

## Customization

### Adding New Chart Types

1. Create a new chart module following the template pattern
2. Add entry to `chart_types` dictionary in main GUI
3. Implement `main()` function with argument parsing
4. Include data fetching and chart creation functions

### Modifying Existing Charts

Each chart module is standalone and can be customized independently:
- Modify chart layouts and styling
- Add new metrics and calculations
- Change color schemes and formatting
- Add additional analysis features

### Configuration Options

In `portfolio_chart_manager.py`, you can modify:
- Default analysis periods
- Chart colors and styling
- Auto-refresh intervals
- Available chart types
- GUI layout and sizing

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `portfolio_analyzer_update_3.py` is in the same directory
2. **API Authentication**: Check Schwab API credentials and environment variables
3. **Data Fetching**: Verify network connection and API rate limits
4. **Chart Display**: Ensure matplotlib backend is properly configured for your system

### Data Quality

The system includes automatic data quality checks:
- Detection of extreme daily moves (>10%)
- Identification of missing or zero price data
- Handling of problematic tickers (like SNSXX money market funds)

### Performance

For large portfolios:
- Consider reducing analysis periods for faster loading
- Use save chart options to avoid repeated API calls
- Monitor API rate limits when fetching data for many tickers

## API Rate Limiting

The system includes built-in rate limiting:
- 0.5-second delay between API calls
- Automatic retry logic for failed requests
- Efficient data fetching to minimize API usage

## Output Files

When saving charts, files are created in the current directory:
- Format: `{chart_type}_{days}days.png`
- High resolution (300 DPI)
- Suitable for inclusion in reports and presentations

## Support

For issues related to:
- **Schwab API**: Check schwab-py documentation
- **Chart functionality**: Review individual chart module code
- **GUI issues**: Check tkinter and matplotlib installation
- **Data problems**: Verify API authentication and network connectivity

## Extension Ideas

The modular design allows for easy extensions:
- Additional chart types (sector analysis, correlation matrices)
- Integration with other brokers or data sources
- Export to PDF reports
- Email notifications for significant events
- Web-based interface using Flask/Django
- Real-time streaming data updates

This system provides a solid foundation for portfolio analysis and can be extended based on your specific needs and requirements.
