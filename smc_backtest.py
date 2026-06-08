import yfinance as yf
import pandas as pd
import numpy as np
import json
import time

def find_order_block(opens, highs, lows, closes):
    n = len(closes)
    best_ob = None
    max_momentum = 0
    for i in range(max(0, n - 40), max(0, n - 5)):
        if closes[i] < opens[i]:  
            try:
                momentum = closes[i+3] - closes[i]
                if momentum > max_momentum:
                    max_momentum = momentum
                    best_ob = {'top': highs[i], 'bottom': lows[i]}
            except IndexError:
                pass
    return best_ob

def find_fvg(highs, lows, closes):
    n = len(closes)
    fvgs = []
    for i in range(max(0, n - 30), max(0, n - 2)):
        gap_bottom = highs[i]
        gap_top = lows[i+2]
        if gap_top > gap_bottom:
            mitigated = False
            for j in range(i+3, n):
                if lows[j] <= gap_bottom:
                    mitigated = True
                    break
            if not mitigated:
                fvgs.append({'top': gap_top, 'bottom': gap_bottom})
    return fvgs[-1] if fvgs else None

def check_liquidity_sweep(lows, closes, current_idx, lookback=15):
    n = len(lows)
    if current_idx >= n: return False
    current_low = lows[current_idx]
    current_close = closes[current_idx]
    start_idx = max(0, current_idx - lookback)
    recent_lows = lows[start_idx:current_idx]
    if not recent_lows: return False
    swing_low = min(recent_lows)
    if current_low < swing_low and current_close > swing_low:
        return swing_low
    return False

def run_backtest():
    print("Loading UNIVERSE...")
    
    # We will test on top 20 Nifty 50 stocks for speed
    top_tickers = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
        "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "L&T.NS", "BAJFINANCE.NS",
        "AXISBANK.NS", "KOTAKBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS"
    ]
    
    trades = []
    print(f"Running historical simulation on Top 15 Nifty stocks for 2 Years...")
    
    for sym in top_tickers:
        print(f"Processing {sym}...")
        try:
            df = yf.Ticker(sym).history(period="2y", interval="1d", auto_adjust=True)
            if df.empty or len(df) < 100: continue
            
            opens = df['Open'].values
            highs = df['High'].values
            lows = df['Low'].values
            closes = df['Close'].values
            
            in_trade = False
            entry_price = 0
            stop_loss = 0
            target = 0
            
            # Walk forward from day 60 to end
            for i in range(60, len(df)-1):
                if in_trade:
                    # Check exit on day i
                    if lows[i] <= stop_loss:
                        trades.append({'sym': sym, 'res': 'LOSS', 'pnl': stop_loss - entry_price})
                        in_trade = False
                    elif highs[i] >= target:
                        trades.append({'sym': sym, 'res': 'WIN', 'pnl': target - entry_price})
                        in_trade = False
                    continue
                    
                # Not in trade, analyze up to day i
                past_o = opens[:i+1]
                past_h = highs[:i+1]
                past_l = lows[:i+1]
                past_c = closes[:i+1]
                
                price = past_c[-1]
                ob = find_order_block(past_o, past_h, past_l, past_c)
                fvg = find_fvg(past_h, past_l, past_c)
                ls = check_liquidity_sweep(past_l, past_c, -1)
                
                in_ob = False
                in_fvg = False
                
                if fvg and (fvg['bottom'] * 0.95 <= price <= fvg['top'] * 1.05):
                    in_fvg = True
                    sl = fvg['bottom'] * 0.98
                elif ob and (ob['bottom'] * 0.95 <= price <= ob['top'] * 1.05):
                    in_ob = True
                    sl = ob['bottom'] * 0.98
                    
                if in_fvg or in_ob or ls:
                    if ls: sl = ls * 0.99
                    risk = price - sl
                    if risk > 0 and (risk/price) < 0.1: # Max 10% risk
                        in_trade = True
                        entry_price = price
                        stop_loss = sl
                        target = price + (risk * 2.5) # 1:2.5 RR
        except Exception as e:
            pass

    wins = [t for t in trades if t['res'] == 'WIN']
    losses = [t for t in trades if t['res'] == 'LOSS']
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    
    print("\n" + "="*40)
    print("SMC BACKTEST RESULTS (Last 2 Years)")
    print("Universe: Nifty Top 15 Heavyweights")
    print("="*40)
    print(f"Total Trades Taken : {len(trades)}")
    print(f"Winning Trades     : {len(wins)}")
    print(f"Losing Trades      : {len(losses)}")
    print(f"Win Rate           : {win_rate:.1f}%")
    print(f"Reward-to-Risk     : 2.5 R")
    
    if len(trades) > 0:
        expectancy = (win_rate/100 * 2.5) - ((100-win_rate)/100 * 1.0)
        print(f"Trade Expectancy   : +{expectancy:.2f} R per trade")
    print("="*40)
    
if __name__ == "__main__":
    run_backtest()
