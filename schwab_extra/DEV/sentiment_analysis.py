import yfinance as yf
import pandas as pd
import numpy as np
import schwab
import json
import os
from datetime import datetime, timedelta

# Schwab setup using environment variables
def setup_schwab_client():
    """
    Setup Schwab API client using environment variables
    Requires: SCHWAB_TOKEN_PATH, SCHWAB_API_KEY, SCHWAB_APP_SECRET, SCHWAB_CALLBACK_URL
    """
    try:
        token_path = os.environ["SCHWAB_TOKEN_PATH"]
        api_key = os.environ["SCHWAB_API_KEY"]
        app_secret = os.environ["SCHWAB_APP_SECRET"]
        callback_url = os.environ["SCHWAB_CALLBACK_URL"]
        
        # Try to load existing token file
        if os.path.exists(token_path):
            client = schwab.auth.client_from_token_file(
                token_path, 
                api_key,
                app_secret
            )
        else:
            # First time setup - requires manual OAuth
            client = schwab.auth.easy_client(
                api_key,
                app_secret,
                callback_url,
                token_path
            )
        
        print("Schwab API client initialized successfully")
        return client
        
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        print("Please set: SCHWAB_TOKEN_PATH, SCHWAB_API_KEY, SCHWAB_APP_SECRET, SCHWAB_CALLBACK_URL")
        return None
    except Exception as e:
        print(f"Schwab API setup failed: {e}")
        print("Falling back to yfinance only...")
        return None

# Simplified Schwab options data
def get_schwab_options_simple(client, symbol):
    """
    Simplified Schwab options data retrieval
    """
    try:
        # Basic options chain request - using simple parameter format
        response = client.get_option_chain(symbol)
        
        if response.status_code != 200:
            print(f"Schwab API returned status {response.status_code} for {symbol}")
            return None, None, None, None
            
        data = response.json()
        
        # Debug: Print response structure for first ticker
        if symbol == 'MSFT':  # Only print for one ticker to avoid spam
            print(f"Schwab response keys for {symbol}: {list(data.keys())}")
        
        # Initialize counters
        total_call_volume = 0
        total_put_volume = 0
        total_call_oi = 0
        total_put_oi = 0
        call_iv_sum = 0
        put_iv_sum = 0
        call_count = 0
        put_count = 0
        
        # Process call options
        if 'callExpDateMap' in data:
            for exp_date, strikes in data['callExpDateMap'].items():
                for strike_price, contracts in strikes.items():
                    for contract in contracts:
                        volume = contract.get('totalVolume', 0) or 0
                        oi = contract.get('openInterest', 0) or 0
                        iv = contract.get('volatility', 0) or 0
                        
                        total_call_volume += volume
                        total_call_oi += oi
                        if iv > 0:
                            call_iv_sum += iv
                            call_count += 1
        
        # Process put options
        if 'putExpDateMap' in data:
            for exp_date, strikes in data['putExpDateMap'].items():
                for strike_price, contracts in strikes.items():
                    for contract in contracts:
                        volume = contract.get('totalVolume', 0) or 0
                        oi = contract.get('openInterest', 0) or 0
                        iv = contract.get('volatility', 0) or 0
                        
                        total_put_volume += volume
                        total_put_oi += oi
                        if iv > 0:
                            put_iv_sum += iv
                            put_count += 1
        
        # Calculate ratios
        pc_volume_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else None
        pc_oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else None
        avg_call_iv = call_iv_sum / call_count if call_count > 0 else None
        avg_put_iv = put_iv_sum / put_count if put_count > 0 else None
        
        print(f"Schwab data for {symbol}: P/C Vol: {pc_volume_ratio}, P/C OI: {pc_oi_ratio}")
        return pc_volume_ratio, pc_oi_ratio, avg_call_iv, avg_put_iv
        
    except Exception as e:
        print(f"Error with Schwab options for {symbol}: {e}")
        return None, None, None, None

# Fallback yfinance options (improved)
def get_yfinance_options(ticker):
    """
    Improved yfinance options data with better error handling
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Try to get options chain
        try:
            options_chain = stock.option_chain()
        except Exception:
            # If no options chain available, return None
            return None, None, None, None
        
        calls = options_chain.calls
        puts = options_chain.puts
        
        if calls.empty or puts.empty:
            return None, None, None, None
        
        # Calculate metrics with better handling of missing data
        total_call_volume = calls['volume'].fillna(0).sum()
        total_put_volume = puts['volume'].fillna(0).sum()
        total_call_oi = calls['openInterest'].fillna(0).sum()
        total_put_oi = puts['openInterest'].fillna(0).sum()
        
        # Calculate ratios
        pc_volume_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else None
        pc_oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else None
        
        # Get implied volatility if available
        avg_call_iv = calls['impliedVolatility'].mean() if 'impliedVolatility' in calls.columns else None
        avg_put_iv = puts['impliedVolatility'].mean() if 'impliedVolatility' in puts.columns else None
        
        return pc_volume_ratio, pc_oi_ratio, avg_call_iv, avg_put_iv
        
    except Exception as e:
        print(f"Error with yfinance options for {ticker}: {e}")
        return None, None, None, None

# Function to get current price and basic data
def get_current_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Get recent price data
        hist = stock.history(period="5d")
        if len(hist) > 0:
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            daily_change_pct = ((current_price - prev_close) / prev_close) * 100
        else:
            current_price = None
            daily_change_pct = None
            
        # Get basic info
        info = stock.info
        volume = hist['Volume'].iloc[-1] if len(hist) > 0 else None
        
        return current_price, daily_change_pct, volume, info
        
    except Exception as e:
        print(f"Error fetching current data for {ticker}: {e}")
        return None, None, None, {}

# Function to get technical sentiment
def get_technical_sentiment(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Get more history for technical analysis
        hist = stock.history(period="60d")
        if len(hist) < 20:
            return None, None, None
            
        # Calculate moving averages
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        
        current_price = hist['Close'].iloc[-1]
        sma_20 = hist['SMA_20'].iloc[-1]
        sma_50 = hist['SMA_50'].iloc[-1] if len(hist) >= 50 else None
        
        # Price vs moving averages
        price_vs_sma20 = ((current_price - sma_20) / sma_20) * 100 if sma_20 else None
        price_vs_sma50 = ((current_price - sma_50) / sma_50) * 100 if sma_50 else None
        
        # Calculate RSI (14-day)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else None
        
        return price_vs_sma20, price_vs_sma50, current_rsi
        
    except Exception as e:
        print(f"Error calculating technical indicators for {ticker}: {e}")
        return None, None, None

# Main analysis function
def analyze_sentiment_dual_source(tickers, use_schwab=True):
    """
    Analyze sentiment using both Schwab API (if available) and yfinance
    """
    # Try to setup Schwab client
    schwab_client = None
    if use_schwab:
        schwab_client = setup_schwab_client()
        if schwab_client:
            print("✓ Schwab API connected - using enhanced options data")
        else:
            print("✗ Schwab API not available - using yfinance only")
    
    sentiment_data = []
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        
        # Get current data
        current_price, daily_change, volume, info = get_current_data(ticker)
        
        # Get technical indicators
        price_vs_sma20, price_vs_sma50, rsi = get_technical_sentiment(ticker)
        
        # Get options data - try Schwab first, then yfinance
        pc_vol_ratio = pc_oi_ratio = avg_call_iv = avg_put_iv = None
        data_source = "No options"
        
        if schwab_client:
            pc_vol_ratio, pc_oi_ratio, avg_call_iv, avg_put_iv = get_schwab_options_simple(schwab_client, ticker)
            if pc_vol_ratio is not None:
                data_source = "Schwab"
        
        # Fallback to yfinance if Schwab didn't work
        if pc_vol_ratio is None:
            pc_vol_ratio, pc_oi_ratio, avg_call_iv, avg_put_iv = get_yfinance_options(ticker)
            if pc_vol_ratio is not None:
                data_source = "yfinance"
        
        # Analyze sentiment signals
        sentiment_signals = []
        
        # Technical sentiment
        if price_vs_sma20 is not None:
            if price_vs_sma20 > 3:
                sentiment_signals.append("strong_bullish_tech")
            elif price_vs_sma20 > 1:
                sentiment_signals.append("bullish_tech")
            elif price_vs_sma20 < -3:
                sentiment_signals.append("strong_bearish_tech")
            elif price_vs_sma20 < -1:
                sentiment_signals.append("bearish_tech")
        
        if rsi is not None:
            if rsi < 25:
                sentiment_signals.append("strong_oversold")
            elif rsi < 35:
                sentiment_signals.append("oversold")
            elif rsi > 75:
                sentiment_signals.append("strong_overbought")
            elif rsi > 65:
                sentiment_signals.append("overbought")
        
        # Options sentiment
        if pc_vol_ratio is not None:
            if pc_vol_ratio > 2.0:
                sentiment_signals.append("very_bearish_options")
            elif pc_vol_ratio > 1.3:
                sentiment_signals.append("bearish_options")
            elif pc_vol_ratio < 0.6:
                sentiment_signals.append("very_bullish_options")
            elif pc_vol_ratio < 0.85:
                sentiment_signals.append("bullish_options")
        
        # Implied volatility sentiment
        if avg_call_iv is not None and avg_put_iv is not None:
            iv_ratio = avg_put_iv / avg_call_iv
            if iv_ratio > 1.15:
                sentiment_signals.append("fear_iv")
            elif iv_ratio < 0.85:
                sentiment_signals.append("complacency_iv")
        
        # Calculate overall sentiment
        bullish_signals = [s for s in sentiment_signals if 'bullish' in s or 'oversold' in s or 'complacency' in s]
        bearish_signals = [s for s in sentiment_signals if 'bearish' in s or 'overbought' in s or 'fear' in s]
        
        if len(bullish_signals) > len(bearish_signals):
            overall_sentiment = "bullish"
        elif len(bearish_signals) > len(bullish_signals):
            overall_sentiment = "bearish"
        else:
            overall_sentiment = "neutral"
        
        sentiment_data.append({
            "Ticker": ticker,
            "Price": round(current_price, 2) if current_price else "No data",
            "Daily_Chg_%": round(daily_change, 2) if daily_change else "No data",
            "RSI": round(rsi, 1) if rsi else "No data",
            "vs_SMA20_%": round(price_vs_sma20, 2) if price_vs_sma20 else "No data",
            "P/C_Vol": round(pc_vol_ratio, 3) if pc_vol_ratio else "No data",
            "P/C_OI": round(pc_oi_ratio, 3) if pc_oi_ratio else "No data",
            "Call_IV": round(avg_call_iv, 3) if avg_call_iv else "No data",
            "Put_IV": round(avg_put_iv, 3) if avg_put_iv else "No data",
            "Source": data_source,
            "Sentiment": overall_sentiment,
            "Signals": ', '.join(sentiment_signals) if sentiment_signals else "neutral"
        })
    
    return pd.DataFrame(sentiment_data)

# Main execution
if __name__ == "__main__":
    # Your ticker list
    tickers = ['BOND', 'CALF', 'CGGR', 'CGIE', 'COWG', 'COWZ', 'FTSM', 'JEPQ', 
              'JSCP', 'MSFT', 'PPA', 'PVAL', 'RDVI', 'SPLG', 'SPSM', 'SPYV', 
              'STXE', 'TOUS', 'QQQ', 'QYLD']
    
    # Run analysis with Schwab API enabled
    results_df = analyze_sentiment_dual_source(tickers, use_schwab=True)
    
    # Display results
    print("\n" + "="*120)
    print("DUAL-SOURCE SENTIMENT ANALYSIS")
    print("="*120)
    print(results_df.to_string(index=False))
    
    # Summary
    sentiment_counts = results_df['Sentiment'].value_counts()
    print(f"\nSUMMARY:")
    for sentiment, count in sentiment_counts.items():
        print(f"{sentiment.capitalize()}: {count}")
    
    # Data source breakdown
    source_counts = results_df['Source'].value_counts()
    print(f"\nDATA SOURCES:")
    for source, count in source_counts.items():
        print(f"  {source}: {count}")
    
    # Show most interesting signals
    interesting = results_df[results_df['Signals'] != 'neutral']
    if len(interesting) > 0:
        print(f"\nTICKERS WITH CLEAR SIGNALS:")
        for _, row in interesting.iterrows():
            print(f"  {row['Ticker']}: {row['Sentiment']} - {row['Signals']}")