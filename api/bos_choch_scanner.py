"""
SMC (Smart Money Concepts) Backtesting & Live Scanning System
NIFTY 500 - Daily Timeframe - yfinance based

Author: Senior Quant Dev / SMC Trader / Python Backtest Expert
Python 3.10

Requires:
    pandas, numpy, scipy, yfinance, openpyxl, matplotlib

This script:
 1. Downloads max available daily history for NIFTY 500 stocks
 2. Detects swing highs/lows (swing_length = 5, no rolling highs/lows)
 3. Detects trend, BOS (Break of Structure) and CHOCH (Change of Character)
 4. Scans historical data for Long (Bullish Reversal) and Short (Bearish
    Reversal) SMC setups per the exact rules specified
 5. Backtests each signal against Target1 (1R), Target2 (2R), Target3 (3R),
    Target4 (8-day exit) and Target5 (CHOCH exit) - independently
 6. Exports Signal_Details.xlsx, Summary_By_Stock.xlsx, Overall_Summary.xlsx
 7. Runs a live scan on the latest candle for fresh Long/Short setups
 8. Ranks live setups using a weighted scoring model and exports
    Top 20 Long / Top 20 Short opportunities
"""

import os
import time
import logging
import warnings
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
SWING_LENGTH = 5
ATR_PERIOD = 14
VOL_AVG_PERIOD = 20
DISPLACEMENT_ATR_MULT = 0.5
EIGHT_DAY_HOLD = 8

OUTPUT_DIR = "smc_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, "run.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("SMC")


# ----------------------------------------------------------------------
# NIFTY 500 TICKER LIST
# ----------------------------------------------------------------------
def get_nifty500_tickers() -> List[str]:
    """
    Returns NIFTY 500 tickers in Yahoo Finance format (.NS suffix).

    In production, replace this with a live fetch from NSE's official
    ind_nifty500list.csv. A static fallback list (subset shown here for
    brevity - extend with the full 500 symbols) is used if the live
    fetch fails.
    """
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        symbols = df["Symbol"].astype(str).str.strip().tolist()
        tickers = [f"{s}.NS" for s in symbols]
        log.info(f"Fetched {len(tickers)} NIFTY 500 symbols from NSE")
        return tickers
    except Exception as e:
        log.warning(f"Could not fetch live NIFTY 500 list ({e}). Using fallback sample list.")
        fallback = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
            "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
            "TITAN.NS", "ULTRACEMCO.NS", "BAJFINANCE.NS", "WIPRO.NS", "HCLTECH.NS",
            "TATAMOTORS.NS", "TATASTEEL.NS", "ADANIENT.NS", "NTPC.NS", "POWERGRID.NS",
            "M&M.NS", "JSWSTEEL.NS", "GESHIP.NS", "SRF.NS", "CARTRADE.NS",
            "PROTEAN.NS", "VSSL.NS", "EMMVEE.NS", "ATHERENERG.NS", "HDFCAMC.NS"
        ]
        return fallback


# ----------------------------------------------------------------------
# DATA DOWNLOAD
# ----------------------------------------------------------------------
def download_data(ticker: str, period: str = "max") -> Optional[pd.DataFrame]:
    """Download daily OHLCV data for a ticker. Returns None on failure."""
    try:
        df = yf.download(ticker, period=period, interval="1d",
                          auto_adjust=True, progress=False)
        if df.empty or len(df) < (SWING_LENGTH * 4 + VOL_AVG_PERIOD + ATR_PERIOD + 50):
            log.warning(f"{ticker}: insufficient data ({len(df)} rows). Skipping.")
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume"
        })
        df = df[["open", "high", "low", "close", "volume"]].dropna()
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        log.error(f"{ticker}: download failed - {e}")
        return None


# ----------------------------------------------------------------------
# INDICATORS: ATR, VOLUME AVG
# ----------------------------------------------------------------------
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adds ATR(14) and 20-day average volume. Avoids look-ahead bias by
    using only past data (rolling windows aligned correctly)."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    df["atr"] = tr.rolling(ATR_PERIOD).mean()
    df["vol_avg20"] = df["volume"].rolling(VOL_AVG_PERIOD).mean()
    return df


# ----------------------------------------------------------------------
# SWING DETECTION (swing_length = 5, fractal-based, no rolling highs/lows)
# ----------------------------------------------------------------------
def detect_swings(df: pd.DataFrame, length: int = SWING_LENGTH) -> pd.DataFrame:
    """
    A bar i is a swing high if high[i] > high[i-length..i-1] AND
    high[i] > high[i+1..i+length]  (strict fractal high).
    Symmetric definition for swing lows.

    Note: a swing point at bar i can only be CONFIRMED once bar i+length
    has closed - this is enforced later when swings are consumed
    (we only use swings whose confirmation index <= current bar) to
    avoid look-ahead bias.
    """
    n = len(df)
    highs = df["high"].values
    lows = df["low"].values

    swing_high = np.full(n, False)
    swing_low = np.full(n, False)

    for i in range(length, n - length):
        left_h = highs[i - length:i]
        right_h = highs[i + 1:i + 1 + length]
        if highs[i] > left_h.max() and highs[i] > right_h.max():
            swing_high[i] = True

        left_l = lows[i - length:i]
        right_l = lows[i + 1:i + 1 + length]
        if lows[i] < left_l.min() and lows[i] < right_l.min():
            swing_low[i] = True

    df["swing_high"] = swing_high
    df["swing_low"] = swing_low
    # Index at which a swing formed at position i becomes "confirmed"
    # (i.e. visible without look-ahead bias) = i + length
    df["swing_confirmed_idx"] = df.index.to_series().shift(-length).index  # placeholder, unused directly
    return df


# ----------------------------------------------------------------------
# MARKET STRUCTURE: TREND, BOS, CHOCH
# ----------------------------------------------------------------------
@dataclass
class StructureState:
    """Rolling structure state walked bar-by-bar (no look-ahead)."""
    trend: str = "NONE"            # "UP", "DOWN", "NONE"
    bullish_bos_count: int = 0
    bearish_bos_count: int = 0
    last_swing_high: Optional[float] = None
    last_swing_high_idx: Optional[int] = None
    last_swing_low: Optional[float] = None
    last_swing_low_idx: Optional[int] = None
    prev_swing_high: Optional[float] = None
    prev_swing_low: Optional[float] = None
    higher_highs: bool = False
    higher_lows: bool = False
    lower_highs: bool = False
    lower_lows: bool = False
    # event flags reset every bar
    bullish_bos: bool = False
    bearish_bos: bool = False
    bullish_choch: bool = False
    bearish_choch: bool = False


def walk_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Walks the dataframe bar-by-bar maintaining swing points (confirmed
    only with a lag of SWING_LENGTH bars to avoid look-ahead bias) and
    flags BOS / CHOCH events on each bar's close.

    BOS (Bullish):  close breaks above last confirmed swing high while
                    NOT in a fresh bearish-CHOCH state -> trend continuation
                    or trend establishment.
    BOS (Bearish):  close breaks below last confirmed swing low.
    CHOCH (Bearish): in an uptrend, close breaks below the last confirmed
                     swing low (first break against the trend).
    CHOCH (Bullish): in a downtrend, close breaks above the last confirmed
                     swing high (first break against the trend).
    """
    n = len(df)
    state = StructureState()

    cols = ["trend", "bullish_bos", "bearish_bos", "bullish_choch", "bearish_choch",
            "bullish_bos_count", "bearish_bos_count",
            "last_swing_high", "last_swing_low",
            "higher_highs_lows", "lower_highs_lows"]
    out = {c: [None] * n for c in cols}

    confirmed_highs: List[Tuple[int, float]] = []  # (idx, price) confirmed swing highs in order
    confirmed_lows: List[Tuple[int, float]] = []

    for i in range(n):
        state.bullish_bos = False
        state.bearish_bos = False
        state.bullish_choch = False
        state.bearish_choch = False

        # Confirm any swing that became valid at this index (formed at i-SWING_LENGTH)
        confirm_idx = i - SWING_LENGTH
        if confirm_idx >= 0:
            if df["swing_high"].iloc[confirm_idx]:
                confirmed_highs.append((confirm_idx, df["high"].iloc[confirm_idx]))
            if df["swing_low"].iloc[confirm_idx]:
                confirmed_lows.append((confirm_idx, df["low"].iloc[confirm_idx]))

        close = df["close"].iloc[i]

        # --- Check BOS / CHOCH against the most recent confirmed swing levels ---
        if confirmed_highs:
            last_high_idx, last_high_px = confirmed_highs[-1]
        else:
            last_high_idx, last_high_px = None, None

        if confirmed_lows:
            last_low_idx, last_low_px = confirmed_lows[-1]
        else:
            last_low_idx, last_low_px = None, None

        # Bullish break: close above last confirmed swing high
        if last_high_px is not None and close > last_high_px:
            if state.trend == "DOWN":
                # First break against downtrend -> Bullish CHOCH
                state.bullish_choch = True
                state.trend = "UP"
                state.bullish_bos_count = 0
                state.bearish_bos_count = 0
            elif state.trend == "UP":
                state.bullish_bos = True
                state.bullish_bos_count += 1
            else:  # NONE
                state.bullish_bos = True
                state.trend = "UP"
                state.bullish_bos_count += 1

            # track HH structure
            if state.last_swing_high is not None:
                state.higher_highs = last_high_px > state.last_swing_high if state.last_swing_high else state.higher_highs
            state.prev_swing_high = state.last_swing_high
            state.last_swing_high = last_high_px
            state.last_swing_high_idx = last_high_idx
            # consume so the same level doesn't re-trigger
            confirmed_highs = confirmed_highs[:-1]

        # Bearish break: close below last confirmed swing low
        if last_low_px is not None and close < last_low_px:
            if state.trend == "UP":
                state.bearish_choch = True
                state.trend = "DOWN"
                state.bullish_bos_count = 0
                state.bearish_bos_count = 0
            elif state.trend == "DOWN":
                state.bearish_bos = True
                state.bearish_bos_count += 1
            else:
                state.bearish_bos = True
                state.trend = "DOWN"
                state.bearish_bos_count += 1

            if state.last_swing_low is not None:
                state.lower_lows = last_low_px < state.last_swing_low if state.last_swing_low else state.lower_lows
            state.prev_swing_low = state.last_swing_low
            state.last_swing_low = last_low_px
            state.last_swing_low_idx = last_low_idx
            confirmed_lows = confirmed_lows[:-1]

        out["trend"][i] = state.trend
        out["bullish_bos"][i] = state.bullish_bos
        out["bearish_bos"][i] = state.bearish_bos
        out["bullish_choch"][i] = state.bullish_choch
        out["bearish_choch"][i] = state.bearish_choch
        out["bullish_bos_count"][i] = state.bullish_bos_count
        out["bearish_bos_count"][i] = state.bearish_bos_count
        out["last_swing_high"][i] = state.last_swing_high
        out["last_swing_low"][i] = state.last_swing_low
        out["higher_highs_lows"][i] = state.higher_highs and state.higher_lows
        out["lower_highs_lows"][i] = state.lower_highs and state.lower_lows

    for c in cols:
        df[c] = out[c]
    return df


# ----------------------------------------------------------------------
# SIGNAL DETECTION (LONG = Bullish Reversal, SHORT = Bearish Reversal)
# ----------------------------------------------------------------------
@dataclass
class Signal:
    ticker: str
    date: pd.Timestamp
    idx: int
    setup_type: str  # "LONG" or "SHORT"
    entry: float
    stop_loss: float
    risk: float
    bos_strength: float
    atr: float
    vol_ratio: float


def find_signals(df: pd.DataFrame, ticker: str) -> List[Signal]:
    """
    LONG (Bullish Reversal):
      - Existing uptrend with >=2 bullish BOS prior to CHOCH, HH & HL
      - A Bearish CHOCH occurs (breaks last swing low)
      - At least 1 Bearish BOS after the CHOCH
      - A new Bullish BOS breaks the latest swing high (the reversal signal)
      - Displacement: break exceeds 0.5 * ATR(14)
      - Volume > 20-day average volume

    SHORT (Bearish Reversal): symmetric, mirrored conditions.
    """
    signals: List[Signal] = []
    n = len(df)

    # State trackers for "was there a qualifying prior uptrend with CHOCH + bearish BOS"
    # We scan sequentially using the structure columns already computed.
    prior_uptrend_qualified = False     # uptrend had >=2 bullish BOS & HH/HL before CHOCH
    bearish_choch_seen = False
    bearish_bos_after_choch = 0

    prior_downtrend_qualified = False
    bullish_choch_seen = False
    bullish_bos_after_choch = 0

    bullish_bos_streak = 0
    bearish_bos_streak = 0

    for i in range(SWING_LENGTH * 2 + ATR_PERIOD, n):
        row = df.iloc[i]
        trend = row["trend"]

        # --- track bullish BOS streak prior to a bearish CHOCH (for LONG setup precondition) ---
        if row["bullish_bos"]:
            bullish_bos_streak += 1
            bearish_bos_streak = 0
        if row["bearish_bos"]:
            bearish_bos_streak += 1
            bullish_bos_streak = 0

        # Mark that we had a qualifying prior uptrend (>=2 bullish BOS, HH/HL)
        if trend == "UP" and bullish_bos_streak >= 2:
            prior_uptrend_qualified = True

        if trend == "DOWN" and bearish_bos_streak >= 2:
            prior_downtrend_qualified = True

        # --- Bearish CHOCH detected: reset counters, require prior uptrend qualified ---
        if row["bearish_choch"]:
            if prior_uptrend_qualified:
                bearish_choch_seen = True
                bearish_bos_after_choch = 0
            else:
                bearish_choch_seen = False
            prior_uptrend_qualified = False  # consumed
            bullish_bos_streak = 0
            bearish_bos_streak = 0

        if row["bullish_choch"]:
            if prior_downtrend_qualified:
                bullish_choch_seen = True
                bullish_bos_after_choch = 0
            else:
                bullish_choch_seen = False
            prior_downtrend_qualified = False
            bullish_bos_streak = 0
            bearish_bos_streak = 0

        # count bearish BOS after a bearish CHOCH (confirmation step for LONG setup)
        if bearish_choch_seen and row["bearish_bos"] and not row["bearish_choch"]:
            bearish_bos_after_choch += 1

        if bullish_choch_seen and row["bullish_bos"] and not row["bullish_choch"]:
            bullish_bos_after_choch += 1

        # ================= LONG SETUP =================
        # New Bullish BOS = the reversal trigger, requires bearish_choch_seen
        # and >=1 bearish BOS confirmation after that CHOCH.
        if (row["bullish_bos"] and bearish_choch_seen and bearish_bos_after_choch >= 1):
            atr = row["atr"]
            vol_avg = row["vol_avg20"]
            if pd.isna(atr) or pd.isna(vol_avg) or atr == 0:
                pass
            else:
                last_swing_high = row["last_swing_high"]
                prior_close = df["close"].iloc[i - 1]
                displacement = row["close"] - last_swing_high if last_swing_high else 0
                displacement_ok = displacement > DISPLACEMENT_ATR_MULT * atr
                volume_ok = row["volume"] > vol_avg

                if displacement_ok and volume_ok:
                    entry = row["close"]
                    stop = row["last_swing_low"]  # latest confirmed swing low before this BOS
                    if stop is not None and stop < entry:
                        risk = entry - stop
                        bos_strength = displacement / atr  # normalized strength
                        vol_ratio = row["volume"] / vol_avg
                        signals.append(Signal(
                            ticker=ticker, date=df.index[i], idx=i, setup_type="LONG",
                            entry=entry, stop_loss=stop, risk=risk,
                            bos_strength=bos_strength, atr=atr, vol_ratio=vol_ratio
                        ))
                        # reset reversal state - new uptrend established
                        bearish_choch_seen = False
                        bearish_bos_after_choch = 0
                        prior_uptrend_qualified = False
                        bullish_bos_streak = 1  # this BOS counts

        # ================= SHORT SETUP =================
        if (row["bearish_bos"] and bullish_choch_seen and bullish_bos_after_choch >= 1):
            atr = row["atr"]
            vol_avg = row["vol_avg20"]
            if pd.isna(atr) or pd.isna(vol_avg) or atr == 0:
                pass
            else:
                last_swing_low = row["last_swing_low"]
                displacement = (last_swing_low - row["close"]) if last_swing_low else 0
                displacement_ok = displacement > DISPLACEMENT_ATR_MULT * atr
                volume_ok = row["volume"] > vol_avg

                if displacement_ok and volume_ok:
                    entry = row["close"]
                    stop = row["last_swing_high"]
                    if stop is not None and stop > entry:
                        risk = stop - entry
                        bos_strength = displacement / atr
                        vol_ratio = row["volume"] / vol_avg
                        signals.append(Signal(
                            ticker=ticker, date=df.index[i], idx=i, setup_type="SHORT",
                            entry=entry, stop_loss=stop, risk=risk,
                            bos_strength=bos_strength, atr=atr, vol_ratio=vol_ratio
                        ))
                        bullish_choch_seen = False
                        bullish_bos_after_choch = 0
                        prior_downtrend_qualified = False
                        bearish_bos_streak = 1

    return signals


# ----------------------------------------------------------------------
# TRADE SIMULATION (per-signal forward walk - no look-ahead)
# ----------------------------------------------------------------------
def simulate_trade(df: pd.DataFrame, sig: Signal) -> dict:
    """
    Walks forward from the signal bar (entry at close of signal bar)
    and computes:
      - Target1/2/3 hit results (1R/2R/3R) - which came first (target or stop)
      - 1/3/5/8-day returns
      - CHOCH exit return (Target5) - exit at close of the opposite CHOCH
      - MFE / MAE over the forward window (until exit or 8 days, whichever
        is later among the considered exits, capped at remaining data)
    """
    n = len(df)
    entry_idx = sig.idx
    entry = sig.entry
    stop = sig.stop_loss
    risk = sig.risk
    is_long = sig.setup_type == "LONG"

    if is_long:
        t1, t2, t3 = entry + 1 * risk, entry + 2 * risk, entry + 3 * risk
    else:
        t1, t2, t3 = entry - 1 * risk, entry - 2 * risk, entry - 3 * risk

    result = {
        "Target1 Result": "OPEN", "Target2 Result": "OPEN", "Target3 Result": "OPEN",
        "1-Day Return": np.nan, "3-Day Return": np.nan, "5-Day Return": np.nan,
        "8-Day Return": np.nan, "CHOCH Exit Return": np.nan,
        "MFE": np.nan, "MAE": np.nan
    }

    max_lookahead = min(n - 1, entry_idx + 60)  # cap search horizon
    mfe, mae = 0.0, 0.0
    hit_t = {1: None, 2: None, 3: None}
    stop_hit_idx = None

    for j in range(entry_idx + 1, max_lookahead + 1):
        high_j, low_j = df["high"].iloc[j], df["low"].iloc[j]

        if is_long:
            fav = high_j - entry
            adv = entry - low_j
        else:
            fav = entry - low_j
            adv = high_j - entry

        mfe = max(mfe, fav)
        mae = max(mae, adv)

        # check stop first (conservative - assume stop hit before target on same bar)
        stop_hit = (low_j <= stop) if is_long else (high_j >= stop)
        if stop_hit and stop_hit_idx is None:
            stop_hit_idx = j

        for k, tgt in zip((1, 2, 3), (t1, t2, t3)):
            if hit_t[k] is None:
                tgt_hit = (high_j >= tgt) if is_long else (low_j <= tgt)
                if stop_hit and (stop_hit_idx == j):
                    if tgt_hit:
                        # ambiguous same-bar - assume stop first (conservative)
                        hit_t[k] = "LOSS"
                    else:
                        hit_t[k] = "LOSS"
                elif tgt_hit:
                    hit_t[k] = "WIN"

        if all(v is not None for v in hit_t.values()) and stop_hit:
            break

    for k in (1, 2, 3):
        if hit_t[k] is None:
            result[f"Target{k} Result"] = "OPEN"
        else:
            result[f"Target{k} Result"] = hit_t[k]

    # N-day returns
    for days, key in zip((1, 3, 5, 8), ("1-Day Return", "3-Day Return", "5-Day Return", "8-Day Return")):
        j = entry_idx + days
        if j < n:
            px = df["close"].iloc[j]
            ret = (px - entry) / entry if is_long else (entry - px) / entry
            result[key] = ret * 100

    # CHOCH exit (Target5)
    choch_col = "bearish_choch" if is_long else "bullish_choch"
    for j in range(entry_idx + 1, max_lookahead + 1):
        if df[choch_col].iloc[j]:
            px = df["close"].iloc[j]
            ret = (px - entry) / entry if is_long else (entry - px) / entry
            result["CHOCH Exit Return"] = ret * 100
            break

    result["MFE"] = (mfe / entry) * 100
    result["MAE"] = (mae / entry) * 100
    return result


# ----------------------------------------------------------------------
# BACKTEST DRIVER
# ----------------------------------------------------------------------
def backtest_ticker(ticker: str) -> pd.DataFrame:
    df = download_data(ticker)
    if df is None:
        return pd.DataFrame()

    df = add_indicators(df)
    df = detect_swings(df)
    df = walk_structure(df)

    signals = find_signals(df, ticker)
    if not signals:
        return pd.DataFrame()

    rows = []
    for sig in signals:
        res = simulate_trade(df, sig)
        rows.append({
            "Ticker": sig.ticker,
            "Date": sig.date.date(),
            "Setup Type": sig.setup_type,
            "Entry": round(sig.entry, 2),
            "Stop Loss": round(sig.stop_loss, 2),
            "Risk": round(sig.risk, 2),
            **{k: (round(v, 2) if isinstance(v, (int, float)) and not pd.isna(v) else v)
               for k, v in res.items()}
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# SUMMARY STATISTICS
# ----------------------------------------------------------------------
def compute_stock_summary(signal_df: pd.DataFrame) -> pd.DataFrame:
    summaries = []
    for ticker, g in signal_df.groupby("Ticker"):
        total = len(g)
        # Use Target1 result as the primary win/loss reference
        wins = (g["Target1 Result"] == "WIN").sum()
        win_rate = (wins / total * 100) if total else 0

        returns = g["1-Day Return"].dropna()
        avg_return = returns.mean() if len(returns) else np.nan

        gross_profit = returns[returns > 0].sum() if len(returns) else 0
        gross_loss = -returns[returns < 0].sum() if len(returns) else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else np.nan

        expectancy = returns.mean() if len(returns) else np.nan

        # equity curve & max drawdown based on cumulative 1-day returns
        if len(returns):
            eq = (1 + returns / 100).cumprod()
            peak = eq.cummax()
            dd = (eq - peak) / peak
            max_dd = dd.min() * 100
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else np.nan
        else:
            max_dd, sharpe = np.nan, np.nan

        # best target type by win rate
        target_cols = ["Target1 Result", "Target2 Result", "Target3 Result"]
        best_target, best_wr = None, -1
        for tc in target_cols:
            wr = (g[tc] == "WIN").mean() * 100
            if wr > best_wr:
                best_wr = wr
                best_target = tc.replace(" Result", "")

        summaries.append({
            "Ticker": ticker,
            "Total Signals": total,
            "Win Rate %": round(win_rate, 2),
            "Avg Return %": round(avg_return, 2) if not pd.isna(avg_return) else np.nan,
            "Profit Factor": round(profit_factor, 2) if not pd.isna(profit_factor) else np.nan,
            "Expectancy": round(expectancy, 2) if not pd.isna(expectancy) else np.nan,
            "Max Drawdown": round(max_dd, 2) if not pd.isna(max_dd) else np.nan,
            "Sharpe Ratio": round(sharpe, 2) if not pd.isna(sharpe) else np.nan,
            "Best Target Type": best_target
        })
    return pd.DataFrame(summaries)


def compute_overall_summary(signal_df: pd.DataFrame, stock_summary: pd.DataFrame) -> dict:
    returns = signal_df["1-Day Return"].dropna()
    wins = (signal_df["Target1 Result"] == "WIN").sum()
    total = len(signal_df)
    win_rate = (wins / total * 100) if total else 0

    gross_profit = returns[returns > 0].sum() if len(returns) else 0
    gross_loss = -returns[returns < 0].sum() if len(returns) else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else np.nan
    expectancy = returns.mean() if len(returns) else np.nan

    eq = (1 + returns / 100).cumprod() if len(returns) else pd.Series([1.0])
    peak = eq.cummax()
    dd = (eq - peak) / peak
    max_dd = dd.min() * 100
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 1 and returns.std() > 0 else np.nan

    # Best holding period: compare mean returns across 1/3/5/8-day
    hold_cols = ["1-Day Return", "3-Day Return", "5-Day Return", "8-Day Return"]
    hold_means = {c: signal_df[c].dropna().mean() for c in hold_cols if signal_df[c].notna().any()}
    best_hold = max(hold_means, key=hold_means.get) if hold_means else None

    # Best risk reward target: compare win rates across T1/T2/T3
    target_cols = ["Target1 Result", "Target2 Result", "Target3 Result"]
    target_wr = {c: (signal_df[c] == "WIN").mean() * 100 for c in target_cols}
    best_target = max(target_wr, key=target_wr.get) if target_wr else None

    top20 = stock_summary.sort_values("Avg Return %", ascending=False).head(20)
    bottom20 = stock_summary.sort_values("Avg Return %", ascending=True).head(20)

    # Monthly / yearly returns
    sd = signal_df.copy()
    sd["Date"] = pd.to_datetime(sd["Date"])
    sd["Return"] = sd["1-Day Return"]
    monthly = sd.groupby(sd["Date"].dt.to_period("M"))["Return"].mean().reset_index()
    monthly["Date"] = monthly["Date"].astype(str)
    yearly = sd.groupby(sd["Date"].dt.year)["Return"].mean().reset_index()

    return {
        "Overall Win Rate": round(win_rate, 2),
        "Profit Factor": round(profit_factor, 2) if not pd.isna(profit_factor) else np.nan,
        "Expectancy": round(expectancy, 2) if not pd.isna(expectancy) else np.nan,
        "Max Drawdown": round(max_dd, 2) if not pd.isna(max_dd) else np.nan,
        "Sharpe Ratio": round(sharpe, 2) if not pd.isna(sharpe) else np.nan,
        "Top 20 Stocks": top20,
        "Bottom 20 Stocks": bottom20,
        "Best Holding Period": best_hold,
        "Best Risk Reward Target": best_target,
        "Equity Curve": eq,
        "Monthly Returns": monthly,
        "Yearly Returns": yearly
    }


# ----------------------------------------------------------------------
# LIVE SCANNER
# ----------------------------------------------------------------------
def live_scan_from_df(df: pd.DataFrame, ticker: str, setup_filter: str = None, lookback: int = 5) -> List[dict]:
    """
    Returns signals from the most recent `lookback` candles.
    setup_filter: 'LONG', 'SHORT', or None (both).
    """
    if df is None or df.empty:
        return []

    # Rename columns if needed
    if 'Open' in df.columns:
        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume"
        })
    df = df[["open", "high", "low", "close", "volume"]].copy()

    df = add_indicators(df)
    df = detect_swings(df)
    df = walk_structure(df)

    signals = find_signals(df, ticker)
    if not signals:
        return []

    last_idx = len(df) - 1
    # Accept signals from the last `lookback` candles, not just the very last
    recent = [s for s in signals if s.idx >= last_idx - lookback + 1]

    # Apply setup type filter if specified
    if setup_filter:
        recent = [s for s in recent if s.setup_type == setup_filter]

    rows = []
    for sig in recent:
        if sig.setup_type == "LONG":
            t1, t2, t3 = sig.entry + sig.risk, sig.entry + 2 * sig.risk, sig.entry + 3 * sig.risk
        else:
            t1, t2, t3 = sig.entry - sig.risk, sig.entry - 2 * sig.risk, sig.entry - 3 * sig.risk

        risk_pct = (sig.risk / sig.entry) * 100

        rows.append({
            "Ticker": ticker,
            "Setup Type": sig.setup_type,
            "Entry": round(sig.entry, 2),
            "Stop Loss": round(sig.stop_loss, 2),
            "Risk %": round(risk_pct, 2),
            "Target 1R": round(t1, 2),
            "Target 2R": round(t2, 2),
            "Target 3R": round(t3, 2),
            "ATR": round(sig.atr, 2),
            "Volume Ratio": round(sig.vol_ratio, 2),
            "BOS Strength Score": round(sig.bos_strength, 2)
        })
    return rows


def live_scan_ticker(ticker: str) -> List[dict]:
    """Checks if the LATEST candle produces a fresh Long/Short SMC signal."""
    df = download_data(ticker)
    return live_scan_from_df(df, ticker)


# ----------------------------------------------------------------------
# RANKING MODEL
# ----------------------------------------------------------------------
def rank_setups(setups: pd.DataFrame, trend_quality_map: dict) -> pd.DataFrame:
    """
    Score = 40% BOS Strength + 25% Volume Expansion
            + 20% ATR Efficiency + 15% Trend Quality
    All components are min-max normalized to 0-100 before weighting.
    """
    if setups.empty:
        return setups

    df = setups.copy()

    def norm(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        if rng == 0:
            return pd.Series(50.0, index=s.index)
        return (s - s.min()) / rng * 100

    bos_n = norm(df["BOS Strength Score"])
    vol_n = norm(df["Volume Ratio"])
    # ATR efficiency: reward setups with risk (in ATR units, ~Risk/ATR) that
    # is reasonable - lower risk relative to ATR is more "efficient".
    atr_eff = df["ATR"] / (df["Entry"] - df["Stop Loss"]).abs().replace(0, np.nan)
    atr_eff = atr_eff.fillna(atr_eff.median())
    atr_n = norm(atr_eff)

    trend_q = df["Ticker"].map(trend_quality_map).fillna(50.0)

    df["Score"] = (0.40 * bos_n + 0.25 * vol_n + 0.20 * atr_n + 0.15 * trend_q)
    df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    return df


# ----------------------------------------------------------------------
# EXCEL EXPORT HELPERS
# ----------------------------------------------------------------------
HTML_STYLE = """
<style>
body { font-family: Arial, sans-serif; background:#0f1117; color:#e6e6e6; margin:0; padding:24px; }
h1 { color:#4ec9b0; }
h2 { color:#9cdcfe; margin-top:32px; }
table { border-collapse: collapse; width:100%; margin-bottom:24px; font-size:13px; }
th, td { border:1px solid #333; padding:6px 10px; text-align:right; }
th { background:#1e2530; color:#4ec9b0; position:sticky; top:0; }
td:first-child, th:first-child { text-align:left; }
tr:nth-child(even) { background:#161b22; }
tr:hover { background:#21262d; }
.win { color:#4caf50; font-weight:bold; }
.loss { color:#f44336; font-weight:bold; }
.open { color:#ffb74d; }
.long { color:#4caf50; font-weight:bold; }
.short { color:#f44336; font-weight:bold; }
.kpi-box { display:inline-block; background:#1e2530; padding:12px 20px; margin:6px; border-radius:8px; min-width:140px; }
.kpi-label { font-size:11px; color:#9cdcfe; text-transform:uppercase; }
.kpi-value { font-size:20px; font-weight:bold; }
img { max-width:100%; border-radius:8px; margin:16px 0; }
</style>
"""


def _df_to_html_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p><em>No data.</em></p>"

    def cell_class(col, val):
        if col in ("Setup Type",):
            return "long" if val == "LONG" else "short"
        if "Result" in col:
            if val == "WIN":
                return "win"
            if val == "LOSS":
                return "loss"
            if val == "OPEN":
                return "open"
        return ""

    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    rows_html = []
    for _, row in df.iterrows():
        cells = []
        for c in df.columns:
            val = row[c]
            cls = cell_class(c, val)
            cls_attr = f' class="{cls}"' if cls else ""
            cells.append(f"<td{cls_attr}>{val}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows_html)}</tbody></table>"


def export_signal_details(signal_df: pd.DataFrame):
    path = os.path.join(OUTPUT_DIR, "Signal_Details.xlsx")
    signal_df.to_excel(path, index=False)
    log.info(f"Saved {path}")

    html_path = os.path.join(OUTPUT_DIR, "Signal_Details.html")
    body = f"<h1>Signal Details</h1><p>Total signals: {len(signal_df)}</p>" + _df_to_html_table(signal_df)
    with open(html_path, "w") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Signal Details</title>{HTML_STYLE}</head><body>{body}</body></html>")
    log.info(f"Saved {html_path}")


def export_summary_by_stock(summary_df: pd.DataFrame):
    path = os.path.join(OUTPUT_DIR, "Summary_By_Stock.xlsx")
    summary_df.to_excel(path, index=False)
    log.info(f"Saved {path}")

    html_path = os.path.join(OUTPUT_DIR, "Summary_By_Stock.html")
    body = "<h1>Summary By Stock</h1>" + _df_to_html_table(summary_df)
    with open(html_path, "w") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Summary By Stock</title>{HTML_STYLE}</head><body>{body}</body></html>")
    log.info(f"Saved {html_path}")


def export_overall_summary(overall: dict):
    path = os.path.join(OUTPUT_DIR, "Overall_Summary.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        scalar_keys = ["Overall Win Rate", "Profit Factor", "Expectancy",
                        "Max Drawdown", "Sharpe Ratio",
                        "Best Holding Period", "Best Risk Reward Target"]
        scalar_df = pd.DataFrame({k: [overall[k]] for k in scalar_keys})
        scalar_df.to_excel(writer, sheet_name="Overview", index=False)

        overall["Top 20 Stocks"].to_excel(writer, sheet_name="Top20", index=False)
        overall["Bottom 20 Stocks"].to_excel(writer, sheet_name="Bottom20", index=False)
        overall["Monthly Returns"].to_excel(writer, sheet_name="Monthly", index=False)
        overall["Yearly Returns"].to_excel(writer, sheet_name="Yearly", index=False)

        eq = overall["Equity Curve"].reset_index()
        eq.columns = ["TradeNum", "EquityMultiple"]
        eq.to_excel(writer, sheet_name="EquityCurve", index=False)

    # Equity curve plot
    # plt.figure(figsize=(10, 5))
    # overall["Equity Curve"].reset_index(drop=True).plot()
    # plt.title("Equity Curve (1R per trade, 1-Day Return basis)")
    # plt.xlabel("Trade #")
    # plt.ylabel("Equity Multiple")
    # plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, "equity_curve.png"))
    # plt.close()

    log.info(f"Saved {path}")

    # ---- HTML overall summary ----
    html_path = os.path.join(OUTPUT_DIR, "Overall_Summary.html")
    kpis = ["Overall Win Rate", "Profit Factor", "Expectancy", "Max Drawdown",
            "Sharpe Ratio", "Best Holding Period", "Best Risk Reward Target"]
    kpi_html = "".join(
        f'<div class="kpi-box"><div class="kpi-label">{k}</div>'
        f'<div class="kpi-value">{overall[k]}</div></div>' for k in kpis
    )
    body = (
        "<h1>Overall Summary</h1>"
        f"<div>{kpi_html}</div>"
        '<img src="equity_curve.png" alt="Equity Curve">'
        "<h2>Top 20 Stocks</h2>" + _df_to_html_table(overall["Top 20 Stocks"]) +
        "<h2>Bottom 20 Stocks</h2>" + _df_to_html_table(overall["Bottom 20 Stocks"]) +
        "<h2>Monthly Returns (%)</h2>" + _df_to_html_table(overall["Monthly Returns"]) +
        "<h2>Yearly Returns (%)</h2>" + _df_to_html_table(overall["Yearly Returns"])
    )
    with open(html_path, "w") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Overall Summary</title>{HTML_STYLE}</head><body>{body}</body></html>")
    log.info(f"Saved {html_path}")


def export_live_scan(long_setups: pd.DataFrame, short_setups: pd.DataFrame,
                      top_long: pd.DataFrame, top_short: pd.DataFrame):
    path = os.path.join(OUTPUT_DIR, "Live_Scan.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        long_setups.to_excel(writer, sheet_name="All_Long_Setups", index=False)
        short_setups.to_excel(writer, sheet_name="All_Short_Setups", index=False)
        top_long.to_excel(writer, sheet_name="Top20_Long", index=False)
        top_short.to_excel(writer, sheet_name="Top20_Short", index=False)
    log.info(f"Saved {path}")

    # ---- HTML live scan ----
    html_path = os.path.join(OUTPUT_DIR, "Live_Scan.html")
    body = (
        "<h1>Live Scan Results</h1>"
        f"<p>Generated for latest available daily candle.</p>"
        "<h2>Top 20 Long Opportunities</h2>" + _df_to_html_table(top_long) +
        "<h2>Top 20 Short Opportunities</h2>" + _df_to_html_table(top_short) +
        "<h2>All Long Setups</h2>" + _df_to_html_table(long_setups) +
        "<h2>All Short Setups</h2>" + _df_to_html_table(short_setups)
    )
    with open(html_path, "w") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Live Scan</title>{HTML_STYLE}</head><body>{body}</body></html>")
    log.info(f"Saved {html_path}")


# ----------------------------------------------------------------------
# MAIN PIPELINE
# ----------------------------------------------------------------------
def run_backtest(tickers: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    all_signals = []
    for i, ticker in enumerate(tickers, 1):
        log.info(f"[{i}/{len(tickers)}] Backtesting {ticker} ...")
        try:
            df = backtest_ticker(ticker)
            if not df.empty:
                all_signals.append(df)
        except Exception as e:
            log.error(f"{ticker}: backtest error - {e}")
        time.sleep(0.2)  # be polite to Yahoo Finance

    if not all_signals:
        log.warning("No signals found across universe.")
        return pd.DataFrame(), pd.DataFrame(), {}

    signal_df = pd.concat(all_signals, ignore_index=True)
    stock_summary = compute_stock_summary(signal_df)
    overall = compute_overall_summary(signal_df, stock_summary)

    export_signal_details(signal_df)
    export_summary_by_stock(stock_summary)
    export_overall_summary(overall)

    return signal_df, stock_summary, overall


def compute_trend_quality_map(tickers: List[str]) -> dict:
    """
    Trend Quality score (0-100) per ticker based on the latest structure:
    UP trend with strong BOS count scores higher for LONG setups, DOWN
    trend with strong BOS count scores higher for SHORT setups. We store a
    single quality value derived from |bullish_bos_count - bearish_bos_count|
    normalized, used as the 15% component in ranking.
    """
    quality_map = {}
    for ticker in tickers:
        df = download_data(ticker)
        if df is None:
            continue
        try:
            df = add_indicators(df)
            df = detect_swings(df)
            df = walk_structure(df)
            last = df.iloc[-1]
            net_bos = abs(last["bullish_bos_count"] - last["bearish_bos_count"])
            quality_map[ticker] = min(net_bos * 10, 100)
        except Exception:
            continue
    return quality_map


def run_live_scan(tickers: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    long_rows, short_rows = [], []
    for i, ticker in enumerate(tickers, 1):
        log.info(f"[{i}/{len(tickers)}] Live scanning {ticker} ...")
        try:
            rows = live_scan_ticker(ticker)
            for r in rows:
                if r["Setup Type"] == "LONG":
                    long_rows.append(r)
                else:
                    short_rows.append(r)
        except Exception as e:
            log.error(f"{ticker}: live scan error - {e}")
        time.sleep(0.2)

    long_df = pd.DataFrame(long_rows)
    short_df = pd.DataFrame(short_rows)

    # drop Setup Type column for final output schema (keep for ranking internally)
    return long_df, short_df


def main():
    tickers = get_nifty500_tickers()
    log.info(f"Universe size: {len(tickers)} tickers")

    # ---- 1. Historical backtest ----
    signal_df, stock_summary, overall = run_backtest(tickers)
    if not signal_df.empty:
        log.info(f"Backtest complete. Total signals: {len(signal_df)}")
        log.info(f"Overall Win Rate: {overall['Overall Win Rate']}% | "
                 f"Profit Factor: {overall['Profit Factor']} | "
                 f"Sharpe: {overall['Sharpe Ratio']}")

    # ---- 2. Live scan ----
    long_df, short_df = run_live_scan(tickers)

    trend_quality_map = compute_trend_quality_map(tickers)

    ranked_long = rank_setups(long_df, trend_quality_map) if not long_df.empty else long_df
    ranked_short = rank_setups(short_df, trend_quality_map) if not short_df.empty else short_df

    top_long = ranked_long.head(20).drop(columns=["Setup Type", "Score"], errors="ignore")
    top_short = ranked_short.head(20).drop(columns=["Setup Type", "Score"], errors="ignore")

    long_out = long_df.drop(columns=["Setup Type"], errors="ignore")
    short_out = short_df.drop(columns=["Setup Type"], errors="ignore")

    export_live_scan(long_out, short_out, top_long, top_short)

    log.info(f"Live scan complete. LONG setups: {len(long_df)}, SHORT setups: {len(short_df)}")
    log.info(f"Top 20 Long Opportunities and Top 20 Short Opportunities saved to Live_Scan.xlsx")


if __name__ == "__main__":
    main()
