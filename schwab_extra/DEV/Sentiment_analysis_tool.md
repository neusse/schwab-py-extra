# Financial Sentiment Analysis Tool

## Overview
This is a comprehensive financial sentiment analysis tool that evaluates market sentiment for stocks and ETFs using multiple data sources and analytical approaches. The tool combines technical analysis, options flow analysis, and fundamental metrics to generate bullish, bearish, or neutral sentiment ratings for a portfolio of securities.

## Core Functionality

### Multi-Source Data Integration
- **Primary Data Source**: Schwab API for enhanced options data and real-time market information
- **Fallback Data Source**: Yahoo Finance (yfinance) for broader market coverage and reliability
- **Automatic Failover**: Seamlessly switches between data sources based on availability and data quality

### Analysis Components

#### 1. Technical Analysis
- **Price Action**: Current price vs 20-day and 50-day simple moving averages
- **Momentum Indicators**: 14-day Relative Strength Index (RSI) for overbought/oversold conditions
- **Trend Analysis**: Daily percentage changes and price momentum signals

#### 2. Options Flow Analysis
- **Put/Call Ratios**: Analyzes both volume-based and open interest-based put/call ratios
- **Implied Volatility**: Compares call vs put implied volatility for fear/greed indicators
- **Options Volume**: Evaluates total options activity as a measure of investor interest
- **Enhanced Thresholds**: Multiple sensitivity levels for bullish/bearish options signals

#### 3. Data Quality Assessment
- **Source Tracking**: Identifies which API provided each data point
- **Coverage Analysis**: Reports data availability across different securities
- **Error Handling**: Robust fallback mechanisms for missing or incomplete data

## Input Requirements

### Environment Variables (for Schwab API)
```bash
SCHWAB_TOKEN_PATH     # Path to token storage file
SCHWAB_API_KEY        # Schwab developer API key
SCHWAB_APP_SECRET     # Schwab application secret
SCHWAB_CALLBACK_URL   # OAuth callback URL
```

### Ticker List
- Accepts any list of stock symbols or ETF tickers
- Optimized for both individual stocks and exchange-traded funds
- Handles mixed portfolios (stocks + ETFs)

## Output Format

### Comprehensive Data Table
- **Current Price & Daily Change**: Real-time pricing information
- **Technical Indicators**: RSI, moving average relationships
- **Options Metrics**: Put/call ratios, implied volatility data
- **Data Source Attribution**: Shows which API provided each data point
- **Sentiment Classification**: Overall bullish/bearish/neutral rating
- **Signal Details**: Specific factors contributing to sentiment score

### Summary Statistics
- Portfolio-wide sentiment distribution
- Data source reliability metrics
- Coverage analysis by security type

## Sentiment Scoring Methodology

### Signal Classification
- **Technical Signals**: Based on price momentum and RSI levels
- **Options Signals**: Derived from put/call flow and implied volatility
- **Strength Indicators**: Multiple threshold levels (mild, strong, very strong)

### Overall Sentiment Calculation
- Weighs multiple signal types equally
- Requires multiple confirming signals for strong sentiment ratings
- Defaults to neutral when signals are conflicting or insufficient

## Use Cases

### Portfolio Management
- Daily sentiment screening for investment portfolios
- Risk assessment through options flow analysis
- Technical momentum confirmation for entry/exit decisions

### Market Research
- Sector sentiment analysis across ETF holdings
- Comparative sentiment analysis between securities
- Options market structure analysis

### Risk Management
- Early warning system for sentiment shifts
- Volatility forecasting through implied volatility analysis
- Diversification assessment through sentiment correlation

## Technical Architecture

### Dependencies
- **schwab-py**: Official Schwab API client library
- **yfinance**: Yahoo Finance data retrieval
- **pandas/numpy**: Data processing and analysis
- **Standard libraries**: os, json, datetime for system integration

### Error Handling
- Graceful degradation when API limits are reached
- Automatic retry logic for transient network issues
- Comprehensive logging for troubleshooting

### Performance Considerations
- Optimized API calls to minimize rate limiting
- Efficient data processing for large ticker lists
- Memory-conscious data structures for scalability

## Limitations and Considerations

### Data Limitations
- Options data availability varies by security
- Some ETFs may have limited options markets
- Real-time data subject to exchange delays

### Methodology Constraints
- Sentiment analysis is backward-looking based on recent data
- Does not incorporate fundamental analysis or news sentiment
- Should be used as one component of a broader investment process

This tool is designed for quantitative analysts, portfolio managers, and individual investors seeking systematic approaches to market sentiment analysis.