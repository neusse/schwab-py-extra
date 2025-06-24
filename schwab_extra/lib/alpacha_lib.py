"""
alpaca lib
"""

from datetime import datetime, timedelta
import pytz
import pandas as pd
#import numpy as np
import requests

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest

client = StockHistoricalDataClient(api_key, secret_key)

def get_stock_trades(symbol, day):
    eastern_tz = pytz.timezone("US/Eastern")
    
    dt_day = datetime.strptime(day, "%Y-%m-%d")
    
    market_open_eastern = eastern_tz.localize(datetime(dt_day.year, dt_day.month, dt_day.day, 9, 30))
    market_close_eastern = eastern_tz.localize(datetime(dt_day.year, dt_day.month, dt_day.day, 16, 0))
    
    market_open_utc = market_open_eastern.astimezone(pytz.utc)
    market_close_utc = market_close_eastern.astimezone(pytz.utc)
    
    req = StockTradesRequest(
        symbol_or_symbols=symbol,
        start=market_open_utc,
        end=market_close_utc
    )
    
    trades = client.get_stock_trades(req)
    return trades.df

df = get_stock_trades("AAPL", "2024-09-20")


##  faster

# Alpaca data API base URL
BASE_URL = 'https://data.alpaca.markets/'

# Alpaca API credentials
API_KEY = 'xxxxx'
SECRET_KEY = 'xxxxx'

# Request headers
HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}
ENDPOINT = 'v2/stocks/trades'

# set the begin and end datetimes
begin = pd.to_datetime('2024-09-20 9:30').tz_localize('America/New_York')
end = pd.to_datetime('2024-09-20 16:00').tz_localize('America/New_York')

# list of symbols
symbols = ['AAPL']

# initialize things needed to loop
page_token = 'default'
trade_list = []

start_time = pd.Timestamp('now', tz='America/New_York')

for symbol in symbols:
  # fetch one symbol at a time but can fetch more 
  while page_token is not None:
    parameters = {'symbols': symbol,
                  'start': begin.isoformat(),
                  'end': end.isoformat(),
                  'limit':10000,
                  'page_token': page_token if page_token!='default' else None,
                  }

    response = requests.get(BASE_URL+ENDPOINT, headers=HEADERS, params=parameters).json()
    page_token = response.get('next_page_token')
    # the response is a dict with symbol as the single key
    # (because the request was just for 1 symbol)
    trade_list += response.get('trades').get(symbol)

end_time = pd.Timestamp('now', tz='America/New_York')
delta_time = end_time - start_time
print(f'symbol: {symbol} start: {begin.isoformat()} end: {end.isoformat()}')
print(f'execution time: {delta_time} total trades: {len(trade_list)}')

# one needs to save the list of trades somewhere here
pass
  