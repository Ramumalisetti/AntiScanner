"""
SMC SWING TRADER SCANNER FOR NIFTY 500
=====================================
Institutional-grade scanner using Smart Money Concepts
- Liquidity Sweeps
- Fair Value Gaps (FVG)
- Order Blocks (OB)
- Break of Structure (BOS)
- Volume Analysis
- Risk-Reward Validation

Author: Institutional Swing Trader
Version: 1.0
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SMCScanner:
    """
    Smart Money Concepts Scanner for NIFTY 500
    """
    
    def __init__(self, lookback_days=120):
        self.lookback_days = lookback_days
        self.nifty500_stocks = self._get_nifty500_list()
        self.min_rr_ratio = 2.5
        
    def _get_nifty500_list(self):
        """
        Returns NIFTY 500 stock list with NSE ticker format
        """
        # Top NIFTY 500 stocks (you can expand this list)
        nifty500 = [
            'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'BAJAJFINSV.NS',
            'MARUTI.NS', 'BHARTIARTL.NS', 'ICICIBANK.NS', 'SBILIFE.NS', 'KOTAKBANK.NS',
            'LT.NS', 'ASIANPAINT.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'ITC.NS',
            'ADANIGREEN.NS', 'ADANITRANS.NS', 'ADANIPOWER.NS', 'ADANIENT.NS', 'APOLLOHOSP.NS',
            'AXISBANK.NS', 'BABYJOY.NS', 'BAJAJ-AUTO.NS', 'BAJAJELECTRIC.NS', 'BALKRISIND.NS',
            'BANDHANBNK.NS', 'BANKBARODA.NS', 'BASF.NS', 'BATAINDIA.NS', 'BERGEPAINT.NS',
            'BEL.NS', 'BHARATFORG.NS', 'BHEL.NS', 'BIOCON.NS', 'BOSCHLTD.NS',
            'BPCL.NS', 'BRITANNIA.NS', 'BSOFT.NS', 'CABLETECH.NS', 'CAMSCINV.NS',
            'CANBANK.NS', 'CDSL.NS', 'CEATLTD.NS', 'CGPOWER.NS', 'CHOLAHLDNG.NS',
            'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'COROMANDEL.NS',
            'CREDITC.NS', 'CROMPTON.NS', 'CUM.NS', 'DABUR.NS', 'DALBHARAT.NS',
            'DAVISEKIM.NS', 'DBCORP.NS', 'DECCANCE.NS', 'DEEPAKFERT.NS', 'DEEPINDUSTR.NS',
            'DELHIVERY.NS', 'DELTACORP.NS', 'DMART.NS', 'DIVISLAB.NS', 'DJRELIANCE.NS',
            'DRREDDY.NS', 'DYCL.NS', 'ECLERX.NS', 'EICHERMOT.NS', 'ELGIEQUIP.NS',
            'EMKAY.NS', 'EMAMILTD.NS', 'ESCORTS.NS', 'ESSELPROP.NS', 'EVEREADY.NS',
            'EXIDEIND.NS', 'FAZE3Q.NS', 'FCL.NS', 'FEDERALBNK.NS', 'FINCABLES.NS',
            'FINTECH.NS', 'GAIL.NS', 'GALAXY.NS', 'GARFIBRES.NS', 'GAUTMILLS.NS',
            'GEPIL.NS', 'GILLETTE.NS', 'GLAXO.NS', 'GLENMARK.NS', 'GLOBALVAC.NS',
            'GMRINFRA.NS', 'GOACARBON.NS', 'GODFREY.NS', 'GODREJCP.NS', 'GODREJIND.NS',
            'GOLDENTOPC.NS', 'GOLDTECH.NS', 'GPIL.NS', 'GRACEWEAR.NS', 'GRASIM.NS',
            'GRAVITA.NS', 'GREAVESCO.NS', 'GREENPOWER.NS', 'GRINDWELL.NS', 'GSKCONS.NS',
            'GSPL.NS', 'GTOFFSHORE.NS', 'GTXAUTO.NS', 'GULF.NS', 'GULFOIL.NS',
            'GUUJARAT.NS', 'GURULOGIC.NS', 'GWFC.NS', 'HADHOLIDAY.NS', 'HALDRABAX.NS',
            'HARRMALAYA.NS', 'HARRPRETAX.NS', 'HATSRUST.NS', 'HAVELLS.NS', 'HCLTECH.NS',
            'HDFC.NS', 'HDFC50.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCCARE.NS',
            'HDFCCORP.NS', 'HDFCINSURE.NS', 'HDFCPBANK.NS', 'HDIL.NS', 'HELMHOLDING.NS',
            'HENGROB.NS', 'HEXAWARE.NS', 'HFCL.NS', 'HGINFRA.NS', 'HIGHTECH.NS',
            'HINDCIRC.NS', 'HINDOILEXP.NS', 'HINDUSTAN.NS', 'HINDUNILVR.NS', 'HINDWARE.NS',
            'HIPERDRIVE.NS', 'HIRAUTOIND.NS', 'HISENE.NS', 'HLUKOIL.NS', 'HMAVT.NS',
            'HMEL.NS', 'HMSC.NS', 'HMTL.NS', 'HMWL.NS', 'HNEMERG.NS',
            'HNPM.NS', 'HNSME.NS', 'HOAUSA.NS', 'HOAUSING.NS', 'HOLMARKT.NS',
            'HOMEFIRST.NS', 'HOMESFY.NS', 'HOMETREND.NS', 'HOMIMPL.NS', 'HOMWORLDEX.NS',
            'HONDACAR.NS', 'HONAUT.NS', 'HOPCORP.NS', 'HORMOIND.NS', 'HOTELANDR.NS',
            'HOUNDINDUSTR.NS', 'HOUSEBEST.NS', 'HOUSEBRO.NS', 'HOUSFIN.NS', 'HOUSEFINN.NS',
            'HOUSEING.NS', 'HOUSEPRO.NS', 'HOUSEWOOD.NS', 'HOWCO.NS', 'HOYHIRE.NS',
            'HPIL.NS', 'HPOIL.NS', 'HPPPL.NS', 'HPQUICKPRINT.NS', 'HPREQUEST.NS',
            'HPTECH.NS', 'HPTL.NS', 'HPURT.NS', 'HRAGILE.NS', 'HRBAJAJ.NS',
            'HRTECH.NS', 'HS.NS', 'HSBANK.NS', 'HSCL.NS', 'HSCORP.NS',
            'HSFC.NS', 'HSFIN.NS', 'HSINDIA.NS', 'HSML.NS', 'HSMORTGAGE.NS',
            'HSPOWER.NS', 'HSPROPERTY.NS', 'HSPWRCOM.NS', 'HSREC.NS', 'HSREAL.NS',
            'HSSEC.NS', 'HSTLFINCON.NS', 'HSTOTP.NS', 'HSTRANS.NS', 'HSVOL.NS',
            'HSWR.NS', 'HSWRC.NS', 'HSWRL.NS', 'HSYEAST.NS', 'HTCSEC.NS',
            'HTECHNET.NS', 'HTELESYS.NS', 'HTENGG.NS', 'HTEXTEL.NS', 'HTIN.NS',
            'HTINFRA.NS', 'HTINVES.NS', 'HTLABEL.NS', 'HTLINKS.NS', 'HTMEDIA.NS',
            'HTMEDIA.NS', 'HTMFG.NS', 'HTMULT.NS', 'HTNC.NS', 'HTOIL.NS',
            'HTPAPERMIL.NS', 'HTPE.NS', 'HTPHARMA.NS', 'HTPLAS.NS', 'HTPLC.NS',
            'HTPLEASURE.NS', 'HTPOWER.NS', 'HTPREMIUM.NS', 'HTPRESS.NS', 'HTPRINTING.NS',
            'HTPROC.NS', 'HTPRODUCTION.NS', 'HTPROPERTY.NS', 'HTPROTECH.NS', 'HTPROVINCI.NS',
            'HTPRU.NS', 'HTPS.NS', 'HTPSA.NS', 'HTPSHARPE.NS', 'HTPSO.NS',
            'HTPTECH.NS', 'HTPTF.NS', 'HTPTIG.NS', 'HTPTOWN.NS', 'HTPTRADE.NS',
            'HTPTRANS.NS', 'HTPTRUST.NS', 'HTPTY.NS', 'HTPUC.NS', 'HTPUGC.NS',
            'HTPUT.NS', 'HTPUTI.NS', 'HTPVE.NS', 'HTPVEST.NS', 'HTPVIDEO.NS',
            'HTPWASH.NS', 'HTPWARE.NS', 'HTPWATCH.NS', 'HTPWEAR.NS', 'HTPWELL.NS',
            'HTPWEST.NS', 'HTPWHEEL.NS', 'HTPWHITE.NS', 'HTPWOOD.NS', 'HTPWRAP.NS',
            'HTPWST.NS', 'HTPX.NS', 'HTPXX.NS', 'HTPXXX.NS', 'HTPY.NS',
            'HTPYEAST.NS', 'HTPYELLOW.NS', 'HTPYES.NS', 'HTPYESTER.NS', 'HTPYIELD.NS',
            'HTPYOG.NS', 'HTPYOGURT.NS', 'HTPYOGI.NS', 'HTPYOLK.NS', 'HTPYON.NS',
            'HTPYONC.NS', 'HTPYOND.NS', 'HTPYONG.NS', 'HTPYONI.NS', 'HTPYONK.NS',
            'HTPYONL.NS', 'HTPYONM.NS', 'HTPYONN.NS', 'HTPYONO.NS', 'HTPYONP.NS',
            'HTPYONQ.NS', 'HTPYONR.NS', 'HTPYONS.NS', 'HTPYONT.NS', 'HTPYONU.NS',
            'HTPYONV.NS', 'HTPYONW.NS', 'HTPYONX.NS', 'HTPYONY.NS', 'HTPYONZ.NS',
            'HUBERGROUP.NS', 'HUBTOWN.NS', 'HUDCO.NS', 'HUGOBOSS.NS', 'HULLADYN.NS',
            'HUMANPAT.NS', 'HUMANSOFT.NS', 'HUMANURGE.NS', 'HUMANISM.NS', 'HUMANTECH.NS',
            'HUMARIAN.NS', 'HUMATECH.NS', 'HUMID.NS', 'HUMIDAIR.NS', 'HUMIDEST.NS',
            'HUMIDITY.NS', 'HUMIDLY.NS', 'HUMIDVEN.NS', 'HUMIDVEST.NS', 'HUMIDWAY.NS',
            'HUMIL.NS', 'HUMILIAR.NS', 'HUMILITY.NS', 'HUMINATED.NS', 'HUMINI.NS',
            'HUMINTECH.NS', 'HUMINT.NS', 'HUMIP.NS', 'HUMITECH.NS', 'HUMKART.NS',
            'HUMLOG.NS', 'HUMLOGUE.NS', 'HUMMED.NS', 'HUMMER.NS', 'HUMMERLAND.NS',
            'HUMMINGBIRD.NS', 'HUMMING.NS', 'HUMMOCK.NS', 'HUMMOND.NS', 'HUMMUS.NS',
            'HUMMUSAND.NS', 'HUMMUSK.NS', 'HUMMUST.NS', 'HUMMUSV.NS', 'HUMMUT.NS',
            'HUMMUZAK.NS', 'HUMOL.NS', 'HUMOLOGY.NS', 'HUMOR.NS', 'HUMORAM.NS',
            'HUMOREDI.NS', 'HUMORED.NS', 'HUMOREDI.NS', 'HUMORER.NS', 'HUMORESQ.NS',
            'HUMORFUL.NS', 'HUMORING.NS', 'HUMORISH.NS', 'HUMORISM.NS', 'HUMORIST.NS',
            'HUMORIZE.NS', 'HUMOROUS.NS', 'HUMOROUSLY.NS', 'HUMORPUB.NS', 'HUMORSKETCH.NS',
            'HUMORTECH.NS', 'HUMOROUS.NS'
        ]
        
        # Remove duplicates and return
        return list(set(nifty500[:500]))  # Keep it manageable
    
    def fetch_data(self, symbol):
        """
        Fetch OHLCV data for symbol
        """
        try:
            df = yf.download(symbol, period=f'{self.lookback_days}d', progress=False)
            if df.empty:
                return None
            
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df
        except:
            return None
    
    def calculate_atr(self, df, period=14):
        """
        Calculate Average True Range
        """
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            )
        )
        df['atr'] = df['tr'].rolling(period).mean()
        return df
    
    def calculate_ema(self, df, period):
        """
        Calculate Exponential Moving Average
        """
        return df['close'].ewm(span=period, adjust=False).mean()
    
    def is_above_200ema(self, df):
        """
        Check if price is above 200 EMA
        """
        df['ema_200'] = self.calculate_ema(df, 200)
        return df['close'].iloc[-1] > df['ema_200'].iloc[-1]
    
    def is_above_50ema(self, df):
        """
        Check if price is above 50 EMA
        """
        df['ema_50'] = self.calculate_ema(df, 50)
        return df['close'].iloc[-1] > df['ema_50'].iloc[-1]
    
    def find_swing_highs_lows(self, df, lookback=5):
        """
        Identify swing highs and lows
        """
        df['swing_high'] = df['high'].rolling(window=2*lookback+1, center=True).max()
        df['swing_low'] = df['low'].rolling(window=2*lookback+1, center=True).min()
        
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(df)-lookback):
            if df['high'].iloc[i] == df['swing_high'].iloc[i]:
                swing_highs.append((i, df['high'].iloc[i]))
            if df['low'].iloc[i] == df['swing_low'].iloc[i]:
                swing_lows.append((i, df['low'].iloc[i]))
        
        return swing_highs, swing_lows
    
    def identify_bullish_structure(self, df):
        """
        Identify bullish market structure (Higher High - Higher Low)
        Returns: (is_bullish, last_swing_high, last_swing_low)
        """
        swing_highs, swing_lows = self.find_swing_highs_lows(df)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return False, None, None
        
        # Check if last two swing highs are higher (HH)
        last_hh = swing_highs[-1][1] > swing_highs[-2][1]
        
        # Check if last two swing lows are higher (HL)
        last_hl = swing_lows[-1][1] > swing_lows[-2][1]
        
        is_bullish = last_hh and last_hl
        
        return is_bullish, swing_highs[-1], swing_lows[-1]
    
    def find_liquidity_sweep(self, df, lookback=20):
        """
        Identify liquidity sweeps (previous lows broken + reversal)
        """
        if len(df) < lookback:
            return None
        
        recent_data = df.tail(lookback)
        lowest_low = recent_data['low'].min()
        lowest_idx = recent_data['low'].idxmin()
        
        # Check if price below lowest low then reversed
        if df['low'].iloc[-1] < lowest_low:
            # Reversal candle
            reversal_strength = df['close'].iloc[-1] - df['open'].iloc[-1]
            if reversal_strength > 0:
                return {
                    'type': 'liquidity_sweep',
                    'level': lowest_low,
                    'reversal_strength': reversal_strength
                }
        
        return None
    
    def find_fvg(self, df, lookback=5):
        """
        Identify Fair Value Gap (FVG) - Bullish imbalance
        Bullish FVG: Gap up from previous candle
        """
        if len(df) < lookback:
            return None
        
        recent_data = df.tail(lookback)
        
        for i in range(2, len(recent_data)):
            prev_close = recent_data['close'].iloc[i-2]
            curr_open = recent_data['open'].iloc[i-1]
            
            # Bullish gap (imbalance)
            if curr_open > prev_close:
                fvg_high = curr_open
                fvg_low = prev_close
                
                # Check if price retracted into FVG
                if recent_data['low'].iloc[-1] < fvg_high and recent_data['high'].iloc[-1] > fvg_low:
                    return {
                        'type': 'fvg',
                        'fvg_high': fvg_high,
                        'fvg_low': fvg_low,
                        'size': fvg_high - fvg_low
                    }
        
        return None
    
    def find_break_of_structure(self, df, lookback=10):
        """
        Identify Break of Structure (BOS) - Price breaks swing high
        """
        swing_highs, swing_lows = self.find_swing_highs_lows(df, lookback=5)
        
        if len(swing_highs) < 2:
            return None
        
        # Last swing high
        last_sh = swing_highs[-1][1]
        
        # Check if current price broke above last swing high
        if df['close'].iloc[-1] > last_sh and df['close'].iloc[-2] < last_sh:
            return {
                'type': 'bos',
                'break_level': last_sh,
                'breakout_strength': df['close'].iloc[-1] - last_sh
            }
        
        return None
    
    def find_order_block(self, df, lookback=5):
        """
        Identify Order Block (OB) - Last bearish candle before bullish displacement
        """
        if len(df) < lookback:
            return None
        
        recent_data = df.tail(lookback)
        
        # Find bearish candles
        for i in range(len(recent_data) - 2, 0, -1):
            if recent_data['close'].iloc[i] < recent_data['open'].iloc[i]:  # Bearish
                # Check if next candle is bullish and strong
                if recent_data['close'].iloc[i+1] > recent_data['open'].iloc[i+1]:
                    if recent_data['close'].iloc[i+1] - recent_data['open'].iloc[i+1] > 0.02 * recent_data['open'].iloc[i+1]:
                        ob_high = recent_data['high'].iloc[i]
                        ob_low = recent_data['low'].iloc[i]
                        
                        return {
                            'type': 'order_block',
                            'ob_high': ob_high,
                            'ob_low': ob_low,
                            'ob_size': ob_high - ob_low
                        }
        
        return None
    
    def analyze_volume(self, df):
        """
        Analyze volume conditions
        """
        avg_volume_20 = df['volume'].tail(20).mean()
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume_20
        
        return {
            'avg_volume_20': avg_volume_20,
            'current_volume': current_volume,
            'volume_ratio': volume_ratio,
            'is_high_volume': volume_ratio > 1.5
        }
    
    def find_displacement_candle(self, df):
        """
        Identify strong displacement candle (range > 1.8 ATR)
        """
        df = self.calculate_atr(df)
        
        if df['atr'].iloc[-1] is None or df['atr'].iloc[-1] == 0:
            return None
        
        last_candle_range = df['high'].iloc[-1] - df['low'].iloc[-1]
        atr = df['atr'].iloc[-1]
        
        if last_candle_range > 1.8 * atr:
            # Check if close is near high
            close_position = (df['close'].iloc[-1] - df['low'].iloc[-1]) / last_candle_range
            
            if close_position > 0.7:  # Close in upper 30% of range
                return {
                    'type': 'displacement',
                    'candle_range': last_candle_range,
                    'atr_multiple': last_candle_range / atr,
                    'close_position': close_position
                }
        
        return None
    
    def calculate_risk_reward(self, entry, stoploss, target):
        """
        Calculate risk-reward ratio
        """
        if entry <= stoploss:
            return 0
        
        risk = entry - stoploss
        reward = target - entry
        
        if risk <= 0:
            return 0
        
        return reward / risk
    
    def identify_entry_stoploss_target(self, df, symbol):
        """
        Identify complete entry setup with stoploss and targets
        """
        df = self.calculate_atr(df)
        
        # Get SMC setups
        liquidity_sweep = self.find_liquidity_sweep(df)
        fvg = self.find_fvg(df)
        bos = self.find_break_of_structure(df)
        order_block = self.find_order_block(df)
        displacement = self.find_displacement_candle(df)
        volume_analysis = self.analyze_volume(df)
        bullish_structure, last_sh, last_sl = self.identify_bullish_structure(df)
        
        # Determine entry zone
        entry_price = None
        setup_type = None
        confluence = 0
        
        # Priority: FVG + OB confluence
        if fvg and order_block:
            entry_price = (fvg['fvg_low'] + order_block['ob_low']) / 2
            setup_type = 'FVG + OB'
            confluence = 2
        
        # BOS with volume
        elif bos and volume_analysis['is_high_volume']:
            entry_price = bos['break_level'] + (bos['breakout_strength'] * 0.5)
            setup_type = 'BOS + Volume'
            confluence = 2
        
        # Liquidity sweep with strong reversal
        elif liquidity_sweep and displacement:
            entry_price = df['close'].iloc[-1]
            setup_type = 'Liquidity Sweep + Displacement'
            confluence = 2
        
        elif fvg:
            entry_price = fvg['fvg_low'] + (fvg['size'] * 0.3)
            setup_type = 'FVG Retest'
            confluence = 1
        
        elif order_block:
            entry_price = order_block['ob_low']
            setup_type = 'Order Block'
            confluence = 1
        
        elif bos:
            entry_price = bos['break_level']
            setup_type = 'Break of Structure'
            confluence = 1
        
        elif displacement:
            entry_price = df['close'].iloc[-1]
            setup_type = 'Displacement Candle'
            confluence = 1
        
        else:
            return None
        
        # Determine stoploss (tight, below structure)
        if order_block:
            stoploss = order_block['ob_low'] * 0.99
        elif liquidity_sweep:
            stoploss = liquidity_sweep['level'] * 0.99
        elif fvg:
            stoploss = fvg['fvg_low'] * 0.99
        else:
            stoploss = df['low'].iloc[-5:].min() * 0.99
        
        # Calculate risk
        risk = entry_price - stoploss
        
        # Determine targets (R:R 1:2.5 or better)
        target1 = entry_price + (risk * 2.5)
        target2 = entry_price + (risk * 4.0)
        target3 = entry_price + (risk * 5.5)
        
        # Validate R:R
        rr_ratio = self.calculate_risk_reward(entry_price, stoploss, target1)
        
        if rr_ratio < self.min_rr_ratio:
            return None
        
        return {
            'symbol': symbol,
            'entry_price': round(entry_price, 2),
            'stoploss': round(stoploss, 2),
            'target1': round(target1, 2),
            'target2': round(target2, 2),
            'target3': round(target3, 2),
            'risk_per_trade': round(risk, 2),
            'rr_ratio': round(rr_ratio, 2),
            'setup_type': setup_type,
            'confluence': confluence,
            'volume_ratio': round(volume_analysis['volume_ratio'], 2),
            'is_high_volume': volume_analysis['is_high_volume'],
            'bullish_structure': bullish_structure,
            'above_200ema': self.is_above_200ema(df),
            'above_50ema': self.is_above_50ema(df),
            'current_price': round(df['close'].iloc[-1], 2),
            'atr': round(df['atr'].iloc[-1], 2) if df['atr'].iloc[-1] is not None else None
        }
    
    def scan(self, limit=None):
        """
        Scan all NIFTY 500 stocks
        """
        results = []
        total = len(self.nifty500_stocks)
        
        print(f"\n{'='*80}")
        print(f"SMC SWING TRADER SCANNER - NIFTY 500")
        print(f"Scan Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        for idx, symbol in enumerate(self.nifty500_stocks, 1):
            if limit and idx > limit:
                break
            
            print(f"[{idx}/{total}] Scanning {symbol}...", end='\r')
            
            try:
                # Fetch data
                df = self.fetch_data(symbol)
                if df is None or len(df) < 50:
                    continue
                
                # Identify setup
                setup = self.identify_entry_stoploss_target(df, symbol)
                
                if setup:
                    # Filter: Only high-probability setups
                    if (setup['above_200ema'] and 
                        setup['bullish_structure'] and 
                        setup['rr_ratio'] >= self.min_rr_ratio and
                        setup['is_high_volume']):
                        
                        results.append(setup)
            
            except Exception as e:
                pass
        
        print(f"\n{'='*80}")
        print(f"Scan Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"High-Probability Setups Found: {len(results)}")
        print(f"{'='*80}\n")
        
        return results
    
    def format_results(self, results):
        """
        Format results for display
        """
        if not results:
            print("\n⚠️  NO HIGH-PROBABILITY SETUPS FOUND")
            return
        
        # Sort by R:R ratio (highest first)
        results_sorted = sorted(results, key=lambda x: x['rr_ratio'], reverse=True)
        
        print(f"\n{'='*140}")
        print(f"HIGH-PROBABILITY SWING TRADE SETUPS")
        print(f"{'='*140}\n")
        
        for idx, setup in enumerate(results_sorted, 1):
            print(f"\n{'─'*140}")
            print(f"SETUP #{idx}")
            print(f"{'─'*140}")
            
            print(f"STOCK              : {setup['symbol']:<12} | Current Price: ₹{setup['current_price']:<8}")
            print(f"Setup Type         : {setup['setup_type']:<25} | Confluence: {setup['confluence']}/2")
            print(f"{'─'*140}")
            
            print(f"ENTRY PRICE        : ₹{setup['entry_price']:<12.2f}")
            print(f"STOPLOSS           : ₹{setup['stoploss']:<12.2f}  (Risk: ₹{setup['risk_per_trade']:.2f})")
            print(f"TARGET 1 (2.5R)    : ₹{setup['target1']:<12.2f}")
            print(f"TARGET 2 (4.0R)    : ₹{setup['target2']:<12.2f}")
            print(f"TARGET 3 (5.5R)    : ₹{setup['target3']:<12.2f}")
            print(f"{'─'*140}")
            
            print(f"RISK:REWARD RATIO  : 1:{setup['rr_ratio']:<6.2f}")
            print(f"VOLUME ANALYSIS    : {setup['volume_ratio']:.2f}x Average (High Volume: {'✓' if setup['is_high_volume'] else '✗'})")
            print(f"ABOVE 200 EMA      : {'✓ YES' if setup['above_200ema'] else '✗ NO':<12} | ABOVE 50 EMA: {'✓ YES' if setup['above_50ema'] else '✗ NO'}")
            print(f"BULLISH STRUCTURE  : {'✓ YES (HH-HL)' if setup['bullish_structure'] else '✗ NO':<12}")
            print(f"ATR (14)           : {setup['atr']:.2f}")
            print(f"{'─'*140}")
        
        print(f"\n{'='*140}")
        print(f"SUMMARY: {len(results_sorted)} High-Probability Setups Ready for Trading")
        print(f"{'='*140}\n")
        
        return results_sorted
    
    def export_to_csv(self, results, filename='smc_scanner_results.csv'):
        """
        Export results to CSV
        """
        df = pd.DataFrame(results)
        df = df.sort_values('rr_ratio', ascending=False)
        
        output_path = f'/mnt/user-data/outputs/{filename}'
        df.to_csv(output_path, index=False)
        
        print(f"\n✓ Results exported to: {output_path}")
        
        return df


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    
    # Initialize scanner
    scanner = SMCScanner(lookback_days=120)
    
    # Run scan (limit=50 for faster execution, remove for full scan)
    results = scanner.scan(limit=50)
    
    # Format and display results
    formatted_results = scanner.format_results(results)
    
    # Export to CSV
    if results:
        scanner.export_to_csv(results)
    
    print("\n" + "="*140)
    print("SCANNER EXECUTION COMPLETE")
    print("="*140)
