import yfinance as yf
import pandas as pd
import os, sys
from datetime import datetime, date
from rich.console import Console
from rich.table import Table
from schwab_extra.lib.schwab_lib import get_positions_shares as gps 
from collections import defaultdict
import calendar

def get_dividends(tickers, start_date, end_date):
    dividend_data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends[start_date:end_date]
        #print(f"Dividends for {ticker}:\n{dividends}\n")  # Debug print
        dividend_data[ticker] = dividends
    #print(dividend_data)
    return dividend_data

def clear_screen() -> None:
    """
    Clear the terminal on Windows, macOS, and Linux.

    Uses the standard console commands:
      * Windows  →  cls
      * POSIX    →  clear
    Falls back to printing new-lines if the system call fails.
    """
    try:
        if os.name == "nt":               # Windows (cls)
            os.system("cls")
        else:                             # Linux / macOS / other POSIX (clear)
            os.system("clear")
    except Exception:                     # noqa: BLE001
        # Last-ditch fallback: scroll old content off the viewport.
        sys.stdout.write("\n" * 100)
        sys.stdout.flush()


def create_dividend_calendar(dividend_data, shares_data, start_date, end_date):
    dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    calendar = pd.DataFrame(index=dates)

    for ticker, dividends in dividend_data.items():
        if not dividends.empty:
            dividends = dividends.tz_localize(None)
            monthly_dividends = dividends.resample('MS').sum() * shares_data[ticker]
            monthly_dividends = monthly_dividends.reindex(calendar.index, fill_value=0)
            calendar[ticker] = monthly_dividends

    calendar = calendar.T
    calendar.index.name = 'Stock'
    calendar['Total'] = calendar.sum(axis=1)
    grand_total = calendar.sum(axis=0)
    calendar.loc['Grand Total'] = grand_total
    # Convert date headings to %Y-%m-%d format
    date_columns = [col for col in calendar.columns if col not in ['Total', 'Grand Total']]
    formatted_date_columns = {col: pd.to_datetime(col).strftime('%b-%Y') for col in date_columns}
    calendar.rename(columns=formatted_date_columns, inplace=True)
    return calendar

def print_dividend_calendar(calendar):
    console = Console()
    table = Table(title="Dividend Calendar")

    # Add columns
    table.add_column("Stock", style="cyan", no_wrap=True)
    for col in calendar.columns:
        if col == "Total":
            table.add_column(col, style="green", justify="right")
        else:
            table.add_column(col, style="magenta", justify="right")

    # Add rows
    for index, row in calendar.iterrows():
        row_style = "green" if index == "Grand Total" else None
        table.add_row(index, *[f"{val:.2f}" for val in row], style=row_style)

    console.print(table)


def twelve_month_window(today: date | None = None) -> tuple[str, str]:
    """
    Return the 12-month rolling window as ISO strings.

    * start = 1 st of the month *after* the same month last year  
      (e.g. if today is 2025-06-21 → 2024-07-01)
    * end   = last calendar day of the current month
    """
    today = today or date.today()

    # ---- end date ----
    last_dom = calendar.monthrange(today.year, today.month)[1]
    end_date = date(today.year, today.month, last_dom)

    # ---- start date ----
    next_month = (today.month % 12) + 1
    start_year = today.year if today.month == 12 else today.year - 1
    start_date = date(start_year, next_month, 1)

    return start_date.isoformat(), end_date.isoformat()


def main():
    # Define portfolio and date range
    
    my_positions = gps()

    new_positions: dict[str, float] = defaultdict(float)
    for item in my_positions:
        new_positions[item["symbol"]] += item["shares"]

    tickers = list(new_positions.keys())
    start_date, end_date = twelve_month_window()

    # Get dividend data
    dividend_data = get_dividends(tickers, start_date, end_date)

    # Create dividend calendar
    calendar = create_dividend_calendar(dividend_data, new_positions, start_date, end_date)
    
    clear_screen()

    # Print dividend calendar using Rich
    print_dividend_calendar(calendar)

if __name__ == '__main__':
    main()


