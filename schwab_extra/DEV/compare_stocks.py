import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# Define the portfolio components and weights
tickers = ['IVV', 'QQQ', 'COWZ', 'MGC', 'PULS', 'QYLD', 'SPYV']
# weights are the percentage in dollar value of each stock in the entire portfolio
weights = np.array([0.25, 0.25, 0.10, 0.10, 0.10, 0.10, 0.10])
start_date = '2014-01-01'
end_date = '2023-12-31'

# Download historical data
data = yf.download(tickers, start=start_date, end=end_date)['Close']

# Calculate daily returns
returns = data.pct_change().dropna()

# Calculate portfolio returns
portfolio_returns = returns.dot(weights)

# Calculate cumulative returns for the portfolio
cumulative_returns_portfolio = (1 + portfolio_returns).cumprod()

# Plot cumulative returns for each stock
plt.figure(figsize=(14, 8))
for ticker in tickers:
    cumulative_returns_stock = (1 + returns[ticker]).cumprod()
    plt.plot(cumulative_returns_stock, label=ticker)

# Plot cumulative returns for the portfolio
plt.plot(cumulative_returns_portfolio, label='Portfolio', linewidth=2, color='black')

plt.title('Cumulative Returns of Individual Stocks and Portfolio')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.legend()
plt.show()

# Function to calculate performance metrics
def calculate_performance_metrics(returns, weights=None):
    if weights is not None:
        returns = returns.dot(weights)
    annualized_return = returns.mean() * 252
    annualized_volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = annualized_return / annualized_volatility
    cumulative_returns = (1 + returns).cumprod()
    max_drawdown = (cumulative_returns / cumulative_returns.cummax() - 1).min()
    return annualized_return, annualized_volatility, sharpe_ratio, max_drawdown

# Calculate and print performance metrics for each stock and the portfolio
report = pd.DataFrame(columns=['Annualized Return', 'Annualized Volatility', 'Sharpe Ratio', 'Max Drawdown'])

for ticker in tickers:
    ann_return, ann_volatility, sharpe, max_dd = calculate_performance_metrics(returns[ticker])
    report.loc[ticker] = [f"{ann_return:.2%}", f"{ann_volatility:.2%}", f"{sharpe:.2f}", f"{max_dd:.2%}"]

# Calculate and add portfolio performance metrics
ann_return_portfolio, ann_volatility_portfolio, sharpe_portfolio, max_dd_portfolio = calculate_performance_metrics(portfolio_returns)
report.loc['Portfolio'] = [f"{ann_return_portfolio:.2%}", f"{ann_volatility_portfolio:.2%}", f"{sharpe_portfolio:.2f}", f"{max_dd_portfolio:.2%}"]

print(report)
