import json
import httpx
import pandas as pd
from rich.console import Console
from rich.table import Table
from datetime import datetime

from schwab_extra.lib.schwab_lib import authenticate as client_auth 
import time
import os


def append_to_csv(timestamp: str, profit_loss: float):
    # Define the file path
    file_path = "schwab_pl.csv"
    
    # Create a DataFrame with the new data
    new_data = pd.DataFrame({
        'timestamp': [timestamp],
        'profit_loss': [profit_loss]
    })
    
    # Check if the file exists
    if not os.path.isfile(file_path):
        # If the file does not exist, write the data with the header
        new_data.to_csv(file_path, mode='w', header=True, index=False)
    else:
        # If the file exists, append the data without the header
        new_data.to_csv(file_path, mode='a', header=False, index=False)


def create_table(mypositions):
    table = Table(title="Schwab Positions")

    # Get the current local time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Rename columns as needed
    column_mapping = {
        'instrument.symbol': 'Stock',
        'instrument.description': f'{current_time} -- DESCRIPTION',
        'currentDayProfitLossPercentage': 'Days P/L %',
        'currentDayProfitLoss': 'Days P/L',
    }
    mypositions.rename(columns=column_mapping, inplace=True)

    # Add columns to the table
    for col in mypositions.columns:
        if col == 'Stock':  # Customize styles for specific columns if needed
            table.add_column(col, style="green", no_wrap=True)
        elif col == f'{current_time} -- DESCRIPTION':
            table.add_column(col, style="green", no_wrap=True)
        else:
            table.add_column(col, style="yellow", justify="right")

    # Add rows to the table
    for _, row in mypositions.iterrows():

        # Applying rounding and formatting
        #df['Days P/L %'] = df['Days P/L %'].apply(lambda x: "{:.2f}".format(round(x, 2)))
        #row['Days P/L %'] = "{:.2f}".format(round(row['Days P/L %'], 2))

        # Round Days P/L % to 2 decimal places if they exist in the row
        if 'Days P/L %' in row:
            row['Days P/L %'] = f"{row['Days P/L %']:.2f}"
            #row['Days P/L %'] = round(row['Days P/L %'], 2)
        if 'Days P/L' in row:
            row['Days P/L'] = f"{row['Days P/L']:.2f}"
        if 'lastPrice' in row:
            row['lastPrice'] = f"{row['lastPrice']:.2f}"
            #row['averagePrice'] = round(row['averagePrice'], 2)
        # if 'averageLongPrice' in row:
        #     row['averageLongPrice'] = f"{row['averageLongPrice']:.2f}"
        if 'marketValue' in row:
            row['marketValue'] = f"{row['marketValue']:.2f}"
        if 'longOpenProfitLoss' in row:
            row['longOpenProfitLoss'] = f"{row['longOpenProfitLoss']:.2f}"
        
        # Check if Days P/L % is negative
        row_style = "bold red" if 'Days P/L %' in row and "-" in row['Days P/L %'] else None

        # Prepare row data with appropriate styles
        row_data = []
        for col, val in row.items():
            if "DESCRIPTION" in col:
                row_data.append(f"[yellow]{val}[/yellow]")
            elif col == 'longOpenProfitLoss' and "-" in val:
                row_data.append(f"[bold red]{val}[/bold red]")
            elif col == 'longOpenProfitLoss' and not "-" in val:
                row_data.append(f"[yellow]{val}[/yellow]")
            else:
                row_data.append(f"[{row_style}]{val}[/{row_style}]" if row_style else str(val))

        table.add_row(*row_data)

    # Calculate totals
    total_days_pl = mypositions['Days P/L'].sum()
    total_market_value = mypositions['marketValue'].sum()
    total_long_open_pl = mypositions['longOpenProfitLoss'].sum()
    mytimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    append_to_csv(mytimestamp,total_days_pl)

    # Add a summary row with totals
    summary_row = [
        "Total",
        "",
        "",
        f"{total_days_pl:.2f}",
        "",
        "",
        f"{total_market_value:.2f}",
        #f"{total_long_open_pl:.2f}"
        f"[bold red]{total_long_open_pl:.2f}[/bold red]" if total_long_open_pl < 0 else f"{total_long_open_pl:.2f}"
    ]

    # Adding an empty section to create a box for the summary row
    table.add_section()
    table.add_row(*summary_row, style="bold green")

    return table
    
def get_my_positions(client):
    resp = client.get_accounts(fields=client.Account.Fields)
    assert resp.status_code == httpx.codes.OK
    data = resp.json()
    return data

def setup_positions(positions):
    # Normalize the JSON data into DataFrame
    positions_df = pd.json_normalize(positions)

    # Specifying the columns that correspond to the Excel template fields
    position_columns = [
        "instrument.description",
        "instrument.symbol",
        "lastPrice",
        "currentDayProfitLoss",
        "currentDayProfitLossPercentage",
        "longQuantity",
        "marketValue",
        "longOpenProfitLoss",

    ]

    positions_df['lastPrice'] = positions_df["marketValue"] / positions_df['longQuantity']


    # Filter the DataFrame to include only the specified columns
    positions_df = positions_df[position_columns]

    positions_df['currentDayProfitLoss'] = positions_df['currentDayProfitLoss'].round(2)
    positions_df['longOpenProfitLoss'] = positions_df['longOpenProfitLoss'].round(2)
    positions_df['lastPrice'] = positions_df['lastPrice'].round(2)
    
    return positions_df

def get_all_positions(client):
    positions = get_my_positions(client)
    #print(positions)
    #quotes = get_all_quotes(client, tickers)
    data = json.loads(json.dumps(positions))
    #print(data)
    # Extract positions data
    all_positions = []
    for sec in data:
        #print(sec["securitiesAccount"]["positions"])
        #print()
        all_positions.extend(sec["securitiesAccount"]["positions"])

    # Convert to DataFrame and setup positions
    df_positions = setup_positions(all_positions)

    # Create and return table
    table = create_table(df_positions)
    return table


def main():
    console = Console()
    # c is the returned client from schwab-py API
    client = client_auth()

    while True:
        table = get_all_positions(client)

        with console.capture() as capture:
            console.print(table)

        # Clear the console and print the captured content
        console.clear()
        print(capture.get())
        
        time.sleep(60)

if __name__ == "__main__":
    main()
