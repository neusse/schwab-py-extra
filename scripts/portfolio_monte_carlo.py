"""
Portfolio Monte Carlo

Automatically generated by Colab.

#Monte Carlo Simulation of a Stock Portfolio with Python

https://www.youtube.com/watch?v=6-dhdMDiYWQ

###playlist:
https://www.youtube.com/playlist?list=PLqpCwow11-OqqfELduCMcRI6wcnoM3GAZ

#Links:

###★ ★ Code Available on GitHub ★ ★
GitHub: https://github.com/TheQuantPy
Specific Tutorial Link: https://github.com/TheQuantPy/youtube...

###★ ★ QuantPy GitHub ★ ★
Collection of resources used on QuantPy YouTube channel. https://github.com/thequantpy
"""

# import all the magic libraries/modules
import pandas as pd
import numpy as np
import datetime as dt
from scipy.stats import norm, t
import matplotlib.pyplot as plt
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

#  configuration Items


potfolio_value = 590000
days_to_retrieve_historical_data = 3*252
future_days = 252   # days to run MC into the future

number_of_simulations = 10000

# weights represent a percentage of the portfolio.  all weights must add up to 1.

stockList = [
    "MSFT",
    "FTSM",
    "RDVI",
    "PPA",
    "JEPQ",
   "JSCP",
    "ICOW",
    "ECOW",
    "COWG",
    "CALF",
    "BOND",
    "TOUS",
    "SPLG",
    "SPYV",
    "PVAL",
    "QYLD"

]
# these are the current weights of the above portfolio.
# JSCP 0.0808,
weights = [0.0108, 0.169, 0.0366, 0.0103, 0.0389, 0.0808, 0.0849, 0.0424, 0.0396, 0.0286, 0.01494, 0.0758, 0.0605, 0.0835, 0.0836, 0.01 ]

# Import data
def getData(stocks, start, end):
    stockData = pd.DataFrame()
    for stock in stocks:
        print(stock)
        stockData[stock] = yf.download(stock, start=start, end=end, auto_adjust=False, progress=False)['Close']
    returns = stockData.pct_change()
    meanReturns = returns.mean()
    covMatrix = returns.cov()
    #print(stockData)
    return returns, meanReturns, covMatrix

# Portfolio Performance
def portfolioPerformance(weights, meanReturns, covMatrix, Time):
    returns = np.sum(meanReturns*weights)*Time
    std = np.sqrt( np.dot(weights.T, np.dot(covMatrix, weights)) ) * np.sqrt(Time)
    return returns, std

stocks=stockList

endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=days_to_retrieve_historical_data)

# retieve stock data
returns, meanReturns, covMatrix = getData(stocks, start=startDate, end=endDate)
returns = returns.dropna()

# normalize weights to add up to 1, just in case.
weights /= np.sum(weights)

print(f"\n{weights}")

returns['portfolio'] = returns.dot(weights)

def historicalVaR(returns, alpha=5):
    """
    Read in a pandas dataframe of returns / a pandas series of returns
    Output the percentile of the distribution at the given alpha confidence level
    """
    if isinstance(returns, pd.Series):
        return np.percentile(returns, alpha)

    # A passed user-defined-function will be passed a Series for evaluation.
    elif isinstance(returns, pd.DataFrame):
        return returns.aggregate(historicalVaR, alpha=alpha)

    else:
        raise TypeError("Expected returns to be dataframe or series")

def historicalCVaR(returns, alpha=5):
    """
    Read in a pandas dataframe of returns / a pandas series of returns
    Output the CVaR for dataframe / series
    """
    if isinstance(returns, pd.Series):
        belowVaR = returns <= historicalVaR(returns, alpha=alpha)
        return returns[belowVaR].mean()

    # A passed user-defined-function will be passed a Series for evaluation.
    elif isinstance(returns, pd.DataFrame):
        return returns.aggregate(historicalCVaR, alpha=alpha)

    else:
        raise TypeError("Expected returns to be dataframe or series")

# 100 days
Time = future_days

hVaR = -historicalVaR(returns['portfolio'], alpha=5)*np.sqrt(Time)
hCVaR = -historicalCVaR(returns['portfolio'], alpha=5)*np.sqrt(Time)
pRet, pStd = portfolioPerformance(weights, meanReturns, covMatrix, Time)

InitialInvestment = potfolio_value
print(f'Expected Portfolio Return over {future_days} days:   ', round(InitialInvestment*pRet,2))
print('Value at Risk 95th CI                  :   ', round(InitialInvestment*hVaR,2))
print('Conditional VaR 95th CI                :   ', round(InitialInvestment*hCVaR,2))

def var_parametric(portofolioReturns, portfolioStd, distribution='normal', alpha=5, dof=6):
    # because the distribution is symmetric
    if distribution == 'normal':
        VaR = norm.ppf(1-alpha/100)*portfolioStd - portofolioReturns
    elif distribution == 't-distribution':
        nu = dof
        VaR = np.sqrt((nu-2)/nu) * t.ppf(1-alpha/100, nu) * portfolioStd - portofolioReturns
    else:
        raise TypeError("Expected distribution type 'normal'/'t-distribution'")
    return VaR

def cvar_parametric(portofolioReturns, portfolioStd, distribution='normal', alpha=5, dof=6):
    if distribution == 'normal':
        CVaR = (alpha/100)**-1 * norm.pdf(norm.ppf(alpha/100))*portfolioStd - portofolioReturns
    elif distribution == 't-distribution':
        nu = dof
        xanu = t.ppf(alpha/100, nu)
        CVaR = -1/(alpha/100) * (1-nu)**(-1) * (nu-2+xanu**2) * t.pdf(xanu, nu) * portfolioStd - portofolioReturns
    else:
        raise TypeError("Expected distribution type 'normal'/'t-distribution'")
    return CVaR

normVaR = var_parametric(pRet, pStd)
normCVaR = cvar_parametric(pRet, pStd)

tVaR = var_parametric(pRet, pStd, distribution='t-distribution')
tCVaR = cvar_parametric(pRet, pStd, distribution='t-distribution')

print("Normal VaR 95th CI       :      ", round(InitialInvestment*normVaR,2))
print("Normal CVaR 95th CI      :      ", round(InitialInvestment*normCVaR,2))
print("t-dist VaR 95th CI       :      ", round(InitialInvestment*tVaR,2))
print("t-dist CVaR 95th CI      :      ", round(InitialInvestment*tCVaR,2))

# Monte Carlo Method
mc_sims = number_of_simulations
T = future_days #timeframe in days

meanM = np.full(shape=(T, len(weights)), fill_value=meanReturns)
meanM = meanM.T

portfolio_sims = np.full(shape=(T, mc_sims), fill_value=0.0)

initialPortfolio = potfolio_value

for m in range(0, mc_sims):
    # MC loops
    Z = np.random.normal(size=(T, len(weights)))
    L = np.linalg.cholesky(covMatrix)
    dailyReturns = meanM + np.inner(L, Z)
    portfolio_sims[:,m] = np.cumprod(np.inner(weights, dailyReturns.T)+1)*initialPortfolio

def mcVaR(returns, alpha=5):
    """ Input: pandas series of returns
        Output: percentile on return distribution to a given confidence level alpha
    """
    if isinstance(returns, pd.Series):
        return np.percentile(returns, alpha)
    else:
        raise TypeError("Expected a pandas data series.")

def mcCVaR(returns, alpha=5):
    """ Input: pandas series of returns
        Output: CVaR or Expected Shortfall to a given confidence level alpha
    """
    if isinstance(returns, pd.Series):
        belowVaR = returns <= mcVaR(returns, alpha=alpha)
        return returns[belowVaR].mean()
    else:
        raise TypeError("Expected a pandas data series.")

portResults = pd.Series(portfolio_sims[-1,:])

VaR = initialPortfolio - mcVaR(portResults, alpha=5)
CVaR = initialPortfolio - mcCVaR(portResults, alpha=5)

# give us the report

plt.plot(portfolio_sims)
plt.ylabel('Portfolio Value ($)')
plt.xlabel('Days')
plt.title('MC simulation of a stock portfolio')
plt.show()


print("Starting Potfolio Value = ${:,.2f}".format(InitialInvestment))
print()
print('Expected Portfolio Return over '+f"{future_days}"+' days:   ${:,.2f}'.format(round(InitialInvestment*pRet,2)))
print('Value at Risk 95th CI                  :   ${:,.2f}'.format(round(InitialInvestment*hVaR,2)))
print('Conditional VaR 95th CI                :   ${:,.2f}'.format(round(InitialInvestment*hCVaR,2)))

print()

# worst case losses here
#50 percentile loss
print('MC VaR ${:,.2f}'.format(round(VaR,2)))
#95 percentile loss
print('MC CVaR ${:,.2f}'.format(round(CVaR,2)))


print("\nVaR:")

print(' historical VaR 95th CI   :      ${:,.2f}'.format(round(InitialInvestment*hVaR,2)))
print(" Normal VaR 95th CI       :      ${:,.2f}".format(round(InitialInvestment*normVaR,2)))
print(" t-dist VaR 95th CI       :      ${:,.2f}".format(round(InitialInvestment*tVaR,2)))
print(" MC VaR  95th CI          :      ${:,.2f}".format(round(VaR,2)))


print("\nCVaR:")

print(' historical CVaR 95th CI  :      ${:,.2f}'.format(round(InitialInvestment*hCVaR,2)))
print(" Normal CVaR 95th CI      :      ${:,.2f}".format(round(InitialInvestment*normCVaR,2)))
print(" t-dist CVaR 95th CI      :      ${:,.2f}".format(round(InitialInvestment*tCVaR,2)))
print(" MC CVaR 95th CI          :      ${:,.2f}".format(round(CVaR,2)))