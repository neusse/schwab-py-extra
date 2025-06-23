"""
schwab_extra general library

"""


from __future__ import annotations

from functools import lru_cache
from typing import List
import json
import requests
import pandas as pd
from datetime import datetime
import pandas_market_calendars as mcal




"""
sp500.py

Utility to fetch the current S&P 500 constituency list from Wikipedia.
"""


WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CodeCopilot/1.0; +https://example.com/bot)"
}


class SP500FetchError(RuntimeError):
    """Raised when the S&P 500 list cannot be fetched or parsed."""


@lru_cache(maxsize=1)
def get_sp500_tickers() -> List[str]:
    """Return the list of S&P 500 tickers scraped from Wikipedia.

    Results are memoized for the duration of the process.

    Raises
    ------
    SP500FetchError
        If the Wikipedia page cannot be fetched or parsed.
    """
    try:
        response = requests.get(WIKI_SP500_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SP500FetchError("Network error while fetching S&P 500 page") from exc

    try:
        tables = pd.read_html(response.text, attrs={"id": "constituents"})
    except ValueError as exc:
        raise SP500FetchError("Failed to parse S&P 500 table") from exc

    if not tables:
        raise SP500FetchError("No constituents table found on Wikipedia page")

    df = tables[0]
    if "Symbol" not in df.columns:
        raise SP500FetchError("Expected 'Symbol' column missing in Wikipedia table")

    tickers: list[str] = df["Symbol"].astype(str).str.strip().tolist()
    return [ticker for ticker in tickers if ticker and ticker != "nan"]


    ################################################################
    #
    ################################################################
    def is_weekday(self):
        """
        Checks if the current date is a weekday.

        Returns:
        True if the current date is a weekday (Monday to Friday), False otherwise.
        """
        current_date = datetime.datetime.now().date()
        return current_date.weekday() < 5  # Monday is 0 and Sunday is 6

    def is_tuesday(self):
        """
        Checks if the current date is Tuesday.

        Returns:
        True if the current date is Tuesday, False otherwise.
        """
        current_date = datetime.datetime.now().date()
        return current_date.weekday() == 1  # Monday is 0 and Sunday is 6

    ################################################################
    #
    ################################################################
    def is_market_open(self, date):
        """
        Checks if the stock market is open on a specific date.

        Arguments:
        date -- A datetime.date object representing the date to check

        Returns:
        True if the stock market is open on the given date, False otherwise.

        ::example of use
        date = datetime.date.today()  # Use the desired date

        if not is_market_open(date):
            print(mu.mytimestamp())
            print("Market not open today!")
            raise
        """
        # Get the calendar for the NYSE (New York Stock Exchange)
        nyse = mcal.get_calendar("NYSE")

        # Check if the given date is a valid trading day
        return nyse.valid_days(start_date=date, end_date=date).size > 0






if __name__ == "__main__":
    print(get_sp500_tickers())
