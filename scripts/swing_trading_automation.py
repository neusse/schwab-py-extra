import yfinance as yf
import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
import tabulate
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
#TICKERS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN']  # Your holdings

AI_tickers = """
SPY
TLT
BIL
AMZN
MPWR
AMT
BLK
CMG
PRU
ITB
V
TIP
XHB
SCHD
DLR
AMT
BLK
PRU
CTAS
WM
COR
TJX
KDP
TLT
TIP
XLV
GLD
VNQ
FRO
UPS
CNXC
"""



# Basic operation - split on whitespace
TICKERS = AI_tickers.split()

TIMEFRAME = 'hourly'  # 'daily' or 'hourly'

# Indicator Parameters
SUPERTREND_PERIOD = 10
SUPERTREND_MULTIPLIER = 3.0
BB_LENGTH = 20
BB_STDDEV = 2.0
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Caching
USE_CACHE = True
CACHE_DIR = 'market_data_cache'

# Data periods (will fetch double what's needed)
MIN_PERIODS = max(SUPERTREND_PERIOD, BB_LENGTH, MACD_SLOW) * 2

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def ensure_cache_dir():
    """Create cache directory if it doesn't exist"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_filename(ticker, timeframe):
    """Generate cache filename"""
    return os.path.join(CACHE_DIR, f"{ticker}_{timeframe}.pkl")

def is_cache_valid(filename, max_age_hours=1):
    """Check if cache file is recent enough"""
    if not os.path.exists(filename):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getmtime(filename))
    age = datetime.now() - file_time
    return age < timedelta(hours=max_age_hours)

# =============================================================================
# INDICATOR CALCULATIONS
# =============================================================================
def calculate_atr(high, low, close, period):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

def calculate_supertrend(df, period=10, multiplier=3.0):
    """Calculate SuperTrend indicator"""
    high, low, close = df['High'], df['Low'], df['Close']
    hl2 = (high + low) / 2
    
    atr = calculate_atr(high, low, close, period)
    
    # Calculate upper and lower bands
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Initialize SuperTrend
    supertrend = pd.Series(index=df.index, dtype=float)
    trend = pd.Series(index=df.index, dtype=int)
    
    # Calculate SuperTrend
    for i in range(1, len(df)):
        # Upper band calculation
        if close.iloc[i-1] <= upper_band.iloc[i-1]:
            upper_band.iloc[i] = min(upper_band.iloc[i], upper_band.iloc[i-1])
        
        # Lower band calculation  
        if close.iloc[i-1] >= lower_band.iloc[i-1]:
            lower_band.iloc[i] = max(lower_band.iloc[i], lower_band.iloc[i-1])
        
        # Trend calculation
        if i == 1:
            trend.iloc[i] = 1
        else:
            if trend.iloc[i-1] == -1 and close.iloc[i] > lower_band.iloc[i-1]:
                trend.iloc[i] = 1
            elif trend.iloc[i-1] == 1 and close.iloc[i] < upper_band.iloc[i-1]:
                trend.iloc[i] = -1
            else:
                trend.iloc[i] = trend.iloc[i-1]
        
        # SuperTrend value
        if trend.iloc[i] == 1:
            supertrend.iloc[i] = lower_band.iloc[i]
        else:
            supertrend.iloc[i] = upper_band.iloc[i]
    
    return supertrend, trend, upper_band, lower_band

def calculate_bollinger_bands(df, length=20, std_dev=2.0):
    """Calculate Bollinger Bands"""
    close = df['Close']
    sma = close.rolling(window=length).mean()
    std = close.rolling(window=length).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return sma, upper_band, lower_band

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    close = df['Close']
    
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

# =============================================================================
# SIGNAL GENERATION
# =============================================================================
def get_supertrend_signal(trend):
    """Generate SuperTrend buy/sell signals"""
    if len(trend) < 2:
        return "HOLD"
    
    current_trend = trend.iloc[-1]
    previous_trend = trend.iloc[-2]
    
    if previous_trend == -1 and current_trend == 1:
        return "BUY"
    elif previous_trend == 1 and current_trend == -1:
        return "SELL"
    else:
        return "HOLD"

def get_bollinger_signal(df, upper_band, lower_band):
    """Generate Bollinger Bands buy/sell signals"""
    if len(df) < 2:
        return "HOLD"
    
    current_close = df['Close'].iloc[-1]
    current_high = df['High'].iloc[-1]
    current_low = df['Low'].iloc[-1]
    
    current_upper = upper_band.iloc[-1]
    current_lower = lower_band.iloc[-1]
    
    # Buy when price touches/penetrates upper band
    if current_high >= current_upper or current_close >= current_upper:
        return "BUY"
    # Sell when price touches/penetrates lower band
    elif current_low <= current_lower or current_close <= current_lower:
        return "SELL"
    else:
        return "HOLD"

def get_macd_signal(histogram):
    """Generate MACD buy/sell signals"""
    if len(histogram) < 2:
        return "HOLD"
    
    current_hist = histogram.iloc[-1]
    previous_hist = histogram.iloc[-2]
    
    # Buy when histogram crosses above 0
    if previous_hist <= 0 and current_hist > 0:
        return "BUY"
    # Sell when histogram crosses below 0
    elif previous_hist >= 0 and current_hist < 0:
        return "SELL"
    else:
        return "HOLD"

# =============================================================================
# DATA FETCHING
# =============================================================================
def fetch_data(ticker, timeframe, use_cache=True):
    """Fetch stock data with caching"""
    ensure_cache_dir()
    cache_file = get_cache_filename(ticker, timeframe)
    
    # Try to load from cache
    if use_cache and is_cache_valid(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            pass  # Cache failed, fetch fresh data
    
    # Fetch fresh data
    try:
        if timeframe == 'daily':
            # Fetch enough daily data
            data = yf.download(ticker, period=f"{MIN_PERIODS*2}d", interval="1d")
        else:  # hourly
            # Fetch enough hourly data
            data = yf.download(ticker, period=f"{MIN_PERIODS//4}d", interval="1h")
        
        if data.empty:
            raise ValueError(f"No data found for {ticker}")
        
        # Flatten MultiIndex columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        else:
            # Handle case where columns might be tuples but not MultiIndex
            if len(data.columns) > 0 and isinstance(data.columns[0], tuple):
                data.columns = [col[0] for col in data.columns]
        
        # Ensure we have the required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}. Available: {list(data.columns)}")
        
        # Cache the data
        if use_cache:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        
        return data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================
def analyze_ticker(ticker):
    """Analyze a single ticker and return signals"""
    print(f"Analyzing {ticker}...")
    
    # Fetch data
    df = fetch_data(ticker, TIMEFRAME, USE_CACHE)
    if df is None or df.empty:
        return {
            'Ticker': ticker,
            'Current_Price': 'N/A',
            'SuperTrend_Signal': 'ERROR',
            'SuperTrend_Value': 'N/A',
            'BB_Signal': 'ERROR',
            'BB_Position': 'N/A',
            'MACD_Signal': 'ERROR',
            'MACD_Histogram': 'N/A',
            'Last_Updated': 'N/A'
        }
    
    try:
        # Calculate indicators
        supertrend, trend, st_upper, st_lower = calculate_supertrend(
            df, SUPERTREND_PERIOD, SUPERTREND_MULTIPLIER
        )
        bb_sma, bb_upper, bb_lower = calculate_bollinger_bands(
            df, BB_LENGTH, BB_STDDEV
        )
        macd_line, signal_line, histogram = calculate_macd(
            df, MACD_FAST, MACD_SLOW, MACD_SIGNAL
        )
        
        # Generate signals
        st_signal = get_supertrend_signal(trend)
        bb_signal = get_bollinger_signal(df, bb_upper, bb_lower)
        macd_signal = get_macd_signal(histogram)
        
        # Get current values
        current_price = df['Close'].iloc[-1]
        current_supertrend = supertrend.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        # Determine BB position
        current_close = df['Close'].iloc[-1]
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]
        current_bb_sma = bb_sma.iloc[-1]
        
        if current_close > current_bb_upper:
            bb_position = "Above Upper"
        elif current_close < current_bb_lower:
            bb_position = "Below Lower"
        elif current_close > current_bb_sma:
            bb_position = "Above Middle"
        else:
            bb_position = "Below Middle"
        
        return {
            'Ticker': ticker,
            'Current_Price': f"${current_price:.2f}",
            'SuperTrend_Signal': st_signal,
            'SuperTrend_Value': f"${current_supertrend:.2f}",
            'BB_Signal': bb_signal,
            'BB_Position': bb_position,
            'MACD_Signal': macd_signal,
            'MACD_Histogram': f"{current_histogram:.4f}",
            'Last_Updated': df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")
        return {
            'Ticker': ticker,
            'Current_Price': 'N/A',
            'SuperTrend_Signal': 'ERROR',
            'SuperTrend_Value': 'N/A',
            'BB_Signal': 'ERROR',
            'BB_Position': 'N/A',
            'MACD_Signal': 'ERROR',
            'MACD_Histogram': 'N/A',
            'Last_Updated': 'N/A'
        }

# =============================================================================
# OUTPUT FUNCTIONS
# =============================================================================
def display_results(results):
    """Display results in console table"""
    headers = [
        'Ticker', 'Price', 'ST Signal', 'ST Value', 
        'BB Signal', 'BB Position', 'MACD Signal', 'MACD Hist', 'Updated'
    ]
    
    table_data = []
    for result in results:
        row = [
            result['Ticker'],
            result['Current_Price'],
            result['SuperTrend_Signal'],
            result['SuperTrend_Value'],
            result['BB_Signal'],
            result['BB_Position'],
            result['MACD_Signal'],
            result['MACD_Histogram'],
            result['Last_Updated']
        ]
        table_data.append(row)
    
    print("\n" + "="*120)
    print(f"TRADING SIGNALS ANALYSIS - {TIMEFRAME.upper()} TIMEFRAME")
    print("="*120)
    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    print("="*120)

def save_to_csv(results):
    """Save results to CSV with timestamp"""
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trading_signals_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"\nResults saved to: {filename}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    print(f"Starting trading analysis for {len(TICKERS)} tickers...")
    print(f"Timeframe: {TIMEFRAME}")
    print(f"Cache enabled: {USE_CACHE}")
    
    results = []
    
    for ticker in TICKERS:
        result = analyze_ticker(ticker)
        results.append(result)
    
    # Display results
    display_results(results)
    
    # Save to CSV
    #save_to_csv(results)
    
    print(f"\nAnalysis complete! Processed {len(results)} tickers.")

if __name__ == "__main__":
    # Install required packages if needed
    try:
        import tabulate
    except ImportError:
        print("Installing required package: tabulate")
        os.system("pip install tabulate")
        import tabulate
    
    main()
