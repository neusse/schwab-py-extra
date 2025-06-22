import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta
from rich import print
from typing import Tuple, Optional
import warnings
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from mplfinance import plot as mpf_plot
import mplfinance as mpf

warnings.filterwarnings('ignore')


class DataFetcher:
    """Handle data fetching operations"""
    
    @staticmethod
    def fetch_price_data(symbol: str, period: str = "1mo", interval: str = "5m") -> pd.DataFrame:
        """Fetch historical price data from yfinance"""
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Flatten multi-level columns if they exist
            if isinstance(df.columns, pd.MultiIndex):
                # Keep only the first level (Price level: Close, High, Low, Open, Volume)
                df.columns = df.columns.get_level_values(0)
            
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            latest_timestamp = df.index[-1]
            print(f"\n{symbol} Latest bar timestamp: {latest_timestamp}")
            print(f"Data shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()


class TechnicalIndicators:
    """Calculate various technical indicators"""
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
        """Calculate Average True Range"""
        df = df.copy()
        atr_result = ta.atr(df["High"], df["Low"], df["Close"], length=length)
        if atr_result is not None:
            df["ATR"] = atr_result
        else:
            # Fallback ATR calculation
            df["TR"] = np.maximum(
                df["High"] - df["Low"],
                np.maximum(
                    abs(df["High"] - df["Close"].shift(1)),
                    abs(df["Low"] - df["Close"].shift(1))
                )
            )
            df["ATR"] = df["TR"].rolling(window=length).mean()
            df.drop("TR", axis=1, inplace=True)
        return df
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, short_window: int = 6, 
                      long_window: int = 13, signal_window: int = 5) -> pd.DataFrame:
        """Calculate MACD indicator"""
        df = df.copy()
        df["EMA12"] = df["Close"].ewm(span=short_window, adjust=False).mean()
        df["EMA26"] = df["Close"].ewm(span=long_window, adjust=False).mean()
        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal_Line"] = df["MACD"].ewm(span=signal_window, adjust=False).mean()
        return TechnicalIndicators.calculate_atr(df)
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Calculate RSI indicator"""
        df = df.copy()
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        return TechnicalIndicators.calculate_atr(df)
    
    @staticmethod
    def calculate_supertrend(df: pd.DataFrame, length: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
        """Calculate Supertrend indicator"""
        df = df.copy()
        
        try:
            supertrend = ta.supertrend(
                df["High"], df["Low"], df["Close"], length=length, multiplier=multiplier
            )
            
            if supertrend is not None and not supertrend.empty:
                # Try different column name formats
                supertrend_col = None
                direction_col = None
                
                for col in supertrend.columns:
                    if 'SUPERT_' in col and not 'd_' in col:
                        supertrend_col = col
                    elif 'SUPERTd_' in col:
                        direction_col = col
                
                if supertrend_col and direction_col:
                    df["supertrend"] = supertrend[supertrend_col]
                    df["direction"] = supertrend[direction_col]
                else:
                    # Fallback: manual supertrend calculation
                    df = TechnicalIndicators._manual_supertrend(df, length, multiplier)
            else:
                # Fallback: manual supertrend calculation
                df = TechnicalIndicators._manual_supertrend(df, length, multiplier)
                
        except Exception as e:
            print(f"Supertrend calculation failed, using manual method: {e}")
            df = TechnicalIndicators._manual_supertrend(df, length, multiplier)
            
        return TechnicalIndicators.calculate_atr(df)
    
    @staticmethod
    def _manual_supertrend(df: pd.DataFrame, length: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
        """Manual Supertrend calculation as fallback"""
        # Calculate ATR first
        df = TechnicalIndicators.calculate_atr(df, length)
        
        # Calculate basic upper and lower bands
        hl2 = (df["High"] + df["Low"]) / 2
        df["basic_ub"] = hl2 + (multiplier * df["ATR"])
        df["basic_lb"] = hl2 - (multiplier * df["ATR"])
        
        # Calculate final upper and lower bands
        df["final_ub"] = df["basic_ub"]
        df["final_lb"] = df["basic_lb"]
        
        for i in range(1, len(df)):
            # Final Upper Band
            if df["basic_ub"].iloc[i] < df["final_ub"].iloc[i-1] or df["Close"].iloc[i-1] > df["final_ub"].iloc[i-1]:
                df.loc[df.index[i], "final_ub"] = df["basic_ub"].iloc[i]
            else:
                df.loc[df.index[i], "final_ub"] = df["final_ub"].iloc[i-1]
            
            # Final Lower Band
            if df["basic_lb"].iloc[i] > df["final_lb"].iloc[i-1] or df["Close"].iloc[i-1] < df["final_lb"].iloc[i-1]:
                df.loc[df.index[i], "final_lb"] = df["basic_lb"].iloc[i]
            else:
                df.loc[df.index[i], "final_lb"] = df["final_lb"].iloc[i-1]
        
        # Calculate Supertrend
        df["supertrend"] = df["final_ub"]
        df["direction"] = 1
        
        for i in range(1, len(df)):
            if df["Close"].iloc[i] <= df["final_ub"].iloc[i]:
                df.loc[df.index[i], "supertrend"] = df["final_ub"].iloc[i]
                df.loc[df.index[i], "direction"] = -1
            else:
                df.loc[df.index[i], "supertrend"] = df["final_lb"].iloc[i]
                df.loc[df.index[i], "direction"] = 1
        
        # Clean up temporary columns
        df.drop(["basic_ub", "basic_lb", "final_ub", "final_lb"], axis=1, inplace=True)
        
        return df


class TradingStrategies:
    """Various trading strategies"""
    
    @staticmethod
    def supertrend_signals(df: pd.DataFrame, length: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
        """Generate Supertrend buy/sell signals"""
        df = TechnicalIndicators.calculate_supertrend(df, length, multiplier)
        
        df["Signal"] = 0
        df.loc[(df["Close"] > df["supertrend"]) & (df["direction"] == 1), "Signal"] = 1  # Buy
        df.loc[(df["Close"] < df["supertrend"]) & (df["direction"] == -1), "Signal"] = -1  # Sell
        df["Position"] = df["Signal"].diff()
        
        return df
    
    @staticmethod
    def macd_signals(df: pd.DataFrame) -> pd.DataFrame:
        """Generate MACD buy/sell signals"""
        df = TechnicalIndicators.calculate_macd(df)
        
        # Initialize signals
        df["Signal"] = 0
        
        # Create boolean masks for cleaner logic
        macd_above_signal = df["MACD"] > df["Signal_Line"]
        macd_below_signal = df["MACD"] <= df["Signal_Line"]
        
        # Set signals based on MACD crossovers
        df.loc[macd_above_signal, "Signal"] = 1  # Buy when MACD > Signal Line
        df.loc[macd_below_signal, "Signal"] = -1  # Sell when MACD <= Signal Line
        
        # Generate position changes (buy/sell triggers)
        df["Position"] = 0
        df["Signal_prev"] = df["Signal"].shift(1).fillna(0)
        
        # Position change only occurs when signal changes
        df.loc[(df["Signal"] == 1) & (df["Signal_prev"] != 1), "Position"] = 1  # New buy signal
        df.loc[(df["Signal"] == -1) & (df["Signal_prev"] != -1), "Position"] = -1  # New sell signal
        
        # Clean up temporary column
        df.drop("Signal_prev", axis=1, inplace=True)
        
        return df
    
    @staticmethod
    def rsi_signals(df: pd.DataFrame, oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
        """Generate RSI buy/sell signals"""
        df = TechnicalIndicators.calculate_rsi(df)
        
        df["Signal"] = 0
        df.loc[df["RSI"] < oversold, "Signal"] = 1  # Buy (oversold)
        df.loc[df["RSI"] > overbought, "Signal"] = -1  # Sell (overbought)
        df["Position"] = df["Signal"].diff()
        
        return df
    
    @staticmethod
    def resistance_breakout_signals(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Generate resistance breakout signals"""
        df = TechnicalIndicators.calculate_atr(df)
        
        # Calculate indicators
        df["sma"] = ta.sma(df["Close"], length=period)
        df["resistance"] = df["Close"].rolling(window=period).max()
        df["vol_sma"] = ta.sma(df["Volume"], length=period)
        df["breakout_prob"] = (df["Volume"] / df["vol_sma"]) * 100
        
        # Generate signals
        df["Signal"] = 0
        df.loc[
            (df["Close"] > df["resistance"]) & (df["Volume"] > df["vol_sma"]),
            "Signal"
        ] = 1  # Buy
        df.loc[
            (df["Close"] < df["sma"]) & (df["Volume"] > df["vol_sma"]),
            "Signal"
        ] = -1  # Sell
        
        df["Position"] = df["Signal"].diff()
        return df


class ChandelierExitIndicator:
    """Chandelier Exit Indicator implementation"""
    
    def __init__(self, atr_period: int = 22, atr_multiplier: float = 3.0, 
                 use_close: bool = True, await_bar_confirmation: bool = True):
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.use_close = use_close
        self.await_bar_confirmation = await_bar_confirmation
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Chandelier Exit levels"""
        df = df.copy()
        
        # Calculate ATR using the robust method
        df = TechnicalIndicators.calculate_atr(df, self.atr_period)
        
        # Multiply ATR by the multiplier
        df["ATR_multiplied"] = df["ATR"] * self.atr_multiplier
        
        # Calculate initial stops
        if self.use_close:
            df["LongStop"] = df["Close"].rolling(window=self.atr_period).max() - df["ATR_multiplied"]
            df["ShortStop"] = df["Close"].rolling(window=self.atr_period).min() + df["ATR_multiplied"]
        else:
            df["LongStop"] = df["High"].rolling(window=self.atr_period).max() - df["ATR_multiplied"]
            df["ShortStop"] = df["Low"].rolling(window=self.atr_period).min() + df["ATR_multiplied"]
        
        # Adjust stops to prevent them from moving against the trend
        df["LongStopPrev"] = df["LongStop"].shift(1)
        df["ShortStopPrev"] = df["ShortStop"].shift(1)
        
        # Fill NaN values in the first row
        df["LongStopPrev"] = df["LongStopPrev"].fillna(df["LongStop"])
        df["ShortStopPrev"] = df["ShortStopPrev"].fillna(df["ShortStop"])
        
        # Adjust long stop
        close_prev = df["Close"].shift(1)
        df["LongStop"] = np.where(
            close_prev > df["LongStopPrev"],
            np.maximum(df["LongStop"], df["LongStopPrev"]),
            df["LongStop"]
        )
        
        # Adjust short stop
        df["ShortStop"] = np.where(
            close_prev < df["ShortStopPrev"],
            np.minimum(df["ShortStop"], df["ShortStopPrev"]),
            df["ShortStop"]
        )
        
        # Determine direction
        df["Dir"] = np.where(
            df["Close"] > df["ShortStopPrev"],
            1,
            np.where(df["Close"] < df["LongStopPrev"], -1, np.nan)
        )
        df["Dir"] = df["Dir"].ffill().fillna(1)  # Fill with 1 for initial values
        
        # Generate signals
        dir_prev = df["Dir"].shift(1).fillna(0)
        df["BuySignal"] = (df["Dir"] == 1) & (dir_prev == -1)
        df["SellSignal"] = (df["Dir"] == -1) & (dir_prev == 1)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        df = self.calculate(df)
        
        df["Signal"] = 0
        df.loc[df["BuySignal"], "Signal"] = 1
        df.loc[df["SellSignal"], "Signal"] = -1
        df["Position"] = df["Signal"].diff()
        
        return df


class BacktestEngine:
    """Backtesting engine for trading strategies"""
    
    @staticmethod
    def simple_backtest(df: pd.DataFrame, take_profit_pct: float = 0.05, 
                       stop_loss_pct: float = 0.06, initial_capital: float = 10000.0) -> Tuple:
        """Simple backtest with fixed take profit and stop loss"""
        capital = initial_capital
        shares = 0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        entry_price = 0
        profit_exits = 0
        sl_exits = 0
        
        for _, row in df.iterrows():
            current_price = row["Close"]
            
            # Entry signals
            if row["Position"] == 1.0 and capital > 0 and shares == 0:  # Buy signal
                shares = capital / current_price
                capital = 0
                entry_price = current_price
                
            elif row["Position"] == -1.0 and shares > 0:  # Sell signal
                exit_price = current_price
                capital = shares * exit_price
                shares = 0
                total_trades += 1
                
                if exit_price > entry_price:
                    winning_trades += 1
                else:
                    losing_trades += 1
            
            # Take profit and stop loss checks
            elif shares > 0:
                # Take profit
                if current_price >= entry_price * (1 + take_profit_pct):
                    capital = shares * current_price
                    shares = 0
                    total_trades += 1
                    winning_trades += 1
                    profit_exits += 1
                
                # Stop loss
                elif current_price <= entry_price * (1 - stop_loss_pct):
                    capital = shares * current_price
                    shares = 0
                    total_trades += 1
                    losing_trades += 1
                    sl_exits += 1
        
        # Close any remaining position
        if shares > 0:
            final_price = df.iloc[-1]["Close"]
            capital = shares * final_price
            total_trades += 1
            
            if final_price > entry_price:
                winning_trades += 1
            else:
                losing_trades += 1
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return (capital, total_trades, winning_trades, losing_trades, 
                win_rate, profit_exits, sl_exits)
    
    @staticmethod
    def trailing_stop_backtest(df: pd.DataFrame, tsl_factor: float = 2.0, 
                             initial_capital: float = 10000.0) -> Tuple:
        """Backtest with trailing stop loss using ATR"""
        capital = initial_capital
        shares = 0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        entry_price = 0
        sl_exits = 0
        in_position = False
        position_type = None
        highest_price = 0
        lowest_price = float('inf')
        
        for _, row in df.iterrows():
            current_price = row["Close"]
            current_atr = row.get("ATR", 0)
            
            # Handle NaN ATR values
            if pd.isna(current_atr) or current_atr == 0:
                current_atr = current_price * 0.02  # Use 2% as fallback
            
            if not in_position:
                # Long entry
                if row.get("Position", 0) == 1.0 and capital > 0:
                    shares = capital / current_price
                    capital = 0
                    entry_price = current_price
                    highest_price = current_price
                    in_position = True
                    position_type = "long"
                
                # Short entry
                elif row.get("Position", 0) == -1.0 and capital > 0:
                    shares = capital / current_price
                    capital = 0
                    entry_price = current_price
                    lowest_price = current_price
                    in_position = True
                    position_type = "short"
            
            else:
                # Update trailing stops
                if position_type == "long":
                    if current_price > highest_price:
                        highest_price = current_price
                    
                    tsl = highest_price - (current_atr * tsl_factor)
                    
                    if current_price < tsl:
                        capital = shares * current_price
                        shares = 0
                        total_trades += 1
                        in_position = False
                        position_type = None
                        sl_exits += 1
                        
                        if current_price > entry_price:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                
                elif position_type == "short":
                    if current_price < lowest_price:
                        lowest_price = current_price
                    
                    tsl = lowest_price + (current_atr * tsl_factor)
                    
                    if current_price > tsl:
                        capital = shares * current_price
                        shares = 0
                        total_trades += 1
                        in_position = False
                        position_type = None
                        sl_exits += 1
                        
                        if current_price < entry_price:
                            winning_trades += 1
                        else:
                            losing_trades += 1
        
        # Close remaining position
        if shares > 0:
            final_price = df.iloc[-1]["Close"]
            capital = shares * final_price
            total_trades += 1
            
            if ((position_type == "long" and final_price > entry_price) or 
                (position_type == "short" and final_price < entry_price)):
                winning_trades += 1
            else:
                losing_trades += 1
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return (capital, total_trades, winning_trades, losing_trades, win_rate, sl_exits)


class ChartGenerator:
    """Generate candlestick charts with trading signals"""
    
    @staticmethod
    def create_signal_chart(df: pd.DataFrame, ticker: str, strategy: str) -> None:
        """Create candlestick chart with buy/sell signals"""
        try:
            # Prepare data for mplfinance - remove NaN values first
            chart_df = df.copy()
            
            # Ensure proper column names and datetime index
            chart_df = chart_df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            
            # Remove any NaN values that might cause issues
            chart_df = chart_df.dropna()
            
            if chart_df.empty:
                print(f"No valid data for chart: {ticker} {strategy}")
                return
            
            # Get the valid index range
            valid_index = chart_df.index
            
            # Create signal markers aligned with chart_df index
            buy_markers = pd.Series(index=valid_index, dtype=float)
            sell_markers = pd.Series(index=valid_index, dtype=float)
            
            # Get positions from original df, but only for valid index range
            if 'Position' in df.columns:
                # Reindex Position to match chart_df
                positions = df['Position'].reindex(valid_index)
                
                buy_mask = positions == 1.0
                sell_mask = positions == -1.0
                
                # Set marker positions only where we have buy/sell signals
                buy_markers[buy_mask] = chart_df.loc[buy_mask, 'Low'] * 0.995
                sell_markers[sell_mask] = chart_df.loc[sell_mask, 'High'] * 1.005
            
            # Create addplot for signals
            addplots = []
            
            # Add buy signals if any exist
            buy_clean = buy_markers.dropna()
            if not buy_clean.empty:
                buy_plot = mpf.make_addplot(
                    buy_markers,  # Keep full series with NaN for alignment
                    type='scatter',
                    markersize=100,
                    marker='^',
                    color='green'
                )
                addplots.append(buy_plot)
            
            # Add sell signals if any exist
            sell_clean = sell_markers.dropna()
            if not sell_clean.empty:
                sell_plot = mpf.make_addplot(
                    sell_markers,  # Keep full series with NaN for alignment
                    type='scatter',
                    markersize=100,
                    marker='v',
                    color='red'
                )
                addplots.append(sell_plot)
            
            # Add strategy-specific indicators with proper alignment
            if strategy.lower() == 'chandelier':
                if 'LongStop' in df.columns and 'ShortStop' in df.columns:
                    # Align indicators with chart_df index
                    long_stop = df['LongStop'].reindex(valid_index)
                    short_stop = df['ShortStop'].reindex(valid_index)
                    
                    # Only add if we have data
                    if not long_stop.dropna().empty:
                        long_stop_plot = mpf.make_addplot(
                            long_stop,
                            type='line',
                            color='blue',
                            width=1,
                            alpha=0.7
                        )
                        addplots.append(long_stop_plot)
                    
                    if not short_stop.dropna().empty:
                        short_stop_plot = mpf.make_addplot(
                            short_stop,
                            type='line',
                            color='orange',
                            width=1,
                            alpha=0.7
                        )
                        addplots.append(short_stop_plot)
            
            elif strategy.lower() == 'supertrend':
                if 'supertrend' in df.columns:
                    # Align supertrend with chart_df index
                    supertrend = df['supertrend'].reindex(valid_index)
                    if not supertrend.dropna().empty:
                        supertrend_plot = mpf.make_addplot(
                            supertrend,
                            type='line',
                            color='purple',
                            width=2
                        )
                        addplots.append(supertrend_plot)
            
            # Create the plot with error handling
            plot_kwargs = {
                'data': chart_df,
                'type': 'candle',
                'style': 'charles',
                'title': f'{ticker} - {strategy.title()} Strategy\nGreen ▲ = Buy, Red ▼ = Sell',
                'ylabel': 'Price ($)',
                'volume': True,
                'figsize': (15, 10),
                'savefig': f'{ticker}_{strategy}_chart.png'
            }
            
            if addplots:
                plot_kwargs['addplot'] = addplots
            
            mpf.plot(**plot_kwargs)
            
            print(f"Chart saved: {ticker}_{strategy}_chart.png")
            
        except Exception as e:
            print(f"Error creating chart for {ticker} {strategy}: {e}")
            # Fallback to basic matplotlib chart
            ChartGenerator._create_basic_chart(df, ticker, strategy)
    
    @staticmethod
    def _create_basic_chart(df: pd.DataFrame, ticker: str, strategy: str) -> None:
        """Fallback basic chart using matplotlib"""
        try:
            # Clean the data first - remove NaN values consistently
            clean_df = df.copy()
            
            # Remove rows where essential columns have NaN
            essential_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            clean_df = clean_df.dropna(subset=essential_cols)
            
            if clean_df.empty:
                print(f"No valid data for basic chart: {ticker} {strategy}")
                return
            
            # Create figure with subplots
            if strategy.lower() == 'macd' and 'MACD' in clean_df.columns:
                fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), 
                                                   gridspec_kw={'height_ratios': [3, 1, 1]})
                macd_panel = ax3
            else:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), 
                                             gridspec_kw={'height_ratios': [3, 1]})
                macd_panel = None
            
            # Main price chart
            ax1.plot(clean_df.index, clean_df['Close'], label='Close Price', 
                    linewidth=1.5, color='black')
            
            # Buy and sell signals - ensure alignment with clean_df
            if 'Position' in clean_df.columns:
                buy_signals = clean_df[clean_df['Position'] == 1.0]
                if not buy_signals.empty:
                    ax1.scatter(buy_signals.index, buy_signals['Close'], 
                               color='green', marker='^', s=120, label='Buy Signal', 
                               zorder=5, edgecolors='darkgreen', linewidth=0.5)
                
                sell_signals = clean_df[clean_df['Position'] == -1.0]
                if not sell_signals.empty:
                    ax1.scatter(sell_signals.index, sell_signals['Close'], 
                               color='red', marker='v', s=120, label='Sell Signal', 
                               zorder=5, edgecolors='darkred', linewidth=0.5)
            
            # Add strategy-specific indicators with proper alignment
            if strategy.lower() == 'supertrend' and 'supertrend' in clean_df.columns:
                # Only plot where we have valid supertrend data
                supertrend_valid = clean_df['supertrend'].dropna()
                if not supertrend_valid.empty:
                    ax1.plot(supertrend_valid.index, supertrend_valid.values, 
                            label='Supertrend', color='purple', linewidth=2, alpha=0.8)
            
            elif strategy.lower() == 'chandelier':
                if 'LongStop' in clean_df.columns:
                    long_stop_valid = clean_df['LongStop'].dropna()
                    if not long_stop_valid.empty:
                        ax1.plot(long_stop_valid.index, long_stop_valid.values, 
                                label='Long Stop', color='blue', linewidth=1.5, alpha=0.7)
                
                if 'ShortStop' in clean_df.columns:
                    short_stop_valid = clean_df['ShortStop'].dropna()
                    if not short_stop_valid.empty:
                        ax1.plot(short_stop_valid.index, short_stop_valid.values, 
                                label='Short Stop', color='orange', linewidth=1.5, alpha=0.7)
            
            ax1.set_title(f'{ticker} - {strategy.title()} Strategy\nGreen ▲ = Buy, Red ▼ = Sell', 
                         fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price ($)', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Volume chart with proper alignment
            colors = ['red' if clean_df['Close'].iloc[i] < clean_df['Open'].iloc[i] else 'green' 
                     for i in range(len(clean_df))]
            ax2.bar(clean_df.index, clean_df['Volume'], alpha=0.7, color=colors, width=0.8)
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # MACD panel if applicable
            if (macd_panel is not None and 'MACD' in clean_df.columns and 
                'Signal_Line' in clean_df.columns):
                
                # Only plot where we have valid MACD data
                macd_valid = clean_df[['MACD', 'Signal_Line']].dropna()
                if not macd_valid.empty:
                    macd_panel.plot(macd_valid.index, macd_valid['MACD'], 
                                   label='MACD', color='blue', linewidth=1.5)
                    macd_panel.plot(macd_valid.index, macd_valid['Signal_Line'], 
                                   label='Signal Line', color='red', linewidth=1.5)
                    macd_panel.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                    macd_panel.set_ylabel('MACD', fontsize=12)
                    macd_panel.legend()
                    macd_panel.grid(True, alpha=0.3)
                    ax2.set_xlabel('')  # Remove xlabel from volume panel
                    macd_panel.set_xlabel('Date', fontsize=12)
            else:
                ax2.set_xlabel('Date', fontsize=12)
            
            # Format x-axis for better date display
            for ax in [ax1, ax2] + ([macd_panel] if macd_panel else []):
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(f'{ticker}_{strategy}_basic_chart.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Basic chart saved: {ticker}_{strategy}_basic_chart.png")
            
        except Exception as e:
            print(f"Error creating basic chart for {ticker} {strategy}: {e}")


class TradingAnalyzer:
    """Main class to analyze trading strategies"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.backtest_engine = BacktestEngine()
        self.chart_generator = ChartGenerator()
    
    def get_last_signal(self, df: pd.DataFrame) -> Tuple[str, pd.Timestamp, float]:
        """Get the last significant trading signal"""
        signals = df[df["Position"].notna() & (df["Position"] != 0)]
        if signals.empty:
            return "No Signal", df.index[-1], df.iloc[-1]["Close"]
        
        last_signal = signals.iloc[-1]
        signal_type = "Buy" if last_signal["Position"] > 0 else "Sell"
        return signal_type, last_signal.name, last_signal["Close"]
    
    def analyze_ticker(self, ticker: str, strategy: str = "chandelier", 
                      initial_capital: float = 10000.0, period: str = "1mo", 
                      create_chart: bool = True) -> None:
        """Analyze a single ticker with specified strategy"""
        print(f"\n{'='*50}")
        print(f"Analyzing {ticker}")
        print(f"{'='*50}")
        
        # Fetch data
        df = self.data_fetcher.fetch_price_data(ticker, period=period)
        if df.empty:
            print(f"No data available for {ticker}")
            return
        
        # Apply strategy
        if strategy == "chandelier":
            ce = ChandelierExitIndicator()
            df = ce.generate_signals(df)
        elif strategy == "supertrend":
            df = TradingStrategies.supertrend_signals(df)
        elif strategy == "macd":
            df = TradingStrategies.macd_signals(df)
        elif strategy == "rsi":
            df = TradingStrategies.rsi_signals(df)
        elif strategy == "resistance":
            df = TradingStrategies.resistance_breakout_signals(df)
        else:
            print(f"Unknown strategy: {strategy}")
            return
        
        # Create chart if requested
        if create_chart:
            self.chart_generator.create_signal_chart(df, ticker, strategy)
        
        # Backtest
        (final_capital, total_trades, winning_trades, losing_trades, 
         win_rate, sl_exits) = self.backtest_engine.trailing_stop_backtest(
            df, tsl_factor=2.0, initial_capital=initial_capital
        )
        
        # Calculate P/L
        pl_percent = ((final_capital - initial_capital) / initial_capital) * 100
        
        # Get last signal
        last_signal, last_date, last_price = self.get_last_signal(df)
        
        # Print results
        print(f"Strategy: {strategy.title()}")
        print(f"Final Capital: ${final_capital:.2f}")
        print(f"P/L Percent: {pl_percent:.2f}%")
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Stop Loss Exits: {sl_exits}")
        print(f"Last Signal: {last_signal} on {last_date} at ${last_price:.2f}")
    
    def analyze_multiple_tickers(self, tickers: list, strategy: str = "chandelier", 
                               initial_capital: float = 1000.0, create_charts: bool = True) -> None:
        """Analyze multiple tickers"""
        for ticker in tickers:
            try:
                self.analyze_ticker(ticker, strategy, initial_capital, create_chart=create_charts)
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")


def main():
    """Main function"""
    symbol_list = [
        "NVDA", "AAPL", "IBM", "MSFT", "TSLA", "AMD", "QQQ", 
        "SPLG", "BAC", "SPY", "SMCI", "ADSK", "GLW"
    ]
    
    analyzer = TradingAnalyzer()
    
    # Analyze with different strategies and create charts
    strategies = ["chandelier", "supertrend", "macd"]
    
    for strategy in strategies:
        print(f"\n{'#'*60}")
        print(f"RUNNING {strategy.upper()} STRATEGY")
        print(f"{'#'*60}")
        
        analyzer.analyze_multiple_tickers(
            symbol_list[:3],  # Test with first 3 symbols
            strategy=strategy,
            initial_capital=1000.0,
            create_charts=True  # Enable chart creation
        )


if __name__ == "__main__":
    main()
