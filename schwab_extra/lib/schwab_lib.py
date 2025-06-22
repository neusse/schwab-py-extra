"""schwab_lib.py

Schwab‑py convenience wrapper
=============================

Features
--------
* **Authentication** helpers (memoised).
* Quotes:
  * :pyfunc:`fetch_quote` – raw “kitchen‑sink” dict.
  * :pyfunc:`normalize_quotes` – tidy *DataFrame*.
  * :pyfunc:`fetch_quote_df` – one‑liner that returns the DataFrame directly.
* Account helper :pyfunc:`get_positions_shares`.
* Candle utilities via :class:`CandleFetcher` + :pyfunc:`resample_intraday` to
  roll lower‑frequency OHLCV bars.

Environment variables (see *ENV_VARS*): ``SCHWAB_TOKEN_PATH``,
``SCHWAB_API_KEY``, ``SCHWAB_APP_SECRET``, ``SCHWAB_CALLBACK_URL``.
"""

from __future__ import annotations

import logging
import json
import os
from datetime import datetime, timedelta, timezone

from functools import lru_cache
from typing import Any, Dict, List, MutableMapping, Sequence, cast

import httpx
import pandas as pd
from schwab.auth import client_from_token_file

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

__all__ = [
    "SchwabAuthError",
    "fetch_env_creds",
    "authenticate",
    "get_positions_shares",
    "fetch_quote",
    "normalize_quotes",
    "fetch_quote_df",
    #"resample_intraday",
    "CandleFetcher",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

ENV_VARS = {
    "SCHWAB_TOKEN_PATH": "Path to the token JSON file",
    "SCHWAB_API_KEY": "Schwab developer API key",
    "SCHWAB_APP_SECRET": "Schwab app secret",
    "SCHWAB_CALLBACK_URL": "OAuth callback URL registered with Schwab",
}


class SchwabAuthError(RuntimeError):
    """Raised when mandatory environment variables are missing or auth fails."""


def _require_env_vars() -> None:
    missing = [name for name in ENV_VARS if not os.getenv(name)]
    if missing:
        for name in missing:
            logger.error("Missing environment variable %s – %s", name, ENV_VARS[name])
        raise SchwabAuthError("Missing environment variables: " + ", ".join(missing))


# ---------------------------------------------------------------------------
# Credential handling & client authentication
# ---------------------------------------------------------------------------


def fetch_env_creds() -> tuple[str, str, str, str]:
    _require_env_vars()
    token_path = os.environ["SCHWAB_TOKEN_PATH"]
    api_key = os.environ["SCHWAB_API_KEY"]
    app_secret = os.environ["SCHWAB_APP_SECRET"]
    callback_url = os.environ["SCHWAB_CALLBACK_URL"]
    return token_path, api_key, app_secret, callback_url


@lru_cache(maxsize=1)
def authenticate() -> Any:  # Schwab client type isn’t stubbed
    token_path, api_key, app_secret, callback_url = fetch_env_creds()
    try:
        return client_from_token_file(token_path, api_key, app_secret) #, redirect_uri=callback_url)
    except Exception as exc:  # noqa: BLE001
        raise SchwabAuthError("Failed to authenticate with Schwab API") from exc


# ---------------------------------------------------------------------------
# Quote helpers
# ---------------------------------------------------------------------------


def _fill_missing_fundamentals(symbol_quote: MutableMapping[str, Any]) -> None:
    """Compute basic fundamentals if absent (inline mutation)."""
    price: float | None = cast(
        float | None,
        symbol_quote.get("lastPrice")
        or symbol_quote.get("mark")
        or symbol_quote.get("regularMarketLastPrice"),
    )

    if price and "eps" in symbol_quote and "peRatio" not in symbol_quote:
        eps = cast(float | None, symbol_quote.get("eps")) or 0.0
        if eps:
            symbol_quote["peRatio"] = round(price / eps, 4)

    if price and "sharesOutstanding" in symbol_quote and "marketCap" not in symbol_quote:
        shares = cast(float | None, symbol_quote.get("sharesOutstanding")) or 0.0
        if shares:
            symbol_quote["marketCap"] = round(price * shares, 2)

    if price and "dividendAmount" in symbol_quote and "dividendYield" not in symbol_quote:
        dividend = cast(float | None, symbol_quote.get("dividendAmount")) or 0.0
        if dividend:
            symbol_quote["dividendYield"] = round((dividend / price) * 100, 2)


def fetch_quote(
    symbols: str | Sequence[str],
    compute_missing_fundamentals: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Return Schwab *kitchen‑sink* quote payload for *symbols*."""
    client = authenticate()

    symbol_list = [symbols] if isinstance(symbols, str) else list(symbols)

#    if hasattr(client, "get_quotes"):
    resp = client.get_quotes(symbol_list)
#    elif hasattr(client, "get_quote"):
#        resp = client.get_quote(symbol_list)  # type: ignore[func-returns-value]
#    else:
#        raise AttributeError("Client does not expose get_quotes/get_quote API")

    if resp.status_code != httpx.codes.OK:
        raise RuntimeError(f"Schwab API responded with status {resp.status_code}")

    data: Dict[str, Dict[str, Any]] = resp.json()

    if compute_missing_fundamentals:
        for quote in data.values():
            _fill_missing_fundamentals(quote)

    return data


def normalize_quotes(quotes: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Flatten *quotes* dict into a :class:`pandas.DataFrame`."""
    df = pd.DataFrame.from_dict(quotes, orient="index").reset_index(names="symbol")
    cols = ["symbol"] + [c for c in df.columns if c != "symbol"]
    return df[cols]


def fetch_quote_df(
    symbols: str | Sequence[str],
    *,
    compute_missing_fundamentals: bool = True,
    client: Any | None = None,
) -> pd.DataFrame:
    """One‑liner → returns :class:`pandas.DataFrame` instead of raw dict."""
    raw = fetch_quote(symbols, compute_missing_fundamentals=compute_missing_fundamentals)
    return normalize_quotes(raw)




# ---------------------------------------------------------------------------
# Account helper
# ---------------------------------------------------------------------------


def get_positions_shares(*, debug: bool = False) -> List[Dict[str, Any]]:
    client = authenticate()
    resp = client.get_accounts(fields=client.Account.Fields)
    if resp.status_code != httpx.codes.OK:
        raise RuntimeError(f"Schwab API responded with status {resp.status_code} {resp}")

    positions: List[Dict[str, Any]] = []
    for account in resp.json():
        acct = account.get("securitiesAccount", {})
        for pos in acct.get("positions", []):
            symbol = pos["instrument"].get("symbol")
            shares = pos.get("longQuantity", 0.0)
            positions.append({"symbol": symbol, "shares": shares})
            if debug:
                print(symbol, shares)

    return positions


# ---------------------------------------------------------------------------
# Candle utilities (unchanged except resample passthrough)
# ---------------------------------------------------------------------------


class CandleFetcher:
    """Fetch and prepare candle data and provide resampling."""

    def __init__(self) -> None:
        self.client = authenticate()

    # ------------------------------------------------------------------
    # Normalisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_response(
        resp_json: Sequence[Dict[str, Any]] | Dict[str, Any]
    ) -> pd.DataFrame:
        """Convert raw JSON payload into a tidy DataFrame.

        Converts the *Series* returned by ``df.pop('candles')`` into a list for
        Pylance‑friendly typing.
        """
        df = pd.DataFrame(resp_json)
        candles_raw: List[Dict[str, Any]] = df.pop("candles").tolist()  # type: ignore[arg-type]
        candles_df = pd.json_normalize(candles_raw)

        # Drop placeholder columns if present
        df.drop(columns=[c for c in ("empty",) if c in df], inplace=True)

        out = pd.concat([candles_df, df], axis=1)
        out["isodate"] = (
            pd.to_datetime(out["datetime"], unit="ms")
            .dt.tz_localize("UTC", nonexistent="shift_forward")
            .dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        )

        cols = [
            "datetime",
            "isodate",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
        return out[cols]

    # ------------------------------------------------------------------
    # Resampling helper
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_30min_to_hour(df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate consecutive 30‑minute candles into hourly bars.

        Converts numeric attributes to *float* to placate static type checkers
        before mathematical operations (Pylance: _scalar cannot be assigned to
        parameter arg1_).
        """
        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
        df = df.sort_values("datetime").reset_index(drop=True)

        records: list[dict[str, Any]] = []
        for first, second in zip(
            df.iloc[::2].itertuples(index=False),
            df.iloc[1::2].itertuples(index=False),
        ):
            open_price: float = cast(float, first.open)
            close_price: float = cast(float, second.close)
            high_price: float = max(cast(float, first.high), cast(float, second.high))
            low_price: float = min(cast(float, first.low), cast(float, second.low))
            volume_total: float = cast(float, first.volume) + cast(float, second.volume)

            records.append(
                {
                    "datetime": first.datetime,
                    "isodate": first.isodate,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume_total,
                }
            )
        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Date utilities
    # ------------------------------------------------------------------

    @staticmethod
    def now() -> datetime:
        """Current UTC timestamp (timezone-aware)."""
        return datetime.now(timezone.utc)                # no deprecation warning

    @staticmethod
    def days_ago(days: int) -> datetime:
        """UTC timestamp *days* ago."""
        return datetime.now(timezone.utc) - timedelta(days=days)

    # ------------------------------------------------------------------
    # Client wrappers
    # ------------------------------------------------------------------

    def get_5m_candles(
        self, symbol: str, start_dt: datetime, end_dt: datetime
    ) -> pd.DataFrame:
        resp = self.client.get_price_history_every_five_minutes(
            symbol, start_datetime=start_dt, end_datetime=end_dt
        )
        return self._normalise_response(resp.json())
    
    def get_15m_candles(
        self, symbol: str, start_dt: datetime, end_dt: datetime
    ) -> pd.DataFrame:
        resp = self.client.get_price_history_every_fifteen_minutes(
            symbol, start_datetime=start_dt, end_datetime=end_dt
        )
        return self._normalise_response(resp.json())

    def get_daily_candles(
        self, symbol: str, start_dt: datetime, end_dt: datetime
    ) -> pd.DataFrame:
        resp = self.client.get_price_history_every_day(
            symbol, start_datetime=start_dt, end_datetime=end_dt
        )
        return self._normalise_response(resp.json())

    def get_hourly_candles(
        self, symbol: str, start_dt: datetime, end_dt: datetime
    ) -> pd.DataFrame:
        resp = self.client.get_price_history_every_thirty_minutes(
            symbol, start_datetime=start_dt, end_datetime=end_dt
        )
        df_30m = self._normalise_response(resp.json())
        return self._merge_30min_to_hour(df_30m)


    # New generic resample wrapper
    # @staticmethod
    # def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:  # noqa: D401,E501
    #     """Delegate to module‑level :pyfunc:`resample_intraday`."""
    #     return resample_intraday(df, rule)


# ---------------------------------------------------------------------------
# ── CLI demo ────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

if __name__ == "__main__":
#    logging.basicConfig(level=logging.INFO)

    quote_df = fetch_quote(["AAPL", "MSFT"])
    print(json.dumps(quote_df,indent=4))

    fetcher = CandleFetcher()
    raw_5m = fetcher.get_5m_candles("AAPL", CandleFetcher.days_ago(1), CandleFetcher.now())
    print(raw_5m)
    #hourly = resample_intraday(raw_5m, "1H")
    #print(hourly.head())


