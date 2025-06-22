import yfinance as yf
import pandas as pd
import pandas_ta as ta
from backtesting import Strategy, Backtest
import numpy as np

class TrendIndicators:
    """Class to handle trend-following indicators."""
    
    @staticmethod
    def dual_moving_averages(df, fast_period=20, slow_period=50):
        """Calculate fast and slow moving averages."""
        df['MA_Fast'] = df['Close'].rolling(window=fast_period).mean()
        df['MA_Slow'] = df['Close'].rolling(window=slow_period).mean()
        return df
    
    @staticmethod
    def atr(df, window=14):
        """Calculate Average True Range for volatility-based stops."""
        try:
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=window)
        except:
            # Manual ATR calculation
            df['TR1'] = df['High'] - df['Low']
            df['TR2'] = abs(df['High'] - df['Close'].shift(1))
            df['TR3'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['TR1', 'TR2', 'TR3']].max(axis=1)
            df['ATR'] = df['TR'].rolling(window=window).mean()
            df = df.drop(['TR1', 'TR2', 'TR3', 'TR'], axis=1)
        return df
    
    @staticmethod
    def trend_strength(df, window=20):
        """Calculate trend strength using linear regression slope."""
        def calculate_slope(series):
            if len(series) < 2:
                return 0
            x = np.arange(len(series))
            y = series.values
            slope = np.polyfit(x, y, 1)[0]
            return slope
        
        df['Trend_Strength'] = df['Close'].rolling(window=window).apply(calculate_slope, raw=False)
        return df
    
    @staticmethod
    def rsi(df, window=14):
        """Calculate RSI for momentum confirmation."""
        try:
            df['RSI'] = ta.rsi(df['Close'], length=window)
        except:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
        return df

class TrendSignalGenerator:
    """Class to generate trend-following signals."""
    
    @staticmethod
    def generate_signals(df):
        """Generate trend-following signals."""
        signals = np.zeros(len(df))
        
        for i in range(50, len(df)):  # Need enough history for reliable signals
            # Current values
            ma_fast = df['MA_Fast'].iloc[i]
            ma_slow = df['MA_Slow'].iloc[i]
            prev_ma_fast = df['MA_Fast'].iloc[i-1]
            prev_ma_slow = df['MA_Slow'].iloc[i-1]
            trend_strength = df['Trend_Strength'].iloc[i]
            rsi = df['RSI'].iloc[i]
            close = df['Close'].iloc[i]
            
            if pd.isna(ma_fast) or pd.isna(ma_slow) or pd.isna(trend_strength):
                continue
            
            # Golden Cross: Fast MA crosses above Slow MA
            golden_cross = (prev_ma_fast <= prev_ma_slow and ma_fast > ma_slow)
            
            # Death Cross: Fast MA crosses below Slow MA
            death_cross = (prev_ma_fast >= prev_ma_slow and ma_fast < ma_slow)
            
            # Strong trend confirmation
            strong_uptrend = trend_strength > 0.5 and close > ma_fast > ma_slow
            strong_downtrend = trend_strength < -0.5 and close < ma_fast < ma_slow
            
            # RSI momentum confirmation (avoid extremes)
            rsi_bullish = 40 < rsi < 80
            rsi_bearish = 20 < rsi < 60
            
            # Long signal: Golden cross with strong uptrend
            if golden_cross and strong_uptrend and rsi_bullish:
                signals[i] = 1
            
            # Short signal: Death cross with strong downtrend  
            elif death_cross and strong_downtrend and rsi_bearish:
                signals[i] = -1
        
        df['Signal'] = signals
        return df

class DataManager:
    """Class to handle data fetching and processing."""
    
    @staticmethod
    def get_stock_data(ticker, period='2y', interval='1d'):
        """Fetch daily stock data - longer timeframe for trend following."""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                raise ValueError(f"No data found for ticker {ticker}")
            
            return df
        except Exception as e:
            raise Exception(f"Error fetching data for {ticker}: {str(e)}")
    
    @staticmethod
    def prepare_data(ticker, period='2y', interval='1d'):
        """Fetch and prepare data with trend indicators."""
        df = DataManager.get_stock_data(ticker, period, interval)
        
        print(f"Data shape: {df.shape}")
        
        # Calculate trend indicators
        df = TrendIndicators.dual_moving_averages(df)
        df = TrendIndicators.atr(df)
        df = TrendIndicators.trend_strength(df)
        df = TrendIndicators.rsi(df)
        
        # Generate signals
        df = TrendSignalGenerator.generate_signals(df)
        
        # Drop rows with NaN values
        df = df.dropna()
        
        print(f"Data shape after processing: {df.shape}")
        print(f"Buy signals: {(df['Signal'] == 1).sum()}")
        print(f"Sell signals: {(df['Signal'] == -1).sum()}")
        
        return df

class TrendFollowingStrategy(Strategy):
    """Long-term trend following strategy with minimal trades."""
    
    # Strategy parameters
    position_size = 0.95
    atr_multiplier = 2.0  # Stop loss based on ATR
    min_trade_duration = 30  # Minimum days to hold (avoid whipsaws)
    
    def init(self):
        """Initialize strategy indicators."""
        self.signal = self.I(lambda: self.data.Signal)
        self.ma_fast = self.I(lambda: self.data.MA_Fast)
        self.ma_slow = self.I(lambda: self.data.MA_Slow)
        self.atr = self.I(lambda: self.data.ATR)
        self.close = self.I(lambda: self.data.Close)
        
    def next(self):
        """Execute strategy logic for each bar."""
        # Don't exit trades too early (minimum holding period)
        if len(self.trades) > 0:
            last_trade = self.trades[-1]
            bars_since_entry = len(self.data) - 1 - last_trade.entry_bar
            
            # Only allow early exit if trend has clearly reversed
            if bars_since_entry < self.min_trade_duration:
                ma_fast = self.ma_fast[-1]
                ma_slow = self.ma_slow[-1]
                
                # Keep long position if fast MA still above slow MA
                if last_trade.is_long and ma_fast > ma_slow:
                    return
                # Keep short position if fast MA still below slow MA
                elif last_trade.is_short and ma_fast < ma_slow:
                    return
        
        current_signal = self.signal[-1]
        current_price = self.close[-1]
        current_atr = self.atr[-1]
        
        # Close opposite position before opening new one
        if len(self.trades) > 0:
            last_trade = self.trades[-1]
            if (current_signal == 1 and last_trade.is_short) or \
               (current_signal == -1 and last_trade.is_long):
                last_trade.close()
        
        # Only enter if no position or we just closed one
        if len(self.trades) == 0:
            # Long entry
            if current_signal == 1:
                stop_loss = current_price - (current_atr * self.atr_multiplier)
                self.buy(size=self.position_size, sl=stop_loss)
            
            # Short entry
            elif current_signal == -1:
                stop_loss = current_price + (current_atr * self.atr_multiplier)
                self.sell(size=self.position_size, sl=stop_loss)

def run_backtest(ticker='AAPL', period='2y', interval='1d', cash=10000, commission=0.001):
    """Run backtest for the given ticker."""
    print(f"Preparing trend following strategy for {ticker}...")
    df = DataManager.prepare_data(ticker, period, interval)
    
    if df.empty:
        print("No data available for backtesting")
        return None, None
    
    print(f"Running trend following backtest...")
    bt = Backtest(
        df, 
        TrendFollowingStrategy,
        cash=cash,
        commission=commission
    )
    
    results = bt.run()
    return results, bt

# Example usage
if __name__ == "__main__":
    ticker = 'NVDA'
    
    try:
        results, backtest = run_backtest(ticker, period='2y', interval='1d')
        
        if results is not None:
            print("\n" + "="*50)
            print(f"TREND FOLLOWING RESULTS FOR {ticker}")
            print("="*50)
            print(results)
            
            # Show some key metrics
            if hasattr(results, '_trades') and not results._trades.empty:
                print(f"\nKey Statistics:")
                print(f"Total Trades: {len(results._trades)}")
                print(f"Win Rate: {results['Win Rate [%]']:.1f}%")
                print(f"Return: {results['Return [%]']:.2f}%")
                print(f"Max Drawdown: {results['Max. Drawdown [%]']:.2f}%")
                print(f"Sharpe Ratio: {results['Sharpe Ratio']:.2f}")
                
                # Calculate average holding period
                if len(results._trades) > 0:
                    avg_duration = results._trades['Duration'].mean()
                    print(f"Average Trade Duration: {avg_duration}")
            
            # Uncomment to show plot
            # backtest.plot()
        
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
