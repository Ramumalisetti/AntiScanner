"""
DarvaX Scanner — @AmitabhJha3 Methodology
52W High Filter · Darvas Box · Volume Breakout · RSI 40/80 Rule · 200 EMA · Pyramiding

Usage:
  pip install yfinance pandas numpy requests flask
  python darvax_scanner.py --demo --top 80
  python darvax_scanner.py --top 100          (live Yahoo Finance)
  python darvax_scanner.py --sector Banking
  python darvax_scanner.py --cap Small        (Mid/Small preferred)
  python darvax_scanner.py --serve            (web server)
  set OPENROUTER_API_KEY=your_key             (free AI at openrouter.ai)
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

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY","")
OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL","deepseek/deepseek-r1:free")

def call_ai(prompt, max_tokens=900):
    if not OPENROUTER_API_KEY: return None
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", timeout=60,
            headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json",
                     "HTTP-Referer":"https://github.com/darvax","X-Title":"DarvaX Scanner"},
            json={"model":OPENROUTER_MODEL,"messages":[{"role":"user","content":prompt}],
                  "max_tokens":max_tokens,"temperature":0.2})
        r.raise_for_status()
        t = r.json()["choices"][0]["message"]["content"].strip()
        if "</think>" in t: t = t[t.rfind("</think>")+8:].strip()
        return t
    except Exception as e:
        print(f"  AI error: {e}"); return None

# ── UNIVERSE ──
UNIVERSE = [
    {"sym":"HDFCBANK",   "yf":"HDFCBANK.NS",   "sector":"Banking",   "mcap":1300000,"cap":"Large"},
    {"sym":"ICICIBANK",  "yf":"ICICIBANK.NS",   "sector":"Banking",   "mcap":900000, "cap":"Large"},
    {"sym":"SBIN",       "yf":"SBIN.NS",        "sector":"Banking",   "mcap":730000, "cap":"Large"},
    {"sym":"AXISBANK",   "yf":"AXISBANK.NS",    "sector":"Banking",   "mcap":390000, "cap":"Large"},
    {"sym":"KOTAKBANK",  "yf":"KOTAKBANK.NS",   "sector":"Banking",   "mcap":380000, "cap":"Large"},
    {"sym":"INDUSINDBK", "yf":"INDUSINDBK.NS",  "sector":"Banking",   "mcap":115000, "cap":"Mid"},
    {"sym":"BANKBARODA", "yf":"BANKBARODA.NS",  "sector":"Banking",   "mcap":135000, "cap":"Mid"},
    {"sym":"PNB",        "yf":"PNB.NS",         "sector":"Banking",   "mcap":120000, "cap":"Mid"},
    {"sym":"IDFCFIRSTB", "yf":"IDFCFIRSTB.NS",  "sector":"Banking",   "mcap":55000,  "cap":"Mid"},
    {"sym":"FEDERALBNK", "yf":"FEDERALBNK.NS",  "sector":"Banking",   "mcap":48000,  "cap":"Mid"},
    {"sym":"BAJFINANCE", "yf":"BAJFINANCE.NS",  "sector":"Finance",   "mcap":420000, "cap":"Large"},
    {"sym":"BAJAJFINSV", "yf":"BAJAJFINSV.NS",  "sector":"Finance",   "mcap":265000, "cap":"Large"},
    {"sym":"SHRIRAMFIN", "yf":"SHRIRAMFIN.NS",  "sector":"Finance",   "mcap":90000,  "cap":"Mid"},
    {"sym":"CHOLAFIN",   "yf":"CHOLAFIN.NS",    "sector":"Finance",   "mcap":85000,  "cap":"Mid"},
    {"sym":"MUTHOOTFIN", "yf":"MUTHOOTFIN.NS",  "sector":"Finance",   "mcap":85000,  "cap":"Mid"},
    {"sym":"HDFCAMC",    "yf":"HDFCAMC.NS",     "sector":"Finance",   "mcap":95000,  "cap":"Mid"},
    {"sym":"BSE",        "yf":"BSE.NS",         "sector":"Finance",   "mcap":88000,  "cap":"Mid"},
    {"sym":"CDSL",       "yf":"CDSL.NS",        "sector":"Finance",   "mcap":30000,  "cap":"Small"},
    {"sym":"MCX",        "yf":"MCX.NS",         "sector":"Finance",   "mcap":35000,  "cap":"Small"},
    {"sym":"ANGELONE",   "yf":"ANGELONE.NS",    "sector":"Finance",   "mcap":25000,  "cap":"Small"},
    {"sym":"SBILIFE",    "yf":"SBILIFE.NS",     "sector":"Insurance", "mcap":180000, "cap":"Large"},
    {"sym":"HDFCLIFE",   "yf":"HDFCLIFE.NS",    "sector":"Insurance", "mcap":130000, "cap":"Mid"},
    {"sym":"LICI",       "yf":"LICI.NS",        "sector":"Insurance", "mcap":580000, "cap":"Large"},
    {"sym":"ICICIGI",    "yf":"ICICIGI.NS",     "sector":"Insurance", "mcap":85000,  "cap":"Mid"},
    {"sym":"ICICIPRULI", "yf":"ICICIPRULI.NS",  "sector":"Insurance", "mcap":75000,  "cap":"Mid"},
    {"sym":"TCS",        "yf":"TCS.NS",         "sector":"IT",        "mcap":890000, "cap":"Large"},
    {"sym":"INFY",       "yf":"INFY.NS",        "sector":"IT",        "mcap":625000, "cap":"Large"},
    {"sym":"HCLTECH",    "yf":"HCLTECH.NS",     "sector":"IT",        "mcap":325000, "cap":"Large"},
    {"sym":"WIPRO",      "yf":"WIPRO.NS",       "sector":"IT",        "mcap":270000, "cap":"Large"},
    {"sym":"TECHM",      "yf":"TECHM.NS",       "sector":"IT",        "mcap":155000, "cap":"Large"},
    {"sym":"LTIM",       "yf":"LTIM.NS",        "sector":"IT",        "mcap":155000, "cap":"Large"},
    {"sym":"PERSISTENT", "yf":"PERSISTENT.NS",  "sector":"IT",        "mcap":60000,  "cap":"Mid"},
    {"sym":"COFORGE",    "yf":"COFORGE.NS",     "sector":"IT",        "mcap":30000,  "cap":"Small"},
    {"sym":"MPHASIS",    "yf":"MPHASIS.NS",     "sector":"IT",        "mcap":42000,  "cap":"Small"},
    {"sym":"KPITTECH",   "yf":"KPITTECH.NS",    "sector":"IT",        "mcap":22000,  "cap":"Small"},
    {"sym":"TATAELXSI",  "yf":"TATAELXSI.NS",   "sector":"IT",        "mcap":28000,  "cap":"Small"},
    {"sym":"RELIANCE",   "yf":"RELIANCE.NS",    "sector":"Energy",    "mcap":1760000,"cap":"Large"},
    {"sym":"ONGC",       "yf":"ONGC.NS",        "sector":"Energy",    "mcap":340000, "cap":"Large"},
    {"sym":"BPCL",       "yf":"BPCL.NS",        "sector":"Energy",    "mcap":138000, "cap":"Mid"},
    {"sym":"IOC",        "yf":"IOC.NS",         "sector":"Energy",    "mcap":200000, "cap":"Large"},
    {"sym":"GAIL",       "yf":"GAIL.NS",        "sector":"Energy",    "mcap":145000, "cap":"Mid"},
    {"sym":"IGL",        "yf":"IGL.NS",         "sector":"Energy",    "mcap":24000,  "cap":"Small"},
    {"sym":"NTPC",       "yf":"NTPC.NS",        "sector":"Power",     "mcap":350000, "cap":"Large"},
    {"sym":"POWERGRID",  "yf":"POWERGRID.NS",   "sector":"Power",     "mcap":295000, "cap":"Large"},
    {"sym":"ADANIGREEN", "yf":"ADANIGREEN.NS",  "sector":"Power",     "mcap":145000, "cap":"Mid"},
    {"sym":"TATAPOWER",  "yf":"TATAPOWER.NS",   "sector":"Power",     "mcap":140000, "cap":"Mid"},
    {"sym":"SUZLON",     "yf":"SUZLON.NS",      "sector":"Power",     "mcap":77000,  "cap":"Mid"},
    {"sym":"TORNTPOWER", "yf":"TORNTPOWER.NS",  "sector":"Power",     "mcap":68000,  "cap":"Mid"},
    {"sym":"MARUTI",     "yf":"MARUTI.NS",      "sector":"Auto",      "mcap":400000, "cap":"Large"},
    {"sym":"TATAMOTORS", "yf":"TATAMOTORS.NS",  "sector":"Auto",      "mcap":320000, "cap":"Large"},
    {"sym":"EICHERMOT",  "yf":"EICHERMOT.NS",   "sector":"Auto",      "mcap":365000, "cap":"Large"},
    {"sym":"HEROMOTOCO", "yf":"HEROMOTOCO.NS",  "sector":"Auto",      "mcap":100000, "cap":"Mid"},
    {"sym":"BAJAJ-AUTO", "yf":"BAJAJ-AUTO.NS",  "sector":"Auto",      "mcap":295000, "cap":"Large"},
    {"sym":"M&M",        "yf":"M&M.NS",         "sector":"Auto",      "mcap":380000, "cap":"Large"},
    {"sym":"TVSMOTORS",  "yf":"TVSMOTORS.NS",   "sector":"Auto",      "mcap":115000, "cap":"Mid"},
    {"sym":"BALKRISIND", "yf":"BALKRISIND.NS",  "sector":"Auto",      "mcap":38000,  "cap":"Small"},
    {"sym":"MOTHERSON",  "yf":"MOTHERSON.NS",   "sector":"Auto",      "mcap":88000,  "cap":"Mid"},
    {"sym":"SUNPHARMA",  "yf":"SUNPHARMA.NS",   "sector":"Pharma",    "mcap":420000, "cap":"Large"},
    {"sym":"DRREDDY",    "yf":"DRREDDY.NS",     "sector":"Pharma",    "mcap":105000, "cap":"Mid"},
    {"sym":"CIPLA",      "yf":"CIPLA.NS",       "sector":"Pharma",    "mcap":125000, "cap":"Mid"},
    {"sym":"DIVISLAB",   "yf":"DIVISLAB.NS",    "sector":"Pharma",    "mcap":132000, "cap":"Mid"},
    {"sym":"LUPIN",      "yf":"LUPIN.NS",       "sector":"Pharma",    "mcap":105000, "cap":"Mid"},
    {"sym":"AUROPHARMA", "yf":"AUROPHARMA.NS",  "sector":"Pharma",    "mcap":81000,  "cap":"Mid"},
    {"sym":"TORNTPHARM", "yf":"TORNTPHARM.NS",  "sector":"Pharma",    "mcap":56000,  "cap":"Mid"},
    {"sym":"ALKEM",      "yf":"ALKEM.NS",       "sector":"Pharma",    "mcap":32000,  "cap":"Small"},
    {"sym":"GLENMARK",   "yf":"GLENMARK.NS",    "sector":"Pharma",    "mcap":38000,  "cap":"Small"},
    {"sym":"IPCALAB",    "yf":"IPCALAB.NS",     "sector":"Pharma",    "mcap":22000,  "cap":"Small"},
    {"sym":"GRANULES",   "yf":"GRANULES.NS",    "sector":"Pharma",    "mcap":8000,   "cap":"Small"},
    {"sym":"APOLLOHOSP", "yf":"APOLLOHOSP.NS",  "sector":"Healthcare","mcap":110000, "cap":"Mid"},
    {"sym":"MAXHEALTH",  "yf":"MAXHEALTH.NS",   "sector":"Healthcare","mcap":35000,  "cap":"Small"},
    {"sym":"TATASTEEL",  "yf":"TATASTEEL.NS",   "sector":"Metal",     "mcap":195000, "cap":"Large"},
    {"sym":"JSWSTEEL",   "yf":"JSWSTEEL.NS",    "sector":"Metal",     "mcap":320000, "cap":"Large"},
    {"sym":"HINDALCO",   "yf":"HINDALCO.NS",    "sector":"Metal",     "mcap":230000, "cap":"Large"},
    {"sym":"COALINDIA",  "yf":"COALINDIA.NS",   "sector":"Metal",     "mcap":290000, "cap":"Large"},
    {"sym":"VEDL",       "yf":"VEDL.NS",        "sector":"Metal",     "mcap":112000, "cap":"Mid"},
    {"sym":"NMDC",       "yf":"NMDC.NS",        "sector":"Metal",     "mcap":27000,  "cap":"Small"},
    {"sym":"APLAPOLLO",  "yf":"APLAPOLLO.NS",   "sector":"Metal",     "mcap":28000,  "cap":"Small"},
    {"sym":"JINDALSTEL", "yf":"JINDALSTEL.NS",  "sector":"Metal",     "mcap":32000,  "cap":"Small"},
    {"sym":"HINDUNILVR", "yf":"HINDUNILVR.NS",  "sector":"FMCG",      "mcap":535000, "cap":"Large"},
    {"sym":"ITC",        "yf":"ITC.NS",         "sector":"FMCG",      "mcap":580000, "cap":"Large"},
    {"sym":"NESTLEIND",  "yf":"NESTLEIND.NS",   "sector":"FMCG",      "mcap":140000, "cap":"Mid"},
    {"sym":"TATACONSUM", "yf":"TATACONSUM.NS",  "sector":"FMCG",      "mcap":115000, "cap":"Mid"},
    {"sym":"MARICO",     "yf":"MARICO.NS",      "sector":"FMCG",      "mcap":103000, "cap":"Mid"},
    {"sym":"DABUR",      "yf":"DABUR.NS",       "sector":"FMCG",      "mcap":97000,  "cap":"Mid"},
    {"sym":"COLPAL",     "yf":"COLPAL.NS",      "sector":"FMCG",      "mcap":57000,  "cap":"Mid"},
    {"sym":"VBL",        "yf":"VBL.NS",         "sector":"FMCG",      "mcap":96000,  "cap":"Mid"},
    {"sym":"LT",         "yf":"LT.NS",          "sector":"Infra",     "mcap":500000, "cap":"Large"},
    {"sym":"ADANIENT",   "yf":"ADANIENT.NS",    "sector":"Infra",     "mcap":280000, "cap":"Large"},
    {"sym":"ADANIPORTS", "yf":"ADANIPORTS.NS",  "sector":"Infra",     "mcap":375000, "cap":"Large"},
    {"sym":"DLF",        "yf":"DLF.NS",         "sector":"Realty",    "mcap":148000, "cap":"Mid"},
    {"sym":"GODREJPROP", "yf":"GODREJPROP.NS",  "sector":"Realty",    "mcap":72000,  "cap":"Mid"},
    {"sym":"PRESTIGE",   "yf":"PRESTIGE.NS",    "sector":"Realty",    "mcap":58000,  "cap":"Mid"},
    {"sym":"JSWINFRA",   "yf":"JSWINFRA.NS",    "sector":"Infra",     "mcap":62000,  "cap":"Mid"},
    {"sym":"ULTRACEMCO", "yf":"ULTRACEMCO.NS",  "sector":"Cement",    "mcap":340000, "cap":"Large"},
    {"sym":"GRASIM",     "yf":"GRASIM.NS",      "sector":"Cement",    "mcap":185000, "cap":"Large"},
    {"sym":"AMBUJACEM",  "yf":"AMBUJACEM.NS",   "sector":"Cement",    "mcap":110000, "cap":"Mid"},
    {"sym":"BHARTIARTL", "yf":"BHARTIARTL.NS",  "sector":"Telecom",   "mcap":560000, "cap":"Large"},
    {"sym":"TITAN",      "yf":"TITAN.NS",       "sector":"Consumer",  "mcap":300000, "cap":"Large"},
    {"sym":"ASIANPAINT", "yf":"ASIANPAINT.NS",  "sector":"Consumer",  "mcap":215000, "cap":"Large"},
    {"sym":"TRENT",      "yf":"TRENT.NS",       "sector":"Retail",    "mcap":220000, "cap":"Large"},
    {"sym":"DMART",      "yf":"DMART.NS",       "sector":"Retail",    "mcap":265000, "cap":"Large"},
    {"sym":"ZOMATO",     "yf":"ZOMATO.NS",      "sector":"Retail",    "mcap":225000, "cap":"Large"},
    {"sym":"JUBLFOOD",   "yf":"JUBLFOOD.NS",    "sector":"Retail",    "mcap":30000,  "cap":"Small"},
    {"sym":"HAVELLS",    "yf":"HAVELLS.NS",     "sector":"Consumer",  "mcap":103000, "cap":"Mid"},
    {"sym":"VOLTAS",     "yf":"VOLTAS.NS",      "sector":"Consumer",  "mcap":42000,  "cap":"Small"},
    {"sym":"CROMPTON",   "yf":"CROMPTON.NS",    "sector":"Consumer",  "mcap":20000,  "cap":"Small"},
    {"sym":"PIDILITIND", "yf":"PIDILITIND.NS",  "sector":"Chemical",  "mcap":160000, "cap":"Mid"},
    {"sym":"SRF",        "yf":"SRF.NS",         "sector":"Chemical",  "mcap":56000,  "cap":"Mid"},
    {"sym":"DEEPAKNTR",  "yf":"DEEPAKNTR.NS",   "sector":"Chemical",  "mcap":43000,  "cap":"Small"},
    {"sym":"AARTIIND",   "yf":"AARTIIND.NS",    "sector":"Chemical",  "mcap":18000,  "cap":"Small"},
    {"sym":"NAVINFLUOR", "yf":"NAVINFLUOR.NS",  "sector":"Chemical",  "mcap":18000,  "cap":"Small"},
    {"sym":"BEL",        "yf":"BEL.NS",         "sector":"Defence",   "mcap":151000, "cap":"Mid"},
    {"sym":"HAL",        "yf":"HAL.NS",         "sector":"Defence",   "mcap":139000, "cap":"Mid"},
    {"sym":"BHEL",       "yf":"BHEL.NS",        "sector":"Defence",   "mcap":130000, "cap":"Mid"},
    {"sym":"COCHINSHIP", "yf":"COCHINSHIP.NS",  "sector":"Defence",   "mcap":24000,  "cap":"Small"},
    {"sym":"IRCTC",      "yf":"IRCTC.NS",       "sector":"PSU",       "mcap":46000,  "cap":"Small"},
    {"sym":"IRFC",       "yf":"IRFC.NS",        "sector":"PSU",       "mcap":81000,  "cap":"Mid"},
    {"sym":"PFC",        "yf":"PFC.NS",         "sector":"PSU",       "mcap":150000, "cap":"Mid"},
    {"sym":"REC",        "yf":"REC.NS",         "sector":"PSU",       "mcap":157000, "cap":"Mid"},
    {"sym":"RVNL",       "yf":"RVNL.NS",        "sector":"PSU",       "mcap":78000,  "cap":"Mid"},
    {"sym":"HUDCO",      "yf":"HUDCO.NS",       "sector":"PSU",       "mcap":40000,  "cap":"Small"},
    {"sym":"SIEMENS",    "yf":"SIEMENS.NS",     "sector":"CapGoods",  "mcap":255000, "cap":"Large"},
    {"sym":"ABB",        "yf":"ABB.NS",         "sector":"CapGoods",  "mcap":155000, "cap":"Mid"},
    {"sym":"CUMMINSIND", "yf":"CUMMINSIND.NS",  "sector":"CapGoods",  "mcap":55000,  "cap":"Mid"},
    {"sym":"THERMAX",    "yf":"THERMAX.NS",     "sector":"CapGoods",  "mcap":32000,  "cap":"Small"},
    {"sym":"UPL",        "yf":"UPL.NS",         "sector":"Agri",      "mcap":38000,  "cap":"Small"},
    {"sym":"PIIND",      "yf":"PIIND.NS",       "sector":"Agri",      "mcap":15000,  "cap":"Small"},
    {"sym":"COROMANDEL", "yf":"COROMANDEL.NS",  "sector":"Agri",      "mcap":33000,  "cap":"Small"},
    {"sym":"PAYTM",      "yf":"PAYTM.NS",       "sector":"FinTech",   "mcap":52000,  "cap":"Mid"},
    {"sym":"POLICYBZR",  "yf":"POLICYBZR.NS",   "sector":"FinTech",   "mcap":42000,  "cap":"Small"},
]

PRICES = {
    "HDFCBANK":1680,"ICICIBANK":1280,"SBIN":820,"AXISBANK":1180,"KOTAKBANK":1900,
    "INDUSINDBK":1450,"BANKBARODA":260,"PNB":105,"IDFCFIRSTB":72,"FEDERALBNK":195,
    "BAJFINANCE":6800,"BAJAJFINSV":1680,"SHRIRAMFIN":950,"CHOLAFIN":1640,"MUTHOOTFIN":2100,
    "HDFCAMC":4200,"BSE":6500,"CDSL":1230,"MCX":6500,"ANGELONE":2800,
    "SBILIFE":1810,"HDFCLIFE":600,"LICI":920,"ICICIGI":1760,"ICICIPRULI":535,
    "TCS":2450,"INFY":1560,"HCLTECH":1200,"WIPRO":620,"TECHM":1550,"LTIM":5200,
    "PERSISTENT":4820,"COFORGE":1165,"MPHASIS":2240,"KPITTECH":778,"TATAELXSI":6200,
    "RELIANCE":1310,"ONGC":270,"BPCL":320,"IOC":145,"GAIL":210,"IGL":168,
    "NTPC":360,"POWERGRID":320,"ADANIGREEN":1310,"TATAPOWER":445,"SUZLON":55,"TORNTPOWER":890,
    "MARUTI":13400,"TATAMOTORS":950,"EICHERMOT":13400,"HEROMOTOCO":5020,"BAJAJ-AUTO":10060,
    "M&M":3080,"TVSMOTORS":2400,"BALKRISIND":2400,"MOTHERSON":165,
    "SUNPHARMA":1800,"DRREDDY":6200,"CIPLA":1540,"DIVISLAB":6610,"LUPIN":2200,
    "AUROPHARMA":1385,"TORNTPHARM":3300,"ALKEM":5320,"GLENMARK":1350,"IPCALAB":1560,"GRANULES":495,
    "APOLLOHOSP":7690,"MAXHEALTH":1000,"TATASTEEL":155,"JSWSTEEL":1255,"HINDALCO":1040,
    "COALINDIA":475,"VEDL":302,"NMDC":89,"APLAPOLLO":1200,"JINDALSTEL":820,
    "HINDUNILVR":2350,"ITC":465,"NESTLEIND":1460,"TATACONSUM":1150,"MARICO":790,
    "DABUR":455,"COLPAL":2750,"VBL":580,"LT":3650,"ADANIENT":2480,"ADANIPORTS":1740,
    "DLF":600,"GODREJPROP":2800,"PRESTIGE":1435,"JSWINFRA":310,
    "ULTRACEMCO":11780,"GRASIM":2850,"AMBUJACEM":438,"BHARTIARTL":1820,
    "TITAN":3400,"ASIANPAINT":2250,"TRENT":6200,"DMART":4310,"ZOMATO":245,
    "JUBLFOOD":472,"HAVELLS":1650,"VOLTAS":1340,"CROMPTON":420,
    "PIDILITIND":3200,"SRF":2500,"DEEPAKNTR":1740,"AARTIIND":420,"NAVINFLUOR":3400,
    "BEL":434,"HAL":4640,"BHEL":382,"COCHINSHIP":1520,"IRCTC":572,"IRFC":106,
    "PFC":470,"REC":490,"RVNL":300,"HUDCO":210,"SIEMENS":7200,"ABB":7274,
    "CUMMINSIND":3200,"THERMAX":3400,"UPL":520,"PIIND":3010,"COROMANDEL":1900,
    "PAYTM":780,"POLICYBZR":1580,
}

# ── DATA ──
def fetch_ohlcv(yf_sym):
    df = yf.Ticker(yf_sym).history(period="1y",interval="1d",auto_adjust=True)
    if df.empty or len(df)<50: raise ValueError("Insufficient data")
    df = df[["Open","High","Low","Close","Volume"]].copy()
    df.columns = ["open","high","low","close","volume"]
    return df.dropna().reset_index(drop=True)

def demo_ohlcv(sym):
    rng = random.Random(hash(sym)%99991)
    np_rng = np.random.default_rng(hash(sym)%99991)
    bp = float(PRICES.get(sym, rng.uniform(100,5000)))
    char = hash(sym) % 10
    trend = 0.003 if char<3 else 0.001 if char<5 else 0.0001 if char<7 else -0.001
    closes = [bp * rng.uniform(0.55, 0.75)]
    for i in range(251):
        if 55<i<75 or 145<i<165:
            closes.append(max(closes[-1]*(1+np_rng.normal(0,0.005)), bp*0.2))
        else:
            closes.append(max(closes[-1]*(1+np_rng.normal(trend,0.013)), bp*0.2))
    rows = []
    for c in closes:
        sp = c*rng.uniform(0.007,0.025); h=c+sp*rng.uniform(0.4,1); l=c-sp*rng.uniform(0.4,1)
        vm = rng.uniform(1.5,3.0) if rng.random()<0.08 else rng.uniform(0.5,1.3)
        rows.append({"open":rng.uniform(l,h),"high":h,"low":l,"close":c,"volume":int(200000*vm*(bp/500))})
    return pd.DataFrame(rows)

# ── INDICATORS ──
def calc_ema(c,p):
    if len(c)<p: return float(c[-1])
    k=2/(p+1); e=float(c[-p])
    for v in c[-p+1:]: e=v*k+e*(1-k)
    return round(e,2)

def calc_rsi(c,p=14):
    if len(c)<p+2: return 50.0
    d=np.diff(c[-p*2:]); g=np.where(d>0,d,0.0); lo=np.where(d<0,-d,0.0)
    ag,al=g[-p:].mean(),lo[-p:].mean()
    if al==0: return 100.0
    return round(100-100/(1+ag/al),1)

def calc_atr(df,p=14):
    h,l,c=df["high"].values,df["low"].values,df["close"].values
    trs=[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(df))]
    return float(np.mean(trs[-p:])) if trs else c[-1]*0.018

# ── DARVAS BOX ──
def find_boxes(df):
    h=df["high"].values; l=df["low"].values; c=df["close"].values; n=len(df)
    boxes=[]; i=0
    while i<n-6:
        lh=h[i]
        if not all(h[i+1:i+4]<=lh): i+=1; continue
        ll=float(min(l[i:i+4]))
        if not all(l[i+1:i+4]>=ll*0.997): i+=1; continue
        if lh<=ll*1.005: i+=1; continue
        j=i+1; bc=1
        while j<n and h[j]<=lh and l[j]>=ll*0.996: bc+=1; j+=1
        if bc>=3:
            boxes.append({"ceiling":round(float(lh),2),"floor":round(float(ll),2),
                          "start":i,"end":j-1,"candles":bc,"broke_out":j<n and c[j]>lh})
        i=j
    return boxes

# ── MAIN ANALYSIS ──
def analyze(df, stock):
    if df is None or len(df)<60: return None
    c=df["close"].values; h=df["high"].values; l=df["low"].values; v=df["volume"].values; n=len(df)
    price=float(c[-1])
    w52h=float(h[-252:].max()) if n>=252 else float(h.max())
    w52l=float(l[-252:].min()) if n>=252 else float(l.min())
    from52h=round((w52h-price)/w52h*100,1)
    from52l=round((price-w52l)/w52l*100,1)
    pos52=round((price-w52l)/max(w52h-w52l,1)*100,1)
    near52h=from52h<=5.0; doubled=from52l>=100.0
    passes=near52h and doubled
    ema10=calc_ema(c,10); ema20=calc_ema(c,20)
    ema200=calc_ema(c,200) if n>=200 else calc_ema(c,min(n-1,50))
    above200=price>ema200
    rsi_val=calc_rsi(c); atr_val=calc_atr(df)
    rsi_buy=40<=rsi_val<=55; rsi_ok=rsi_val>=40; rsi_ob=rsi_val>=80
    avg_vol=float(np.mean(v[-20:])); vr=round(float(v[-1]/avg_vol),1) if avg_vol>0 else 1.0
    high_vol=vr>=1.5
    boxes=find_boxes(df)
    lb=boxes[-1] if boxes else None; pb=boxes[-2] if len(boxes)>=2 else None
    bc_ceil=lb["ceiling"] if lb else None; bc_floor=lb["floor"] if lb else None
    bc_cand=lb["candles"] if lb else 0
    active_bo=bool(bc_ceil and price>bc_ceil and high_vol)
    new52bo=price>=w52h*0.99 and high_vol
    recent_ranges=[(h[i]-l[i])/l[i]*100 for i in range(max(0,n-10),n)]
    avg_range=float(np.mean(recent_ranges)); range_contr=avg_range<2.0
    rs=round(price/float(np.mean(c[-20:])),3) if n>=20 else 1.0; strong_rs=rs>=1.02
    pyr={"add":round(bc_ceil*1.001,2),"sl":round(bc_floor,2),"box":len(boxes)} if (pb and lb and lb["ceiling"]>pb["ceiling"]) else None
    score=0; signals=[]
    if near52h: score+=25; signals.append({"s":"Near 52W High 📈","t":"BULL","d":f"Only {from52h}% below 52W high ₹{w52h:.0f} ✅"})
    if doubled:  score+=20; signals.append({"s":"2× from 52W Low 🚀","t":"BULL","d":f"+{from52l:.0f}% from low ₹{w52l:.0f} ✅"})
    elif from52l>=50: score+=8; signals.append({"s":f"+{from52l:.0f}% from Low","t":"BULL","d":f"Building strength from low"})
    if active_bo: score+=35; signals.append({"s":"BOX BREAKOUT 📦⬆️","t":"BULL","d":f"Above ceiling ₹{bc_ceil:.0f} Vol:{vr}x ✅ ENTER NOW"})
    elif lb and bc_floor and price>bc_floor:
        score+=10; signals.append({"s":f"Inside Box ({bc_cand}c) 📦","t":"WATCH","d":f"Box ₹{bc_floor:.0f}–₹{bc_ceil:.0f} — wait for breakout"})
    elif lb and bc_floor and price<bc_floor:
        score-=20; signals.append({"s":"Below Box Floor ⚠️","t":"BEAR","d":f"Below floor ₹{bc_floor:.0f} — SL triggered"})
    if new52bo: score+=15; signals.append({"s":"52W High Break 🎯","t":"BULL","d":f"At/near 52W high ₹{w52h:.0f} with volume"})
    if high_vol and active_bo: score+=10; signals.append({"s":f"High Vol {vr}x ✅","t":"BULL","d":f"Vol {vr}x avg — institutional confirmed"})
    elif vr>=2: score+=5; signals.append({"s":f"Vol Spike {vr}x 📊","t":"BULL","d":f"Unusual vol {vr}x"})
    if above200: score+=10; signals.append({"s":"Above 200 EMA ✅","t":"BULL","d":f"₹{price:.0f} > 200EMA ₹{ema200:.0f}"})
    else: score-=15; signals.append({"s":"Below 200 EMA ❌","t":"BEAR","d":"AmitabhJha avoids — wait for recovery"})
    if rsi_buy: score+=10; signals.append({"s":f"RSI {rsi_val} BUY ZONE","t":"BULL","d":"RSI 40-55 = DarvaX uptrend buy zone ✅"})
    elif rsi_ok: score+=5; signals.append({"s":f"RSI {rsi_val} OK","t":"BULL","d":"RSI above 40 = uptrend intact"})
    elif rsi_ob: score-=5; signals.append({"s":f"RSI {rsi_val} OVERBOUGHT","t":"WARN","d":"Near RSI 80 resistance — wait for pullback"})
    else: score-=10; signals.append({"s":f"RSI {rsi_val} AVOID","t":"BEAR","d":"Below RSI 40 — downtrend zone"})
    if range_contr and lb: score+=8; signals.append({"s":"Range Contraction 🔵","t":"BULL","d":f"Avg range {avg_range:.1f}% — energy coiling for breakout"})
    if strong_rs: score+=7; signals.append({"s":"Strong RS ⚡","t":"BULL","d":"Outperforming own average — high RS"})
    if pyr: score+=5; signals.append({"s":f"Pyramid #{pyr['box']} 🔺","t":"BULL","d":f"New box — add at ₹{pyr['add']}, trail SL ₹{pyr['sl']}"})
    score=max(-50,min(100,round(score)))
    trade=None
    if score>=25 and passes:
        entry=round((bc_ceil or price)*1.001,2)
        sl_box=round(bc_floor,2) if bc_floor else round(price*0.95,2)
        sl=sl_box if sl_box<entry else round(ema20,2)
        sl_pct=round((entry-sl)/entry*100,1) if entry>sl>0 else 3.0
        br=((bc_ceil or price)-(bc_floor or price*0.95)) if (bc_ceil and bc_floor) else price*0.05
        t1=round(entry+br,2); t2=round(entry+br*2,2); t3=round(entry+br*3.5,2)
        rr1=round((t1-entry)/(entry-sl),1) if entry>sl else 0
        rr2=round((t2-entry)/(entry-sl),1) if entry>sl else 0
        if active_bo: timing=f"ENTER NOW — ₹{bc_ceil:.0f} broken Vol:{vr}x ✅"
        elif new52bo: timing=f"ENTER NOW — 52W high ₹{w52h:.0f} breaking ✅"
        elif lb: timing=f"WAIT — Enter above ₹{bc_ceil:.0f} with high volume"
        else: timing=f"WATCH — Enter on high-volume breakout above ₹{entry:.0f}"
        trade={"entry":entry,"sl":sl,"sl_box":sl_box,"sl_10ema":round(ema10,2),
               "sl_20ema":round(ema20,2),"sl_pct":sl_pct,"t1":t1,"t2":t2,"t3":t3,
               "rr1":rr1,"rr2":rr2,"timing":timing,"add_on":pyr["add"] if pyr else t1,
               "ema10":ema10,"ema20":ema20,"ema200":ema200}
    pct_chg=round(((c[-1]-c[-2])/c[-2]*100) if len(c)>1 else 0,2)
    grade=("A" if passes and score>=60 else "B" if passes and score>=40
           else "C" if passes else "D" if near52h else "F")
    rsi_zone=("BUY" if rsi_buy else "OK" if rsi_ok else "WARN" if rsi_ob else "AVOID")
    return {"score":score,"grade":grade,"signals":signals,"price":round(price,2),
            "pct_chg":pct_chg,"w52h":round(w52h,2),"w52l":round(w52l,2),
            "from52h":from52h,"from52l":round(from52l,1),"pos52":pos52,
            "passes":passes,"near52h":near52h,"doubled":doubled,
            "boxes":len(boxes),"box_ceil":bc_ceil,"box_floor":bc_floor,"box_cand":bc_cand,
            "active_bo":active_bo,"new52bo":new52bo,"vr":vr,"high_vol":high_vol,
            "rsi":rsi_val,"rsi_zone":rsi_zone,"above200":above200,
            "ema10":ema10,"ema20":ema20,"ema200":ema200,
            "range_contr":range_contr,"avg_range":round(avg_range,1),"strong_rs":strong_rs,
            "pyr":pyr,"trade":trade,"atr":round(atr_val,2)}

# ── SECTOR RANK ──
def sector_rank(results):
    from collections import defaultdict
    d=defaultdict(list)
    for r in results:
        if r.get("a"): d[r["sector"]].append(r["a"]["score"])
    return dict(sorted({s:{"avg":round(sum(v)/len(v),1),"bull":sum(1 for x in v if x>=25),"count":len(v)}
                        for s,v in d.items()}.items(), key=lambda x:x[1]["avg"],reverse=True))

# ── PICKS ──
def picks(results, sr):
    valid=[r for r in results if r.get("a") and r["a"]["trade"]]
    def q(r):
        a=r["a"]; s=a["score"]; b=0
        if a["active_bo"]: b+=30
        if a["new52bo"]: b+=20
        if a["doubled"]: b+=15
        if a["high_vol"]: b+=10
        if a["range_contr"]: b+=8
        if a.get("cap") in ("Mid","Small"): b+=5
        sec_pos=list(sr.keys()).index(r["sector"]) if r["sector"] in sr else 99
        b+=max(0,15-sec_pos*2)
        return s+b
    ga=[r for r in valid if r["a"]["grade"]=="A"]
    gb=[r for r in valid if r["a"]["grade"]=="B"]
    ga.sort(key=q,reverse=True); gb.sort(key=q,reverse=True)
    seen=set(); top=[]
    for r in ga+gb:
        if r["sector"] not in seen: top.append(r); seen.add(r["sector"])
        if len(top)>=5: break
    watch=[r for r in results if r.get("a") and r["a"]["grade"] in ("B","C")
           and r["a"].get("boxes",0)>=1 and r["a"].get("near52h")][:6]
    return {"top":top,"ga":ga[:8],"gb":gb[:8],"watch":watch}

# ── AI ──
def ai_brief(pk, sr):
    if not OPENROUTER_API_KEY or not pk["top"]: return ""
    def fmt(r):
        a=r["a"]; t=a["trade"]
        return (f"{r['sym']} [{r['sector']}] Grade:{a['grade']} Cap:{r['cap']}\n"
                f"  CMP:₹{a['price']} {a['from52h']}%below52H +{a['from52l']}%from52L"
                f" RSI:{a['rsi']}({a['rsi_zone']}) Vol:{a['vr']}x Score:{a['score']}\n"
                f"  Boxes:{a['boxes']} {'BREAKOUT!' if a['active_bo'] else 'In box' if a['box_ceil'] else 'No box'}\n"
                f"  Entry:₹{t['entry']} SL:₹{t['sl']} T1:₹{t['t1']} T2:₹{t['t2']} RR:{t['rr1']}:1")
    top_s=list(sr.items())[:4]
    p=f"""You are AmitabhJha (@AmitabhJha3), the DarvaX trader. Your style: #DarvaXClassRooM, educational, enthusiastic.
Rules: buy near 52W high + 100%+ from low + box breakout + high volume + above 200EMA + RSI>40.

Top sectors: {', '.join(f"{s}({d['avg']:+.0f})" for s,d in top_s)}
Top setups:
{chr(10).join(fmt(r) for r in pk['top'])}

Write 180-word DarvaX brief for your community. Cover:
1. Best sector for DarvaX today + why
2. Top 2 picks — box number, entry, RSI situation, SL (which EMA)
3. One pyramid add-on opportunity
4. One stock on watchlist only (box forming, not broken yet)
Be specific with ₹ prices. Sound like a tweet thread. Max 180 words."""
    print("  🤖 Calling AI for DarvaX brief...")
    return call_ai(p,800) or ""

# ── SCAN ──
def run_scan(stocks, demo=False, verbose=True):
    results=[]; total=len(stocks)
    for idx,stock in enumerate(stocks):
        sym=stock["sym"]; pct=int((idx+1)/total*100)
        bar="█"*(pct//5)+"░"*(20-pct//5)
        if verbose: print(f"\r  [{bar}] {pct:3d}%  {sym:<14}",end="",flush=True)
        try:
            df=demo_ohlcv(sym) if demo else fetch_ohlcv(stock["yf"])
            a=analyze(df,stock)
            result={**stock,"a":a,"error":None}
            if verbose and a:
                grade=a["grade"]; bo="📦BO!" if a["active_bo"] else "📦" if a["box_ceil"] else "   "
                print(f"\r  ✓ {sym:<14} [{grade}] {a['score']:+4d}  {bo}  "
                      f"RSI:{str(a['rsi']):<5}  {a['from52h']}%below52H  Vol:{a['vr']}x",flush=True)
        except Exception as e:
            result={**stock,"a":None,"error":str(e)}
            if verbose: print(f"\r  ✗ {sym:<14} {str(e)[:45]}",flush=True)
        results.append(result)
        if not demo: time.sleep(0.12)
    if verbose: print()
    return results

# ── HTML ──
GC={"A":"#00e5a0","B":"#4ade80","C":"#f5c842","D":"#f97316","F":"#f56060"}
SC={"BULL":"#00e5a0","BEAR":"#f56060","WATCH":"#f5c842","WARN":"#f97316"}

def build_html(results,meta,pk,sr,ai_text):
    valid=[r for r in results if r.get("a")]
    errors=[r for r in results if r.get("error")]
    ga_ct=sum(1 for r in valid if r["a"]["grade"]=="A")
    gb_ct=sum(1 for r in valid if r["a"]["grade"]=="B")
    n52h=sum(1 for r in valid if r["a"].get("near52h"))
    bos=sum(1 for r in valid if r["a"].get("active_bo"))
    dbl=sum(1 for r in valid if r["a"].get("doubled"))
    st=meta.get("scan_time","—"); mode=("DEMO" if meta.get("demo") else "LIVE · YAHOO FINANCE")
    aim=(OPENROUTER_MODEL.split("/")[1].split(":")[0] if OPENROUTER_API_KEY else "Rule-Based")
    sorted_r=sorted(valid,key=lambda r:r["a"]["score"],reverse=True)
    sectors=list(sr.keys())

    def pc(r):
        a=r["a"]; t=a.get("trade") or {}; gc=GC.get(a["grade"],"#304560")
        bo_b='<span class="mb bo-b">📦 BREAKOUT</span>' if a.get("active_bo") else ""
        h52_b='<span class="mb h52-b">🎯 52W HIGH</span>' if a.get("new52bo") else ""
        dbl_b='<span class="mb dbl-b">🚀 2× FROM LOW</span>' if a.get("doubled") else ""
        pyr_b='<span class="mb pyr-b">🔺 PYRAMID</span>' if a.get("pyr") else ""
        rc="#00e5a0" if a["rsi_zone"]=="BUY" else "#f5c842" if a["rsi_zone"]=="OK" else "#f97316"
        sh="".join(f'<div class="ps"><span style="color:{SC.get(s["t"],"#f5c842")}">◆ {s["s"]}</span><span class="pd">{s["d"]}</span></div>' for s in a["signals"][:5])
        bi=f'Box ₹{a["box_floor"]:.0f}–₹{a["box_ceil"]:.0f} ({a["box_cand"]}c)' if a.get("box_ceil") else "No box yet"
        return f"""<div class="pc">
          <div class="pct"><div><span class="psym">{r['sym']}</span><span class="psec">{r['sector']} · {r['cap']}</span></div>
            <div style="text-align:right"><span class="pg" style="background:{gc}20;color:{gc};border:1px solid {gc}40">Grade {a['grade']}</span>
              <div class="psc" style="color:{gc}">{a['score']:+d}</div></div></div>
          <div class="pbd">{bo_b}{h52_b}{dbl_b}{pyr_b}</div>
          <div class="pcm">CMP ₹{a['price']:,.2f} <span style="color:{'#00e5a0' if a['pct_chg']>=0 else '#f56060'}">{a['pct_chg']:+.2f}%</span>
            · RSI <span style="color:{rc}">{a['rsi']} ({a['rsi_zone']})</span> · Vol {a['vr']}x</div>
          <div class="p52">52W: ₹{a['w52l']:.0f} — {a['pos52']:.0f}% — ₹{a['w52h']:.0f} · {a['from52h']}% below high · +{a['from52l']}% from low</div>
          <div class="pbi">{bi} · {a['boxes']} box{'es' if a['boxes']!=1 else ''}</div>
          <div class="pl"><span class="pll" style="color:#2d7ff9">ENTRY</span><span class="plv" style="color:#2d7ff9">₹{t.get('entry','—')}</span></div>
          <div class="pl"><span class="pll" style="color:#f56060">SL BOX FLOOR</span><span class="plv" style="color:#f56060">₹{t.get('sl_box','—')}</span></div>
          <div class="pl"><span class="pll" style="color:#f97316">SL 10EMA (Swing)</span><span class="plv" style="color:#f97316">₹{t.get('sl_10ema','—')}</span></div>
          <div class="pl"><span class="pll" style="color:#f97316">SL 20EMA (Positional)</span><span class="plv" style="color:#f97316">₹{t.get('sl_20ema','—')}</span></div>
          <div class="pl"><span class="pll" style="color:#86efac">T1 (1× range)</span><span class="plv" style="color:#86efac">₹{t.get('t1','—')} · RR {t.get('rr1','—')}:1</span></div>
          <div class="pl"><span class="pll" style="color:#00e5a0">T2 (next box)</span><span class="plv" style="color:#00e5a0">₹{t.get('t2','—')} · RR {t.get('rr2','—')}:1</span></div>
          <div class="pl"><span class="pll" style="color:#f5c842">T3 (multibagger)</span><span class="plv" style="color:#f5c842">₹{t.get('t3','—')}</span></div>
          <div class="pl"><span class="pll" style="color:#9d7cfc">PYRAMID ADD-ON</span><span class="plv" style="color:#9d7cfc">₹{t.get('add_on','—')}</span></div>
          <div class="pt">⏰ {t.get('timing','—')}</div>
          <div class="pss">{sh}</div></div>"""

    top_h="".join(pc(r) for r in pk["top"])
    ga_h ="".join(pc(r) for r in pk["ga"])
    gb_h ="".join(pc(r) for r in pk["gb"])
    no='<div class="np">No qualifying setups. Market may be extended — wait for next breakout.</div>'
    watch_h="".join(f'<div class="pc" style="opacity:.8"><div class="pct"><div><span class="psym">{r["sym"]}</span><span class="psec">{r["sector"]} · {r["a"]["grade"]}</span></div><span class="psc" style="color:#f5c842">{r["a"]["score"]:+d}</span></div><div class="pcm">₹{r["a"]["price"]:,.2f} · RSI {r["a"]["rsi"]} · {r["a"]["from52h"]}% below 52H · {r["a"]["boxes"]} boxes</div><div class="pt">👁 Box forming — wait for high-vol breakout above ₹{r["a"].get("box_ceil","—")}</div></div>' for r in pk["watch"]) or no
    sb="".join(f'<div class="sb"><div class="sbt"><span>{s}</span><span style="color:{"#00e5a0" if d["avg"]>=0 else "#f56060"}">{d["avg"]:+.0f}</span></div><div class="sbtr"><div class="sbf" style="width:{min(100,max(0,(d["avg"]+50)/1.5))}%;background:{"#00e5a0" if d["avg"]>=0 else "#f56060"}"></div></div><div class="sbs">{d["bull"]} setups · {d["count"]} scanned</div></div>' for s,d in list(sr.items())[:14])
    secb="".join(f'<button class="fb" onclick="fSec(this,\'{s}\')">{s}</button>' for s in sectors)

    def rh(r,rank):
        a=r["a"]; t=a.get("trade") or {}
        gc=GC.get(a["grade"],"#304560"); ri=["🥇","🥈","🥉"][rank-1] if rank<=3 else f"#{rank}"
        up=a["pct_chg"]>=0; rc="#00e5a0" if a["rsi_zone"]=="BUY" else "#f5c842" if a["rsi_zone"]=="OK" else "#f97316"
        bo_ic="📦⬆" if a.get("active_bo") else "📦" if a.get("box_ceil") else "  "
        chips="".join(f'<span class="chip" style="color:{SC.get(s["t"],"#f5c842")};background:{SC.get(s["t"],"#f5c842")}18;border:1px solid {SC.get(s["t"],"#f5c842")}28">{s["s"]}</span>' for s in a["signals"][:3]) or '<span class="chip" style="color:#304560">Scanning</span>'
        sd="".join(f'<div class="sr"><span style="color:{SC.get(s["t"],"#f5c842")}">◆</span><span style="color:{SC.get(s["t"],"#f5c842")};font-family:var(--mono);font-size:10px"> {s["s"]} — {s["d"]}</span></div>' for s in a["signals"]) or '<div style="color:#304560;font-size:10px;font-family:var(--mono)">No signals</div>'
        th=""
        if t:
            th=f"""<div class="tb"><div class="tbh"><span style="color:#00e5a0;font-weight:600">LONG SETUP</span><span class="tbt">{t.get('timing','—')}</span></div>
              <div class="tbg">
                <div class="tbc ebg"><div class="tbl">ENTRY</div><div class="tbv" style="color:#2d7ff9">₹{t.get('entry','—')}</div></div>
                <div class="tbc slbg"><div class="tbl">SL — Box Floor ({t.get('sl_pct','—')}%)</div><div class="tbv" style="color:#f56060">₹{t.get('sl_box','—')}</div></div>
                <div class="tbc"><div class="tbl">SL — 10 EMA Swing</div><div class="tbv" style="color:#f97316">₹{t.get('sl_10ema','—')}</div></div>
                <div class="tbc"><div class="tbl">SL — 20 EMA Positional</div><div class="tbv" style="color:#f97316">₹{t.get('sl_20ema','—')}</div></div>
                <div class="tbc"><div class="tbl">T1 · 1× Box Range</div><div class="tbv" style="color:#86efac">₹{t.get('t1','—')} · RR {t.get('rr1','—')}:1</div></div>
                <div class="tbc"><div class="tbl">T2 · Next Box Target</div><div class="tbv" style="color:#00e5a0">₹{t.get('t2','—')} · RR {t.get('rr2','—')}:1</div></div>
                <div class="tbc"><div class="tbl">T3 · Multibagger Trail</div><div class="tbv" style="color:#f5c842">₹{t.get('t3','—')}</div></div>
                <div class="tbc"><div class="tbl">Pyramid Add-On</div><div class="tbv" style="color:#9d7cfc">₹{t.get('add_on','—')}</div></div>
              </div>
              <div class="tbf">EMA10: ₹{t.get('ema10','—')} · EMA20: ₹{t.get('ema20','—')} · EMA200: ₹{t.get('ema200','—')} · 200EMA: {'✅ Above' if a.get('above200') else '❌ Below'}</div>
              <div class="tb5">52W High: ₹{a['w52h']} · 52W Low: ₹{a['w52l']} · {a['from52h']}% below · +{a['from52l']}% from low · {a['boxes']} boxes</div></div>"""
        return f"""<div class="row" data-score="{a['score']}" data-sector="{r['sector']}" data-grade="{a['grade']}" data-bo="{'1' if a.get('active_bo') else '0'}" data-flt="{'1' if a.get('passes') else '0'}" data-cap="{r.get('cap','')}">
          <div class="rm" onclick="tog('{r['sym']}_{rank}')">
            <div class="rnk">{ri}</div>
            <div><div class="sym">{r['sym']} <span style="font-size:9px">{bo_ic}</span></div><div class="stag">{r['sector']} · {r.get('cap','')}</div></div>
            <div class="gp" style="color:{gc};background:{gc}20;border:1px solid {gc}40">{a['grade']}<br><span style="font-size:10px">{a['score']:+d}</span></div>
            <div class="cchips">{chips}</div>
            <div class="cprice"><div class="price">₹{a['price']:,.1f}</div><div style="font-family:var(--mono);font-size:9px;color:{'#00e5a0' if up else '#f56060'}">{'+' if up else ''}{a['pct_chg']}%</div></div>
            <div class="r52w"><div style="font-size:10px;color:#f5c842">{a['from52h']}% below 52H</div><div style="font-size:9px;color:{'#00e5a0' if a['doubled'] else '#304560'}">+{a['from52l']}% from low</div></div>
            <div class="rrsi"><div style="color:{rc};font-family:var(--mono);font-size:11px">{a['rsi']}</div><div style="font-size:8px;color:{rc}">{a['rsi_zone']}</div></div>
            <div style="font-family:var(--mono);font-size:9px;text-align:right;color:{'#f5c842' if float(a['vr'])>=1.5 else '#304560'}">{a['vr']}x</div>
            <div class="ei" id="ei-{r['sym']}_{rank}">▼</div>
          </div>
          <div class="rd" id="det-{r['sym']}_{rank}" style="display:none">
            <div class="d3c"><div><div class="dt">DARVAX SIGNALS ({len(a['signals'])})</div>{sd}</div><div>{th}</div><div></div></div>
          </div></div>"""

    rows_h="".join(rh(r,i+1) for i,r in enumerate(sorted_r))
    err_h=f'<div class="err">⚠ {len(errors)} errors: {", ".join(r["sym"] for r in errors[:8])}</div>' if errors else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DarvaX Scanner — {st}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--bg:#03050a;--s1:#07090f;--s2:#090d17;--b1:#111a28;--b2:#172235;
  --tx:#c8daf5;--mu:#2a3f58;--g:#00e5a0;--b:#2d7ff9;--y:#f5c842;--r:#f56060;--o:#f97316;--p:#9d7cfc;
  --mono:'JetBrains Mono',monospace;--dis:'Orbitron',monospace;--body:'Rajdhani',sans-serif;}}
body{{background:var(--bg);font-family:var(--body);color:var(--tx);min-height:100vh;font-size:15px;}}
body::before{{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:radial-gradient(ellipse 80% 60% at 50% -10%,rgba(0,229,160,.04) 0%,transparent 60%);}}
body::after{{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,229,160,.004) 3px,rgba(0,229,160,.004) 4px);}}
.w{{max-width:1350px;margin:0 auto;padding:14px 12px 60px;position:relative;z-index:1;}}
.hdr{{text-align:center;padding:22px 0 16px;border-bottom:1px solid var(--b1);margin-bottom:16px;background:radial-gradient(ellipse 70% 100% at 50% 0%,rgba(0,229,160,.04) 0%,transparent 70%);}}
.hb{{font-family:var(--mono);font-size:9px;letter-spacing:.2em;color:var(--g);border:1px solid rgba(0,229,160,.2);padding:3px 12px;border-radius:20px;display:inline-flex;align-items:center;gap:5px;margin-bottom:9px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--g);animation:bl 1s infinite;}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
h1{{font-family:var(--dis);font-size:clamp(14px,3.5vw,32px);font-weight:900;letter-spacing:.1em;background:linear-gradient(90deg,#f5c842 0%,#00e5a0 40%,#2d7ff9 80%,#9d7cfc 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.hs{{font-family:var(--mono);font-size:9px;color:var(--mu);letter-spacing:.07em;margin-top:5px;line-height:1.8;}}
.mr{{display:flex;justify-content:center;gap:10px;margin-top:10px;flex-wrap:wrap;}}
.mt{{font-family:var(--mono);font-size:9px;color:var(--mu);padding:3px 10px;border:1px solid var(--b2);border-radius:4px;}}
.mt span{{color:var(--g);font-weight:600;}}
.rules{{background:var(--s1);border:1px solid rgba(245,200,66,.2);border-radius:10px;padding:13px 16px;margin-bottom:16px;}}
.rt{{font-family:var(--mono);font-size:9px;color:var(--y);text-transform:uppercase;letter-spacing:.16em;margin-bottom:10px;}}
.rg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:7px;}}
.ri{{display:flex;gap:7px;align-items:flex-start;}}
.rn{{width:20px;height:20px;border-radius:50%;background:rgba(245,200,66,.15);color:var(--y);font-family:var(--mono);font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.rx{{font-size:11px;line-height:1.5;}}
.rx strong{{color:var(--tx);display:block;}}
.rx span{{color:var(--mu);}}
.ai-box{{background:var(--s1);border:1px solid rgba(0,229,160,.2);border-radius:10px;padding:13px 16px;margin-bottom:16px;}}
.at{{font-family:var(--mono);font-size:9px;color:var(--g);text-transform:uppercase;letter-spacing:.16em;margin-bottom:8px;}}
.atx{{font-family:var(--mono);font-size:11.5px;color:#3a6050;line-height:1.9;white-space:pre-wrap;}}
.aph{{font-family:var(--mono);font-size:10px;color:var(--mu);padding:8px;border:1px dashed var(--b2);border-radius:5px;}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:6px;margin-bottom:14px;}}
.stat{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;padding:8px 11px;text-align:center;}}
.stl{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.14em;margin-bottom:3px;}}
.stv{{font-family:var(--dis);font-size:19px;font-weight:700;}}
.picks{{margin-bottom:20px;}}
.ptit{{font-family:var(--dis);font-size:clamp(13px,2.5vw,22px);letter-spacing:.1em;text-align:center;background:linear-gradient(90deg,#f5c842,#00e5a0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:4px;}}
.psub{{font-family:var(--mono);font-size:9px;color:var(--mu);text-align:center;-webkit-text-fill-color:var(--mu);margin-bottom:14px;display:block;}}
.ptabs{{display:flex;gap:7px;margin-bottom:12px;flex-wrap:wrap;}}
.ptab{{padding:6px 14px;border-radius:6px;border:1px solid var(--b2);background:var(--s1);color:var(--mu);font-family:var(--mono);font-size:9px;letter-spacing:.07em;cursor:pointer;transition:all .13s;}}
.ptab:hover,.ptab.on{{border-color:var(--g);color:var(--g);background:rgba(0,229,160,.07);}}
.pg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px;}}
.pc{{background:var(--s1);border:1px solid var(--b2);border-radius:10px;padding:14px;}}
.pct{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:7px;}}
.psym{{font-family:var(--dis);font-size:17px;font-weight:900;color:#fff;letter-spacing:.05em;}}
.psec{{font-family:var(--mono);font-size:8px;color:var(--mu);display:block;margin-top:2px;}}
.pg2{{font-family:var(--dis);font-size:10px;padding:3px 8px;border-radius:5px;display:block;text-align:center;letter-spacing:.08em;}}
.psc{{font-family:var(--dis);font-size:20px;font-weight:900;text-align:right;}}
.pbd{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px;}}
.mb{{font-family:var(--mono);font-size:8px;padding:2px 7px;border-radius:4px;}}
.bo-b{{background:rgba(0,229,160,.15);color:var(--g);border:1px solid rgba(0,229,160,.3);}}
.h52-b{{background:rgba(245,200,66,.12);color:var(--y);border:1px solid rgba(245,200,66,.25);}}
.dbl-b{{background:rgba(45,127,249,.12);color:var(--b);border:1px solid rgba(45,127,249,.25);}}
.pyr-b{{background:rgba(157,124,252,.12);color:var(--p);border:1px solid rgba(157,124,252,.25);}}
.pcm{{font-family:var(--mono);font-size:11px;color:var(--tx);margin-bottom:5px;}}
.p52{{font-family:var(--mono);font-size:9px;color:var(--mu);margin-bottom:4px;padding:4px 6px;background:rgba(245,200,66,.04);border-radius:4px;}}
.pbi{{font-family:var(--mono);font-size:9px;color:var(--mu);margin-bottom:7px;}}
.pl{{display:grid;grid-template-columns:160px 1fr;gap:4px;align-items:baseline;margin-bottom:3px;}}
.pll{{font-family:var(--mono);font-size:8px;text-transform:uppercase;letter-spacing:.09em;}}
.plv{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.pt{{font-family:var(--mono);font-size:10px;color:var(--y);margin:7px 0;padding:5px 7px;background:rgba(245,200,66,.05);border-radius:5px;border-left:2px solid rgba(245,200,66,.3);}}
.pss{{display:flex;flex-direction:column;gap:4px;}}
.ps{{display:flex;gap:6px;align-items:flex-start;}}
.pd{{font-family:var(--mono);font-size:9px;color:var(--mu);margin-left:4px;line-height:1.5;}}
.np{{font-family:var(--mono);font-size:11px;color:var(--mu);text-align:center;padding:24px;border:1px dashed var(--b2);border-radius:8px;}}
.sec-s{{background:var(--s1);border:1px solid var(--b1);border-radius:9px;padding:12px 14px;margin-bottom:14px;}}
.sect{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.16em;margin-bottom:10px;}}
.sec-bars{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:7px;}}
.sb{{display:flex;flex-direction:column;gap:2px;}}
.sbt{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;}}
.sbtr{{height:4px;background:var(--b2);border-radius:2px;overflow:hidden;}}
.sbf{{height:100%;border-radius:2px;}}
.sbs{{font-family:var(--mono);font-size:8px;color:var(--mu);}}
.ctrl{{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-bottom:7px;}}
.ctrl-lbl{{font-family:var(--mono);font-size:8px;color:var(--mu);letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;}}
.fb{{padding:5px 10px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);color:var(--mu);font-family:var(--mono);font-size:9px;cursor:pointer;transition:all .12s;text-transform:uppercase;white-space:nowrap;}}
.fb:hover,.fb.on{{border-color:var(--g);color:var(--g);background:rgba(0,229,160,.07);}}
.si{{padding:6px 12px;border-radius:5px;border:1px solid var(--b2);background:var(--s1);color:var(--tx);font-family:var(--mono);font-size:11px;outline:none;min-width:130px;}}
.si:focus{{border-color:var(--g);}}
.si::placeholder{{color:var(--mu);}}
.th{{display:grid;grid-template-columns:32px 115px 60px 1fr 95px 110px 60px 60px 20px;gap:5px;padding:6px 10px;font-family:var(--mono);font-size:7px;text-transform:uppercase;letter-spacing:.12em;color:var(--mu);border-bottom:1px solid var(--b1);margin-bottom:3px;}}
.results{{display:flex;flex-direction:column;gap:4px;}}
.row{{background:var(--s1);border:1px solid var(--b1);border-radius:7px;overflow:hidden;}}
.rm{{display:grid;grid-template-columns:32px 115px 60px 1fr 95px 110px 60px 60px 20px;gap:5px;padding:8px 10px;align-items:center;cursor:pointer;transition:background .12s;}}
.rm:hover{{background:var(--s2);}}
.rnk{{font-family:var(--dis);font-size:10px;color:var(--mu);text-align:center;}}
.sym{{font-family:var(--dis);font-size:13px;font-weight:700;color:#fff;letter-spacing:.04em;}}
.stag{{font-family:var(--mono);font-size:8px;color:var(--mu);margin-top:1px;}}
.gp{{font-family:var(--dis);font-size:11px;font-weight:700;padding:3px 6px;border-radius:5px;text-align:center;}}
.cchips{{display:flex;flex-wrap:wrap;gap:2px;}}
.chip{{font-family:var(--mono);font-size:8px;padding:2px 5px;border-radius:3px;font-weight:600;white-space:nowrap;}}
.cprice{{text-align:right;}}
.price{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.r52w{{font-family:var(--mono);font-size:9px;text-align:center;}}
.rrsi{{text-align:center;}}
.ei{{color:var(--mu);font-size:9px;text-align:center;transition:transform .17s;}}
.rd{{border-top:1px solid var(--b1);padding:12px 10px;background:rgba(3,5,10,.65);}}
.d3c{{display:grid;grid-template-columns:1fr 1.4fr 1fr;gap:12px;}}
@media(max-width:950px){{.d3c,.th,.rm{{grid-template-columns:1fr;}}}}
.dt{{font-family:var(--mono);font-size:8px;color:var(--mu);text-transform:uppercase;letter-spacing:.12em;margin-bottom:7px;}}
.sr{{display:flex;gap:5px;align-items:flex-start;margin-bottom:5px;}}
.tb{{background:rgba(7,9,15,.8);border:1px solid var(--b2);border-radius:7px;overflow:hidden;}}
.tbh{{padding:7px 11px;border-bottom:1px solid var(--b1);display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:10px;flex-wrap:wrap;}}
.tbt{{font-family:var(--mono);font-size:9px;color:var(--y);flex:1;}}
.tbg{{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:7px 10px;}}
.tbc{{background:var(--s2);border:1px solid var(--b1);border-radius:4px;padding:5px 8px;}}
.tbc.ebg{{border-color:rgba(45,127,249,.2);}} .tbc.slbg{{border-color:rgba(245,96,96,.2);}}
.tbl{{font-family:var(--mono);font-size:7px;color:var(--mu);text-transform:uppercase;letter-spacing:.09em;margin-bottom:2px;}}
.tbv{{font-family:var(--mono);font-size:12px;font-weight:600;}}
.tbf{{font-family:var(--mono);font-size:9px;color:var(--mu);padding:5px 10px;border-top:1px solid var(--b1);}}
.tb5{{font-family:var(--mono);font-size:9px;color:#304560;padding:4px 10px;}}
.err{{font-family:var(--mono);font-size:9px;color:var(--mu);padding:6px 10px;margin-top:5px;}}
.dis{{text-align:center;font-family:var(--mono);font-size:8px;color:#0d1820;margin-top:28px;line-height:2;}}
::-webkit-scrollbar{{width:3px;height:3px;}}
::-webkit-scrollbar-track{{background:var(--b1);}}
::-webkit-scrollbar-thumb{{background:var(--b2);border-radius:2px;}}
</style>
</head>
<body><div class="w">
<div class="hdr">
  <div class="hb"><span class="dot"></span>DARVAX SCANNER · @AmitabhJha3 · #DarvaXClassRooM</div>
  <h1>DARVAX SCANNER — NIFTY 500</h1>
  <div class="hs">52W High Filter · Darvas Box · Volume Breakout · RSI 40/80 · 200 EMA · EMA 10/20 SL · Pyramiding</div>
  <div class="mr">
    <div class="mt">SCANNED <span>{len(valid)}</span></div>
    <div class="mt">GRADE A <span>{ga_ct}</span></div>
    <div class="mt">GRADE B <span>{gb_ct}</span></div>
    <div class="mt">NEAR 52H <span>{n52h}</span></div>
    <div class="mt">BREAKOUTS <span>{bos}</span></div>
    <div class="mt">2× FROM LOW <span>{dbl}</span></div>
    <div class="mt">AI <span>{aim}</span></div>
    <div class="mt">SCAN <span>{st}</span></div>
  </div>
</div>
<div class="rules">
  <div class="rt">📖 AMITABHJHA (@AmitabhJha3) — DARVAX RULES</div>
  <div class="rg">
    <div class="ri"><div class="rn">1</div><div class="rx"><strong>52W High Filter (Must Pass)</strong><span>Within 5% of 52W high AND 100%+ above 52W low. Only buy strong stocks going higher.</span></div></div>
    <div class="ri"><div class="rn">2</div><div class="rx"><strong>Darvas Box Detection</strong><span>Min 3 candles: ceiling holds 3 days, floor holds 3 days. Entry above ceiling only.</span></div></div>
    <div class="ri"><div class="rn">3</div><div class="rx"><strong>High Volume Breakout</strong><span>Vol ≥1.5× avg. Low volume breakout = false signal. AmitabhJha's critical filter.</span></div></div>
    <div class="ri"><div class="rn">4</div><div class="rx"><strong>RSI 40/80 Rule #DarvaXClassRooM</strong><span>Uptrend: RSI 40 = support (BUY ZONE), RSI 80 = resistance. Exit only on DCB below 40.</span></div></div>
    <div class="ri"><div class="rn">5</div><div class="rx"><strong>200 EMA Trend Filter</strong><span>Price MUST be above 200 EMA. Don't fight the trend.</span></div></div>
    <div class="ri"><div class="rn">6</div><div class="rx"><strong>EMA Stop Loss</strong><span>5EMA=very short · 10EMA=swing · 20EMA=positional · 200EMA=investor. Exit on Daily Close Below (DCB) only.</span></div></div>
    <div class="ri"><div class="rn">7</div><div class="rx"><strong>Pyramiding — Add to Winners</strong><span>New box above old box → add position. Trail SL to new box floor. Ride winners.</span></div></div>
    <div class="ri"><div class="rn">8</div><div class="rx"><strong>Mid + Small Cap Preferred</strong><span>Bigger moves. CANSLIM fundamentals: high EPS growth, industry leader, high RS.</span></div></div>
  </div>
</div>
<div class="ai-box">
  <div class="at">🤖 DARVAX AI BRIEF — {aim}</div>
  {f'<div class="atx">{ai_text}</div>' if ai_text else '<div class="aph">Set OPENROUTER_API_KEY for AmitabhJha-style AI brief. Free at openrouter.ai → use deepseek/deepseek-r1:free</div>'}
</div>
<div class="stats">
  {''.join(f'<div class="stat"><div class="stl">{l}</div><div class="stv" style="color:{c}">{v}</div></div>' for l,v,c in [
    ("Scanned",len(valid),"var(--b)"),("Grade A",ga_ct,"var(--g)"),("Grade B",gb_ct,"#4ade80"),
    ("Near 52H",n52h,"var(--y)"),("Breakouts",bos,"var(--g)"),("2× Low",dbl,"var(--b)"),("Mode",mode,"var(--mu)")])}
</div>
<div class="picks">
  <div class="ptit">📦 TODAY'S DARVAX SETUPS</div>
  <div class="psub">AmitabhJha's "Only buy stocks at NEW HIGHS with HIGH VOLUME" · Grade A = all filters · Grade B = most filters</div>
  <div class="ptabs">
    <button class="ptab on" onclick="sp('top',this)">⭐ TOP PICKS ({len(pk['top'])})</button>
    <button class="ptab" onclick="sp('a',this)">🟢 GRADE A ({len(pk['ga'])})</button>
    <button class="ptab" onclick="sp('b',this)">🟡 GRADE B ({len(pk['gb'])})</button>
    <button class="ptab" onclick="sp('w',this)">👁 WATCHLIST ({len(pk['watch'])})</button>
  </div>
  <div id="p-top" class="pg">{top_h or no}</div>
  <div id="p-a"   class="pg" style="display:none">{ga_h or no}</div>
  <div id="p-b"   class="pg" style="display:none">{gb_h or no}</div>
  <div id="p-w"   class="pg" style="display:none">{watch_h}</div>
</div>
<div class="sec-s">
  <div class="sect">⚡ SECTOR STRENGTH — AmitabhJha: trade strongest sector stocks</div>
  <div class="sec-bars">{sb}</div>
</div>
<div class="ctrl">
  <span class="ctrl-lbl">Filter:</span>
  <button class="fb on" onclick="fF(this,'all')">ALL</button>
  <button class="fb" onclick="fF(this,'flt')">✅ Passes 52W Filter</button>
  <button class="fb" onclick="fF(this,'bo')">📦 Breakout</button>
  <button class="fb" onclick="fF(this,'a')">Grade A</button>
  <button class="fb" onclick="fF(this,'ab')">Grade A+B</button>
  <button class="fb" onclick="fF(this,'mid')">Mid Cap</button>
  <button class="fb" onclick="fF(this,'small')">Small Cap</button>
  <input class="si" placeholder="Search symbol…" oninput="fS(this.value)">
</div>
<div class="ctrl" style="margin-bottom:12px;gap:4px">
  <span class="ctrl-lbl">Sector:</span>
  <button class="fb on" onclick="fSec(this,'ALL')">ALL</button>
  {secb}
</div>
<div class="th"><div>#</div><div>STOCK</div><div>GRADE</div><div>DARVAX SIGNALS</div><div>PRICE</div><div>52W POSITION</div><div>RSI</div><div>VOL</div><div></div></div>
<div class="results" id="rc">{rows_h}</div>
{err_h}
<div class="dis">DARVAX METHODOLOGY · @AmitabhJha3 #DarvaXClassRooM · DATA: {mode} · {len(valid)} STOCKS<br>EDUCATIONAL PURPOSES ONLY · NOT SEBI REGISTERED · CONDUCT OWN RESEARCH</div>
</div>
<script>
function sp(t,btn){{['top','a','b','w'].forEach(x=>document.getElementById('p-'+x).style.display='none');document.getElementById('p-'+t).style.display='grid';document.querySelectorAll('.ptab').forEach(b=>b.classList.remove('on'));btn.classList.add('on');}}
let F={{f:'all',sec:'ALL',search:''}};
function apF(){{
  const rows=[...document.querySelectorAll('.row')];let vis=[];
  rows.forEach(r=>{{
    const gr=r.dataset.grade,bo=r.dataset.bo,flt=r.dataset.flt,cap=r.dataset.cap,sec=r.dataset.sector;
    const sym=r.querySelector('.sym').textContent.toLowerCase();
    let show=true;
    if(F.f==='flt'&&flt!=='1') show=false;
    else if(F.f==='bo'&&bo!=='1') show=false;
    else if(F.f==='a'&&gr!=='A') show=false;
    else if(F.f==='ab'&&!['A','B'].includes(gr)) show=false;
    else if(F.f==='mid'&&cap!=='Mid') show=false;
    else if(F.f==='small'&&cap!=='Small') show=false;
    if(F.sec!=='ALL'&&sec!==F.sec) show=false;
    if(F.search&&!sym.includes(F.search.toLowerCase())) show=false;
    r.style.display=show?'':'none';if(show) vis.push(r);
  }});
  const rc=document.getElementById('rc');
  vis.sort((a,b)=>parseInt(b.dataset.score)-parseInt(a.dataset.score));
  vis.forEach(r=>rc.appendChild(r));
}}
function fF(btn,v){{document.querySelectorAll('.ctrl .fb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');F.f=v;apF();}}
function fSec(btn,v){{document.querySelectorAll('.ctrl:nth-of-type(2) .fb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');F.sec=v;apF();}}
function fS(v){{F.search=v;apF();}}
function tog(id){{
  const d=document.getElementById('det-'+id),e=document.getElementById('ei-'+id);
  if(d.style.display==='none'){{d.style.display='block';e.style.transform='rotate(180deg)';}}
  else{{d.style.display='none';e.style.transform='';}}
}}
</script>
</body></html>"""

# ── MAIN ──
def main():
    ap=argparse.ArgumentParser(description="DarvaX Scanner — @AmitabhJha3")
    ap.add_argument("--top",type=int,default=None); ap.add_argument("--sector",type=str,default=None)
    ap.add_argument("--sym",type=str,default=None); ap.add_argument("--cap",type=str,default=None)
    ap.add_argument("--demo",action="store_true"); ap.add_argument("--serve",action="store_true")
    ap.add_argument("--port",type=int,default=5000); ap.add_argument("--output",type=str,default=None)
    ap.add_argument("--no-ai",action="store_true"); args=ap.parse_args()
    print("""
╔══════════════════════════════════════════════════════════╗
║  DARVAX SCANNER — @AmitabhJha3 #DarvaXClassRooM         ║
║  52W High · Darvas Box · Volume · RSI 40/80 · Pyramid   ║
╚══════════════════════════════════════════════════════════╝""")
    print(f"  AI: {OPENROUTER_MODEL}" if OPENROUTER_API_KEY and not args.no_ai else "  Rule-Based | Set OPENROUTER_API_KEY for AI (free at openrouter.ai)")
    if args.sym: syms=[s.strip().upper() for s in args.sym.split(",")]; stocks=[s for s in UNIVERSE if s["sym"] in syms]
    elif args.sector: stocks=[s for s in UNIVERSE if s["sector"].lower()==args.sector.lower()]
    elif args.cap: stocks=[s for s in UNIVERSE if s.get("cap","").lower()==args.cap.lower()]
    elif args.top: stocks=sorted(UNIVERSE,key=lambda s:s["mcap"],reverse=True)[:args.top]
    else: stocks=UNIVERSE.copy()
    if not YF_AVAILABLE and not args.demo: print("  yfinance not found — demo mode"); args.demo=True
    print(f"  Stocks: {len(stocks)} | Mode: {'DEMO' if args.demo else 'LIVE'}\n")
    t0=time.time(); results=run_scan(stocks,demo=args.demo); elapsed=round(time.time()-t0,1)
    valid=[r for r in results if r.get("a")]
    sr=sector_rank(results); pk=picks(results,sr)
    ga=[r for r in valid if r["a"]["grade"]=="A"]; bos=[r for r in valid if r["a"].get("active_bo")]
    print(f"\n  ✅ {elapsed}s · {len(valid)} stocks\n")
    print("  ── TOP SECTORS ─────────────────────────────")
    for i,(s,d) in enumerate(list(sr.items())[:5]): print(f"  {i+1}. {s:<14} avg {d['avg']:+.0f}  {d['bull']} setups")
    print(f"\n  ── GRADE A — PERFECT DARVAX ────────────────")
    for r in ga[:6]:
        a=r["a"]; t=a.get("trade") or {}
        print(f"  {r['sym']:<14} [{r['cap']}] RSI:{a['rsi']:<5} {a['from52h']}%below52H  E:₹{t.get('entry','—')} SL:₹{t.get('sl_20ema','—')}{'  📦BO!' if a.get('active_bo') else ''}")
    if bos:
        print(f"\n  ── 📦 ACTIVE BREAKOUTS ──────────────────────")
        for r in bos[:5]:
            a=r["a"]; t=a.get("trade") or {}
            print(f"  {r['sym']:<14} Vol:{a['vr']}x  E:₹{t.get('entry','—')}  SL:₹{t.get('sl','—')}  T1:₹{t.get('t1','—')}")
    ai_text=""
    if OPENROUTER_API_KEY and not args.no_ai: ai_text=ai_brief(pk,sr)
    meta={"scan_time":datetime.now().strftime("%d %b %Y, %I:%M %p"),"demo":args.demo,"elapsed":elapsed}
    out=args.output or f"darvax_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    Path(out).write_text(build_html(results,meta,pk,sr,ai_text),encoding="utf-8")
    print(f"\n  💾 Report: {out}")
    if args.serve:
        try:
            from flask import Flask,Response
            app=Flask(__name__)
            @app.route("/")
            def index():
                r2=run_scan(stocks,demo=args.demo,verbose=False); sr2=sector_rank(r2); p2=picks(r2,sr2)
                ai2=ai_brief(p2,sr2) if OPENROUTER_API_KEY and not args.no_ai else ""
                return Response(build_html(r2,meta,p2,sr2,ai2),mimetype="text/html")
            print(f"\n  🌐 http://localhost:{args.port}"); webbrowser.open(f"http://localhost:{args.port}")
            app.run(host="0.0.0.0",port=args.port,debug=False)
        except ImportError: print("  pip install flask")
    else: webbrowser.open(f"file://{Path(out).resolve()}")

if __name__=="__main__":
    main()
