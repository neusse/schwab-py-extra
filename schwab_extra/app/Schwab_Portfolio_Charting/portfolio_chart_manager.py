"""
Portfolio Chart Manager - Main GUI Application
Displays a small portfolio vs S&P 500 chart and allows launching of individual chart applications
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import sys
import os
from typing import Dict, List

# Import from the existing portfolio analyzer
try:
    from portfolio_analyzer_update_3 import (
        get_portfolio_positions, 
        fetch_market_data, 
        calculate_benchmark_comparison,
        SP500_TICKER
    )
except ImportError:
    print("Warning: Could not import portfolio analyzer functions")
    print("Make sure portfolio_analyzer_update_3.py is in the same directory")

class PortfolioChartManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Portfolio Chart Manager")
        self.root.geometry("1200x800")
        
        # Available chart types
        self.chart_types = {
            "Portfolio Value & Trend": "chart_portfolio_value.py",
            "Daily Changes & Moving Averages": "chart_daily_changes.py", 
            "Portfolio vs S&P 500": "chart_benchmark_comparison.py",
            "Drawdown Analysis": "chart_drawdown.py",
            "Individual Tickers": "chart_individual_tickers.py",
            "Gain/Loss Analysis": "chart_gainloss_analysis.py",
            "Risk Metrics Dashboard": "chart_risk_dashboard.py",
            "Dividend Analysis": "chart_dividend_analysis.py"
        }
        
        # Data storage
        self.portfolio_data = None
        self.benchmark_data = None
        self.positions = None
        
        self.setup_gui()
        self.load_portfolio_data()
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Portfolio Chart Manager", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Chart selection
        self.setup_chart_selection_panel(main_frame)
        
        # Right panel - Live portfolio chart
        self.setup_live_chart_panel(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_chart_selection_panel(self, parent):
        """Setup the left panel with chart selection"""
        # Chart selection frame
        selection_frame = ttk.LabelFrame(parent, text="Available Charts", padding="10")
        selection_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Chart listbox
        self.chart_listbox = tk.Listbox(selection_frame, height=12, width=30)
        self.chart_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Populate listbox
        for chart_name in self.chart_types.keys():
            self.chart_listbox.insert(tk.END, chart_name)
            
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(selection_frame, orient=tk.VERTICAL, command=self.chart_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.chart_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(selection_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        # Launch chart button
        launch_btn = ttk.Button(buttons_frame, text="Launch Selected Chart", 
                               command=self.launch_selected_chart)
        launch_btn.grid(row=0, column=0, padx=(0, 5))
        
        # Refresh data button
        refresh_btn = ttk.Button(buttons_frame, text="Refresh Data", 
                                command=self.refresh_data)
        refresh_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(selection_frame, text="Settings", padding="5")
        settings_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Days back setting
        ttk.Label(settings_frame, text="Days Back:").grid(row=0, column=0, sticky=tk.W)
        self.days_var = tk.StringVar(value="90")
        days_spinbox = ttk.Spinbox(settings_frame, from_=30, to=365, width=10, 
                                  textvariable=self.days_var)
        days_spinbox.grid(row=0, column=1, padx=(5, 0))
        
        # Save charts checkbox
        self.save_charts_var = tk.BooleanVar()
        save_checkbox = ttk.Checkbutton(settings_frame, text="Save Charts", 
                                       variable=self.save_charts_var)
        save_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
    def setup_live_chart_panel(self, parent):
        """Setup the right panel with live portfolio chart"""
        # Chart frame
        chart_frame = ttk.LabelFrame(parent, text="Portfolio vs S&P 500 (Live)", padding="10")
        chart_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=80)
        self.ax = self.fig.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Chart controls frame
        controls_frame = ttk.Frame(chart_frame)
        controls_frame.grid(row=1, column=0, pady=(10, 0))
        
        # Update chart button
        update_chart_btn = ttk.Button(controls_frame, text="Update Chart", 
                                     command=self.update_live_chart)
        update_chart_btn.grid(row=0, column=0)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar()
        auto_refresh_checkbox = ttk.Checkbutton(controls_frame, text="Auto-refresh (5 min)", 
                                               variable=self.auto_refresh_var,
                                               command=self.toggle_auto_refresh)
        auto_refresh_checkbox.grid(row=0, column=1, padx=(10, 0))
        
    def load_portfolio_data(self):
        """Load initial portfolio data"""
        self.status_var.set("Loading portfolio data...")
        self.root.update()
        
        try:
            # Get positions
            self.positions = get_portfolio_positions()
            if not self.positions:
                raise Exception("No positions found")
                
            # Remove problematic tickers
            if 'SNSXX' in self.positions:
                del self.positions['SNSXX']
            
            # Fetch market data
            days_back = int(self.days_var.get())
            tickers = list(self.positions.keys()) + [SP500_TICKER]
            data = fetch_market_data(tickers, days_back)
            
            if data.empty:
                raise Exception("No market data retrieved")
            
            # Calculate benchmark comparison
            self.benchmark_data = calculate_benchmark_comparison(data, self.positions)
            
            self.status_var.set(f"Loaded data for {len(self.positions)} positions")
            self.update_live_chart()
            
        except Exception as e:
            self.status_var.set(f"Error loading data: {str(e)}")
            messagebox.showerror("Data Error", f"Failed to load portfolio data:\n{str(e)}")
    
    def update_live_chart(self):
        """Update the live portfolio chart"""
        if not self.benchmark_data:
            return
            
        try:
            self.ax.clear()
            
            portfolio_values = self.benchmark_data['portfolio_values']
            benchmark_normalized = self.benchmark_data['benchmark_normalized']
            
            # Plot portfolio and benchmark
            self.ax.plot(portfolio_values.index, portfolio_values, 
                        color='green', label='Portfolio', linewidth=2)
            self.ax.plot(benchmark_normalized.index, benchmark_normalized, 
                        color='blue', linestyle='--', label='S&P 500', linewidth=2)
            
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel('Value ($)')
            self.ax.set_title('Portfolio vs S&P 500 Performance')
            self.ax.legend()
            self.ax.grid(True, alpha=0.3)
            
            # Format y-axis as currency
            self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Rotate x-axis labels
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            self.status_var.set(f"Error updating chart: {str(e)}")
    
    def launch_selected_chart(self):
        """Launch the selected chart application"""
        selection = self.chart_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a chart to launch")
            return
            
        chart_name = self.chart_listbox.get(selection[0])
        chart_file = self.chart_types[chart_name]
        
        self.status_var.set(f"Launching {chart_name}...")
        
        try:
            # Launch the chart application as a separate process
            days_back = self.days_var.get()
            save_charts = "1" if self.save_charts_var.get() else "0"
            
            # Pass parameters as command line arguments
            cmd = [sys.executable, chart_file, "--days", days_back, "--save", save_charts]
            
            subprocess.Popen(cmd, cwd=os.getcwd())
            self.status_var.set(f"Launched {chart_name}")
            
        except Exception as e:
            error_msg = f"Failed to launch {chart_name}:\n{str(e)}"
            self.status_var.set(f"Error launching {chart_name}")
            messagebox.showerror("Launch Error", error_msg)
    
    def refresh_data(self):
        """Refresh portfolio data"""
        self.load_portfolio_data()
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality"""
        if self.auto_refresh_var.get():
            self.schedule_refresh()
        
    def schedule_refresh(self):
        """Schedule automatic data refresh"""
        if self.auto_refresh_var.get():
            self.refresh_data()
            # Schedule next refresh in 5 minutes (300000 ms)
            self.root.after(300000, self.schedule_refresh)

def main():
    """Main entry point"""
    root = tk.Tk()
    app = PortfolioChartManager(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()
