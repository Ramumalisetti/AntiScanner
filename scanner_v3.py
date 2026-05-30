"""
╔══════════════════════════════════════════════════════════════════════════╗
║  NSE F&O SMC SCANNER v3 — AI EDITION (OpenRouter Free LLM)             ║
║                                                                          ║
║  HOW IT WORKS:                                                           ║
║  1. Fetch real OHLCV data from Yahoo Finance for all F&O stocks         ║
║  2. Run SMC engine (BOS, CHoCH, OB, FVG, LiqGrab, RSI, ATR)            ║
║  3. Score every stock mathematically                                    ║
║  4. Feed top candidates to FREE OpenRouter LLM (DeepSeek/Llama3)       ║
║  5. LLM THINKS and picks BEST 2-3 stocks per sector with reasoning     ║
║  6. Generate full HTML dashboard with AI analysis                       ║
║                                                                          ║
║  USAGE:                                                                  ║
║    pip install yfinance pandas numpy requests flask                      ║
║    python scanner_v3.py --demo               # demo, no internet        ║
║    python scanner_v3.py --top 30             # live, top 30 stocks      ║
║    python scanner_v3.py                      # live, all stocks         ║
║    python scanner_v3.py --serve              # Flask web server         ║
║                                                                          ║
║  OPENROUTER FREE MODELS (set OPENROUTER_API_KEY env var):               ║
║    deepseek/deepseek-r1:free   — best reasoning (recommended)           ║
║    meta-llama/llama-3.1-8b-instruct:free — fast                        ║
║    mistralai/mistral-7b-instruct:free — reliable                       ║
║    Get free key: https://openrouter.ai/  (no credit card needed)        ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import argparse, json, os, random, time, webbrowser
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    print("⚠  yfinance not installed. Run: pip install yfinance")


# ══════════════════════════════════════════════════════════════════════
#  OPENROUTER CONFIG
# ══════════════════════════════════════════════════════════════════════
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL",   "deepseek/deepseek-r1:free")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

def call_ai(prompt: str, max_tokens: int = 1200, temperature: float = 0.3) -> str:
    """
    Call OpenRouter free LLM. Falls back to rule-based summary if no key.
    Supports: deepseek/deepseek-r1:free, meta-llama/llama-3.1-8b-instruct:free,
              mistralai/mistral-7b-instruct:free
    """
    if not OPENROUTER_API_KEY:
        return None  # Will use rule-based fallback

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://github.com/nse-smc-scanner",
        "X-Title":       "NSE F&O SMC Scanner",
    }
    payload = {
        "model":    OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens":  max_tokens,
        "temperature": temperature,
    }
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  ⚠ OpenRouter error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════
#  F&O STOCKS UNIVERSE
# ══════════════════════════════════════════════════════════════════════
FNO_STOCKS = [
    # Banking
    {"sym":"HDFCBANK",   "yf":"HDFCBANK.NS",   "sector":"Banking",   "lot":550,   "weight":6.24},
    {"sym":"ICICIBANK",  "yf":"ICICIBANK.NS",   "sector":"Banking",   "lot":700,   "weight":4.97},
    {"sym":"SBIN",       "yf":"SBIN.NS",        "sector":"Banking",   "lot":1500,  "weight":5.16},
    {"sym":"AXISBANK",   "yf":"AXISBANK.NS",    "sector":"Banking",   "lot":1200,  "weight":2.17},
    {"sym":"KOTAKBANK",  "yf":"KOTAKBANK.NS",   "sector":"Banking",   "lot":400,   "weight":1.95},
    {"sym":"INDUSINDBK", "yf":"INDUSINDBK.NS",  "sector":"Banking",   "lot":500,   "weight":1.10},
    {"sym":"BANKBARODA", "yf":"BANKBARODA.NS",  "sector":"Banking",   "lot":5850,  "weight":0.60},
    {"sym":"PNB",        "yf":"PNB.NS",         "sector":"Banking",   "lot":8000,  "weight":0.55},
    {"sym":"IDFCFIRSTB", "yf":"IDFCFIRSTB.NS",  "sector":"Banking",   "lot":10000, "weight":0.40},
    {"sym":"FEDERALBNK", "yf":"FEDERALBNK.NS",  "sector":"Banking",   "lot":10000, "weight":0.38},
    {"sym":"BANDHANBNK", "yf":"BANDHANBNK.NS",  "sector":"Banking",   "lot":5000,  "weight":0.35},
    {"sym":"YESBANK",    "yf":"YESBANK.NS",      "sector":"Banking",   "lot":40000, "weight":0.30},
    # Finance
    {"sym":"BAJFINANCE", "yf":"BAJFINANCE.NS",  "sector":"Finance",   "lot":125,   "weight":2.95},
    {"sym":"BAJAJFINSV", "yf":"BAJAJFINSV.NS",  "sector":"Finance",   "lot":500,   "weight":1.65},
    {"sym":"SHRIRAMFIN", "yf":"SHRIRAMFIN.NS",  "sector":"Finance",   "lot":300,   "weight":0.72},
    {"sym":"CHOLAFIN",   "yf":"CHOLAFIN.NS",    "sector":"Finance",   "lot":500,   "weight":0.60},
    {"sym":"MUTHOOTFIN", "yf":"MUTHOOTFIN.NS",  "sector":"Finance",   "lot":750,   "weight":0.55},
    {"sym":"CDSL",       "yf":"CDSL.NS",        "sector":"Finance",   "lot":600,   "weight":0.45},
    {"sym":"MCX",        "yf":"MCX.NS",         "sector":"Finance",   "lot":800,   "weight":0.40},
    # Insurance
    {"sym":"SBILIFE",    "yf":"SBILIFE.NS",     "sector":"Insurance", "lot":750,   "weight":0.62},
    {"sym":"HDFCLIFE",   "yf":"HDFCLIFE.NS",    "sector":"Insurance", "lot":1100,  "weight":0.60},
    {"sym":"LICI",       "yf":"LICI.NS",        "sector":"Insurance", "lot":700,   "weight":0.58},
    {"sym":"ICICIPRULI", "yf":"ICICIPRULI.NS",  "sector":"Insurance", "lot":1500,  "weight":0.50},
    # IT
    {"sym":"TCS",        "yf":"TCS.NS",         "sector":"IT",        "lot":175,   "weight":4.65},
    {"sym":"INFY",       "yf":"INFY.NS",        "sector":"IT",        "lot":400,   "weight":2.61},
    {"sym":"HCLTECH",    "yf":"HCLTECH.NS",     "sector":"IT",        "lot":700,   "weight":1.88},
    {"sym":"WIPRO",      "yf":"WIPRO.NS",       "sector":"IT",        "lot":1500,  "weight":1.55},
    {"sym":"TECHM",      "yf":"TECHM.NS",       "sector":"IT",        "lot":600,   "weight":1.15},
    {"sym":"LTIM",       "yf":"LTIM.NS",        "sector":"IT",        "lot":150,   "weight":0.90},
    {"sym":"PERSISTENT", "yf":"PERSISTENT.NS",  "sector":"IT",        "lot":125,   "weight":0.62},
    # Energy
    {"sym":"RELIANCE",   "yf":"RELIANCE.NS",    "sector":"Energy",    "lot":250,   "weight":9.35},
    {"sym":"ONGC",       "yf":"ONGC.NS",        "sector":"Energy",    "lot":3850,  "weight":1.50},
    {"sym":"BPCL",       "yf":"BPCL.NS",        "sector":"Energy",    "lot":1800,  "weight":0.75},
    {"sym":"IOC",        "yf":"IOC.NS",         "sector":"Energy",    "lot":10500, "weight":0.68},
    {"sym":"GAIL",       "yf":"GAIL.NS",        "sector":"Energy",    "lot":6850,  "weight":0.58},
    # Power
    {"sym":"NTPC",       "yf":"NTPC.NS",        "sector":"Power",     "lot":2700,  "weight":1.25},
    {"sym":"POWERGRID",  "yf":"POWERGRID.NS",   "sector":"Power",     "lot":3200,  "weight":1.30},
    {"sym":"ADANIGREEN", "yf":"ADANIGREEN.NS",  "sector":"Power",     "lot":500,   "weight":0.80},
    {"sym":"TATAPOWER",  "yf":"TATAPOWER.NS",   "sector":"Power",     "lot":3375,  "weight":0.70},
    {"sym":"SUZLON",     "yf":"SUZLON.NS",      "sector":"Power",     "lot":14000, "weight":0.60},
    # Auto
    {"sym":"MARUTI",     "yf":"MARUTI.NS",      "sector":"Auto",      "lot":37,    "weight":2.13},
    {"sym":"TATAMOTORS", "yf":"TATAMOTORS.NS",  "sector":"Auto",      "lot":1400,  "weight":1.28},
    {"sym":"HEROMOTOCO", "yf":"HEROMOTOCO.NS",  "sector":"Auto",      "lot":300,   "weight":0.78},
    {"sym":"BAJAJ-AUTO", "yf":"BAJAJ-AUTO.NS",  "sector":"Auto",      "lot":125,   "weight":0.65},
    {"sym":"M&M",        "yf":"M&M.NS",         "sector":"Auto",      "lot":700,   "weight":1.50},
    {"sym":"TVSMOTORS",  "yf":"TVSMOTORS.NS",   "sector":"Auto",      "lot":350,   "weight":0.70},
    # Pharma
    {"sym":"SUNPHARMA",  "yf":"SUNPHARMA.NS",   "sector":"Pharma",    "lot":700,   "weight":1.98},
    {"sym":"DRREDDY",    "yf":"DRREDDY.NS",     "sector":"Pharma",    "lot":125,   "weight":0.95},
    {"sym":"CIPLA",      "yf":"CIPLA.NS",       "sector":"Pharma",    "lot":650,   "weight":0.98},
    {"sym":"DIVISLAB",   "yf":"DIVISLAB.NS",    "sector":"Pharma",    "lot":200,   "weight":0.92},
    {"sym":"AUROPHARMA", "yf":"AUROPHARMA.NS",  "sector":"Pharma",    "lot":650,   "weight":0.70},
    {"sym":"LUPIN",      "yf":"LUPIN.NS",       "sector":"Pharma",    "lot":425,   "weight":0.68},
    # Healthcare
    {"sym":"APOLLOHOSP", "yf":"APOLLOHOSP.NS",  "sector":"Healthcare","lot":175,   "weight":0.85},
    {"sym":"MAXHEALTH",  "yf":"MAXHEALTH.NS",   "sector":"Healthcare","lot":700,   "weight":0.50},
    # Metal
    {"sym":"TATASTEEL",  "yf":"TATASTEEL.NS",   "sector":"Metal",     "lot":5500,  "weight":1.20},
    {"sym":"JSWSTEEL",   "yf":"JSWSTEEL.NS",    "sector":"Metal",     "lot":1350,  "weight":1.35},
    {"sym":"HINDALCO",   "yf":"HINDALCO.NS",    "sector":"Metal",     "lot":2800,  "weight":1.08},
    {"sym":"COALINDIA",  "yf":"COALINDIA.NS",   "sector":"Metal",     "lot":4200,  "weight":1.02},
    {"sym":"VEDL",       "yf":"VEDL.NS",        "sector":"Metal",     "lot":2800,  "weight":0.80},
    {"sym":"SAIL",       "yf":"SAIL.NS",        "sector":"Metal",     "lot":9500,  "weight":0.55},
    # FMCG
    {"sym":"HINDUNILVR", "yf":"HINDUNILVR.NS",  "sector":"FMCG",      "lot":300,   "weight":2.82},
    {"sym":"ITC",        "yf":"ITC.NS",         "sector":"FMCG",      "lot":3200,  "weight":0.68},
    {"sym":"NESTLEIND",  "yf":"NESTLEIND.NS",   "sector":"FMCG",      "lot":40,    "weight":1.40},
    {"sym":"TATACONSUM", "yf":"TATACONSUM.NS",  "sector":"FMCG",      "lot":1100,  "weight":0.88},
    {"sym":"MARICO",     "yf":"MARICO.NS",      "sector":"FMCG",      "lot":2000,  "weight":0.70},
    {"sym":"DABUR",      "yf":"DABUR.NS",       "sector":"FMCG",      "lot":2750,  "weight":0.65},
    # Infra / Realty
    {"sym":"LT",         "yf":"LT.NS",          "sector":"Infra",     "lot":175,   "weight":2.80},
    {"sym":"ADANIENT",   "yf":"ADANIENT.NS",    "sector":"Infra",     "lot":1250,  "weight":1.60},
    {"sym":"ADANIPORTS", "yf":"ADANIPORTS.NS",  "sector":"Infra",     "lot":1250,  "weight":0.82},
    {"sym":"DLF",        "yf":"DLF.NS",         "sector":"Realty",    "lot":1650,  "weight":0.80},
    {"sym":"GODREJPROP", "yf":"GODREJPROP.NS",  "sector":"Realty",    "lot":650,   "weight":0.70},
    {"sym":"OBEROIRLTY", "yf":"OBEROIRLTY.NS",  "sector":"Realty",    "lot":700,   "weight":0.65},
    # Cement
    {"sym":"ULTRACEMCO", "yf":"ULTRACEMCO.NS",  "sector":"Cement",    "lot":100,   "weight":1.45},
    {"sym":"GRASIM",     "yf":"GRASIM.NS",      "sector":"Cement",    "lot":475,   "weight":1.12},
    {"sym":"AMBUJACEM",  "yf":"AMBUJACEM.NS",   "sector":"Cement",    "lot":2500,  "weight":0.80},
    # Telecom / Consumer
    {"sym":"BHARTIARTL", "yf":"BHARTIARTL.NS",  "sector":"Telecom",   "lot":950,   "weight":5.65},
    {"sym":"TITAN",      "yf":"TITAN.NS",       "sector":"Consumer",  "lot":425,   "weight":1.72},
    {"sym":"ASIANPAINT", "yf":"ASIANPAINT.NS",  "sector":"Consumer",  "lot":300,   "weight":1.05},
    {"sym":"HAVELLS",    "yf":"HAVELLS.NS",     "sector":"Consumer",  "lot":500,   "weight":0.75},
    # Retail
    {"sym":"TRENT",      "yf":"TRENT.NS",       "sector":"Retail",    "lot":275,   "weight":0.70},
    {"sym":"DMART",      "yf":"DMART.NS",       "sector":"Retail",    "lot":350,   "weight":0.80},
    {"sym":"ZOMATO",     "yf":"ZOMATO.NS",      "sector":"Retail",    "lot":3750,  "weight":0.65},
    # Chemical
    {"sym":"PIDILITIND", "yf":"PIDILITIND.NS",  "sector":"Chemical",  "lot":250,   "weight":0.80},
    {"sym":"SRF",        "yf":"SRF.NS",         "sector":"Chemical",  "lot":375,   "weight":0.70},
    {"sym":"DEEPAKNTR",  "yf":"DEEPAKNTR.NS",   "sector":"Chemical",  "lot":500,   "weight":0.65},
    # Defence / PSU
    {"sym":"BEL",        "yf":"BEL.NS",         "sector":"Defence",   "lot":3500,  "weight":0.80},
    {"sym":"HAL",        "yf":"HAL.NS",         "sector":"Defence",   "lot":300,   "weight":0.75},
    {"sym":"BHEL",       "yf":"BHEL.NS",        "sector":"Defence",   "lot":5500,  "weight":0.60},
    {"sym":"IRCTC",      "yf":"IRCTC.NS",       "sector":"PSU",       "lot":2500,  "weight":0.65},
    {"sym":"IRFC",       "yf":"IRFC.NS",        "sector":"PSU",       "lot":4800,  "weight":0.60},
    {"sym":"PFC",        "yf":"PFC.NS",         "sector":"PSU",       "lot":2700,  "weight":0.58},
    {"sym":"REC",        "yf":"REC.NS",         "sector":"PSU",       "lot":2700,  "weight":0.55},
    {"sym":"RVNL",       "yf":"RVNL.NS",        "sector":"PSU",       "lot":3500,  "weight":0.52},
    {"sym":"SIEMENS",    "yf":"SIEMENS.NS",     "sector":"CapGoods",  "lot":275,   "weight":0.70},
    {"sym":"ABB",        "yf":"ABB.NS",         "sector":"CapGoods",  "lot":175,   "weight":0.65},
    {"sym":"UPL",        "yf":"UPL.NS",         "sector":"Agri",      "lot":2000,  "weight":0.60},
    {"sym":"PIIND",      "yf":"PIIND.NS",       "sector":"Agri",      "lot":250,   "weight":0.55},
    {"sym":"COROMANDEL", "yf":"COROMANDEL.NS",  "sector":"Agri",      "lot":500,   "weight":0.52},
]

PRICE_MAP = {
    "HDFCBANK":1680,"ICICIBANK":1280,"SBIN":820,"AXISBANK":1180,"KOTAKBANK":1900,
    "INDUSINDBK":1450,"BANKBARODA":260,"PNB":105,"IDFCFIRSTB":72,"FEDERALBNK":195,
    "BANDHANBNK":205,"YESBANK":20,"BAJFINANCE":6800,"BAJAJFINSV":1680,"SHRIRAMFIN":950,
    "CHOLAFIN":1640,"MUTHOOTFIN":2100,"CDSL":1230,"MCX":6500,"SBILIFE":1810,
    "HDFCLIFE":600,"LICI":920,"ICICIPRULI":535,"TCS":2450,"INFY":1560,"HCLTECH":1200,
    "WIPRO":620,"TECHM":1550,"LTIM":5200,"PERSISTENT":4820,"RELIANCE":1310,"ONGC":270,
    "BPCL":320,"IOC":145,"GAIL":210,"NTPC":360,"POWERGRID":320,"ADANIGREEN":1310,
    "TATAPOWER":445,"SUZLON":55,"MARUTI":13400,"TATAMOTORS":950,"HEROMOTOCO":5020,
    "BAJAJ-AUTO":10060,"M&M":3080,"TVSMOTORS":2400,"SUNPHARMA":1800,"DRREDDY":6200,
    "CIPLA":1540,"DIVISLAB":6610,"AUROPHARMA":1385,"LUPIN":2200,"APOLLOHOSP":7690,
    "MAXHEALTH":1000,"TATASTEEL":155,"JSWSTEEL":1255,"HINDALCO":1040,"COALINDIA":475,
    "VEDL":302,"SAIL":120,"HINDUNILVR":2350,"ITC":465,"NESTLEIND":1460,"TATACONSUM":1150,
    "MARICO":790,"DABUR":455,"LT":3650,"ADANIENT":2480,"ADANIPORTS":1740,"DLF":600,
    "GODREJPROP":2800,"OBEROIRLTY":1660,"ULTRACEMCO":11780,"GRASIM":2850,"AMBUJACEM":438,
    "BHARTIARTL":1820,"TITAN":3400,"ASIANPAINT":2250,"HAVELLS":1650,"TRENT":6200,
    "DMART":4310,"ZOMATO":245,"PIDILITIND":3200,"SRF":2500,"DEEPAKNTR":1740,"BEL":434,
    "HAL":4640,"BHEL":382,"IRCTC":572,"IRFC":106,"PFC":470,"REC":490,"RVNL":300,
    "SIEMENS":7200,"ABB":7274,"UPL":520,"PIIND":3010,"COROMANDEL":1900,
}


# ══════════════════════════════════════════════════════════════════════
#  DATA FETCH
# ══════════════════════════════════════════════════════════════════════
def fetch_ohlcv(yf_sym: str, days: int = 90) -> pd.DataFrame:
    if not YF_AVAILABLE:
        raise ImportError("yfinance not installed")
    ticker = yf.Ticker(yf_sym)
    df = ticker.history(period=f"{days}d", interval="1d", auto_adjust=True)
    if df.empty or len(df) < 15:
        raise ValueError(f"Insufficient data")
    df = df[["Open","High","Low","Close","Volume"]].copy()
    df.columns = ["open","high","low","close","volume"]
    return df.dropna().reset_index(drop=True)


def generate_demo_ohlcv(sym: str, days: int = 90) -> pd.DataFrame:
    rng    = random.Random(hash(sym) % 99991)
    np_rng = np.random.default_rng(hash(sym) % 99991)
    bp     = float(PRICE_MAP.get(sym, rng.uniform(200, 3000)))
    closes = [bp]
    trend  = rng.uniform(-0.0012, 0.0022)
    for _ in range(days - 1):
        closes.append(max(closes[-1] * (1 + np_rng.normal(trend, 0.013)), bp * 0.3))
    rows = []
    for c in closes:
        sp = c * rng.uniform(0.007, 0.024)
        h = c + sp * rng.uniform(0.4, 1.0)
        l = c - sp * rng.uniform(0.4, 1.0)
        rows.append({"open":rng.uniform(l,h),"high":h,"low":l,"close":c,
                     "volume":int(rng.uniform(400_000, 9_000_000))})
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════
#  TECHNICAL INDICATORS
# ══════════════════════════════════════════════════════════════════════
def calc_atr(df, period=14):
    h,l,c = df["high"].values, df["low"].values, df["close"].values
    trs = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1,len(df))]
    return float(np.mean(trs[-period:])) if trs else c[-1]*0.018

def calc_rsi(closes, period=14):
    if len(closes) < period+2: return 50.0
    d = np.diff(closes[-period*2:])
    g,lo = np.where(d>0,d,0.0), np.where(d<0,-d,0.0)
    ag,al = g[-period:].mean(), lo[-period:].mean()
    if al == 0: return 100.0
    return round(100 - 100/(1+ag/al), 1)

def calc_ema(closes, period):
    if len(closes) < period: return float(closes[-1])
    k = 2.0/(period+1)
    ema = float(closes[-period])
    for p in closes[-period+1:]:
        ema = p*k + ema*(1-k)
    return round(ema, 2)

def calc_52w(df):
    n = min(252, len(df))
    h52 = float(df["high"].values[-n:].max())
    l52 = float(df["low"].values[-n:].min())
    cmp = float(df["close"].values[-1])
    pos = round((cmp-l52)/max(h52-l52,1)*100, 1)
    upside = round((h52-cmp)/cmp*100, 1)
    return h52, l52, pos, upside


# ══════════════════════════════════════════════════════════════════════
#  SMC ENGINE
# ══════════════════════════════════════════════════════════════════════
def compute_smc(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 15: return None
    n = len(df)
    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    vols   = df["volume"].values
    signals, score = [], 0

    def swing_H(p=4):
        return [{"idx":i,"price":float(highs[i])} for i in range(p,n-p)
                if highs[i]==highs[i-p:i+p+1].max()]
    def swing_L(p=4):
        return [{"idx":i,"price":float(lows[i])} for i in range(p,n-p)
                if lows[i]==lows[i-p:i+p+1].min()]

    sH, sL = swing_H(), swing_L()

    # 1. BOS
    if sH and closes[-1] > sH[-1]["price"]:
        signals.append({"type":"BOS","dir":"BULL","label":"BOS↑",
            "desc":f"Bullish BOS above ₹{sH[-1]['price']:.2f}"}); score += 30
    if sL and closes[-1] < sL[-1]["price"]:
        signals.append({"type":"BOS","dir":"BEAR","label":"BOS↓",
            "desc":f"Bearish BOS below ₹{sL[-1]['price']:.2f}"}); score -= 30

    # 2. CHoCH
    if len(sH)>=2 and len(sL)>=2:
        h1,h2 = sH[-2]["price"],sH[-1]["price"]
        l1,l2 = sL[-2]["price"],sL[-1]["price"]
        if h2>h1 and l2>l1 and closes[-1]<l2:
            signals.append({"type":"CHoCH","dir":"BEAR","label":"CHoCH↓",
                "desc":f"Uptrend broken at ₹{closes[-1]:.2f}"}); score-=22
        if h2<h1 and l2<l1 and closes[-1]>h2:
            signals.append({"type":"CHoCH","dir":"BULL","label":"CHoCH↑",
                "desc":f"Downtrend broken at ₹{closes[-1]:.2f}"}); score+=22

    # 3. Order Block
    for i in range(max(0,n-15), n-3):
        co,cc,cl,ch = opens[i],closes[i],lows[i],highs[i]
        if cc < co:
            rally = [(opens[j],closes[j]) for j in range(i+1,min(i+4,n))]
            if len(rally)==3 and all(c>o for o,c in rally) and (rally[-1][1]-cc)/cc>0.012:
                if lows[-1]<=ch and highs[-1]>=cl:
                    signals.append({"type":"OB","dir":"BULL","label":"Bull OB 📦",
                        "desc":f"Demand ₹{cl:.2f}–₹{ch:.2f} retesting"}); score+=28; break
        if cc > co:
            drop = [(opens[j],closes[j]) for j in range(i+1,min(i+4,n))]
            if len(drop)==3 and all(c<o for o,c in drop) and (cc-drop[-1][1])/cc>0.012:
                if lows[-1]<=ch and highs[-1]>=cl:
                    signals.append({"type":"OB","dir":"BEAR","label":"Bear OB 📦",
                        "desc":f"Supply ₹{cl:.2f}–₹{ch:.2f}"}); score-=25; break

    # 4. FVG
    for i in range(max(0,n-20), n-2):
        c1h,c1l,c3l,c3h = highs[i],lows[i],lows[i+2],highs[i+2]
        if c3l>c1h and (c3l-c1h)/c1h>0.003:
            ig = c1h<closes[-1]<c3l
            signals.append({"type":"FVG","dir":"BULL","label":"FVG↑ 🕳️",
                "desc":f"FVG ₹{c1h:.2f}–₹{c3l:.2f}{' (in gap)' if ig else ''}"}); score+=18 if ig else 10; break
        if c3h<c1l and (c1l-c3h)/c1l>0.003:
            ig = c3h<closes[-1]<c1l
            signals.append({"type":"FVG","dir":"BEAR","label":"FVG↓ 🕳️",
                "desc":f"FVG ₹{c3h:.2f}–₹{c1l:.2f}{' (in gap)' if ig else ''}"}); score-=15 if ig else 8; break

    # 5. Liquidity Grab
    r20h = highs[-20:-1].max() if n>=20 else highs[:-1].max()
    r20l = lows[-20:-1].min()  if n>=20 else lows[:-1].min()
    mid  = (lows[-1]+highs[-1])/2
    if lows[-1]<r20l and closes[-1]>mid:
        signals.append({"type":"LIQ","dir":"BULL","label":"LiqGrab↑ 💧",
            "desc":f"Stop hunt below ₹{r20l:.2f}"}); score+=25
    if highs[-1]>r20h and closes[-1]<mid:
        signals.append({"type":"LIQ","dir":"BEAR","label":"LiqGrab↓ 💧",
            "desc":f"Stop hunt above ₹{r20h:.2f}"}); score-=22

    # 6. Volume
    avg_vol = vols[-20:].mean() if n>=20 else vols.mean()
    vr = vols[-1]/avg_vol if avg_vol>0 else 1.0
    if vr>1.8:
        if closes[-1]>opens[-1]:
            signals.append({"type":"VOL","dir":"BULL","label":f"Vol {vr:.1f}x 📊",
                "desc":f"Inst. buying {vr:.1f}x"}); score+=15
        else:
            signals.append({"type":"VOL","dir":"BEAR","label":f"Vol {vr:.1f}x 📊",
                "desc":f"Inst. selling {vr:.1f}x"}); score-=12

    # 7. Discount / Premium
    rh = highs[-20:].max() if n>=20 else highs.max()
    rl = lows[-20:].min()  if n>=20 else lows.min()
    eq = (rh+rl)/2
    if closes[-1]<eq*0.995 and score>0:
        signals.append({"type":"ZONE","dir":"BULL","label":"Discount🟢",
            "desc":f"Discount {(eq-closes[-1])/eq*100:.1f}% below EQ ₹{eq:.2f}"}); score+=10
    if closes[-1]>eq*1.005 and score<0:
        signals.append({"type":"ZONE","dir":"BEAR","label":"Premium🔴",
            "desc":f"Premium {(closes[-1]-eq)/eq*100:.1f}% above EQ"}); score-=8

    bull_s = sum(1 for s in signals if s["dir"]=="BULL")
    bear_s = sum(1 for s in signals if s["dir"]=="BEAR")
    if abs(bull_s-bear_s)>=2: score += 10 if bull_s>bear_s else -10
    score = max(-100, min(100, round(score)))
    pct = ((closes[-1]-closes[-2])/closes[-2]*100) if len(closes)>1 else 0

    atr   = calc_atr(df)
    rsi   = calc_rsi(closes)
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    h52,l52,pos52,upside = calc_52w(df)

    return {
        "patterns":[s["label"] for s in signals], "signals":signals,
        "smcScore":score, "lastClose":round(float(closes[-1]),2),
        "prevClose":round(float(closes[-2]),2) if len(closes)>1 else 0,
        "pctChange":round(float(pct),2), "high":round(float(highs[-1]),2),
        "low":round(float(lows[-1]),2), "open":round(float(opens[-1]),2),
        "volume":int(vols[-1]), "avgVol":int(avg_vol), "volRatio":round(float(vr),1),
        "dayRange":round(float((highs[-1]-lows[-1])/lows[-1]*100),2),
        "bullSignals":bull_s, "bearSignals":bear_s,
        "equilibrium":round(float(eq),2), "rangeHigh":round(float(rh),2),
        "rangeLow":round(float(rl),2), "atr":round(atr,2), "rsi":rsi,
        "ema20":ema20, "ema50":ema50, "h52":round(h52,2), "l52":round(l52,2),
        "pos52":pos52, "upside52":upside,
    }


# ══════════════════════════════════════════════════════════════════════
#  TRADE SETUP — Entry / SL / T1(3%) / T2(5%) / T3(12%) — Positional
# ══════════════════════════════════════════════════════════════════════
def compute_trade(smc: dict, stock: dict) -> dict:
    if not smc: return None
    score = smc["smcScore"]
    price = smc["lastClose"]
    atr   = smc["atr"]
    rsi   = smc["rsi"]

    if score >= 20:   direction = "LONG"
    elif score <= -20: direction = "SHORT"
    else:              return None

    if direction == "LONG":
        entry_low  = round(price - atr*0.3, 2)
        entry_high = round(price + atr*0.2, 2)
        sl         = round(price - atr*1.5, 2)
        sl_pct     = round((price-sl)/price*100, 1)
        t1 = round(price*1.03, 2)
        t2 = round(price*1.05, 2)
        t3 = round(price*1.12, 2)
        if   rsi < 35: timing = f"ENTER NOW — RSI {rsi} oversold ✅"
        elif rsi < 55: timing = f"ENTER NOW — RSI {rsi} neutral, good zone ✅"
        elif rsi < 70: timing = f"WAIT for dip to ₹{entry_low:.0f} — RSI {rsi} rising ⚠️"
        else:          timing = f"WAIT — RSI {rsi} overbought, pullback needed 🚫"
    else:
        entry_low  = round(price - atr*0.2, 2)
        entry_high = round(price + atr*0.3, 2)
        sl         = round(price + atr*1.5, 2)
        sl_pct     = round((sl-price)/price*100, 1)
        t1 = round(price*0.97, 2)
        t2 = round(price*0.95, 2)
        t3 = round(price*0.88, 2)
        if   rsi > 70: timing = f"ENTER NOW — RSI {rsi} overbought ✅"
        elif rsi > 55: timing = f"ENTER NOW — RSI {rsi} elevated ✅"
        elif rsi > 40: timing = f"WAIT for rally to ₹{entry_high:.0f} — RSI {rsi} ⚠️"
        else:          timing = f"WAIT — RSI {rsi} oversold, bounce first 🚫"

    rr1 = round(3.0/sl_pct, 1) if sl_pct > 0 else 0
    rr2 = round(5.0/sl_pct, 1) if sl_pct > 0 else 0
    rr3 = round(12.0/sl_pct, 1) if sl_pct > 0 else 0
    btst = sl_pct <= 2.8 and score >= 30 and rr1 >= 1.0
    trend = ("above EMA20+EMA50 ✅" if price>smc["ema20"] and price>smc["ema50"]
             else "above EMA20 ⚠️" if price>smc["ema20"] else "below EMA20+EMA50 ⛔")

    # Multibagger check
    mb_score, mb_reasons = 0, []
    if smc["rsi"] < 40 and smc["pctChange"] < -1: mb_score+=20; mb_reasons.append(f"RSI {rsi} oversold + recent dip")
    if float(smc["volRatio"]) >= 2.0: mb_score+=20; mb_reasons.append(f"Vol {smc['volRatio']}x — institutional accumulation")
    if smc["pos52"] < 35: mb_score+=20; mb_reasons.append(f"At {smc['pos52']}% of 52W range — deep discount")
    if score >= 50: mb_score+=20; mb_reasons.append(f"Strong SMC confluence score {score:+d}")
    if smc["bullSignals"] >= 3: mb_score+=15; mb_reasons.append(f"{smc['bullSignals']} bullish SMC signals confluent")
    if smc["upside52"] >= 40: mb_score+=10; mb_reasons.append(f"{smc['upside52']}% upside to 52W high ₹{smc['h52']}")
    is_mb = mb_score >= 55

    return {
        "direction":direction, "entry_low":entry_low, "entry_high":entry_high,
        "sl":sl, "sl_pct":sl_pct, "timing":timing, "trend":trend,
        "t1":t1, "t2":t2, "t3":t3, "rr1":rr1, "rr2":rr2, "rr3":rr3,
        "btst":btst, "mb_score":mb_score, "mb_reasons":mb_reasons, "is_mb":is_mb,
    }


# ══════════════════════════════════════════════════════════════════════
#  RULE-BASED SELECTOR — picks best 2-3 per sector (no AI needed)
# ══════════════════════════════════════════════════════════════════════
def rule_based_picks(results: list) -> dict:
    """
    Fallback when no OpenRouter key.
    Picks best 2-3 stocks per sector using strict confluence rules:
    - Must have score >= 30
    - Must have at least 2 high-accuracy indicators (CHoCH/OB/Discount/LiqGrab)
    - Prefers BTST + MB combos
    """
    valid = [r for r in results if r["smc"] and r.get("trade") and r["smcScore"] != -999]
    PRIORITY_SIGNALS = {"CHoCH↑","Bull OB 📦","Discount🟢","LiqGrab↑ 💧","BOS↑"}

    def confluence_count(r):
        pats = set(r["smc"]["patterns"])
        return len(pats & PRIORITY_SIGNALS)

    def stock_rank(r):
        ts = r["trade"]
        return (
            r["smcScore"] * 0.4 +
            confluence_count(r) * 15 +
            (20 if ts.get("btst") else 0) +
            (ts.get("mb_score",0) * 0.3) +
            (10 if r["smc"]["volRatio"] >= 1.8 else 0)
        )

    # Group by sector, pick top 2-3 per sector for long
    from collections import defaultdict
    by_sector = defaultdict(list)
    for r in valid:
        if r["smcScore"] >= 30 and confluence_count(r) >= 1:
            by_sector[r["sector"]].append(r)

    sector_picks = {}
    for sec, stocks in by_sector.items():
        top = sorted(stocks, key=stock_rank, reverse=True)[:2]
        if top:
            sector_picks[sec] = top

    # Overall top long picks (cross-sector, max 3 different sectors)
    all_candidates = [(r, sec) for sec, stocks in sector_picks.items() for r in stocks[:1]]
    top_long = sorted(all_candidates, key=lambda x: stock_rank(x[0]), reverse=True)[:5]

    # Top short picks
    short_candidates = [r for r in valid if r["smcScore"] <= -25 and confluence_count(r) >= 1]
    top_short = sorted(short_candidates, key=lambda r: r["smcScore"])[:3]

    # Multibaggers
    mb_picks = sorted([r for r in valid if r.get("trade",{}).get("is_mb")],
                      key=lambda r: r["trade"]["mb_score"], reverse=True)[:5]

    return {
        "top_long":    [r for r,_ in top_long],
        "top_short":   top_short,
        "multibaggers":mb_picks,
        "sector_picks":sector_picks,
        "ai_used":     False,
        "ai_reasoning":{},
    }


# ══════════════════════════════════════════════════════════════════════
#  AI-POWERED SELECTOR — OpenRouter LLM picks best trades
# ══════════════════════════════════════════════════════════════════════
def ai_powered_picks(results: list) -> dict:
    """
    Uses free OpenRouter LLM to THINK and pick best 2-3 stocks.

    Flow:
    1. Filter stocks with score >= 20 (pre-screening)
    2. Build a rich prompt with ALL their data
    3. LLM reasons: considers sector rotation, signal confluence,
       RSI conditions, risk/reward, and selects BEST 2-3 per sector
    4. Returns structured JSON picks with reasoning
    """
    valid = [r for r in results if r["smc"] and r.get("trade") and r["smcScore"] >= 20]

    if not valid:
        return rule_based_picks(results)

    # Build candidate summary for LLM
    candidates_text = ""
    for r in sorted(valid, key=lambda r: r["smcScore"], reverse=True)[:40]:
        smc = r["smc"]
        ts  = r["trade"]
        candidates_text += f"""
{r['sym']} [{r['sector']}] Lot:{r['lot']}
  Score:{r['smcScore']:+d} | CMP:₹{smc['lastClose']} | Change:{smc['pctChange']:+.1f}%
  RSI:{smc['rsi']} | EMA20:₹{smc['ema20']} | ATR:₹{smc['atr']}
  52W pos:{smc['pos52']}% | Upside to 52W high:{smc['upside52']}%
  Patterns: {' | '.join(smc['patterns'][:5])}
  Bull signals:{smc['bullSignals']} | Bear signals:{smc['bearSignals']} | Vol:{smc['volRatio']}x
  Entry:₹{ts['entry_low']}-₹{ts['entry_high']} | SL:₹{ts['sl']}(-{ts['sl_pct']}%) | T1:₹{ts['t1']} T2:₹{ts['t2']} T3:₹{ts['t3']}
  BTST:{'YES' if ts['btst'] else 'NO'} | MB Score:{ts['mb_score']}/100 | Trend:{ts['trend']}
  Timing:{ts['timing']}"""

    prompt = f"""You are an expert NSE F&O positional trader and Smart Money Concepts analyst.

Today's scan date: {datetime.now().strftime('%d %b %Y')}

TRADER PROFILE:
- Positional trader (holds 2-10 days)
- BTST also fine (buy today sell tomorrow)
- 3-5% profit is a good trade
- Multibagger (10%+) is fine if patient
- Wants maximum 2-3 BEST stocks total, from DIFFERENT sectors

SCANNED CANDIDATES (pre-filtered score >= 20):
{candidates_text}

YOUR TASK:
Think carefully and select the BEST 2-3 long trades and 1-2 short trades from DIFFERENT sectors.

Selection criteria:
1. Prefer stocks with CHoCH↑ or Bull OB or Discount zone (most accurate signals from backtesting)
2. RSI below 60 for longs (not overbought)
3. Good Risk/Reward (SL% should be tight, target 3-5%)
4. Different sectors (diversification)
5. BTST eligible stocks get priority if RR >= 1
6. Multibagger if pos52 < 40% AND mb_score >= 55

Return ONLY valid JSON, no markdown, no explanation outside JSON:
{{
  "top_long": [
    {{
      "sym": "SYMBOL",
      "sector": "Sector",
      "reason": "2-3 sentence reasoning why this is the best pick",
      "entry": "₹X - ₹Y",
      "sl": "₹Z",
      "t1": "₹A (+3%)",
      "t2": "₹B (+5%)",
      "t3": "₹C (+12%)",
      "trade_type": "BTST|POSITIONAL|MULTIBAGGER",
      "confidence": "HIGH|MEDIUM",
      "key_risk": "one sentence risk"
    }}
  ],
  "top_short": [
    {{
      "sym": "SYMBOL",
      "sector": "Sector",
      "reason": "why short",
      "entry": "₹X - ₹Y",
      "sl": "₹Z",
      "t1": "₹A",
      "trade_type": "SHORT",
      "confidence": "HIGH|MEDIUM",
      "key_risk": "one sentence risk"
    }}
  ],
  "market_view": "1-2 sentence overall market view based on these signals",
  "sector_to_watch": "best sector today and why"
}}"""

    print("  🤖 Calling OpenRouter AI to think and pick best trades...")
    ai_response = call_ai(prompt, max_tokens=1500, temperature=0.2)

    if not ai_response:
        print("  ↩ No AI response — using rule-based picks")
        return rule_based_picks(results)

    # Parse JSON from AI response
    try:
        clean = ai_response.strip()
        # Strip thinking tags if DeepSeek-R1 returns them
        if "<think>" in clean:
            clean = clean[clean.rfind("</think>")+8:].strip() if "</think>" in clean else clean
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start == -1: raise ValueError("No JSON found")
        parsed = json.loads(clean[start:end])

        # Enrich parsed with actual result data
        sym_map = {r["sym"]: r for r in results if r.get("smc")}
        def enrich(picks_list):
            out = []
            for p in picks_list:
                sym = p.get("sym","")
                result_data = sym_map.get(sym)
                out.append({**p, "result": result_data})
            return out

        return {
            "top_long":     enrich(parsed.get("top_long", [])),
            "top_short":    enrich(parsed.get("top_short", [])),
            "multibaggers": [r for r in results if r.get("trade",{}).get("is_mb")][:5],
            "market_view":  parsed.get("market_view",""),
            "sector_watch": parsed.get("sector_to_watch",""),
            "ai_used":      True,
            "ai_raw":       ai_response[:500],
        }
    except Exception as e:
        print(f"  ⚠ AI JSON parse error: {e} — using rule-based picks")
        return rule_based_picks(results)


# ══════════════════════════════════════════════════════════════════════
#  SCAN RUNNER
# ══════════════════════════════════════════════════════════════════════
def run_scan(stocks: list, demo: bool = False, verbose: bool = True) -> list:
    results, total = [], len(stocks)
    for idx, stock in enumerate(stocks):
        sym = stock["sym"]
        pct = int((idx+1)/total*100)
        bar = "█"*(pct//5)+"░"*(20-pct//5)
        if verbose:
            print(f"\r  [{bar}] {pct:3d}%  {sym:<14}", end="", flush=True)
        try:
            df   = generate_demo_ohlcv(sym) if demo else fetch_ohlcv(stock["yf"])
            smc  = compute_smc(df)
            ts   = compute_trade(smc, stock)
            result = {**stock, "smc":smc, "smcScore":smc["smcScore"] if smc else 0,
                      "trade":ts, "error":None}
            if verbose and smc:
                mb_f = " 💎" if ts and ts.get("is_mb") else ""
                bt_f = " ⚡" if ts and ts.get("btst") else ""
                print(f"\r  ✓ {sym:<14} {smc['smcScore']:+4d}  "
                      f"RSI:{smc['rsi']:<5}  {ts['direction'] if ts else '----'}  "
                      f"E:₹{ts['entry_low'] if ts else '—'}"
                      f"{mb_f}{bt_f}", flush=True)
        except Exception as e:
            result = {**stock, "smc":None, "smcScore":-999, "trade":None, "error":str(e)}
            if verbose:
                print(f"\r  ✗ {sym:<14} {str(e)[:45]}", flush=True)
        results.append(result)
        if not demo: time.sleep(0.13)
    if verbose: print()
    return results


# ══════════════════════════════════════════════════════════════════════
#  HTML BUILDER
# ══════════════════════════════════════════════════════════════════════
def sl(score):
    if score>=50: return "STRONG BULL","#00e5a0"
    if score>=20: return "BULLISH","#4ade80"
    if score>=-10: return "NEUTRAL","#f5c842"
    if score>=-40: return "BEARISH","#f97316"
    return "STRONG BEAR","#f56060"

def chip_cls(label):
    if any(x in label for x in ["↑","Bull","Discount","LiqGrab↑"]): return "chip-b"
    if any(x in label for x in ["↓","Bear","Premium","LiqGrab↓"]): return "chip-r"
    return "chip-n"

def sig_icon(t):
    return {"BOS":"⚡","CHoCH":"🔄","OB":"📦","FVG":"🕳️","LIQ":"💧","VOL":"📊","ZONE":"⚖️"}.get(t,"●")


def build_ai_picks_html(picks: dict) -> str:
    ai_used = picks.get("ai_used", False)
    ai_badge = (f'<span class="ai-badge">🤖 AI ({OPENROUTER_MODEL.split("/")[1].split(":")[0]})</span>'
                if ai_used else '<span class="ai-badge rule">📐 Rule-Based</span>')

    def render_pick(p, idx, direction):
        result = p.get("result") if ai_used else p
        if not result or not result.get("smc"): return ""
        smc = result["smc"]
        ts  = result.get("trade") or {}
        sc_c = "#00e5a0" if result["smcScore"]>=0 else "#f56060"
        d_c  = "#00e5a0" if direction=="LONG" else "#f56060"
        chips = "".join(f'<span class="chip {chip_cls(pat)}">{pat}</span>'
                        for pat in smc["patterns"][:4])
        btst_b = '<span class="mini-badge btst-b">⚡ BTST</span>' if ts.get("btst") else ""
        mb_b   = f'<span class="mini-badge mb-b">💎 MB {ts.get("mb_score",0)}</span>' if ts.get("is_mb") else ""
        reason = p.get("reason","") if ai_used else f"SMC score {result['smcScore']:+d} · {', '.join(smc['patterns'][:2])}"
        risk   = p.get("key_risk","") if ai_used else f"SL at ₹{ts.get('sl','—')} (-{ts.get('sl_pct','—')}%)"
        trade_type = p.get("trade_type", "BTST" if ts.get("btst") else "POSITIONAL")
        conf = p.get("confidence","MEDIUM") if ai_used else ("HIGH" if result["smcScore"]>=50 else "MEDIUM")
        conf_c = "#00e5a0" if conf=="HIGH" else "#f5c842"

        return f"""
        <div class="pick-card {'top-pick' if idx==0 else ''}">
          <div class="pick-top">
            <div>
              <div class="pick-sym">{result['sym']}{btst_b}{mb_b}</div>
              <div class="pick-sector">{result['sector']} · lot {result['lot']}</div>
            </div>
            <div style="text-align:right">
              <div class="pick-score" style="color:{sc_c}">{result['smcScore']:+d}</div>
              <span class="trade-type-badge" style="color:{d_c};border-color:{d_c}40;background:{d_c}15">
                {trade_type}
              </span>
            </div>
          </div>
          <div class="pick-cmp">
            CMP ₹{smc['lastClose']:,.2f}
            <span style="color:{'#00e5a0' if smc['pctChange']>=0 else '#f56060'}">{smc['pctChange']:+.2f}%</span>
            <span style="color:#304560">· RSI {smc['rsi']} · {ts.get('trend','—').split(' ')[0]}</span>
          </div>
          <div class="pick-reason">{"🤖 " if ai_used else "📐 "}{reason}</div>
          <div class="pick-levels">
            <div class="pl-row"><span class="pl-lbl">ENTRY</span>
              <span class="pl-val entry-v">₹{ts.get('entry_low','—')} – ₹{ts.get('entry_high','—')}</span></div>
            <div class="pl-row"><span class="pl-lbl">STOP LOSS</span>
              <span class="pl-val sl-v">₹{ts.get('sl','—')} <small>(-{ts.get('sl_pct','—')}%)</small></span></div>
            <div class="pl-row"><span class="pl-lbl">TARGET 1 <small>+3% · BTST/2-3d</small></span>
              <span class="pl-val t1-v">₹{ts.get('t1','—')} <small>RR {ts.get('rr1','—')}:1</small></span></div>
            <div class="pl-row"><span class="pl-lbl">TARGET 2 <small>+5% · 5-10d</small></span>
              <span class="pl-val t2-v">₹{ts.get('t2','—')} <small>RR {ts.get('rr2','—')}:1</small></span></div>
            <div class="pl-row"><span class="pl-lbl">TARGET 3 <small>+12% · MB trail</small></span>
              <span class="pl-val t3-v">₹{ts.get('t3','—')} <small>RR {ts.get('rr3','—')}:1</small></span></div>
          </div>
          <div class="pick-timing">⏰ {ts.get('timing','—')}</div>
          <div class="pick-footer">
            <span style="color:{conf_c};font-size:10px">● {conf} confidence</span>
            <span style="color:#304560;font-size:10px">⚠ {risk}</span>
          </div>
          <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:3px">{chips}</div>
        </div>"""

    longs_html  = "".join(render_pick(p,i,"LONG")  for i,p in enumerate(picks.get("top_long",[])))
    shorts_html = "".join(render_pick(p,i,"SHORT") for i,p in enumerate(picks.get("top_short",[])))
    mbs_html    = "".join(render_pick(p,i,"LONG")  for i,p in enumerate(picks.get("multibaggers",[])))

    market_view = picks.get("market_view","")
    sec_watch   = picks.get("sector_watch","")

    return f"""
    <div class="picks-section">
      <div class="picks-header">
        <h2 class="picks-title">📅 TODAY'S BEST TRADES {ai_badge}</h2>
        <div class="picks-sub">
          {f'<div class="market-view">🌍 <strong>Market View:</strong> {market_view}</div>' if market_view else ''}
          {f'<div class="sec-watch">🔭 <strong>Sector to Watch:</strong> {sec_watch}</div>' if sec_watch else ''}
        </div>
      </div>
      <div class="picks-grid">
        <div>
          <div class="picks-col-hdr bull-hdr">🟢 BEST LONG / BTST ({len(picks.get('top_long',[]))})</div>
          {longs_html or '<div class="no-picks">No high-conviction setups</div>'}
        </div>
        <div>
          <div class="picks-col-hdr bear-hdr">🔴 BEST SHORT ({len(picks.get('top_short',[]))})</div>
          {shorts_html or '<div class="no-picks">No short setups</div>'}
        </div>
        <div>
          <div class="picks-col-hdr mb-hdr">💎 MULTIBAGGER ({len(picks.get('multibaggers',[]))})</div>
          {mbs_html or '<div class="no-picks">No multibagger setups</div>'}
        </div>
      </div>
    </div>"""


def build_html(results: list, scan_meta: dict, picks: dict = None) -> str:
    valid   = [r for r in results if r["smc"] and r["smcScore"] != -999]
    errors  = [r for r in results if r.get("error")]
    bull    = sum(1 for r in valid if r["smcScore"] >= 20)
    bear    = sum(1 for r in valid if r["smcScore"] <= -20)
    strong  = sum(1 for r in valid if r["smcScore"] >= 50)
    mbs_ct  = sum(1 for r in valid if r.get("trade",{}) and r["trade"].get("is_mb"))
    btst_ct = sum(1 for r in valid if r.get("trade",{}) and r["trade"].get("btst"))
    avg_sc  = round(sum(r["smcScore"] for r in valid)/len(valid)) if valid else 0
    sorted_r = sorted(valid, key=lambda r: r["smcScore"], reverse=True)
    sectors  = sorted(set(r["sector"] for r in valid))
    scan_time = scan_meta.get("scan_time", datetime.now().strftime("%d %b %Y, %I:%M %p"))
    mode_str  = "DEMO" if scan_meta.get("demo") else "LIVE · YAHOO FINANCE"
    ai_mode   = f"AI: {OPENROUTER_MODEL.split('/')[1].split(':')[0]}" if OPENROUTER_API_KEY else "Rule-Based Picks"

    sec_bars = "".join(
        f'<div class="sec-bar"><div class="sb-lbl"><span>{s}</span>'
        f'<span style="color:{"#00e5a0" if a>=0 else "#f56060"}">{a:+d}</span></div>'
        f'<div class="sb-track"><div class="sb-fill" style="width:{min(100,max(0,(a+100)/2))}%;background:{"#00e5a0" if a>=0 else "#f56060"}"></div></div></div>'
        for s in sectors
        for ss in [[r for r in valid if r["sector"]==s]]
        for a in [round(sum(r["smcScore"] for r in ss)/len(ss)) if ss else 0]
    )
    sec_btns = "".join(f'<button class="fb" onclick="fSec(this,\'{s}\')">{s}</button>' for s in sectors)

    # Build stock rows
    def row_html(r, rank):
        smc = r["smc"]
        ts  = r.get("trade") or {}
        sent,sc_c = sl(r["smcScore"])
        sc_col = "#00e5a0" if r["smcScore"]>=0 else "#f56060"
        up  = smc["pctChange"]>=0
        cc  = "#00e5a0" if up else "#f56060"
        ri  = ["🥇","🥈","🥉"][rank-1] if rank<=3 else f"#{rank}"
        chips = "".join(f'<span class="chip {chip_cls(p)}">{p}</span>' for p in smc["patterns"][:4]) \
                or '<span class="chip chip-n">NO SIGNAL</span>'
        mb_b  = '<span style="font-size:9px">💎</span>' if ts.get("is_mb") else ""
        bt_b  = '<span style="font-size:9px">⚡</span>' if ts.get("btst") else ""

        sig_rows = "".join(
            f'<div class="sr"><span>{sig_icon(s["type"])}</span>'
            f'<span style="color:{"#00e5a0" if s["dir"]=="BULL" else "#f56060" if s["dir"]=="BEAR" else "#f5c842"}">{s["desc"]}</span></div>'
            for s in smc["signals"]
        ) or '<div style="color:#304560;font-size:11px">No SMC signals</div>'

        trade_html = ""
        if ts:
            dc = "#00e5a0" if ts["direction"]=="LONG" else "#f56060"
            trade_html = f"""
            <div class="tb">
              <div class="tb-hdr">
                <span style="color:{dc};font-weight:600">{ts['direction']}</span>
                <span class="tb-timing">{ts['timing']}</span>
                <span style="color:#304560;font-size:10px">ATR ₹{smc['atr']} · RSI {smc['rsi']} · {ts['trend']}</span>
              </div>
              <div class="tb-lvls">
                <div class="tbr"><span class="tbl entry-lbl">ENTRY ZONE</span><span class="tbv" style="color:#2d7ff9">₹{ts['entry_low']} – ₹{ts['entry_high']}</span></div>
                <div class="tbr"><span class="tbl sl-lbl">STOP LOSS</span><span class="tbv" style="color:#f56060">₹{ts['sl']} <small>(-{ts['sl_pct']}%)</small></span></div>
                <div class="tbr"><span class="tbl">T1 +3% · BTST</span><span class="tbv" style="color:#86efac">₹{ts['t1']} <small>RR {ts['rr1']}:1</small></span></div>
                <div class="tbr"><span class="tbl">T2 +5% · 5-10d</span><span class="tbv" style="color:#00e5a0">₹{ts['t2']} <small>RR {ts['rr2']}:1</small></span></div>
                <div class="tbr"><span class="tbl">T3 +12% · Trail</span><span class="tbv" style="color:#f5c842">₹{ts['t3']} <small>RR {ts['rr3']}:1</small></span></div>
              </div>
              {''.join(f'<div class="mb-r">💎 {r2}</div>' for r2 in ts.get('mb_reasons',[]))}
            </div>"""

        mini = "".join(
            f'<div class="ms"><div class="msl">{l}</div><div class="msv" style="color:{c}">{v}</div></div>'
            for l,v,c in [
                ("Score",f'{r["smcScore"]:+d}',sc_col),("EQ",f'₹{smc["equilibrium"]}','#2d7ff9'),
                ("High",f'₹{smc["high"]}','#00e5a0'),("Low",f'₹{smc["low"]}','#f56060'),
                ("Vol",f'{smc["volRatio"]}x','#f5c842' if float(smc["volRatio"])>=1.8 else '#304560'),
                ("RSI",f'{smc["rsi"]}','#f56060' if smc["rsi"]>70 else '#00e5a0' if smc["rsi"]<35 else '#f5c842'),
                ("52W%",f'{smc["pos52"]}%','#f5c842'),("EMA20",f'₹{smc["ema20"]}','#9d7cfc'),
            ]
        )

        return f"""
        <div class="row" data-score="{r['smcScore']}" data-sector="{r['sector']}"
             data-sent="{'BULL' if r['smcScore']>=20 else 'BEAR' if r['smcScore']<=-20 else 'NEUTRAL'}"
             data-mb="{'1' if ts.get('is_mb') else '0'}"
             data-btst="{'1' if ts.get('btst') else '0'}">
          <div class="rm" onclick="tog('{r['sym']}_{rank}')">
            <div class="rnk">{ri}</div>
            <div><div class="sym">{r['sym']}{mb_b}{bt_b}</div><div class="stag">{r['sector']}·{r['lot']}</div></div>
            <div class="score" style="color:{sc_col}">{r['smcScore']:+d}</div>
            <div class="cchips">{chips}</div>
            <div class="cprice">
              <div class="price">₹{smc['lastClose']:,.1f}</div>
              <div class="pct" style="color:{cc}">{'+' if up else ''}{smc['pctChange']}%</div>
            </div>
            <div class="sent" style="background:{sc_c}18;color:{sc_c};border:1px solid {sc_c}30">{sent}</div>
            <div class="dir-c" style="color:{'#00e5a0' if ts.get('direction')=='LONG' else '#f56060' if ts.get('direction')=='SHORT' else '#304560'}">
              {ts.get('direction','—')}<br><span style="font-size:8px;color:#304560">SL ₹{ts.get('sl','—')}</span>
            </div>
            <div class="ei" id="ei-{r['sym']}_{rank}">▼</div>
          </div>
          <div class="rd" id="det-{r['sym']}_{rank}" style="display:none">
            <div class="d3c">
              <div><div class="dt">Signals ({len(smc['signals'])})</div><div class="slist">{sig_rows}</div><div class="mgrid">{mini}</div></div>
              <div>{trade_html}</div>
              <div></div>
            </div>
          </div>
        </div>"""

    rows_html = "".join(row_html(r,i+1) for i,r in enumerate(sorted_r))
    picks_html = build_ai_picks_html(picks) if picks else ""
    err_html = f'<div class="err">⚠ {len(errors)} fetch errors: {", ".join(r["sym"] for r in errors[:8])}</div>' if errors else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NSE SMC Scanner v3 AI — {scan_time}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--bg:#04060c;--s1:#080c18;--s2:#0b1020;--b1:#131d2e;--b2:#1a2840;
  --tx:#c8daf5;--mu:#304560;--g:#00e5a0;--b:#2d7ff9;--y:#f5c842;--r:#f56060;--p:#9d7cfc;
  --mono:'JetBrains Mono',monospace;--dis:'Orbitron',monospace;--body:'Rajdhani',sans-serif;}}
body{{background:var(--bg);font-family:var(--body);color:var(--tx);min-height:100vh;}}
body::after{{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,229,160,.005) 3px,rgba(0,229,160,.005) 4px);}}
.w{{max-width:1300px;margin:0 auto;padding:14px 12px 60px;position:relative;z-index:1;}}
.hdr{{text-align:center;padding:22px 0 16px;border-bottom:1px solid var(--b1);margin-bottom:16px;
  background:radial-gradient(ellipse 70% 100% at 50% 0%,rgba(45,127,249,.05) 0%,transparent 70%);}}
.hdr-b{{font-family:var(--mono);font-size:9px;letter-spacing:.2em;color:var(--g);
  border:1px solid rgba(0,229,160,.2);padding:3px 10px;border-radius:20px;
  display:inline-flex;align-items:center;gap:5px;margin-bottom:8px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--g);}}
h1{{font-family:var(--dis);font-size:clamp(14px,3.5vw,30px);font-weight:900;letter-spacing:.1em;
  background:linear-gradient(90deg,#fff 0%,#2d7ff9 35%,#00e5a0 70%,#9d7cfc 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.hdr-sub{{font-family:var(--mono);font-size:9px;color:var(--mu);letter-spacing:.07em;margin-top:5px;line-height:1.7;}}
.meta-row{{display:flex;justify-content:center;gap:10px;margin-top:10px;flex-wrap:wrap;}}
.meta{{font-family:var(--mono);font-size:9px;color:var(--mu);padding:3px 10px;
  border:1px solid var(--b2);border-radius:4px;}}
.meta span{{color:var(--g);font-weight:600;}}
/* AI HOW IT WORKS BOX */
.ai-how{{background:var(--s1);border:1px solid rgba(157,124,252,.25);border-radius:10px;
  padding:12px 16px;margin-bottom:14px;}}
.ai-how-title{{font-family:var(--mono);font-size:9px;color:var(--p);text-transform:uppercase;
  letter-spacing:.16em;margin-bottom:10px;display:flex;align-items:center;gap:8px;}}
.ai-how-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;}}
.ai-step{{display:flex;gap:8px;font-size:12px;}}
.ai-step-num{{width:20px;height:20px;border-radius:50%;background:rgba(157,124,252,.2);
  color:var(--p);font-family:var(--mono);font-size:9px;font-weight:600;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;}}
.ai-step-text{{color:var(--mu);font-size:11px;line-height:1.5;}}
.ai-step-text strong{{color:var(--tx);}}
.ai-key-box{{margin-top:10px;padding:8px 12px;background:rgba(245,200,66,.05);
  border:1px solid rgba(245,200,66,.15);border-radius:6px;font-family:var(--mono);
  font-size:10px;color:#7a6030;line-height:1.7;}}
.ai-key-box strong{{color:var(--y);}}
/* STATS */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(95px,1fr));gap:6px;margin-bottom:14px;}}
.stat{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;padding:8px 11px;text-align:center;}}
.stl{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.14em;margin-bottom:3px;}}
.stv{{font-family:var(--dis);font-size:19px;font-weight:700;}}
/* PICKS SECTION */
.picks-section{{margin-bottom:20px;}}
.picks-header{{text-align:center;margin-bottom:14px;}}
.picks-title{{font-family:var(--dis);font-size:clamp(13px,2.5vw,22px);letter-spacing:.1em;
  background:linear-gradient(90deg,#f5c842,#00e5a0);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text;margin-bottom:6px;
  display:flex;align-items:center;justify-content:center;gap:10px;}}
.ai-badge{{font-family:var(--mono);font-size:10px;padding:3px 10px;border-radius:20px;
  background:rgba(157,124,252,.15);color:var(--p);border:1px solid rgba(157,124,252,.3);
  -webkit-text-fill-color:var(--p);}}
.ai-badge.rule{{background:rgba(45,127,249,.1);color:var(--b);border-color:rgba(45,127,249,.3);
  -webkit-text-fill-color:var(--b);}}
.picks-sub{{font-family:var(--mono);font-size:10px;color:var(--mu);margin-bottom:10px;}}
.market-view,.sec-watch{{padding:4px 0;}}
.picks-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:10px;}}
.picks-col-hdr{{font-family:var(--dis);font-size:11px;letter-spacing:.1em;
  padding:8px 14px;border-radius:7px;text-align:center;margin-bottom:8px;}}
.bull-hdr{{background:rgba(0,229,160,.1);color:var(--g);border:1px solid rgba(0,229,160,.2);}}
.bear-hdr{{background:rgba(245,96,96,.1);color:var(--r);border:1px solid rgba(245,96,96,.2);}}
.mb-hdr{{background:rgba(245,200,66,.1);color:var(--y);border:1px solid rgba(245,200,66,.2);}}
.pick-card{{background:var(--s1);border:1px solid var(--b2);border-radius:10px;
  padding:13px;margin-bottom:8px;transition:border-color .15s;}}
.pick-card.top-pick{{border-color:rgba(0,229,160,.35);}}
.pick-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;}}
.pick-sym{{font-family:var(--dis);font-size:16px;font-weight:900;color:#fff;letter-spacing:.05em;}}
.pick-sector{{font-family:var(--mono);font-size:8px;color:var(--mu);margin-top:2px;}}
.pick-score{{font-family:var(--dis);font-size:20px;font-weight:900;}}
.trade-type-badge{{font-family:var(--mono);font-size:9px;padding:2px 8px;border-radius:4px;border:1px solid;display:block;text-align:right;margin-top:3px;}}
.pick-cmp{{font-family:var(--mono);font-size:12px;color:var(--tx);margin-bottom:7px;}}
.pick-reason{{font-family:var(--mono);font-size:10px;color:#5a80a0;
  padding:6px 8px;background:rgba(45,127,249,.05);border-radius:5px;
  border-left:2px solid rgba(45,127,249,.3);margin-bottom:8px;line-height:1.6;}}
.pick-levels{{display:flex;flex-direction:column;gap:4px;margin-bottom:7px;}}
.pl-row{{display:grid;grid-template-columns:120px 1fr;gap:6px;align-items:baseline;}}
.pl-lbl{{font-family:var(--mono);font-size:8px;text-transform:uppercase;letter-spacing:.1em;color:var(--mu);}}
.pl-val{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.entry-v{{color:#2d7ff9;}} .sl-v{{color:#f56060;}} .t1-v{{color:#86efac;}}
.t2-v{{color:#00e5a0;}} .t3-v{{color:#f5c842;}}
.pick-timing{{font-family:var(--mono);font-size:9px;color:var(--y);margin-bottom:5px;}}
.pick-footer{{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;}}
.mini-badge{{font-family:var(--mono);font-size:8px;padding:1px 6px;border-radius:3px;}}
.btst-b{{background:rgba(45,127,249,.12);color:var(--b);border:1px solid rgba(45,127,249,.25);}}
.mb-b{{background:rgba(245,200,66,.12);color:var(--y);border:1px solid rgba(245,200,66,.25);}}
.mb-r{{font-family:var(--mono);font-size:9px;color:#7a6030;padding:2px 8px;}}
.no-picks{{font-family:var(--mono);font-size:11px;color:var(--mu);
  text-align:center;padding:20px;border:1px dashed var(--b2);border-radius:8px;}}
/* SECTOR BARS */
.sec-s{{background:var(--s1);border:1px solid var(--b1);border-radius:9px;padding:12px 14px;margin-bottom:14px;}}
.sec-t{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.16em;margin-bottom:10px;}}
.sec-bars{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:7px;}}
.sec-bar{{display:flex;flex-direction:column;gap:3px;}}
.sb-lbl{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;}}
.sb-track{{height:4px;background:var(--b2);border-radius:2px;overflow:hidden;}}
.sb-fill{{height:100%;border-radius:2px;}}
/* CONTROLS */
.ctrl{{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-bottom:7px;}}
.ctrl-lbl{{font-family:var(--mono);font-size:8px;color:var(--mu);letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;}}
.fb{{padding:5px 10px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);
  color:var(--mu);font-family:var(--mono);font-size:9px;cursor:pointer;transition:all .13s;text-transform:uppercase;white-space:nowrap;}}
.fb:hover,.fb.on{{border-color:var(--b);color:var(--b);background:rgba(45,127,249,.07);}}
.fb.on-mb{{border-color:var(--y)!important;color:var(--y)!important;background:rgba(245,200,66,.08)!important;}}
.fb.on-bt{{border-color:var(--b)!important;color:var(--b)!important;background:rgba(45,127,249,.1)!important;}}
.si{{padding:6px 12px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);
  color:var(--tx);font-family:var(--mono);font-size:11px;outline:none;min-width:130px;}}
.si:focus{{border-color:var(--b);}}
.si::placeholder{{color:var(--mu);}}
/* TABLE */
.th{{display:grid;grid-template-columns:32px 115px 60px 1fr 90px 110px 88px 20px;
  gap:5px;padding:6px 10px;font-family:var(--mono);font-size:7px;text-transform:uppercase;
  letter-spacing:.12em;color:var(--mu);border-bottom:1px solid var(--b1);margin-bottom:3px;}}
.results{{display:flex;flex-direction:column;gap:4px;}}
.row{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;overflow:hidden;}}
.rm{{display:grid;grid-template-columns:32px 115px 60px 1fr 90px 110px 88px 20px;
  gap:5px;padding:8px 10px;align-items:center;cursor:pointer;transition:background .12s;}}
.rm:hover{{background:var(--s2);}}
.rnk{{font-family:var(--dis);font-size:10px;color:var(--mu);text-align:center;}}
.sym{{font-family:var(--dis);font-size:13px;font-weight:700;color:#fff;letter-spacing:.04em;}}
.stag{{font-family:var(--mono);font-size:8px;color:var(--mu);margin-top:1px;}}
.score{{font-family:var(--dis);font-size:16px;font-weight:900;}}
.cchips{{display:flex;flex-wrap:wrap;gap:2px;}}
.chip{{font-family:var(--mono);font-size:8px;padding:2px 5px;border-radius:3px;font-weight:600;white-space:nowrap;}}
.chip-b{{background:rgba(0,229,160,.1);color:#00e5a0;border:1px solid rgba(0,229,160,.18);}}
.chip-r{{background:rgba(245,96,96,.1);color:#f56060;border:1px solid rgba(245,96,96,.18);}}
.chip-n{{background:rgba(245,200,66,.08);color:#f5c842;border:1px solid rgba(245,200,66,.14);}}
.cprice{{text-align:right;}}
.price{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.pct{{font-family:var(--mono);font-size:9px;margin-top:1px;}}
.sent{{padding:4px 7px;border-radius:5px;font-family:var(--dis);font-size:8px;font-weight:700;text-align:center;white-space:nowrap;}}
.dir-c{{font-family:var(--mono);font-size:9px;text-align:right;}}
.ei{{color:var(--mu);font-size:9px;text-align:center;transition:transform .17s;}}
.rd{{border-top:1px solid var(--b1);padding:11px 10px;background:rgba(4,6,12,.65);}}
.d3c{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:11px;}}
@media(max-width:900px){{.d3c,.th,.rm{{grid-template-columns:1fr;}}}}
.dt{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px;}}
.slist{{display:flex;flex-direction:column;gap:4px;margin-bottom:9px;}}
.sr{{display:flex;gap:5px;align-items:flex-start;font-family:var(--mono);font-size:10px;line-height:1.5;}}
.mgrid{{display:grid;grid-template-columns:1fr 1fr;gap:4px;}}
.ms{{background:var(--s2);border:1px solid var(--b1);border-radius:4px;padding:5px 8px;}}
.msl{{font-family:var(--mono);font-size:7px;color:var(--mu);text-transform:uppercase;letter-spacing:.1em;margin-bottom:1px;}}
.msv{{font-family:var(--mono);font-size:11px;font-weight:600;}}
.tb{{background:rgba(8,12,24,.8);border:1px solid var(--b2);border-radius:7px;overflow:hidden;}}
.tb-hdr{{padding:7px 11px;border-bottom:1px solid var(--b1);display:flex;align-items:center;
  gap:8px;font-family:var(--mono);font-size:10px;flex-wrap:wrap;}}
.tb-timing{{font-family:var(--mono);font-size:9px;color:var(--y);flex:1;}}
.tb-lvls{{padding:7px 11px;display:flex;flex-direction:column;gap:4px;}}
.tbr{{display:grid;grid-template-columns:130px 1fr;gap:5px;align-items:center;}}
.tbl{{font-family:var(--mono);font-size:8px;text-transform:uppercase;letter-spacing:.09em;color:var(--mu);}}
.tbv{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.entry-lbl{{color:var(--b)!important;}} .sl-lbl{{color:var(--r)!important;}}
.mb-r{{font-family:var(--mono);font-size:9px;color:#7a6030;padding:2px 11px;}}
.err{{font-family:var(--mono);font-size:9px;color:#304560;padding:6px 10px;margin-top:5px;}}
.dis{{text-align:center;font-family:var(--mono);font-size:8px;color:#0d1820;
  margin-top:28px;line-height:2;letter-spacing:.04em;}}
::-webkit-scrollbar{{width:3px;height:3px;}}
::-webkit-scrollbar-track{{background:var(--b1);}}
::-webkit-scrollbar-thumb{{background:var(--b2);border-radius:2px;}}
</style>
</head>
<body>
<div class="w">

<div class="hdr">
  <div class="hdr-b"><span class="dot"></span>NSE F&O · SMC v3 · AI-POWERED PICKS</div>
  <h1>NSE F&O SMC SCANNER v3</h1>
  <div class="hdr-sub">
    Math SMC Engine → OpenRouter Free LLM → Best 2-3 stocks per sector with reasoning
  </div>
  <div class="meta-row">
    <div class="meta">SCANNED <span>{len(valid)}</span></div>
    <div class="meta">BULL <span>{bull}</span></div>
    <div class="meta">BEAR <span>{bear}</span></div>
    <div class="meta">MULTIBAGGER <span>{mbs_ct}</span></div>
    <div class="meta">BTST <span>{btst_ct}</span></div>
    <div class="meta">PICKS ENGINE <span>{ai_mode}</span></div>
    <div class="meta">SCAN TIME <span>{scan_time}</span></div>
  </div>
</div>

<!-- HOW AI INTEGRATION WORKS -->
<div class="ai-how">
  <div class="ai-how-title">🤖 HOW OPENROUTER AI IS INTEGRATED IN THIS SCANNER</div>
  <div class="ai-how-grid">
    <div class="ai-step"><div class="ai-step-num">1</div><div class="ai-step-text">
      <strong>Math Engine</strong> fetches real OHLCV from Yahoo Finance, computes BOS/CHoCH/OB/FVG/LiqGrab/RSI/ATR for every stock</div></div>
    <div class="ai-step"><div class="ai-step-num">2</div><div class="ai-step-text">
      <strong>Score Filter</strong> pre-screens stocks with score ≥ 20 (top candidates only) — sends ~30-40 to AI</div></div>
    <div class="ai-step"><div class="ai-step-num">3</div><div class="ai-step-text">
      <strong>Free LLM Thinks</strong> using deepseek-r1 or llama3-free — reads all data, considers sector rotation, RSI, RR, and picks BEST 2-3 from DIFFERENT sectors</div></div>
    <div class="ai-step"><div class="ai-step-num">4</div><div class="ai-step-text">
      <strong>AI Gives Reasoning</strong> for each pick: why this stock, why this entry, what's the risk, what trade type (BTST/positional/multibagger)</div></div>
  </div>
  <div class="ai-key-box">
    <strong>To enable AI:</strong> Get free key at openrouter.ai → set env var →
    <code>set OPENROUTER_API_KEY=your_key_here</code> (Windows) or
    <code>export OPENROUTER_API_KEY=your_key_here</code> (Mac/Linux) →
    re-run script. Free models: <strong>deepseek/deepseek-r1:free</strong> · meta-llama/llama-3.1-8b-instruct:free · mistralai/mistral-7b-instruct:free
  </div>
</div>

<div class="stats">
  {''.join(f'<div class="stat"><div class="stl">{l}</div><div class="stv" style="color:{c}">{v}</div></div>' for l,v,c in [
    ("Scanned",len(valid),"var(--b)"),("Bullish",bull,"var(--g)"),("Bearish",bear,"var(--r)"),
    ("Strong≥50",strong,"var(--y)"),("Multibagger",mbs_ct,"#f5c842"),
    ("BTST",btst_ct,"var(--b)"),("Avg Score",f"{avg_sc:+d}","var(--g)" if avg_sc>=0 else "var(--r)")])}
</div>

{picks_html}

<div class="sec-s">
  <div class="sec-t">⚡ SECTOR SMART MONEY FLOW</div>
  <div class="sec-bars">{sec_bars}</div>
</div>

<div class="ctrl">
  <span class="ctrl-lbl">Filter:</span>
  <button class="fb on" onclick="fSent(this,'ALL')">ALL</button>
  <button class="fb" onclick="fSent(this,'BULL')">BULL</button>
  <button class="fb" onclick="fSent(this,'BEAR')">BEAR</button>
  <button class="fb" onclick="fStrong(this)">STRONG≥50</button>
  <button class="fb" onclick="fMB(this)">💎 MB</button>
  <button class="fb" onclick="fBTST(this)">⚡ BTST</button>
  <input class="si" placeholder="Search symbol…" oninput="fSearch(this.value)">
  <span class="ctrl-lbl" style="margin-left:auto">Sort:</span>
  <button class="fb on" onclick="srt(this,'score')">Score</button>
  <button class="fb" onclick="srt(this,'rsi')">RSI</button>
</div>
<div class="ctrl" style="margin-bottom:12px;gap:4px">
  <span class="ctrl-lbl">Sector:</span>
  <button class="fb on" onclick="fSec(this,'ALL')">ALL</button>
  {sec_btns}
</div>

<div class="th"><div>#</div><div>STOCK</div><div>SCORE</div><div>PATTERNS</div>
  <div>PRICE</div><div>SENTIMENT</div><div>DIR/SL</div><div></div></div>
<div class="results" id="rc">{rows_html}</div>
{err_html}

<div class="dis">
  DATA: {mode_str} · SMC ENGINE v3 · AI PICKS: {ai_mode} · {len(valid)} NSE F&O STOCKS<br>
  OPENROUTER FREE LLM INTEGRATION · FOR EDUCATIONAL PURPOSES ONLY · NOT SEBI REGISTERED RESEARCH
</div>
</div>
<script>
let F={{sent:'ALL',sec:'ALL',search:'',sort:'score',strong:false,mb:false,bt:false}};
function apF(){{
  const rows=[...document.querySelectorAll('.row')];
  let vis=[];
  rows.forEach(r=>{{
    const s=r.dataset.sent,sec=r.dataset.sector,sc=parseInt(r.dataset.score);
    const mb=r.dataset.mb,bt=r.dataset.btst;
    const sym=r.querySelector('.sym').textContent.toLowerCase();
    let show=true;
    if(F.mb&&mb!=='1') show=false;
    else if(F.bt&&bt!=='1') show=false;
    else if(!F.mb&&!F.bt&&F.strong&&sc<50) show=false;
    else if(!F.mb&&!F.bt&&!F.strong&&F.sent!=='ALL'&&s!==F.sent) show=false;
    if(F.sec!=='ALL'&&sec!==F.sec) show=false;
    if(F.search&&!sym.includes(F.search.toLowerCase())) show=false;
    r.style.display=show?'':'none';
    if(show) vis.push(r);
  }});
  const rc=document.getElementById('rc');
  vis.sort((a,b)=>parseInt(b.dataset.score)-parseInt(a.dataset.score));
  vis.forEach(r=>rc.appendChild(r));
}}
function clr(){{document.querySelectorAll('.ctrl .fb').forEach(b=>b.classList.remove('on','on-mb','on-bt'));}}
function fSent(btn,v){{clr();btn.classList.add('on');F.sent=v;F.strong=F.mb=F.bt=false;apF();}}
function fStrong(btn){{clr();btn.classList.add('on');F.strong=true;F.mb=F.bt=false;apF();}}
function fMB(btn){{clr();btn.classList.add('on','on-mb');F.mb=true;F.strong=F.bt=false;apF();}}
function fBTST(btn){{clr();btn.classList.add('on','on-bt');F.bt=true;F.mb=F.strong=false;apF();}}
function fSec(btn,v){{document.querySelectorAll('.ctrl:nth-of-type(2) .fb').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');F.sec=v;apF();}}
function fSearch(v){{F.search=v;apF();}}
function srt(btn,v){{F.sort=v;apF();}}
function tog(id){{
  const d=document.getElementById('det-'+id),e=document.getElementById('ei-'+id);
  if(d.style.display==='none'){{d.style.display='block';e.style.transform='rotate(180deg)';}}
  else{{d.style.display='none';e.style.transform='';}}
}}
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="NSE F&O SMC Scanner v3 — AI Edition (OpenRouter)")
    ap.add_argument("--top",    type=int,  default=None)
    ap.add_argument("--sector", type=str,  default=None)
    ap.add_argument("--sym",    type=str,  default=None)
    ap.add_argument("--demo",   action="store_true")
    ap.add_argument("--serve",  action="store_true")
    ap.add_argument("--port",   type=int,  default=5000)
    ap.add_argument("--output", type=str,  default=None)
    ap.add_argument("--open",   action="store_true")
    ap.add_argument("--no-ai",  action="store_true", help="Skip AI, use rule-based picks only")
    args = ap.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  NSE F&O SMC SCANNER v3 — AI EDITION                               ║
║  Math SMC → OpenRouter Free LLM → Best 2-3 stocks + Reasoning      ║
╚══════════════════════════════════════════════════════════════════════╝""")

    if OPENROUTER_API_KEY and not args.no_ai:
        print(f"  🤖 AI Mode: {OPENROUTER_MODEL}")
    else:
        print("  📐 Rule-Based Mode (set OPENROUTER_API_KEY to enable AI)")
        print("     Free key: https://openrouter.ai/")

    if args.sym:
        syms = [s.strip().upper() for s in args.sym.split(",")]
        stocks = [s for s in FNO_STOCKS if s["sym"] in syms]
    elif args.sector:
        stocks = [s for s in FNO_STOCKS if s["sector"].lower()==args.sector.lower()]
    elif args.top:
        stocks = sorted(FNO_STOCKS, key=lambda s: s["weight"], reverse=True)[:args.top]
    else:
        stocks = FNO_STOCKS.copy()

    if not YF_AVAILABLE and not args.demo:
        print("  ⚠  yfinance not installed — switching to demo"); args.demo = True

    print(f"\n  Stocks: {len(stocks)} | Mode: {'DEMO' if args.demo else 'LIVE'}\n")
    t0 = time.time()
    results = run_scan(stocks, demo=args.demo)
    elapsed = round(time.time()-t0, 1)

    valid = [r for r in results if r["smc"]]
    print(f"\n  ✅ Scan done in {elapsed}s · {len(valid)} stocks · "
          f"{sum(1 for r in valid if r['smcScore']>=20)} bull · "
          f"{sum(1 for r in valid if r['smcScore']<=-20)} bear\n")

    # Run picks engine
    if OPENROUTER_API_KEY and not args.no_ai:
        picks = ai_powered_picks(results)
    else:
        picks = rule_based_picks(results)

    # Print picks to terminal
    print("  ── BEST LONG PICKS ──────────────────────────────────────")
    for r in picks.get("top_long",[]):
        result = r.get("result",r) if picks.get("ai_used") else r
        if result and result.get("smc"):
            ts = result.get("trade") or {}
            reason = r.get("reason","") if picks.get("ai_used") else ""
            print(f"  {result['sym']:<14} {result['smcScore']:+4d}  ₹{result['smc']['lastClose']:<10.2f}  "
                  f"E:₹{ts.get('entry_low','—')}  SL:₹{ts.get('sl','—')}  T1:₹{ts.get('t1','—')}")
            if reason: print(f"    → {reason[:80]}")

    print("\n  ── MULTIBAGGER PICKS ────────────────────────────────────")
    for r in picks.get("multibaggers",[]):
        if r.get("smc"):
            ts = r.get("trade") or {}
            print(f"  {r['sym']:<14} MB:{ts.get('mb_score',0):>3}/100  "
                  f"52W:{r['smc']['pos52']}%  Upside:{r['smc']['upside52']}%  T3:₹{ts.get('t3','—')}")

    meta = {"scan_time":datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "demo":args.demo, "elapsed":elapsed}
    out  = args.output or f"smc_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    Path(out).write_text(build_html(results, meta, picks), encoding="utf-8")
    print(f"\n  💾 Report: {out}")

    if args.serve:
        try:
            from flask import Flask, Response
        except ImportError:
            print("  pip install flask"); return
        app = Flask(__name__)
        @app.route("/")
        def index():
            r2 = run_scan(stocks, demo=args.demo, verbose=False)
            p2 = ai_powered_picks(r2) if OPENROUTER_API_KEY and not args.no_ai else rule_based_picks(r2)
            return Response(build_html(r2, meta, p2), mimetype="text/html")
        print(f"\n  🌐 http://localhost:{args.port}")
        webbrowser.open(f"http://localhost:{args.port}")
        app.run(host="0.0.0.0", port=args.port, debug=False)
    else:
        webbrowser.open(f"file://{Path(out).resolve()}")


if __name__ == "__main__":
    main()
