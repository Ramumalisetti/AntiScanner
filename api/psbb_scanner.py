"""
PSBB — Priyank Sharma "Bread & Butter" Scanner
SEBI Registered RA | HOLD with Priyank Methodology

STRATEGY (Swing / Daily Timeframe):
==============================================
1. MARKET STRUCTURE BIAS (SMC)
   - Higher Highs / Higher Lows  → BULLISH BIAS
   - Lower Highs / Lower Lows    → BEARISH BIAS
   - BOS (Break of Structure)    → Trend confirmation

2. ENTRY ZONE CONFLUENCE (must have ≥2)
   - Fair Value Gap (FVG): 3-candle imbalance gap
   - Bullish/Bearish Order Block (OB): Last bearish candle before bullish impulse
   - 21 EMA: Price touching or retesting the 21 EMA
   - Demand/Supply zone from swing points

3. RSI DIVERGENCE (Bread & Butter signal trigger)
   - Bullish: Price making Lower Low, RSI making Higher Low → entry long
   - Bearish: Price making Higher High, RSI making Lower High → entry short

4. ENTRY + STOP LOSS + TARGETS
   - Entry: Close of the divergence candle / FVG fill zone
   - Stop: Below the OB / swing low (with buffer)
   - Target 1: 1:2 RR (minimum acceptable)
   - Target 2: 1:3 RR (Priyank's preferred)
   - Target 3: Fibonacci 1.618 extension

5. FILTERS (required for trade signal)
   - Price above/below 21 EMA (in direction of trade)
   - Volume above 20-day average
   - RR ≥ 1:2

Returns dict with keys: trade, score, desc, thesis, vol_ratio
"""

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────

def _ema(closes, period):
    k = 2 / (period + 1)
    e = float(closes[0])
    for v in closes[1:]:
        e = v * k + e * (1 - k)
    return e


def _rsi(closes, period=14):
    if len(closes) < period + 2:
        return 50.0
    d = np.diff(closes[-(period * 2):])
    g = np.where(d > 0, d, 0.0)
    lo = np.where(d < 0, -d, 0.0)
    ag, al = g[-period:].mean(), lo[-period:].mean()
    if al == 0:
        return 100.0
    return round(100 - 100 / (1 + ag / al), 1)


def _atr(high, low, close, period=14):
    trs = [
        max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        for i in range(1, len(close))
    ]
    return float(np.mean(trs[-period:])) if trs else close[-1] * 0.018


def _swing_highs(highs, lookback=5):
    """Find swing high indices (local max within lookback)."""
    result = []
    for i in range(lookback, len(highs) - lookback):
        if highs[i] == max(highs[i - lookback: i + lookback + 1]):
            result.append(i)
    return result


def _swing_lows(lows, lookback=5):
    """Find swing low indices (local min within lookback)."""
    result = []
    for i in range(lookback, len(lows) - lookback):
        if lows[i] == min(lows[i - lookback: i + lookback + 1]):
            result.append(i)
    return result


# ─────────────────────────────────────────────────────────────
# STEP 1 — MARKET STRUCTURE BIAS
# ─────────────────────────────────────────────────────────────

def market_structure(high, low, close):
    """
    Returns 'BULL', 'BEAR', or 'RANGING'.
    Uses last 3 swing HH/HL or LH/LL.
    """
    sh = _swing_highs(high, lookback=5)
    sl = _swing_lows(low, lookback=5)

    # Need at least 2 swing highs and 2 swing lows
    if len(sh) < 2 or len(sl) < 2:
        return "RANGING", None, None

    # Most recent two swing highs and lows
    sh1, sh2 = sh[-2], sh[-1]   # older, newer
    sl1, sl2 = sl[-2], sl[-1]   # older, newer

    hh = high[sh2] > high[sh1]   # Higher High
    hl = low[sl2] > low[sl1]     # Higher Low
    ll = low[sl2] < low[sl1]     # Lower Low
    lh = high[sh2] < high[sh1]   # Lower High

    # BOS detection: last close broke above swing high (bull BOS) or below swing low (bear BOS)
    last_close = close[-1]
    bull_bos = last_close > high[sh1]
    bear_bos = last_close < low[sl1]

    if (hh and hl) or bull_bos:
        return "BULL", high[sh2], low[sl2]
    elif (ll and lh) or bear_bos:
        return "BEAR", high[sh2], low[sl2]
    else:
        return "RANGING", high[sh2], low[sl2]


# ─────────────────────────────────────────────────────────────
# STEP 2 — FAIR VALUE GAP DETECTION
# ─────────────────────────────────────────────────────────────

def find_fvg(high, low, close, lookback=20):
    """
    A Bullish FVG exists where:
      candle[i-2].high < candle[i].low   (3-candle gap leaving imbalance)
    A Bearish FVG exists where:
      candle[i-2].low > candle[i].high
    Check if the current price is inside a recent FVG.
    """
    n = len(close)
    start = max(0, n - lookback)

    bullish_fvgs = []
    bearish_fvgs = []

    for i in range(start + 2, n):
        # Bullish FVG
        if high[i - 2] < low[i]:
            bullish_fvgs.append({
                "low":  high[i - 2],
                "high": low[i],
                "mid":  (high[i - 2] + low[i]) / 2,
                "idx":  i
            })
        # Bearish FVG
        if low[i - 2] > high[i]:
            bearish_fvgs.append({
                "low":  high[i],
                "high": low[i - 2],
                "mid":  (high[i] + low[i - 2]) / 2,
                "idx":  i
            })

    # Is current price inside a bullish FVG (potential support / demand)?
    price = close[-1]
    bull_fvg_active = None
    bear_fvg_active = None

    for fvg in reversed(bullish_fvgs):
        if fvg["low"] <= price <= fvg["high"]:
            bull_fvg_active = fvg
            break

    for fvg in reversed(bearish_fvgs):
        if fvg["low"] <= price <= fvg["high"]:
            bear_fvg_active = fvg
            break

    return bull_fvg_active, bear_fvg_active


# ─────────────────────────────────────────────────────────────
# STEP 3 — ORDER BLOCK DETECTION
# ─────────────────────────────────────────────────────────────

def find_order_block(open_, high, low, close, lookback=30):
    """
    Bullish OB: Last BEARISH candle before a STRONG BULLISH impulse
    Bearish OB: Last BULLISH candle before a STRONG BEARISH impulse

    Current price must be retesting the OB zone.
    """
    n = len(close)
    price = close[-1]

    bull_ob = None
    bear_ob = None

    start = max(1, n - lookback)

    for i in range(start, n - 2):
        body = abs(close[i] - open_[i])
        if body == 0:
            continue

        # Bullish OB: bearish candle followed by 2+ bullish candles moving up strongly
        if close[i] < open_[i]:  # bearish candle
            next_move = close[min(i + 2, n - 1)] - high[i]
            if next_move > body * 1.0:  # strong move up after
                ob_zone_low = low[i]
                ob_zone_high = high[i]
                # Is current price retesting this OB?
                if ob_zone_low <= price <= ob_zone_high * 1.01:
                    bull_ob = {
                        "low": round(ob_zone_low, 2),
                        "high": round(ob_zone_high, 2),
                        "idx": i
                    }

        # Bearish OB: bullish candle followed by 2+ bearish candles moving down strongly
        if close[i] > open_[i]:  # bullish candle
            next_move = low[i] - close[min(i + 2, n - 1)]
            if next_move > body * 1.0:
                ob_zone_low = low[i]
                ob_zone_high = high[i]
                if ob_zone_low * 0.99 <= price <= ob_zone_high:
                    bear_ob = {
                        "low": round(ob_zone_low, 2),
                        "high": round(ob_zone_high, 2),
                        "idx": i
                    }

    return bull_ob, bear_ob


# ─────────────────────────────────────────────────────────────
# STEP 4 — RSI DIVERGENCE (Bread & Butter Core Signal)
# ─────────────────────────────────────────────────────────────

def rsi_divergence(high, low, close, lookback=30):
    """
    Bullish Divergence: Price making Lower Low, RSI making Higher Low
    Bearish Divergence: Price making Higher High, RSI making Lower High

    Returns: 'BULL_DIV', 'BEAR_DIV', or None
    """
    n = len(close)
    if n < lookback + 14:
        return None

    # Compute RSI for each candle in lookback window
    rsi_vals = []
    for i in range(n - lookback, n):
        rsi_vals.append(_rsi(close[:i + 1], 14))

    prices_h = high[n - lookback:]
    prices_l = low[n - lookback:]

    # Find two recent pivot lows in price and RSI for bullish divergence
    # Look at last 3 swing lows
    sl_indices = []
    for i in range(2, len(prices_l) - 2):
        if prices_l[i] < prices_l[i - 1] and prices_l[i] < prices_l[i + 1] and \
           prices_l[i] < prices_l[i - 2] and prices_l[i] < prices_l[i + 2]:
            sl_indices.append(i)

    if len(sl_indices) >= 2:
        i1, i2 = sl_indices[-2], sl_indices[-1]
        price_lower_low = prices_l[i2] < prices_l[i1]
        rsi_higher_low = rsi_vals[i2] > rsi_vals[i1]
        if price_lower_low and rsi_higher_low:
            return "BULL_DIV"

    # Bearish divergence: two swing highs
    sh_indices = []
    for i in range(2, len(prices_h) - 2):
        if prices_h[i] > prices_h[i - 1] and prices_h[i] > prices_h[i + 1] and \
           prices_h[i] > prices_h[i - 2] and prices_h[i] > prices_h[i + 2]:
            sh_indices.append(i)

    if len(sh_indices) >= 2:
        i1, i2 = sh_indices[-2], sh_indices[-1]
        price_higher_high = prices_h[i2] > prices_h[i1]
        rsi_lower_high = rsi_vals[i2] < rsi_vals[i1]
        if price_higher_high and rsi_lower_high:
            return "BEAR_DIV"

    return None


# ─────────────────────────────────────────────────────────────
# MAIN PSBB ANALYZE FUNCTION
# ─────────────────────────────────────────────────────────────

def psbb_analyze(df: pd.DataFrame, stock: dict) -> dict:
    """
    Priyank Sharma PSBB Bread & Butter Scanner.
    Requires df with lowercase columns: open, high, low, close, volume
    Returns dict with trade info or None if no setup.
    """
    if df is None or len(df) < 60:
        return None

    o = df["open"].values
    h = df["high"].values
    lo = df["low"].values
    c = df["close"].values
    v = df["volume"].values
    n = len(c)

    price = float(c[-1])

    # ── INDICATORS ──
    atr_val = _atr(h, lo, c, 14)
    ema21   = _ema(c[-40:], 21)
    vol_avg = float(np.mean(v[-20:]))
    vol_ratio = float(v[-1]) / vol_avg if vol_avg > 0 else 1.0
    rsi_now = _rsi(c, 14)

    # ── 1. MARKET STRUCTURE ──
    bias, swing_h, swing_l = market_structure(h, lo, c)
    if bias == "RANGING":
        return None  # No trade in ranging markets

    # ── 2. FVG ──
    bull_fvg, bear_fvg = find_fvg(h, lo, c, lookback=20)

    # ── 3. ORDER BLOCK ──
    bull_ob, bear_ob = find_order_block(o, h, lo, c, lookback=30)

    # ── 4. RSI DIVERGENCE ──
    div_signal = rsi_divergence(h, lo, c, lookback=25)

    # ── 21 EMA PROXIMITY (within 1% is considered a "retest") ──
    ema_retest = abs(price - ema21) / ema21 < 0.015

    # ─────────────────────────────────────────────────────────
    # LONG SETUP
    # Bias=BULL + (FVG or OB confluence) + RSI Bull Div + EMA filter
    # ─────────────────────────────────────────────────────────
    if bias == "BULL":
        confluence_count = 0
        confluence_factors = []

        if bull_fvg:
            confluence_count += 1
            confluence_factors.append("FVG ✓")
        if bull_ob:
            confluence_count += 1
            confluence_factors.append("Order Block ✓")
        if ema_retest:
            confluence_count += 1
            confluence_factors.append("21 EMA Retest ✓")
        if div_signal == "BULL_DIV":
            confluence_count += 2  # divergence is the bread & butter trigger
            confluence_factors.append("RSI Bull Divergence ✓✓")
        if rsi_now < 45:
            confluence_count += 1
            confluence_factors.append("RSI Oversold ✓")

        if confluence_count < 2:
            return None

        # Price must be above 21 EMA for long (trend filter)
        if price < ema21 * 0.97:
            return None

        # Entry and stops
        entry = round(price, 2)
        if bull_ob:
            stop = round(bull_ob["low"] * 0.99, 2)
        elif bull_fvg:
            stop = round(bull_fvg["low"] * 0.99, 2)
        elif swing_l is not None:
            stop = round(float(swing_l) * 0.99, 2)
        else:
            stop = round(entry - 2 * atr_val, 2)

        risk = entry - stop
        if risk <= 0 or risk / entry > 0.12:  # reject if risk > 12%
            return None

        t1 = round(entry + risk * 2, 2)   # 1:2 RR
        t2 = round(entry + risk * 3, 2)   # 1:3 RR
        t3 = round(entry + risk * 4, 2)   # Stretch target

        score = min(100, confluence_count * 18 + (10 if vol_ratio > 1.2 else 0))

        return {
            "trade": "BUY",
            "score": score,
            "desc": f"PSBB LONG — {', '.join(confluence_factors)}",
            "thesis": (
                f"Bullish market structure (BOS/HH-HL) | Entry: ₹{entry} | "
                f"SL: ₹{stop} (Risk: {round(risk/entry*100,1)}%) | "
                f"T1: ₹{t1} | T2: ₹{t2} | RR 1:{round(risk, 0) and round((t2-entry)/risk,1)} | "
                f"21 EMA: ₹{round(ema21,2)} | RSI: {rsi_now}"
            ),
            "vol_ratio": round(vol_ratio, 2),
            "entry": entry,
            "stop_loss": stop,
            "t1": t1, "t2": t2, "t3": t3,
            "rsi": rsi_now,
            "ema21": round(ema21, 2),
            "confluence": confluence_count,
            "confluence_factors": confluence_factors,
            "setup_direction": "LONG"
        }

    # ─────────────────────────────────────────────────────────
    # SHORT SETUP
    # Bias=BEAR + (FVG or OB confluence) + RSI Bear Div
    # ─────────────────────────────────────────────────────────
    if bias == "BEAR":
        confluence_count = 0
        confluence_factors = []

        if bear_fvg:
            confluence_count += 1
            confluence_factors.append("Bearish FVG ✓")
        if bear_ob:
            confluence_count += 1
            confluence_factors.append("Bearish OB ✓")
        if ema_retest:
            confluence_count += 1
            confluence_factors.append("21 EMA Resistance ✓")
        if div_signal == "BEAR_DIV":
            confluence_count += 2
            confluence_factors.append("RSI Bear Divergence ✓✓")
        if rsi_now > 55:
            confluence_count += 1
            confluence_factors.append("RSI Overbought ✓")

        if confluence_count < 2:
            return None

        # Price must be below 21 EMA for short
        if price > ema21 * 1.03:
            return None

        entry = round(price, 2)
        if bear_ob:
            stop = round(bear_ob["high"] * 1.01, 2)
        elif bear_fvg:
            stop = round(bear_fvg["high"] * 1.01, 2)
        elif swing_h is not None:
            stop = round(float(swing_h) * 1.01, 2)
        else:
            stop = round(entry + 2 * atr_val, 2)

        risk = stop - entry
        if risk <= 0 or risk / entry > 0.12:
            return None

        t1 = round(entry - risk * 2, 2)
        t2 = round(entry - risk * 3, 2)
        t3 = round(entry - risk * 4, 2)

        score = min(100, confluence_count * 18 + (10 if vol_ratio > 1.2 else 0))

        return {
            "trade": "SELL",
            "score": score,
            "desc": f"PSBB SHORT — {', '.join(confluence_factors)}",
            "thesis": (
                f"Bearish market structure (BOS/LH-LL) | Entry: ₹{entry} | "
                f"SL: ₹{stop} (Risk: {round(risk/entry*100,1)}%) | "
                f"T1: ₹{t1} | T2: ₹{t2} | RR 1:{round((entry-t2)/risk,1)} | "
                f"21 EMA: ₹{round(ema21,2)} | RSI: {rsi_now}"
            ),
            "vol_ratio": round(vol_ratio, 2),
            "entry": entry,
            "stop_loss": stop,
            "t1": t1, "t2": t2, "t3": t3,
            "rsi": rsi_now,
            "ema21": round(ema21, 2),
            "confluence": confluence_count,
            "confluence_factors": confluence_factors,
            "setup_direction": "SHORT"
        }

    return None
