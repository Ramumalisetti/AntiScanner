"""
PSBB — Priyank Sharma "Bread & Butter" Scanner (Refined v2)
SEBI Registered RA | HOLD with Priyank Methodology

STRATEGY (Swing / Daily Timeframe):
==============================================
1. MARKET STRUCTURE BIAS (SMC)
   - Higher Highs / Higher Lows  → BULLISH BIAS
   - Lower Highs / Lower Lows    → BEARISH BIAS

2. ENTRY ZONE CONFLUENCE (signal on ≥1, strong on ≥2)
   - Fair Value Gap (FVG)
   - Bullish/Bearish Order Block (OB)
   - 21 EMA retest
   - RSI Divergence (Bread & Butter core trigger)
   - RSI Oversold/Overbought

3. ENTRY + STOP LOSS + TARGETS
   - Entry: current close
   - SL: below OB / FVG / swing low
   - T1: 1:2 RR, T2: 1:3 RR

Returns dict or None.
"""

import numpy as np
import pandas as pd


def _ema(closes, period):
    if len(closes) < period:
        return float(closes[-1])
    k = 2 / (period + 1)
    e = float(closes[0])
    for v in closes[1:]:
        e = v * k + e * (1 - k)
    return e


def _rsi(closes, period=14):
    if len(closes) < period + 2:
        return 50.0
    arr = closes[-(period * 2 + 1):]
    d = np.diff(arr)
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
    result = []
    for i in range(lookback, len(highs) - lookback):
        if highs[i] == max(highs[i - lookback: i + lookback + 1]):
            result.append(i)
    return result


def _swing_lows(lows, lookback=5):
    result = []
    for i in range(lookback, len(lows) - lookback):
        if lows[i] == min(lows[i - lookback: i + lookback + 1]):
            result.append(i)
    return result


def market_structure(high, low, close):
    sh = _swing_highs(high, lookback=5)
    sl = _swing_lows(low, lookback=5)

    if len(sh) < 2 or len(sl) < 2:
        # Fallback: use EMA slope
        ema50 = _ema(close[-60:], 50)
        ema21 = _ema(close[-40:], 21)
        if close[-1] > ema50 and ema21 > ema50:
            return "BULL", high[-1], low[-1]
        elif close[-1] < ema50:
            return "BEAR", high[-1], low[-1]
        return "RANGING", None, None

    sh1, sh2 = sh[-2], sh[-1]
    sl1, sl2 = sl[-2], sl[-1]

    hh = high[sh2] > high[sh1]
    hl = low[sl2] > low[sl1]
    ll = low[sl2] < low[sl1]
    lh = high[sh2] < high[sh1]

    last_close = close[-1]
    bull_bos = last_close > high[sh1]
    bear_bos = last_close < low[sl1]

    if (hh and hl) or bull_bos:
        return "BULL", high[sh2], low[sl2]
    elif (ll and lh) or bear_bos:
        return "BEAR", high[sh2], low[sl2]
    else:
        # Use EMA slope as tiebreaker
        ema21 = _ema(close[-40:], 21)
        ema50 = _ema(close[-60:], 50)
        if close[-1] > ema21 > ema50:
            return "BULL", high[sh2], low[sl2]
        elif close[-1] < ema21 < ema50:
            return "BEAR", high[sh2], low[sl2]
        return "RANGING", high[sh2], low[sl2]


def find_fvg(high, low, close, lookback=30):
    n = len(close)
    start = max(0, n - lookback)
    price = close[-1]

    bull_fvg_active = None
    bear_fvg_active = None

    for i in range(start + 2, n):
        # Bullish FVG: gap up — candle[i-2].high < candle[i].low
        if high[i - 2] < low[i]:
            fvg = {"low": high[i - 2], "high": low[i], "mid": (high[i - 2] + low[i]) / 2}
            # Price is at or below the FVG (trading into it for long)
            if price <= fvg["high"] * 1.02:
                bull_fvg_active = fvg

        # Bearish FVG: gap down — candle[i-2].low > candle[i].high
        if low[i - 2] > high[i]:
            fvg = {"low": high[i], "high": low[i - 2], "mid": (high[i] + low[i - 2]) / 2}
            # Price is at or above the FVG (trading into it for short)
            if price >= fvg["low"] * 0.98:
                bear_fvg_active = fvg

    return bull_fvg_active, bear_fvg_active


def find_order_block(open_, high, low, close, lookback=40):
    n = len(close)
    price = close[-1]

    bull_ob = None
    bear_ob = None

    start = max(1, n - lookback)

    for i in range(start, n - 2):
        body = abs(close[i] - open_[i])
        if body == 0:
            continue

        # Bullish OB: last bearish candle before a strong bullish impulse
        if close[i] < open_[i]:
            next_move = close[min(i + 2, n - 1)] - open_[i]
            if next_move > body * 0.5:  # relaxed from 1.0
                if low[i] * 0.98 <= price <= high[i] * 1.02:
                    bull_ob = {"low": round(low[i], 2), "high": round(high[i], 2), "idx": i}

        # Bearish OB: last bullish candle before a strong bearish impulse
        if close[i] > open_[i]:
            next_move = open_[i] - close[min(i + 2, n - 1)]
            if next_move > body * 0.5:
                if low[i] * 0.98 <= price <= high[i] * 1.02:
                    bear_ob = {"low": round(low[i], 2), "high": round(high[i], 2), "idx": i}

    return bull_ob, bear_ob


def rsi_divergence(high, low, close, lookback=40):
    n = len(close)
    if n < lookback + 14:
        return None

    rsi_vals = []
    for i in range(n - lookback, n):
        rsi_vals.append(_rsi(close[:i + 1], 14))

    prices_h = high[n - lookback:]
    prices_l = low[n - lookback:]

    # Bullish divergence
    sl_indices = []
    for i in range(2, len(prices_l) - 1):
        if prices_l[i] < prices_l[i - 1] and prices_l[i] <= prices_l[i + 1]:
            sl_indices.append(i)

    if len(sl_indices) >= 2:
        i1, i2 = sl_indices[-2], sl_indices[-1]
        if prices_l[i2] < prices_l[i1] and rsi_vals[i2] > rsi_vals[i1]:
            return "BULL_DIV"

    # Bearish divergence
    sh_indices = []
    for i in range(2, len(prices_h) - 1):
        if prices_h[i] > prices_h[i - 1] and prices_h[i] >= prices_h[i + 1]:
            sh_indices.append(i)

    if len(sh_indices) >= 2:
        i1, i2 = sh_indices[-2], sh_indices[-1]
        if prices_h[i2] > prices_h[i1] and rsi_vals[i2] < rsi_vals[i1]:
            return "BEAR_DIV"

    return None


def psbb_analyze(df: pd.DataFrame, stock: dict) -> dict:
    """
    Priyank Sharma PSBB Bread & Butter Scanner (Refined).
    Requires df with lowercase columns: open, high, low, close, volume
    Returns dict with trade info or None if no setup.
    """
    if df is None or len(df) < 50:
        return None

    o = df["open"].values
    h = df["high"].values
    lo = df["low"].values
    c = df["close"].values
    v = df["volume"].values

    price = float(c[-1])

    atr_val = _atr(h, lo, c, 14)
    ema21 = _ema(c[-50:], 21)
    ema50 = _ema(c[-70:], 50)
    vol_avg = float(np.mean(v[-20:]))
    vol_ratio = float(v[-1]) / vol_avg if vol_avg > 0 else 1.0
    rsi_now = _rsi(c, 14)

    # ── 1. MARKET STRUCTURE ──
    bias, swing_h, swing_l = market_structure(h, lo, c)
    if bias == "RANGING":
        return None

    # ── 2. FVG ──
    bull_fvg, bear_fvg = find_fvg(h, lo, c, lookback=30)

    # ── 3. ORDER BLOCK ──
    bull_ob, bear_ob = find_order_block(o, h, lo, c, lookback=40)

    # ── 4. RSI DIVERGENCE ──
    div_signal = rsi_divergence(h, lo, c, lookback=40)

    # ── 5. 21 EMA PROXIMITY ──
    ema_retest = abs(price - ema21) / ema21 < 0.025  # within 2.5%

    # ─────────────────────────────────────────────────────────
    # LONG SETUP
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
            confluence_count += 2
            confluence_factors.append("RSI Bull Divergence ✓✓")
        if rsi_now < 50:
            confluence_count += 1
            confluence_factors.append("RSI Pullback ✓")
        if vol_ratio > 1.3:
            confluence_count += 1
            confluence_factors.append(f"Vol Surge {vol_ratio:.1f}x ✓")

        if confluence_count < 1:
            return None

        # Relaxed EMA filter
        if price < ema50 * 0.95:
            return None

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
        if risk <= 0 or risk / entry > 0.15:
            return None

        t1 = round(entry + risk * 2, 2)
        t2 = round(entry + risk * 3, 2)
        t3 = round(entry + risk * 4.618, 2)

        score = min(100, confluence_count * 15 + (10 if vol_ratio > 1.5 else 0) + (5 if rsi_now < 40 else 0))

        return {
            "trade": "BUY",
            "score": score,
            "desc": f"PSBB LONG — {', '.join(confluence_factors)}",
            "thesis": (
                f"Bullish structure (HH-HL) | Entry: ₹{entry} | "
                f"SL: ₹{stop} ({round(risk/entry*100,1)}% risk) | "
                f"T1: ₹{t1} | T2: ₹{t2} | 21 EMA: ₹{round(ema21,2)} | RSI: {rsi_now}"
            ),
            "vol_ratio": round(vol_ratio, 2),
            "entry": entry,
            "stop_loss": stop,
            "sl": stop,
            "t1": t1, "t2": t2, "t3": t3,
            "rsi": rsi_now,
            "ema21": round(ema21, 2),
            "w52h": None,
            "confluence": confluence_count,
            "confluence_factors": confluence_factors,
            "setup_direction": "LONG",
            "signals": [{"sig": f, "desc": "SMC Confluence", "type": "BULL"} for f in confluence_factors]
        }

    # ─────────────────────────────────────────────────────────
    # SHORT SETUP
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
        if rsi_now > 50:
            confluence_count += 1
            confluence_factors.append("RSI Extended ✓")
        if vol_ratio > 1.3:
            confluence_count += 1
            confluence_factors.append(f"Vol Surge {vol_ratio:.1f}x ✓")

        if confluence_count < 1:
            return None

        if price > ema50 * 1.05:
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
        if risk <= 0 or risk / entry > 0.15:
            return None

        t1 = round(entry - risk * 2, 2)
        t2 = round(entry - risk * 3, 2)
        t3 = round(entry - risk * 4.618, 2)

        score = min(100, confluence_count * 15 + (10 if vol_ratio > 1.5 else 0) + (5 if rsi_now > 60 else 0))

        return {
            "trade": "SELL",
            "score": score,
            "desc": f"PSBB SHORT — {', '.join(confluence_factors)}",
            "thesis": (
                f"Bearish structure (LH-LL) | Entry: ₹{entry} | "
                f"SL: ₹{stop} ({round(risk/entry*100,1)}% risk) | "
                f"T1: ₹{t1} | T2: ₹{t2} | 21 EMA: ₹{round(ema21,2)} | RSI: {rsi_now}"
            ),
            "vol_ratio": round(vol_ratio, 2),
            "entry": entry,
            "stop_loss": stop,
            "sl": stop,
            "t1": t1, "t2": t2, "t3": t3,
            "rsi": rsi_now,
            "ema21": round(ema21, 2),
            "w52h": None,
            "confluence": confluence_count,
            "confluence_factors": confluence_factors,
            "setup_direction": "SHORT",
            "signals": [{"sig": f, "desc": "SMC Confluence", "type": "BEAR"} for f in confluence_factors]
        }

    return None
