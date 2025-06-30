# Portfolio Chart Manager Configuration
# Copy this to config.py and modify as needed

# Default settings
DEFAULT_DAYS_BACK = 90
DEFAULT_SAVE_CHARTS = False
AUTO_REFRESH_INTERVAL = 300000  # 5 minutes in milliseconds

# Chart display settings
CHART_FIGSIZE = (14, 7)
CHART_DPI = 300
CHART_STYLE = 'default'

# Colors
PORTFOLIO_COLOR = 'darkgreen'
BENCHMARK_COLOR = 'blue'
GAIN_COLOR = 'green'
LOSS_COLOR = 'red'

# Excluded tickers (problematic data)
EXCLUDED_TICKERS = ['SNSXX']

# API settings
API_RATE_LIMIT_DELAY = 0.5  # seconds between API calls

# GUI settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
REFRESH_INTERVAL_MINUTES = 5
