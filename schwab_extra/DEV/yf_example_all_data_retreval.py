import yfinance as yf

mydata = yf.Ticker("FTSM")


# get all stock info
mydata.info

# get historical market data (candles, dividens some times, seems splits and capital gains are missing)
mydata.history(period="2mo")

# show meta information about the history (requires history() to be called first)
mydata.history_metadata

# show actions (dividends, splits, capital gains)
mydata.actions
mydata.dividends
mydata.splits
mydata.capital_gains  # only for mutual funds & etfs

# show share count
mydata.get_shares_full(start="2022-01-01", end=None)

# show financials:
# - income statement
mydata.income_stmt
mydata.quarterly_income_stmt
# - balance sheet
mydata.balance_sheet
mydata.quarterly_balance_sheet
# - cash flow statement
mydata.cashflow
mydata.quarterly_cashflow
# see `Ticker.get_income_stmt()` for more options

# show holders
mydata.major_holders
mydata.institutional_holders
mydata.mutualfund_holders
mydata.insider_transactions
mydata.insider_purchases
mydata.insider_roster_holders

# show recommendations
mydata.recommendations
mydata.recommendations_summary  # seems empty for all
mydata.upgrades_downgrades

# Show future and historic earnings dates, returns at most next 4 quarters and last 8 quarters by default.
# Note: If more are needed use mydata.get_earnings_dates(limit=XX) with increased limit argument.
mydata.earnings_dates

# show ISIN code - *experimental*
# ISIN = International Securities Identification Number
mydata.isin

# show options expirations
mydata.options

# show news
mydata.news

# get option chain for specific expiration
#opt = mydata.option_chain("YYYY-MM-DD")
# data available via: opt.calls, opt.puts
