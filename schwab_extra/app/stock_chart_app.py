#!/usr/bin/env python3
"""
Stock Chart Application with Candlesticks, Volume, and RSI
Uses schwab-py for data, matplotlib/tkinter for GUI
Auto-refreshes every 5 minutes during market hours (Pacific Time)
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
import threading
import time as time_module
import argparse

try:
    import schwab
    from schwab import auth
    from schwab.client import Client
except ImportError:
    print("Error: schwab-py not installed. Install with: pip install schwab-py")
    sys.exit(1)


class RSICalculator:
    """Calculate RSI (Relative Strength Index)"""
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate RSI for given prices"""
        if len(prices) < period + 1:
            return np.full(len(prices), np.nan)
        
        delta = np.diff(prices)
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)
        
        # Calculate initial averages
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        rsi_values = np.full(len(prices), np.nan)
        
        # Calculate RSI for each point
        for i in range(period, len(prices)):
            if i == period:
                current_avg_gain = avg_gain
                current_avg_loss = avg_loss
            else:
                current_avg_gain = (current_avg_gain * (period - 1) + gains[i-1]) / period
                current_avg_loss = (current_avg_loss * (period - 1) + losses[i-1]) / period
            
            if current_avg_loss == 0:
                rsi_values[i] = 100
            else:
                rs = current_avg_gain / current_avg_loss
                rsi_values[i] = 100 - (100 / (1 + rs))
        
        return rsi_values


class MarketHours:
    """Handle market hours detection for Pacific Time"""
    
    def __init__(self):
        self.pacific_tz = pytz.timezone('America/Los_Angeles')
        self.eastern_tz = pytz.timezone('America/New_York')
    
    def is_market_open(self):
        """Check if market is currently open"""
        now_et = datetime.now(self.eastern_tz)
        
        # Check if it's a weekday
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now_et.time()
        
        return market_open <= current_time <= market_close


class SchwabDataFetcher:
    """Handle Schwab API data fetching"""
    
    def __init__(self):
        self.client = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Schwab API using environment variables"""
        try:
            api_key = os.environ.get('SCHWAB_API_KEY')
            app_secret = os.environ.get('SCHWAB_APP_SECRET')
            token_path = os.environ["SCHWAB_TOKEN_PATH"]
            
            if not api_key or not app_secret or not token_path:
                raise ValueError("Missing SCHWAB_API_KEY or SCHWAB_APP_SECRET environment variables")
            
            # Initialize Schwab client
            self.client = schwab.auth.easy_client(
                api_key=api_key,
                app_secret=app_secret,
                callback_url="https://127.0.0.1:8182/",
                token_path = token_path
            )
            
        except Exception as e:
            raise Exception(f"Schwab authentication failed: {e}")
            
    
    def get_price_history(self, symbol, **params):
        """Fetch price history from Schwab API"""
        try:
            response = self.client.get_price_history(
                symbol=symbol,
                **params
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code}")
            
            data = response.json()
            candles = data.get('candles', [])
            
            if not candles:
                raise Exception("No data returned from API")
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to fetch data: {e}")


class CandlestickChart:
    """Create candlestick chart with volume and RSI"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.fig = Figure(figsize=(12, 8), facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.fig, parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create subplots with height ratios: main chart 2/3, volume 1/3
        from matplotlib import gridspec
        gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])
        self.ax_main = self.fig.add_subplot(gs[0])
        self.ax_volume = self.fig.add_subplot(gs[1])
        self.ax_rsi = self.ax_main.twinx()  # RSI overlaid on main chart
        
        self.setup_chart_style()

    
    def setup_chart_style(self):
        """Configure chart styling"""
        self.fig.tight_layout(pad=2.0)
        
        # Main chart styling
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.set_ylabel('Price ($)', fontsize=10)
        
        # RSI styling
        self.ax_rsi.set_ylabel('RSI', fontsize=10, color='purple')
        self.ax_rsi.tick_params(axis='y', labelcolor='purple')
        self.ax_rsi.set_ylim(0, 100)
        
        # Volume chart styling
        self.ax_volume.grid(True, alpha=0.3)
        self.ax_volume.set_ylabel('Volume', fontsize=10)
        self.ax_volume.set_xlabel('Time', fontsize=10)
    
    def plot_candlesticks(self, df):
        """Plot candlestick chart"""
        self.ax_main.clear()
        
        # Determine colors
        colors = ['green' if close >= open_price else 'red' 
                 for close, open_price in zip(df['close'], df['open'])]
        
        # Plot candlesticks
        for i, (idx, row) in enumerate(df.iterrows()):
            color = colors[i]
            
            # Candlestick body
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['close'], row['open'])
            
            self.ax_main.bar(i, body_height, bottom=body_bottom, 
                           color=color, alpha=0.8, width=0.8)
            
            # Wicks
            self.ax_main.plot([i, i], [row['low'], row['high']], 
                            color='black', linewidth=1)
        
        # Configure x-axis
        self.ax_main.set_xlim(-0.5, len(df) - 0.5)
        self.ax_main.set_xticks(range(0, len(df), max(1, len(df)//10)))
        self.ax_main.set_xticklabels([df.index[i].strftime('%H:%M') 
                                    for i in range(0, len(df), max(1, len(df)//10))], 
                                   rotation=45)
        
        self.ax_main.set_ylabel('Price ($)')
        self.ax_main.grid(True, alpha=0.3)
    
    def plot_rsi(self, df):
        """Plot RSI overlay"""
        self.ax_rsi.clear()
        
        # Calculate RSI
        rsi_values = RSICalculator.calculate_rsi(df['close'].values)
        
        # Plot RSI line
        valid_rsi = ~np.isnan(rsi_values)
        x_coords = np.arange(len(df))[valid_rsi]
        rsi_clean = rsi_values[valid_rsi]
        
        self.ax_rsi.plot(x_coords, rsi_clean, color='purple', linewidth=2, alpha=0.7)
        
        # Add overbought/oversold lines
        self.ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.5, linewidth=1)
        self.ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.5, linewidth=1)
        
        self.ax_rsi.set_ylim(0, 100)
        self.ax_rsi.set_ylabel('RSI', color='purple')
        self.ax_rsi.tick_params(axis='y', labelcolor='purple')
    
    def plot_volume(self, df):
        """Plot volume bars"""
        self.ax_volume.clear()
        
        # Determine colors based on price movement
        colors = ['green' if close >= open_price else 'red' 
                 for close, open_price in zip(df['close'], df['open'])]
        
        # Plot volume bars
        self.ax_volume.bar(range(len(df)), df['volume'], color=colors, alpha=0.6)
        
        # Configure x-axis
        self.ax_volume.set_xlim(-0.5, len(df) - 0.5)
        self.ax_volume.set_xticks(range(0, len(df), max(1, len(df)//10)))
        self.ax_volume.set_xticklabels([df.index[i].strftime('%H:%M') 
                                      for i in range(0, len(df), max(1, len(df)//10))], 
                                     rotation=45)
        
        self.ax_volume.set_ylabel('Volume')
        self.ax_volume.set_xlabel('Time')
        self.ax_volume.grid(True, alpha=0.3)
    
    def update_chart(self, df, symbol, timeframe):
        """Update entire chart with new data"""
        if df is None or df.empty:
            return
        
        self.plot_candlesticks(df)
        self.plot_rsi(df)
        self.plot_volume(df)
        
        # Update title
        last_price = df['close'].iloc[-1]
        self.fig.suptitle(f'{symbol} - {timeframe} - Last: ${last_price:.2f}', 
                         fontsize=14, fontweight='bold')
        
        self.canvas.draw()


class StockChartApp:
    """Main application class"""
    
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.current_timeframe = "15min"
        self.last_timeframe = "15min"  # Remember last selection
        
        # Initialize components
        self.data_fetcher = SchwabDataFetcher()
        self.market_hours = MarketHours()
        
        # Setup GUI
        self.setup_gui()
        
        # Start with initial data load
        self.refresh_data()
        
        # Start auto-refresh timer
        self.start_auto_refresh()
    
    def setup_gui(self):
        """Create GUI elements"""
        self.root = tk.Tk()
        self.root.title(f"Stock Chart - {self.symbol}")
        self.root.geometry("1200x800")
        
        # Control frame
        control_frame = ttk.Frame(self.root, padding="5")
        control_frame.pack(fill=tk.X)
        
        # Stock symbol input - ADD THIS SECTION
        ttk.Label(control_frame, text="Symbol:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.symbol_var = tk.StringVar(value=self.symbol)
        self.symbol_entry = ttk.Entry(control_frame, textvariable=self.symbol_var, width=8)
        self.symbol_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.symbol_entry.bind("<Return>", self.on_symbol_change)  # Enter key to change
        
        ttk.Button(control_frame, text="Change Stock", 
                command=self.on_symbol_change).pack(side=tk.LEFT, padx=(0, 15))
        # END OF NEW SECTION
        
        # Timeframe selection
        ttk.Label(control_frame, text="Timeframe:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.timeframe_var = tk.StringVar(value=self.current_timeframe)
        timeframe_combo = ttk.Combobox(control_frame, textvariable=self.timeframe_var,
                                    values=["5min", "15min", "30min"], state="readonly", width=10)
        timeframe_combo.pack(side=tk.LEFT, padx=(0, 10))
        timeframe_combo.bind("<<ComboboxSelected>>", self.on_timeframe_change)
        
        # Refresh button
        ttk.Button(control_frame, text="Refresh Now", 
                command=self.refresh_data).pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Chart frame
        chart_frame = ttk.Frame(self.root, padding="5")
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create chart
        self.chart = CandlestickChart(chart_frame)
  
 
    def on_symbol_change(self, event=None):
        """Handle stock symbol change"""
        new_symbol = self.symbol_var.get().strip().upper()
        
        # Basic validation
        if not new_symbol:
            self.status_label.config(text="Error: Please enter a valid symbol")
            self.symbol_var.set(self.symbol)  # Reset to current symbol
            return
        
        if not new_symbol.replace('.', '').isalnum():
            self.status_label.config(text="Error: Invalid symbol format")
            self.symbol_var.set(self.symbol)  # Reset to current symbol
            return
        
        # Update symbol if it's different
        if new_symbol != self.symbol:
            self.symbol = new_symbol
            self.symbol_var.set(self.symbol)  # Ensure it's uppercase in the field
            
            # Update window title
            self.root.title(f"Stock Chart - {self.symbol}")
            
            # Clear the chart and refresh with new symbol
            self.status_label.config(text=f"Loading {self.symbol}...")
            self.refresh_data()
    

    def on_timeframe_change(self, event=None):
        """Handle timeframe selection change"""
        new_timeframe = self.timeframe_var.get()
        if new_timeframe != self.current_timeframe:
            self.current_timeframe = new_timeframe
            self.last_timeframe = new_timeframe
            self.refresh_data()
    
    def get_frequency_params(self, timeframe):
        """Convert timeframe to Schwab API enum parameters"""
        if timeframe == "5min":
            return {
                "frequency_type": Client.PriceHistory.FrequencyType.MINUTE,
                "frequency": Client.PriceHistory.Frequency.EVERY_FIVE_MINUTES,
                "period_type": Client.PriceHistory.PeriodType.DAY,
                "period": Client.PriceHistory.Period.ONE_DAY
            }
        elif timeframe == "15min":
            return {
                "frequency_type": Client.PriceHistory.FrequencyType.MINUTE,
                "frequency": Client.PriceHistory.Frequency.EVERY_FIFTEEN_MINUTES,
                "period_type": Client.PriceHistory.PeriodType.DAY,
                "period": Client.PriceHistory.Period.ONE_DAY
            }
        elif timeframe == "30min":
            # No 60-minute enum, so use 30-minute as closest available
            return {
                "frequency_type": Client.PriceHistory.FrequencyType.MINUTE,
                "frequency": Client.PriceHistory.Frequency.EVERY_THIRTY_MINUTES,
                "period_type": Client.PriceHistory.PeriodType.DAY,
                "period": Client.PriceHistory.Period.ONE_DAY
            }
        else:
            return {
                "frequency_type": Client.PriceHistory.FrequencyType.MINUTE,
                "frequency": Client.PriceHistory.Frequency.EVERY_FIVE_MINUTES,
                "period_type": Client.PriceHistory.PeriodType.DAY,
                "period": Client.PriceHistory.Period.ONE_DAY
            }
    
    def refresh_data(self):
        """Refresh chart data"""
        def fetch_and_update():
            try:
                self.status_label.config(text="Fetching data...")
                self.root.update()
                
                # Get API parameters for selected timeframe
                params = self.get_frequency_params(self.current_timeframe)
                
                # Fetch data
                df = self.data_fetcher.get_price_history(
                    symbol=self.symbol,
                    **params
                )
                
                # Update chart on main thread
                self.root.after(0, lambda: self.update_chart_with_data(df))
                
            except Exception as e:
                error_msg = f"Error loading {self.symbol}: {str(e)}"
                if "symbol" in str(e).lower() or "not found" in str(e).lower():
                    error_msg = f"Invalid symbol: {self.symbol}"
                self.root.after(0, lambda: self.status_label.config(text=error_msg))
                print(f"Data fetch error: {e}")
        
        # Run in background thread to avoid GUI freezing
        threading.Thread(target=fetch_and_update, daemon=True).start()
    
    def update_chart_with_data(self, df):
        """Update chart with fetched data (runs on main thread)"""
        try:
            self.chart.update_chart(df, self.symbol, self.current_timeframe)
            
            # Update status
            now = datetime.now().strftime("%H:%M:%S")
            market_status = "Open" if self.market_hours.is_market_open() else "Closed"
            self.status_label.config(text=f"Updated: {now} | Market: {market_status}")
            
        except Exception as e:
            self.status_label.config(text=f"Chart update error: {str(e)}")
            print(f"Chart update error: {e}")
    
    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        def auto_refresh_loop():
            if self.market_hours.is_market_open():
                self.refresh_data()
            
            # Schedule next refresh in 5 minutes
            self.root.after(300000, auto_refresh_loop)  # 5 minutes = 300,000 ms
        
        # Start the auto-refresh loop
        self.root.after(300000, auto_refresh_loop)  # First refresh in 5 minutes
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nApplication interrupted by user")
        except Exception as e:
            print(f"Application error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Stock Chart with Candlesticks, Volume, and RSI")
    parser.add_argument("symbol", help="Stock ticker symbol (e.g., AAPL, TSLA)")
    
    args = parser.parse_args()
    
    # Check for required environment variables
    required_vars = ['SCHWAB_API_KEY', 'SCHWAB_APP_SECRET', "SCHWAB_TOKEN_PATH"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these environment variables before running the application.")
        sys.exit(1)
    
    try:
        app = StockChartApp(args.symbol)
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
