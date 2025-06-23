import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

class Signal(Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish" 
    NEUTRAL = "Neutral"

@dataclass
class PatternResult:
    date: pd.Timestamp
    name: str
    signal: Signal
    strength: float  # 0-100 confidence
    price: float

class RobustPatternAnalyzer:
    def __init__(self):
        self.df = pd.DataFrame()
        self.patterns: List[PatternResult] = []
        
    def load_data(self, ticker: str, start_date: str, end_date: str):
        """Load and prepare stock data"""
        self.df = yf.download(ticker, start=start_date, end=end_date)
        
        if self.df.empty:
            raise ValueError("No data fetched. Check ticker and date range.")
            
        # Handle MultiIndex columns
        if isinstance(self.df.columns, pd.MultiIndex):
            self.df.columns = self.df.columns.droplevel(1)
        
        self._calculate_metrics()
        
    def _calculate_metrics(self):
        """Calculate all necessary candlestick metrics"""
        # Basic candle properties
        self.df['BodySize'] = abs(self.df['Close'] - self.df['Open'])
        self.df['BodyTop'] = self.df[['Open', 'Close']].max(axis=1)
        self.df['BodyBottom'] = self.df[['Open', 'Close']].min(axis=1)
        self.df['UpperWick'] = self.df['High'] - self.df['BodyTop']
        self.df['LowerWick'] = self.df['BodyBottom'] - self.df['Low']
        self.df['TotalRange'] = self.df['High'] - self.df['Low']
        
        # Directional properties
        self.df['IsBullish'] = self.df['Close'] > self.df['Open']
        self.df['IsBearish'] = self.df['Close'] < self.df['Open']
        self.df['IsDoji'] = self.df['BodySize'] / self.df['TotalRange'] < 0.1
        
        # Relative sizes (avoid division by zero)
        self.df['BodyRatio'] = np.where(
            self.df['TotalRange'] > 0,
            self.df['BodySize'] / self.df['TotalRange'],
            0
        )
        self.df['UpperWickRatio'] = np.where(
            self.df['TotalRange'] > 0,
            self.df['UpperWick'] / self.df['TotalRange'],
            0
        )
        self.df['LowerWickRatio'] = np.where(
            self.df['TotalRange'] > 0,
            self.df['LowerWick'] / self.df['TotalRange'],
            0
        )
        
        # Statistical context
        self.avg_body = self.df['BodySize'].rolling(20, min_periods=1).mean()
        self.avg_range = self.df['TotalRange'].rolling(20, min_periods=1).mean()
        
    def detect_patterns(self) -> List[PatternResult]:
        """Detect all candlestick patterns"""
        self.patterns.clear()
        
        for i in range(len(self.df)):
            # Single candle patterns
            self._check_doji_patterns(i)
            self._check_hammer_patterns(i)
            self._check_star_patterns(i)
            self._check_marubozu_patterns(i)
            
            # Multi-candle patterns (need previous candles)
            if i >= 1:
                self._check_engulfing_patterns(i)
                self._check_harami_patterns(i)
                self._check_piercing_patterns(i)
                
            if i >= 2:
                self._check_three_candle_patterns(i)
                
        return self.patterns
    
    def _add_pattern(self, i: int, name: str, signal: Signal, strength: float = 80):
        """Helper to add a pattern result"""
        self.patterns.append(PatternResult(
            date=self.df.index[i],
            name=name,
            signal=signal,
            strength=strength,
            price=self.df.iloc[i]['Close']
        ))
    
    def _check_doji_patterns(self, i: int):
        """Check for Doji pattern variations"""
        row = self.df.iloc[i]
        
        if not row['IsDoji']:
            return
            
        # Basic Doji
        if row['UpperWickRatio'] < 0.6 and row['LowerWickRatio'] < 0.6:
            self._add_pattern(i, "Doji", Signal.NEUTRAL, 70)
            
        # Dragonfly Doji (long lower wick)
        elif row['LowerWickRatio'] > 0.6 and row['UpperWickRatio'] < 0.1:
            self._add_pattern(i, "Dragonfly Doji", Signal.BULLISH, 85)
            
        # Gravestone Doji (long upper wick)
        elif row['UpperWickRatio'] > 0.6 and row['LowerWickRatio'] < 0.1:
            self._add_pattern(i, "Gravestone Doji", Signal.BEARISH, 85)
            
        # Long-legged Doji
        elif row['UpperWickRatio'] > 0.3 and row['LowerWickRatio'] > 0.3:
            self._add_pattern(i, "Long-Legged Doji", Signal.NEUTRAL, 75)
    
    def _check_hammer_patterns(self, i: int):
        """Check for Hammer and related patterns"""
        row = self.df.iloc[i]
        
        # Hammer: Small body, long lower wick, small upper wick
        if (row['LowerWickRatio'] > 0.5 and 
            row['BodyRatio'] < 0.3 and 
            row['UpperWickRatio'] < 0.1):
            
            if row['IsBullish'] or row['IsDoji']:
                self._add_pattern(i, "Hammer", Signal.BULLISH, 80)
            else:
                self._add_pattern(i, "Hanging Man", Signal.BEARISH, 80)
                
        # Inverted Hammer: Small body, long upper wick, small lower wick
        elif (row['UpperWickRatio'] > 0.5 and 
              row['BodyRatio'] < 0.3 and 
              row['LowerWickRatio'] < 0.1):
            
            if row['IsBullish'] or row['IsDoji']:
                self._add_pattern(i, "Inverted Hammer", Signal.BULLISH, 75)
            else:
                self._add_pattern(i, "Shooting Star", Signal.BEARISH, 85)
    
    def _check_star_patterns(self, i: int):
        """Check for spinning top and high wave patterns"""
        row = self.df.iloc[i]
        
        # Spinning Top: Small body with upper and lower wicks
        if (row['BodyRatio'] < 0.3 and 
            row['UpperWickRatio'] > 0.2 and 
            row['LowerWickRatio'] > 0.2):
            self._add_pattern(i, "Spinning Top", Signal.NEUTRAL, 70)
            
        # High Wave: Very long wicks relative to body
        elif (row['UpperWickRatio'] > 0.4 and 
              row['LowerWickRatio'] > 0.4 and 
              row['BodyRatio'] < 0.2):
            self._add_pattern(i, "High Wave", Signal.NEUTRAL, 75)
    
    def _check_marubozu_patterns(self, i: int):
        """Check for Marubozu patterns"""
        row = self.df.iloc[i]
        
        # Marubozu: Large body with minimal wicks
        if (row['BodyRatio'] > 0.8 and 
            row['UpperWickRatio'] < 0.1 and 
            row['LowerWickRatio'] < 0.1):
            
            if row['IsBullish']:
                self._add_pattern(i, "White Marubozu", Signal.BULLISH, 90)
            else:
                self._add_pattern(i, "Black Marubozu", Signal.BEARISH, 90)
    
    def _check_engulfing_patterns(self, i: int):
        """Check for Engulfing patterns"""
        if i < 1:
            return
            
        prev = self.df.iloc[i-1]
        curr = self.df.iloc[i]
        
        # Bullish Engulfing
        if (prev['IsBearish'] and curr['IsBullish'] and
            curr['Open'] < prev['Close'] and curr['Close'] > prev['Open']):
            
            # Strength based on how much it engulfs
            strength = min(95, 80 + (curr['BodySize'] / prev['BodySize'] - 1) * 20)
            self._add_pattern(i, "Bullish Engulfing", Signal.BULLISH, strength)
            
        # Bearish Engulfing
        elif (prev['IsBullish'] and curr['IsBearish'] and
              curr['Open'] > prev['Close'] and curr['Close'] < prev['Open']):
            
            strength = min(95, 80 + (curr['BodySize'] / prev['BodySize'] - 1) * 20)
            self._add_pattern(i, "Bearish Engulfing", Signal.BEARISH, strength)
    
    def _check_harami_patterns(self, i: int):
        """Check for Harami patterns"""
        if i < 1:
            return
            
        prev = self.df.iloc[i-1]
        curr = self.df.iloc[i]
        
        # Current candle body is within previous candle body
        if (curr['BodyTop'] < prev['BodyTop'] and 
            curr['BodyBottom'] > prev['BodyBottom']):
            
            # Bullish Harami
            if prev['IsBearish'] and curr['IsBullish']:
                self._add_pattern(i, "Bullish Harami", Signal.BULLISH, 75)
                
            # Bearish Harami  
            elif prev['IsBullish'] and curr['IsBearish']:
                self._add_pattern(i, "Bearish Harami", Signal.BEARISH, 75)
                
            # Harami Cross (Doji inside)
            elif curr['IsDoji']:
                signal = Signal.BULLISH if prev['IsBearish'] else Signal.BEARISH
                self._add_pattern(i, "Harami Cross", signal, 80)
    
    def _check_piercing_patterns(self, i: int):
        """Check for Piercing Line and Dark Cloud Cover"""
        if i < 1:
            return
            
        prev = self.df.iloc[i-1]
        curr = self.df.iloc[i]
        
        # Piercing Line
        if (prev['IsBearish'] and curr['IsBullish'] and
            curr['Open'] < prev['Low'] and
            curr['Close'] > (prev['Open'] + prev['Close']) / 2 and
            curr['Close'] < prev['Open']):
            self._add_pattern(i, "Piercing Line", Signal.BULLISH, 85)
            
        # Dark Cloud Cover
        elif (prev['IsBullish'] and curr['IsBearish'] and
              curr['Open'] > prev['High'] and
              curr['Close'] < (prev['Open'] + prev['Close']) / 2 and
              curr['Close'] > prev['Open']):
            self._add_pattern(i, "Dark Cloud Cover", Signal.BEARISH, 85)
    
    def _check_three_candle_patterns(self, i: int):
        """Check for three-candle patterns"""
        if i < 2:
            return
            
        first = self.df.iloc[i-2]
        second = self.df.iloc[i-1] 
        third = self.df.iloc[i]
        
        # Morning Star
        if (first['IsBearish'] and 
            second['BodySize'] < first['BodySize'] * 0.5 and
            third['IsBullish'] and
            third['Close'] > (first['Open'] + first['Close']) / 2):
            self._add_pattern(i, "Morning Star", Signal.BULLISH, 90)
            
        # Evening Star
        elif (first['IsBullish'] and
              second['BodySize'] < first['BodySize'] * 0.5 and
              third['IsBearish'] and
              third['Close'] < (first['Open'] + first['Close']) / 2):
            self._add_pattern(i, "Evening Star", Signal.BEARISH, 90)
            
        # Three White Soldiers
        elif (first['IsBullish'] and second['IsBullish'] and third['IsBullish'] and
              second['Close'] > first['Close'] and third['Close'] > second['Close'] and
              second['Open'] > first['BodyBottom'] and second['Open'] < first['BodyTop'] and
              third['Open'] > second['BodyBottom'] and third['Open'] < second['BodyTop']):
            self._add_pattern(i, "Three White Soldiers", Signal.BULLISH, 95)
            
        # Three Black Crows
        elif (first['IsBearish'] and second['IsBearish'] and third['IsBearish'] and
              second['Close'] < first['Close'] and third['Close'] < second['Close'] and
              second['Open'] < first['BodyTop'] and second['Open'] > first['BodyBottom'] and
              third['Open'] < second['BodyTop'] and third['Open'] > second['BodyBottom']):
            self._add_pattern(i, "Three Black Crows", Signal.BEARISH, 95)
    
    def plot_patterns(self, ticker: str):
        """Create interactive candlestick chart with patterns"""
        if self.df.empty:
            raise ValueError("No data loaded. Call load_data() first.")
        
        fig = go.Figure()
        
        # Add candlestick chart
        fig.add_trace(go.Candlestick(
            x=self.df.index,
            open=self.df['Open'],
            high=self.df['High'],
            low=self.df['Low'],
            close=self.df['Close'],
            name='Price'
        ))
        
        # Group patterns by signal type
        signal_groups = {
            Signal.BULLISH: {'patterns': [], 'color': 'green', 'symbol': 'triangle-up'},
            Signal.BEARISH: {'patterns': [], 'color': 'red', 'symbol': 'triangle-down'},
            Signal.NEUTRAL: {'patterns': [], 'color': 'blue', 'symbol': 'circle'}
        }
        
        for pattern in self.patterns:
            signal_groups[pattern.signal]['patterns'].append(pattern)
        
        # Add markers for each signal type
        for signal, data in signal_groups.items():
            if data['patterns']:
                fig.add_trace(go.Scatter(
                    x=[p.date for p in data['patterns']],
                    y=[p.price for p in data['patterns']],
                    mode='markers',
                    marker=dict(
                        symbol=data['symbol'],
                        size=12,
                        color=data['color'],
                        line=dict(width=2, color='white')
                    ),
                    name=f"{signal.value} Patterns",
                    text=[f"{p.name}<br>Strength: {p.strength:.0f}%" for p in data['patterns']],
                    hovertemplate="<b>%{text}</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>"
                ))
        
        fig.update_layout(
            title=f"{ticker} - Candlestick Pattern Analysis",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            width=1200,
            height=700,
            hovermode='x unified'
        )
        
        return fig
    
    def get_summary(self) -> pd.DataFrame:
        """Get summary of detected patterns"""
        if not self.patterns:
            return pd.DataFrame(columns=['Date', 'Pattern', 'Signal', 'Strength', 'Price'])
        
        return pd.DataFrame([
            {
                'Date': p.date.date(),
                'Pattern': p.name,
                'Signal': p.signal.value,
                'Strength': f"{p.strength:.0f}%",
                'Price': f"${p.price:.2f}"
            }
            for p in sorted(self.patterns, key=lambda x: x.date)
        ])

def main():
    analyzer = RobustPatternAnalyzer()
    
    try:
        ticker = input("Enter stock ticker: ").strip().upper()
        start_date = input("Enter start date (YYYY-MM-DD): ").strip()
        end_date = input("Enter end date (YYYY-MM-DD): ").strip()
        
        print(f"\nAnalyzing {ticker} from {start_date} to {end_date}...")
        
        # Load data and detect patterns
        analyzer.load_data(ticker, start_date, end_date)
        patterns = analyzer.detect_patterns()
        
        print(f"\nDetected {len(patterns)} candlestick patterns:")
        
        # Show summary
        summary = analyzer.get_summary()
        if not summary.empty:
            print(summary.to_string(index=False))
            
            # Show signal breakdown
            print(f"\nSignal Summary:")
            for signal in [Signal.BULLISH, Signal.BEARISH, Signal.NEUTRAL]:
                count = len([p for p in patterns if p.signal == signal])
                if count > 0:
                    print(f"  {signal.value}: {count} patterns")
            
            # Create and show plot
            fig = analyzer.plot_patterns(ticker)
            fig.show()
        else:
            print("No patterns detected in the given timeframe.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()