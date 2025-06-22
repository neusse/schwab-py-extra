# schwab_positions_monitor.py
from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import httpx
import pandas as pd
from rich.console import Console
from rich.table import Table

from schwab_extra.lib.schwab_lib import authenticate as client_auth

CSV_PATH = Path("schwab_pl.csv")

# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────

def append_pl(timestamp: str, profit_loss: float) -> None:
    """Append a P/L snapshot to *schwab_pl.csv* (create file on first run)."""
    header = not CSV_PATH.exists()
    pd.DataFrame({"timestamp": [timestamp], "profit_loss": [profit_loss]}).to_csv(
        CSV_PATH, mode="a", header=header, index=False
    )


# -----------------------------------------------------------------------------
# Data fetchers
# -----------------------------------------------------------------------------

def fetch_positions(client) -> List[dict]:
    resp = client.get_accounts(fields=client.Account.Fields)
    resp.raise_for_status()
    return resp.json()


def fetch_quotes(client, symbols: list[str]) -> Dict[str, Any]:
    """Return quote payload keyed by symbol (empty dict on HTTP errors)."""
    if not symbols:
        return {}
    try:
        resp = client.get_quotes(symbols)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError:
        return {}


# -----------------------------------------------------------------------------
# Transformations
# -----------------------------------------------------------------------------

def normalise_positions(raw_positions: List[dict]) -> pd.DataFrame:
    df = pd.json_normalize(raw_positions)
    df["lastPrice"] = df["marketValue"] / df["longQuantity"]

    cols = {
        "instrument.description": "Description",
        "instrument.symbol": "Stock",
        "lastPrice": "Last",
        "currentDayProfitLoss": "Day P/L",
        "currentDayProfitLossPercentage": "Day P/L %",
        "longQuantity": "Qty",
        "marketValue": "Market Value",
        "longOpenProfitLoss": "Long P/L",
    }
    out = df[list(cols)].rename(columns=cols)
    numeric_cols = out.select_dtypes("number").columns
    out[numeric_cols] = out[numeric_cols].round(2)
    return out


def _first_nonempty(*values):
    return next((v for v in values if v not in (None, "", "nan")), None)


def enrich_descriptions(df: pd.DataFrame, client) -> pd.DataFrame:
    """Fill missing `Description` cells solely using quote data."""
    missing_idx = df[df["Description"].isna() | (df["Description"].astype(str).str.lower() == "nan")].index
    if missing_idx.empty:
        return df

    symbols = df.loc[missing_idx, "Stock"].str.upper().unique().tolist()
    quotes = fetch_quotes(client, symbols)

    for idx in missing_idx:
        sym = df.at[idx, "Stock"].upper()
        q = quotes.get(sym, {})
        ref = q.get("reference", {})
        desc = _first_nonempty(
            q.get("description"),
            q.get("name"),
            q.get("longName"),
            q.get("shortName"),
            ref.get("description"),
        )
        if desc:
            df.at[idx, "Description"] = desc.title()
    return df


# -----------------------------------------------------------------------------
# Presentation
# -----------------------------------------------------------------------------

def _style_cell(col: str, val: Any) -> str:
    if isinstance(val, (int, float)):
        if col in {"Day P/L", "Day P/L %", "Long P/L"} and val < 0:
            return f"[bold red]{val:.2f}[/bold red]"
        return f"{val:.2f}"
    return str(val)


def build_table(positions: pd.DataFrame) -> Table:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table = Table(title=f"Schwab Positions — {now}")

    highlight_cols = {"Stock", "Description"}
    for col in positions.columns:
        style = "green" if col in highlight_cols else "yellow"
        table.add_column(col, style=style, justify="right")

    for _, row in positions.iterrows():
        table.add_row(*[_style_cell(col, val) for col, val in row.items()])

    totals = positions[["Day P/L", "Market Value", "Long P/L"]].sum()
    append_pl(now, totals["Day P/L"])

    table.add_section()
    table.add_row(
        "Total",
        "",
        "",
        _style_cell("Day P/L", totals["Day P/L"]),
        "",
        "",
        f"{totals['Market Value']:.2f}",
        _style_cell("Long P/L", totals["Long P/L"]),
        style="bold green",
    )
    return table


# -----------------------------------------------------------------------------
# CLI & Runner
# -----------------------------------------------------------------------------

def run_once(console: Console, client) -> None:
    raw = fetch_positions(client)
    all_pos = [pos for acct in raw for pos in acct["securitiesAccount"].get("positions", [])]
    df = normalise_positions(all_pos)
    df = enrich_descriptions(df, client)
    console.print(build_table(df))


def monitor(console: Console, client, interval: int) -> None:
    while True:
        with console.capture() as cap:
            run_once(console, client)
        console.clear()
        print(cap.get())
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Display Schwab positions.")
    parser.add_argument("-w", "--watch", action="store_true", help="Continuously refresh the output.")
    parser.add_argument(
        "-i", "--interval", type=int, default=60, metavar="SEC", help="Refresh interval when --watch is set (default: 60).",
    )
    args = parser.parse_args()

    console = Console()
    client = client_auth()

    if args.watch:
        monitor(console, client, args.interval)
    else:
        run_once(console, client)


if __name__ == "__main__":
    main()
