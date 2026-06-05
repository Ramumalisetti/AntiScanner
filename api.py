"""
Elite Pullback Reversal Scanner — API Backend
Scans Nifty 500 / F&O universe for top pullback setups daily.

Criteria:
1. Stock above 50 EMA + 200 EMA (confirmed uptrend)
2. Price pulled back 3-8% from recent 20-day high
3. Price sitting on/near 20 EMA, 50 EMA, or previous breakout level
4. Bullish reversal candle (Hammer, Engulfing, Morning Star)
5. Volume drying up on dip, expanding on reversal day
6. RSI pulled back to 45-58 zone after being overbought
"""

import time, math, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# UNIVERSE — Nifty 500 / F&O liquid stocks
# ─────────────────────────────────────────────
UNIVERSE = [
    {"sym":"360ONE","yf":"360ONE.NS","sector":"Financial Services"},
    {"sym":"3MINDIA","yf":"3MINDIA.NS","sector":"Diversified"},
    {"sym":"ABB","yf":"ABB.NS","sector":"Capital Goods"},
    {"sym":"ACC","yf":"ACC.NS","sector":"Construction Materials"},
    {"sym":"ACMESOLAR","yf":"ACMESOLAR.NS","sector":"Power"},
    {"sym":"AIAENG","yf":"AIAENG.NS","sector":"Capital Goods"},
    {"sym":"APLAPOLLO","yf":"APLAPOLLO.NS","sector":"Capital Goods"},
    {"sym":"AUBANK","yf":"AUBANK.NS","sector":"Financial Services"},
    {"sym":"AWL","yf":"AWL.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"AADHARHFC","yf":"AADHARHFC.NS","sector":"Financial Services"},
    {"sym":"AARTIIND","yf":"AARTIIND.NS","sector":"Chemicals"},
    {"sym":"AAVAS","yf":"AAVAS.NS","sector":"Financial Services"},
    {"sym":"ABBOTINDIA","yf":"ABBOTINDIA.NS","sector":"Healthcare"},
    {"sym":"ACE","yf":"ACE.NS","sector":"Capital Goods"},
    {"sym":"ACUTAAS","yf":"ACUTAAS.NS","sector":"Healthcare"},
    {"sym":"ADANIENSOL","yf":"ADANIENSOL.NS","sector":"Power"},
    {"sym":"ADANIENT","yf":"ADANIENT.NS","sector":"Metals & Mining"},
    {"sym":"ADANIGREEN","yf":"ADANIGREEN.NS","sector":"Power"},
    {"sym":"ADANIPORTS","yf":"ADANIPORTS.NS","sector":"Services"},
    {"sym":"ADANIPOWER","yf":"ADANIPOWER.NS","sector":"Power"},
    {"sym":"ATGL","yf":"ATGL.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"ABCAPITAL","yf":"ABCAPITAL.NS","sector":"Financial Services"},
    {"sym":"ABFRL","yf":"ABFRL.NS","sector":"Consumer Services"},
    {"sym":"ABLBL","yf":"ABLBL.NS","sector":"Consumer Services"},
    {"sym":"ABREL","yf":"ABREL.NS","sector":"Realty"},
    {"sym":"ABSLAMC","yf":"ABSLAMC.NS","sector":"Financial Services"},
    {"sym":"CPPLUS","yf":"CPPLUS.NS","sector":"Capital Goods"},
    {"sym":"AEGISLOG","yf":"AEGISLOG.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"AEGISVOPAK","yf":"AEGISVOPAK.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"AFCONS","yf":"AFCONS.NS","sector":"Construction"},
    {"sym":"AFFLE","yf":"AFFLE.NS","sector":"Information Technology"},
    {"sym":"AJANTPHARM","yf":"AJANTPHARM.NS","sector":"Healthcare"},
    {"sym":"ALKEM","yf":"ALKEM.NS","sector":"Healthcare"},
    {"sym":"ABDL","yf":"ABDL.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"ARE&M","yf":"ARE&M.NS","sector":"Automobile and Auto Components"},
    {"sym":"AMBER","yf":"AMBER.NS","sector":"Consumer Durables"},
    {"sym":"AMBUJACEM","yf":"AMBUJACEM.NS","sector":"Construction Materials"},
    {"sym":"ANANDRATHI","yf":"ANANDRATHI.NS","sector":"Financial Services"},
    {"sym":"ANANTRAJ","yf":"ANANTRAJ.NS","sector":"Realty"},
    {"sym":"ANGELONE","yf":"ANGELONE.NS","sector":"Financial Services"},
    {"sym":"ANTHEM","yf":"ANTHEM.NS","sector":"Healthcare"},
    {"sym":"ANURAS","yf":"ANURAS.NS","sector":"Chemicals"},
    {"sym":"APARINDS","yf":"APARINDS.NS","sector":"Capital Goods"},
    {"sym":"APOLLOHOSP","yf":"APOLLOHOSP.NS","sector":"Healthcare"},
    {"sym":"APOLLOTYRE","yf":"APOLLOTYRE.NS","sector":"Automobile and Auto Components"},
    {"sym":"APTUS","yf":"APTUS.NS","sector":"Financial Services"},
    {"sym":"ASAHIINDIA","yf":"ASAHIINDIA.NS","sector":"Automobile and Auto Components"},
    {"sym":"ASHOKLEY","yf":"ASHOKLEY.NS","sector":"Capital Goods"},
    {"sym":"ASIANPAINT","yf":"ASIANPAINT.NS","sector":"Consumer Durables"},
    {"sym":"ASTERDM","yf":"ASTERDM.NS","sector":"Healthcare"},
    {"sym":"ASTRAL","yf":"ASTRAL.NS","sector":"Capital Goods"},
    {"sym":"ATHERENERG","yf":"ATHERENERG.NS","sector":"Automobile and Auto Components"},
    {"sym":"ATUL","yf":"ATUL.NS","sector":"Chemicals"},
    {"sym":"AUROPHARMA","yf":"AUROPHARMA.NS","sector":"Healthcare"},
    {"sym":"AIIL","yf":"AIIL.NS","sector":"Financial Services"},
    {"sym":"DMART","yf":"DMART.NS","sector":"Consumer Services"},
    {"sym":"AXISBANK","yf":"AXISBANK.NS","sector":"Financial Services"},
    {"sym":"BEML","yf":"BEML.NS","sector":"Capital Goods"},
    {"sym":"BLS","yf":"BLS.NS","sector":"Consumer Services"},
    {"sym":"BSE","yf":"BSE.NS","sector":"Financial Services"},
    {"sym":"BAJAJ-AUTO","yf":"BAJAJ-AUTO.NS","sector":"Automobile and Auto Components"},
    {"sym":"BAJFINANCE","yf":"BAJFINANCE.NS","sector":"Financial Services"},
    {"sym":"BAJAJFINSV","yf":"BAJAJFINSV.NS","sector":"Financial Services"},
    {"sym":"BAJAJHLDNG","yf":"BAJAJHLDNG.NS","sector":"Financial Services"},
    {"sym":"BAJAJHFL","yf":"BAJAJHFL.NS","sector":"Financial Services"},
    {"sym":"BALKRISIND","yf":"BALKRISIND.NS","sector":"Automobile and Auto Components"},
    {"sym":"BALRAMCHIN","yf":"BALRAMCHIN.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"BANDHANBNK","yf":"BANDHANBNK.NS","sector":"Financial Services"},
    {"sym":"BANKBARODA","yf":"BANKBARODA.NS","sector":"Financial Services"},
    {"sym":"BANKINDIA","yf":"BANKINDIA.NS","sector":"Financial Services"},
    {"sym":"MAHABANK","yf":"MAHABANK.NS","sector":"Financial Services"},
    {"sym":"BATAINDIA","yf":"BATAINDIA.NS","sector":"Consumer Durables"},
    {"sym":"BAYERCROP","yf":"BAYERCROP.NS","sector":"Chemicals"},
    {"sym":"BELRISE","yf":"BELRISE.NS","sector":"Automobile and Auto Components"},
    {"sym":"BERGEPAINT","yf":"BERGEPAINT.NS","sector":"Consumer Durables"},
    {"sym":"BDL","yf":"BDL.NS","sector":"Capital Goods"},
    {"sym":"BEL","yf":"BEL.NS","sector":"Capital Goods"},
    {"sym":"BHARATFORG","yf":"BHARATFORG.NS","sector":"Automobile and Auto Components"},
    {"sym":"BHEL","yf":"BHEL.NS","sector":"Capital Goods"},
    {"sym":"BPCL","yf":"BPCL.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"BHARTIARTL","yf":"BHARTIARTL.NS","sector":"Telecommunication"},
    {"sym":"BHARTIHEXA","yf":"BHARTIHEXA.NS","sector":"Telecommunication"},
    {"sym":"BIKAJI","yf":"BIKAJI.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"GROWW","yf":"GROWW.NS","sector":"Financial Services"},
    {"sym":"BIOCON","yf":"BIOCON.NS","sector":"Healthcare"},
    {"sym":"BSOFT","yf":"BSOFT.NS","sector":"Information Technology"},
    {"sym":"BLUEDART","yf":"BLUEDART.NS","sector":"Services"},
    {"sym":"BLUEJET","yf":"BLUEJET.NS","sector":"Healthcare"},
    {"sym":"BLUESTARCO","yf":"BLUESTARCO.NS","sector":"Consumer Durables"},
    {"sym":"BBTC","yf":"BBTC.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"BOSCHLTD","yf":"BOSCHLTD.NS","sector":"Automobile and Auto Components"},
    {"sym":"FIRSTCRY","yf":"FIRSTCRY.NS","sector":"Consumer Services"},
    {"sym":"BRIGADE","yf":"BRIGADE.NS","sector":"Realty"},
    {"sym":"BRITANNIA","yf":"BRITANNIA.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"MAPMYINDIA","yf":"MAPMYINDIA.NS","sector":"Information Technology"},
    {"sym":"CCL","yf":"CCL.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"CESC","yf":"CESC.NS","sector":"Power"},
    {"sym":"CGPOWER","yf":"CGPOWER.NS","sector":"Capital Goods"},
    {"sym":"CIEINDIA","yf":"CIEINDIA.NS","sector":"Automobile and Auto Components"},
    {"sym":"CRISIL","yf":"CRISIL.NS","sector":"Financial Services"},
    {"sym":"CANFINHOME","yf":"CANFINHOME.NS","sector":"Financial Services"},
    {"sym":"CANBK","yf":"CANBK.NS","sector":"Financial Services"},
    {"sym":"CANHLIFE","yf":"CANHLIFE.NS","sector":"Financial Services"},
    {"sym":"CAPLIPOINT","yf":"CAPLIPOINT.NS","sector":"Healthcare"},
    {"sym":"CGCL","yf":"CGCL.NS","sector":"Financial Services"},
    {"sym":"CARBORUNIV","yf":"CARBORUNIV.NS","sector":"Capital Goods"},
    {"sym":"CARTRADE","yf":"CARTRADE.NS","sector":"Consumer Services"},
    {"sym":"CASTROLIND","yf":"CASTROLIND.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"CEATLTD","yf":"CEATLTD.NS","sector":"Automobile and Auto Components"},
    {"sym":"CEMPRO","yf":"CEMPRO.NS","sector":"Construction"},
    {"sym":"CENTRALBK","yf":"CENTRALBK.NS","sector":"Financial Services"},
    {"sym":"CDSL","yf":"CDSL.NS","sector":"Financial Services"},
    {"sym":"CHALET","yf":"CHALET.NS","sector":"Consumer Services"},
    {"sym":"CHAMBLFERT","yf":"CHAMBLFERT.NS","sector":"Chemicals"},
    {"sym":"CHENNPETRO","yf":"CHENNPETRO.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"CHOICEIN","yf":"CHOICEIN.NS","sector":"Financial Services"},
    {"sym":"CHOLAHLDNG","yf":"CHOLAHLDNG.NS","sector":"Financial Services"},
    {"sym":"CHOLAFIN","yf":"CHOLAFIN.NS","sector":"Financial Services"},
    {"sym":"CIPLA","yf":"CIPLA.NS","sector":"Healthcare"},
    {"sym":"CUB","yf":"CUB.NS","sector":"Financial Services"},
    {"sym":"CLEAN","yf":"CLEAN.NS","sector":"Chemicals"},
    {"sym":"COALINDIA","yf":"COALINDIA.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"COCHINSHIP","yf":"COCHINSHIP.NS","sector":"Capital Goods"},
    {"sym":"COFORGE","yf":"COFORGE.NS","sector":"Information Technology"},
    {"sym":"COHANCE","yf":"COHANCE.NS","sector":"Healthcare"},
    {"sym":"COLPAL","yf":"COLPAL.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"CAMS","yf":"CAMS.NS","sector":"Financial Services"},
    {"sym":"CONCORDBIO","yf":"CONCORDBIO.NS","sector":"Healthcare"},
    {"sym":"CONCOR","yf":"CONCOR.NS","sector":"Services"},
    {"sym":"COROMANDEL","yf":"COROMANDEL.NS","sector":"Chemicals"},
    {"sym":"CRAFTSMAN","yf":"CRAFTSMAN.NS","sector":"Automobile and Auto Components"},
    {"sym":"CREDITACC","yf":"CREDITACC.NS","sector":"Financial Services"},
    {"sym":"CROMPTON","yf":"CROMPTON.NS","sector":"Consumer Durables"},
    {"sym":"CUMMINSIND","yf":"CUMMINSIND.NS","sector":"Capital Goods"},
    {"sym":"CYIENT","yf":"CYIENT.NS","sector":"Information Technology"},
    {"sym":"DCMSHRIRAM","yf":"DCMSHRIRAM.NS","sector":"Diversified"},
    {"sym":"DLF","yf":"DLF.NS","sector":"Realty"},
    {"sym":"DOMS","yf":"DOMS.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"DABUR","yf":"DABUR.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"DALBHARAT","yf":"DALBHARAT.NS","sector":"Construction Materials"},
    {"sym":"DATAPATTNS","yf":"DATAPATTNS.NS","sector":"Capital Goods"},
    {"sym":"DEEPAKFERT","yf":"DEEPAKFERT.NS","sector":"Chemicals"},
    {"sym":"DEEPAKNTR","yf":"DEEPAKNTR.NS","sector":"Chemicals"},
    {"sym":"DELHIVERY","yf":"DELHIVERY.NS","sector":"Services"},
    {"sym":"DEVYANI","yf":"DEVYANI.NS","sector":"Consumer Services"},
    {"sym":"DIVISLAB","yf":"DIVISLAB.NS","sector":"Healthcare"},
    {"sym":"DIXON","yf":"DIXON.NS","sector":"Consumer Durables"},
    {"sym":"LALPATHLAB","yf":"LALPATHLAB.NS","sector":"Healthcare"},
    {"sym":"DRREDDY","yf":"DRREDDY.NS","sector":"Healthcare"},
    {"sym":"DUMMYVEDL1","yf":"DUMMYVEDL1.NS","sector":"Metals & Mining"},
    {"sym":"DUMMYVEDL2","yf":"DUMMYVEDL2.NS","sector":"Power"},
    {"sym":"DUMMYVEDL3","yf":"DUMMYVEDL3.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"DUMMYVEDL4","yf":"DUMMYVEDL4.NS","sector":"Metals & Mining"},
    {"sym":"EIDPARRY","yf":"EIDPARRY.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"EIHOTEL","yf":"EIHOTEL.NS","sector":"Consumer Services"},
    {"sym":"EICHERMOT","yf":"EICHERMOT.NS","sector":"Automobile and Auto Components"},
    {"sym":"ELECON","yf":"ELECON.NS","sector":"Capital Goods"},
    {"sym":"ELGIEQUIP","yf":"ELGIEQUIP.NS","sector":"Capital Goods"},
    {"sym":"EMAMILTD","yf":"EMAMILTD.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"EMCURE","yf":"EMCURE.NS","sector":"Healthcare"},
    {"sym":"EMMVEE","yf":"EMMVEE.NS","sector":"Capital Goods"},
    {"sym":"ENDURANCE","yf":"ENDURANCE.NS","sector":"Automobile and Auto Components"},
    {"sym":"ENGINERSIN","yf":"ENGINERSIN.NS","sector":"Construction"},
    {"sym":"ERIS","yf":"ERIS.NS","sector":"Healthcare"},
    {"sym":"ESCORTS","yf":"ESCORTS.NS","sector":"Capital Goods"},
    {"sym":"ETERNAL","yf":"ETERNAL.NS","sector":"Consumer Services"},
    {"sym":"EXIDEIND","yf":"EXIDEIND.NS","sector":"Automobile and Auto Components"},
    {"sym":"NYKAA","yf":"NYKAA.NS","sector":"Consumer Services"},
    {"sym":"FEDERALBNK","yf":"FEDERALBNK.NS","sector":"Financial Services"},
    {"sym":"FACT","yf":"FACT.NS","sector":"Chemicals"},
    {"sym":"FINCABLES","yf":"FINCABLES.NS","sector":"Capital Goods"},
    {"sym":"FSL","yf":"FSL.NS","sector":"Services"},
    {"sym":"FIVESTAR","yf":"FIVESTAR.NS","sector":"Financial Services"},
    {"sym":"FORCEMOT","yf":"FORCEMOT.NS","sector":"Automobile and Auto Components"},
    {"sym":"FORTIS","yf":"FORTIS.NS","sector":"Healthcare"},
    {"sym":"GAIL","yf":"GAIL.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"GVT&D","yf":"GVT&D.NS","sector":"Capital Goods"},
    {"sym":"GMRAIRPORT","yf":"GMRAIRPORT.NS","sector":"Services"},
    {"sym":"GABRIEL","yf":"GABRIEL.NS","sector":"Automobile and Auto Components"},
    {"sym":"GALLANTT","yf":"GALLANTT.NS","sector":"Capital Goods"},
    {"sym":"GRSE","yf":"GRSE.NS","sector":"Capital Goods"},
    {"sym":"GICRE","yf":"GICRE.NS","sector":"Financial Services"},
    {"sym":"GILLETTE","yf":"GILLETTE.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"GLAND","yf":"GLAND.NS","sector":"Healthcare"},
    {"sym":"GLAXO","yf":"GLAXO.NS","sector":"Healthcare"},
    {"sym":"GLENMARK","yf":"GLENMARK.NS","sector":"Healthcare"},
    {"sym":"MEDANTA","yf":"MEDANTA.NS","sector":"Healthcare"},
    {"sym":"GODIGIT","yf":"GODIGIT.NS","sector":"Financial Services"},
    {"sym":"GPIL","yf":"GPIL.NS","sector":"Capital Goods"},
    {"sym":"GODFRYPHLP","yf":"GODFRYPHLP.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"GODREJCP","yf":"GODREJCP.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"GODREJIND","yf":"GODREJIND.NS","sector":"Diversified"},
    {"sym":"GODREJPROP","yf":"GODREJPROP.NS","sector":"Realty"},
    {"sym":"GRANULES","yf":"GRANULES.NS","sector":"Healthcare"},
    {"sym":"GRAPHITE","yf":"GRAPHITE.NS","sector":"Capital Goods"},
    {"sym":"GRASIM","yf":"GRASIM.NS","sector":"Construction Materials"},
    {"sym":"GRAVITA","yf":"GRAVITA.NS","sector":"Metals & Mining"},
    {"sym":"GESHIP","yf":"GESHIP.NS","sector":"Services"},
    {"sym":"FLUOROCHEM","yf":"FLUOROCHEM.NS","sector":"Chemicals"},
    {"sym":"GMDCLTD","yf":"GMDCLTD.NS","sector":"Metals & Mining"},
    {"sym":"HEG","yf":"HEG.NS","sector":"Capital Goods"},
    {"sym":"HBLENGINE","yf":"HBLENGINE.NS","sector":"Capital Goods"},
    {"sym":"HCLTECH","yf":"HCLTECH.NS","sector":"Information Technology"},
    {"sym":"HDBFS","yf":"HDBFS.NS","sector":"Financial Services"},
    {"sym":"HDFCAMC","yf":"HDFCAMC.NS","sector":"Financial Services"},
    {"sym":"HDFCBANK","yf":"HDFCBANK.NS","sector":"Financial Services"},
    {"sym":"HDFCLIFE","yf":"HDFCLIFE.NS","sector":"Financial Services"},
    {"sym":"HFCL","yf":"HFCL.NS","sector":"Telecommunication"},
    {"sym":"HAVELLS","yf":"HAVELLS.NS","sector":"Consumer Durables"},
    {"sym":"HEROMOTOCO","yf":"HEROMOTOCO.NS","sector":"Automobile and Auto Components"},
    {"sym":"HEXT","yf":"HEXT.NS","sector":"Information Technology"},
    {"sym":"HSCL","yf":"HSCL.NS","sector":"Chemicals"},
    {"sym":"HINDALCO","yf":"HINDALCO.NS","sector":"Metals & Mining"},
    {"sym":"HAL","yf":"HAL.NS","sector":"Capital Goods"},
    {"sym":"HINDCOPPER","yf":"HINDCOPPER.NS","sector":"Metals & Mining"},
    {"sym":"HINDPETRO","yf":"HINDPETRO.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"HINDUNILVR","yf":"HINDUNILVR.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"HINDZINC","yf":"HINDZINC.NS","sector":"Metals & Mining"},
    {"sym":"POWERINDIA","yf":"POWERINDIA.NS","sector":"Capital Goods"},
    {"sym":"HOMEFIRST","yf":"HOMEFIRST.NS","sector":"Financial Services"},
    {"sym":"HONASA","yf":"HONASA.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"HONAUT","yf":"HONAUT.NS","sector":"Capital Goods"},
    {"sym":"HUDCO","yf":"HUDCO.NS","sector":"Financial Services"},
    {"sym":"HYUNDAI","yf":"HYUNDAI.NS","sector":"Automobile and Auto Components"},
    {"sym":"ICICIBANK","yf":"ICICIBANK.NS","sector":"Financial Services"},
    {"sym":"ICICIGI","yf":"ICICIGI.NS","sector":"Financial Services"},
    {"sym":"ICICIAMC","yf":"ICICIAMC.NS","sector":"Financial Services"},
    {"sym":"ICICIPRULI","yf":"ICICIPRULI.NS","sector":"Financial Services"},
    {"sym":"IDBI","yf":"IDBI.NS","sector":"Financial Services"},
    {"sym":"IDFCFIRSTB","yf":"IDFCFIRSTB.NS","sector":"Financial Services"},
    {"sym":"IFCI","yf":"IFCI.NS","sector":"Financial Services"},
    {"sym":"IIFL","yf":"IIFL.NS","sector":"Financial Services"},
    {"sym":"IRB","yf":"IRB.NS","sector":"Construction"},
    {"sym":"IRCON","yf":"IRCON.NS","sector":"Construction"},
    {"sym":"ITCHOTELS","yf":"ITCHOTELS.NS","sector":"Consumer Services"},
    {"sym":"ITC","yf":"ITC.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"ITI","yf":"ITI.NS","sector":"Telecommunication"},
    {"sym":"INDGN","yf":"INDGN.NS","sector":"Healthcare"},
    {"sym":"INDIACEM","yf":"INDIACEM.NS","sector":"Construction Materials"},
    {"sym":"INDIAMART","yf":"INDIAMART.NS","sector":"Consumer Services"},
    {"sym":"INDIANB","yf":"INDIANB.NS","sector":"Financial Services"},
    {"sym":"IEX","yf":"IEX.NS","sector":"Financial Services"},
    {"sym":"INDHOTEL","yf":"INDHOTEL.NS","sector":"Consumer Services"},
    {"sym":"IOC","yf":"IOC.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"IOB","yf":"IOB.NS","sector":"Financial Services"},
    {"sym":"IRCTC","yf":"IRCTC.NS","sector":"Consumer Services"},
    {"sym":"IRFC","yf":"IRFC.NS","sector":"Financial Services"},
    {"sym":"IREDA","yf":"IREDA.NS","sector":"Financial Services"},
    {"sym":"IGL","yf":"IGL.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"INDUSTOWER","yf":"INDUSTOWER.NS","sector":"Telecommunication"},
    {"sym":"INDUSINDBK","yf":"INDUSINDBK.NS","sector":"Financial Services"},
    {"sym":"NAUKRI","yf":"NAUKRI.NS","sector":"Consumer Services"},
    {"sym":"INFY","yf":"INFY.NS","sector":"Information Technology"},
    {"sym":"INOXWIND","yf":"INOXWIND.NS","sector":"Capital Goods"},
    {"sym":"INTELLECT","yf":"INTELLECT.NS","sector":"Information Technology"},
    {"sym":"INDIGO","yf":"INDIGO.NS","sector":"Services"},
    {"sym":"IGIL","yf":"IGIL.NS","sector":"Services"},
    {"sym":"IKS","yf":"IKS.NS","sector":"Information Technology"},
    {"sym":"IPCALAB","yf":"IPCALAB.NS","sector":"Healthcare"},
    {"sym":"JBCHEPHARM","yf":"JBCHEPHARM.NS","sector":"Healthcare"},
    {"sym":"JKCEMENT","yf":"JKCEMENT.NS","sector":"Construction Materials"},
    {"sym":"JBMA","yf":"JBMA.NS","sector":"Automobile and Auto Components"},
    {"sym":"JKTYRE","yf":"JKTYRE.NS","sector":"Automobile and Auto Components"},
    {"sym":"JMFINANCIL","yf":"JMFINANCIL.NS","sector":"Financial Services"},
    {"sym":"JSWCEMENT","yf":"JSWCEMENT.NS","sector":"Construction Materials"},
    {"sym":"JSWDULUX","yf":"JSWDULUX.NS","sector":"Consumer Durables"},
    {"sym":"JSWENERGY","yf":"JSWENERGY.NS","sector":"Power"},
    {"sym":"JSWINFRA","yf":"JSWINFRA.NS","sector":"Services"},
    {"sym":"JSWSTEEL","yf":"JSWSTEEL.NS","sector":"Metals & Mining"},
    {"sym":"JAINREC","yf":"JAINREC.NS","sector":"Metals & Mining"},
    {"sym":"JPPOWER","yf":"JPPOWER.NS","sector":"Power"},
    {"sym":"J&KBANK","yf":"J&KBANK.NS","sector":"Financial Services"},
    {"sym":"JINDALSAW","yf":"JINDALSAW.NS","sector":"Capital Goods"},
    {"sym":"JSL","yf":"JSL.NS","sector":"Metals & Mining"},
    {"sym":"JINDALSTEL","yf":"JINDALSTEL.NS","sector":"Metals & Mining"},
    {"sym":"JIOFIN","yf":"JIOFIN.NS","sector":"Financial Services"},
    {"sym":"JUBLFOOD","yf":"JUBLFOOD.NS","sector":"Consumer Services"},
    {"sym":"JUBLINGREA","yf":"JUBLINGREA.NS","sector":"Chemicals"},
    {"sym":"JUBLPHARMA","yf":"JUBLPHARMA.NS","sector":"Healthcare"},
    {"sym":"JWL","yf":"JWL.NS","sector":"Capital Goods"},
    {"sym":"JYOTICNC","yf":"JYOTICNC.NS","sector":"Capital Goods"},
    {"sym":"KPRMILL","yf":"KPRMILL.NS","sector":"Textiles"},
    {"sym":"KEI","yf":"KEI.NS","sector":"Capital Goods"},
    {"sym":"KPITTECH","yf":"KPITTECH.NS","sector":"Information Technology"},
    {"sym":"KAJARIACER","yf":"KAJARIACER.NS","sector":"Consumer Durables"},
    {"sym":"KPIL","yf":"KPIL.NS","sector":"Construction"},
    {"sym":"KALYANKJIL","yf":"KALYANKJIL.NS","sector":"Consumer Durables"},
    {"sym":"KARURVYSYA","yf":"KARURVYSYA.NS","sector":"Financial Services"},
    {"sym":"KAYNES","yf":"KAYNES.NS","sector":"Capital Goods"},
    {"sym":"KEC","yf":"KEC.NS","sector":"Construction"},
    {"sym":"KFINTECH","yf":"KFINTECH.NS","sector":"Financial Services"},
    {"sym":"KIRLOSENG","yf":"KIRLOSENG.NS","sector":"Capital Goods"},
    {"sym":"KOTAKBANK","yf":"KOTAKBANK.NS","sector":"Financial Services"},
    {"sym":"KIMS","yf":"KIMS.NS","sector":"Healthcare"},
    {"sym":"LTF","yf":"LTF.NS","sector":"Financial Services"},
    {"sym":"LTTS","yf":"LTTS.NS","sector":"Information Technology"},
    {"sym":"LGEINDIA","yf":"LGEINDIA.NS","sector":"Consumer Durables"},
    {"sym":"LICHSGFIN","yf":"LICHSGFIN.NS","sector":"Financial Services"},
    {"sym":"LTFOODS","yf":"LTFOODS.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"LTM","yf":"LTM.NS","sector":"Information Technology"},
    {"sym":"LT","yf":"LT.NS","sector":"Construction"},
    {"sym":"LATENTVIEW","yf":"LATENTVIEW.NS","sector":"Information Technology"},
    {"sym":"LAURUSLABS","yf":"LAURUSLABS.NS","sector":"Healthcare"},
    {"sym":"THELEELA","yf":"THELEELA.NS","sector":"Consumer Services"},
    {"sym":"LEMONTREE","yf":"LEMONTREE.NS","sector":"Consumer Services"},
    {"sym":"LENSKART","yf":"LENSKART.NS","sector":"Consumer Services"},
    {"sym":"LICI","yf":"LICI.NS","sector":"Financial Services"},
    {"sym":"LINDEINDIA","yf":"LINDEINDIA.NS","sector":"Chemicals"},
    {"sym":"LLOYDSME","yf":"LLOYDSME.NS","sector":"Metals & Mining"},
    {"sym":"LODHA","yf":"LODHA.NS","sector":"Realty"},
    {"sym":"LUPIN","yf":"LUPIN.NS","sector":"Healthcare"},
    {"sym":"MMTC","yf":"MMTC.NS","sector":"Services"},
    {"sym":"MRF","yf":"MRF.NS","sector":"Automobile and Auto Components"},
    {"sym":"MGL","yf":"MGL.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"M&MFIN","yf":"M&MFIN.NS","sector":"Financial Services"},
    {"sym":"M&M","yf":"M&M.NS","sector":"Automobile and Auto Components"},
    {"sym":"MANAPPURAM","yf":"MANAPPURAM.NS","sector":"Financial Services"},
    {"sym":"MRPL","yf":"MRPL.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"MANKIND","yf":"MANKIND.NS","sector":"Healthcare"},
    {"sym":"MARICO","yf":"MARICO.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"MARUTI","yf":"MARUTI.NS","sector":"Automobile and Auto Components"},
    {"sym":"MFSL","yf":"MFSL.NS","sector":"Financial Services"},
    {"sym":"MAXHEALTH","yf":"MAXHEALTH.NS","sector":"Healthcare"},
    {"sym":"MAZDOCK","yf":"MAZDOCK.NS","sector":"Capital Goods"},
    {"sym":"MEESHO","yf":"MEESHO.NS","sector":"Consumer Services"},
    {"sym":"MINDACORP","yf":"MINDACORP.NS","sector":"Automobile and Auto Components"},
    {"sym":"MSUMI","yf":"MSUMI.NS","sector":"Automobile and Auto Components"},
    {"sym":"MOTILALOFS","yf":"MOTILALOFS.NS","sector":"Financial Services"},
    {"sym":"MPHASIS","yf":"MPHASIS.NS","sector":"Information Technology"},
    {"sym":"MCX","yf":"MCX.NS","sector":"Financial Services"},
    {"sym":"MUTHOOTFIN","yf":"MUTHOOTFIN.NS","sector":"Financial Services"},
    {"sym":"NATCOPHARM","yf":"NATCOPHARM.NS","sector":"Healthcare"},
    {"sym":"NBCC","yf":"NBCC.NS","sector":"Construction"},
    {"sym":"NCC","yf":"NCC.NS","sector":"Construction"},
    {"sym":"NHPC","yf":"NHPC.NS","sector":"Power"},
    {"sym":"NLCINDIA","yf":"NLCINDIA.NS","sector":"Power"},
    {"sym":"NMDC","yf":"NMDC.NS","sector":"Metals & Mining"},
    {"sym":"NSLNISP","yf":"NSLNISP.NS","sector":"Metals & Mining"},
    {"sym":"NTPCGREEN","yf":"NTPCGREEN.NS","sector":"Power"},
    {"sym":"NTPC","yf":"NTPC.NS","sector":"Power"},
    {"sym":"NH","yf":"NH.NS","sector":"Healthcare"},
    {"sym":"NATIONALUM","yf":"NATIONALUM.NS","sector":"Metals & Mining"},
    {"sym":"NAVA","yf":"NAVA.NS","sector":"Power"},
    {"sym":"NAVINFLUOR","yf":"NAVINFLUOR.NS","sector":"Chemicals"},
    {"sym":"NESTLEIND","yf":"NESTLEIND.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"NETWEB","yf":"NETWEB.NS","sector":"Information Technology"},
    {"sym":"NEULANDLAB","yf":"NEULANDLAB.NS","sector":"Healthcare"},
    {"sym":"NEWGEN","yf":"NEWGEN.NS","sector":"Information Technology"},
    {"sym":"NAM-INDIA","yf":"NAM-INDIA.NS","sector":"Financial Services"},
    {"sym":"NIVABUPA","yf":"NIVABUPA.NS","sector":"Financial Services"},
    {"sym":"NUVAMA","yf":"NUVAMA.NS","sector":"Financial Services"},
    {"sym":"NUVOCO","yf":"NUVOCO.NS","sector":"Construction Materials"},
    {"sym":"OBEROIRLTY","yf":"OBEROIRLTY.NS","sector":"Realty"},
    {"sym":"ONGC","yf":"ONGC.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"OIL","yf":"OIL.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"OLAELEC","yf":"OLAELEC.NS","sector":"Automobile and Auto Components"},
    {"sym":"OLECTRA","yf":"OLECTRA.NS","sector":"Automobile and Auto Components"},
    {"sym":"PAYTM","yf":"PAYTM.NS","sector":"Financial Services"},
    {"sym":"ONESOURCE","yf":"ONESOURCE.NS","sector":"Healthcare"},
    {"sym":"OFSS","yf":"OFSS.NS","sector":"Information Technology"},
    {"sym":"POLICYBZR","yf":"POLICYBZR.NS","sector":"Financial Services"},
    {"sym":"PCBL","yf":"PCBL.NS","sector":"Chemicals"},
    {"sym":"PGEL","yf":"PGEL.NS","sector":"Consumer Durables"},
    {"sym":"PIIND","yf":"PIIND.NS","sector":"Chemicals"},
    {"sym":"PNBHOUSING","yf":"PNBHOUSING.NS","sector":"Financial Services"},
    {"sym":"PTCIL","yf":"PTCIL.NS","sector":"Capital Goods"},
    {"sym":"PVRINOX","yf":"PVRINOX.NS","sector":"Media Entertainment & Publication"},
    {"sym":"PAGEIND","yf":"PAGEIND.NS","sector":"Textiles"},
    {"sym":"PARADEEP","yf":"PARADEEP.NS","sector":"Chemicals"},
    {"sym":"PATANJALI","yf":"PATANJALI.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"PERSISTENT","yf":"PERSISTENT.NS","sector":"Information Technology"},
    {"sym":"PETRONET","yf":"PETRONET.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"PFIZER","yf":"PFIZER.NS","sector":"Healthcare"},
    {"sym":"PHOENIXLTD","yf":"PHOENIXLTD.NS","sector":"Realty"},
    {"sym":"PWL","yf":"PWL.NS","sector":"Consumer Services"},
    {"sym":"PIDILITIND","yf":"PIDILITIND.NS","sector":"Chemicals"},
    {"sym":"PINELABS","yf":"PINELABS.NS","sector":"Financial Services"},
    {"sym":"PIRAMALFIN","yf":"PIRAMALFIN.NS","sector":"Financial Services"},
    {"sym":"PPLPHARMA","yf":"PPLPHARMA.NS","sector":"Healthcare"},
    {"sym":"POLYMED","yf":"POLYMED.NS","sector":"Healthcare"},
    {"sym":"POLYCAB","yf":"POLYCAB.NS","sector":"Capital Goods"},
    {"sym":"POONAWALLA","yf":"POONAWALLA.NS","sector":"Financial Services"},
    {"sym":"PFC","yf":"PFC.NS","sector":"Financial Services"},
    {"sym":"POWERGRID","yf":"POWERGRID.NS","sector":"Power"},
    {"sym":"PREMIERENE","yf":"PREMIERENE.NS","sector":"Capital Goods"},
    {"sym":"PRESTIGE","yf":"PRESTIGE.NS","sector":"Realty"},
    {"sym":"PNB","yf":"PNB.NS","sector":"Financial Services"},
    {"sym":"RRKABEL","yf":"RRKABEL.NS","sector":"Capital Goods"},
    {"sym":"RBLBANK","yf":"RBLBANK.NS","sector":"Financial Services"},
    {"sym":"RECLTD","yf":"RECLTD.NS","sector":"Financial Services"},
    {"sym":"RHIM","yf":"RHIM.NS","sector":"Capital Goods"},
    {"sym":"RITES","yf":"RITES.NS","sector":"Construction"},
    {"sym":"RADICO","yf":"RADICO.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"RVNL","yf":"RVNL.NS","sector":"Construction"},
    {"sym":"RAILTEL","yf":"RAILTEL.NS","sector":"Telecommunication"},
    {"sym":"RAINBOW","yf":"RAINBOW.NS","sector":"Healthcare"},
    {"sym":"RKFORGE","yf":"RKFORGE.NS","sector":"Automobile and Auto Components"},
    {"sym":"REDINGTON","yf":"REDINGTON.NS","sector":"Services"},
    {"sym":"RELIANCE","yf":"RELIANCE.NS","sector":"Oil Gas & Consumable Fuels"},
    {"sym":"RPOWER","yf":"RPOWER.NS","sector":"Power"},
    {"sym":"SBFC","yf":"SBFC.NS","sector":"Financial Services"},
    {"sym":"SBICARD","yf":"SBICARD.NS","sector":"Financial Services"},
    {"sym":"SBILIFE","yf":"SBILIFE.NS","sector":"Financial Services"},
    {"sym":"SJVN","yf":"SJVN.NS","sector":"Power"},
    {"sym":"SRF","yf":"SRF.NS","sector":"Chemicals"},
    {"sym":"SAGILITY","yf":"SAGILITY.NS","sector":"Information Technology"},
    {"sym":"SAILIFE","yf":"SAILIFE.NS","sector":"Healthcare"},
    {"sym":"SAMMAANCAP","yf":"SAMMAANCAP.NS","sector":"Financial Services"},
    {"sym":"MOTHERSON","yf":"MOTHERSON.NS","sector":"Automobile and Auto Components"},
    {"sym":"SAPPHIRE","yf":"SAPPHIRE.NS","sector":"Consumer Services"},
    {"sym":"SARDAEN","yf":"SARDAEN.NS","sector":"Metals & Mining"},
    {"sym":"SAREGAMA","yf":"SAREGAMA.NS","sector":"Media Entertainment & Publication"},
    {"sym":"SCHAEFFLER","yf":"SCHAEFFLER.NS","sector":"Automobile and Auto Components"},
    {"sym":"SCHNEIDER","yf":"SCHNEIDER.NS","sector":"Capital Goods"},
    {"sym":"SCI","yf":"SCI.NS","sector":"Services"},
    {"sym":"SHREECEM","yf":"SHREECEM.NS","sector":"Construction Materials"},
    {"sym":"SHRIRAMFIN","yf":"SHRIRAMFIN.NS","sector":"Financial Services"},
    {"sym":"SHYAMMETL","yf":"SHYAMMETL.NS","sector":"Capital Goods"},
    {"sym":"ENRIN","yf":"ENRIN.NS","sector":"Capital Goods"},
    {"sym":"SIEMENS","yf":"SIEMENS.NS","sector":"Capital Goods"},
    {"sym":"SIGNATURE","yf":"SIGNATURE.NS","sector":"Realty"},
    {"sym":"SOBHA","yf":"SOBHA.NS","sector":"Realty"},
    {"sym":"SOLARINDS","yf":"SOLARINDS.NS","sector":"Chemicals"},
    {"sym":"SONACOMS","yf":"SONACOMS.NS","sector":"Automobile and Auto Components"},
    {"sym":"SONATSOFTW","yf":"SONATSOFTW.NS","sector":"Information Technology"},
    {"sym":"STARHEALTH","yf":"STARHEALTH.NS","sector":"Financial Services"},
    {"sym":"SBIN","yf":"SBIN.NS","sector":"Financial Services"},
    {"sym":"SAIL","yf":"SAIL.NS","sector":"Metals & Mining"},
    {"sym":"SUMICHEM","yf":"SUMICHEM.NS","sector":"Chemicals"},
    {"sym":"SUNPHARMA","yf":"SUNPHARMA.NS","sector":"Healthcare"},
    {"sym":"SUNTV","yf":"SUNTV.NS","sector":"Media Entertainment & Publication"},
    {"sym":"SUNDARMFIN","yf":"SUNDARMFIN.NS","sector":"Financial Services"},
    {"sym":"SUPREMEIND","yf":"SUPREMEIND.NS","sector":"Capital Goods"},
    {"sym":"SPLPETRO","yf":"SPLPETRO.NS","sector":"Chemicals"},
    {"sym":"SUZLON","yf":"SUZLON.NS","sector":"Capital Goods"},
    {"sym":"SWANCORP","yf":"SWANCORP.NS","sector":"Chemicals"},
    {"sym":"SWIGGY","yf":"SWIGGY.NS","sector":"Consumer Services"},
    {"sym":"SYNGENE","yf":"SYNGENE.NS","sector":"Healthcare"},
    {"sym":"SYRMA","yf":"SYRMA.NS","sector":"Capital Goods"},
    {"sym":"TBOTEK","yf":"TBOTEK.NS","sector":"Consumer Services"},
    {"sym":"TVSMOTOR","yf":"TVSMOTOR.NS","sector":"Automobile and Auto Components"},
    {"sym":"TATACAP","yf":"TATACAP.NS","sector":"Financial Services"},
    {"sym":"TATACHEM","yf":"TATACHEM.NS","sector":"Chemicals"},
    {"sym":"TATACOMM","yf":"TATACOMM.NS","sector":"Telecommunication"},
    {"sym":"TCS","yf":"TCS.NS","sector":"Information Technology"},
    {"sym":"TATACONSUM","yf":"TATACONSUM.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"TATAELXSI","yf":"TATAELXSI.NS","sector":"Information Technology"},
    {"sym":"TATAINVEST","yf":"TATAINVEST.NS","sector":"Financial Services"},
    {"sym":"TMCV","yf":"TMCV.NS","sector":"Capital Goods"},
    {"sym":"TMPV","yf":"TMPV.NS","sector":"Automobile and Auto Components"},
    {"sym":"TATAPOWER","yf":"TATAPOWER.NS","sector":"Power"},
    {"sym":"TATASTEEL","yf":"TATASTEEL.NS","sector":"Metals & Mining"},
    {"sym":"TATATECH","yf":"TATATECH.NS","sector":"Information Technology"},
    {"sym":"TTML","yf":"TTML.NS","sector":"Telecommunication"},
    {"sym":"TECHM","yf":"TECHM.NS","sector":"Information Technology"},
    {"sym":"TECHNOE","yf":"TECHNOE.NS","sector":"Construction"},
    {"sym":"TEGA","yf":"TEGA.NS","sector":"Capital Goods"},
    {"sym":"TEJASNET","yf":"TEJASNET.NS","sector":"Telecommunication"},
    {"sym":"TENNIND","yf":"TENNIND.NS","sector":"Automobile and Auto Components"},
    {"sym":"NIACL","yf":"NIACL.NS","sector":"Financial Services"},
    {"sym":"RAMCOCEM","yf":"RAMCOCEM.NS","sector":"Construction Materials"},
    {"sym":"THERMAX","yf":"THERMAX.NS","sector":"Capital Goods"},
    {"sym":"TIMKEN","yf":"TIMKEN.NS","sector":"Capital Goods"},
    {"sym":"TITAGARH","yf":"TITAGARH.NS","sector":"Capital Goods"},
    {"sym":"TITAN","yf":"TITAN.NS","sector":"Consumer Durables"},
    {"sym":"TORNTPHARM","yf":"TORNTPHARM.NS","sector":"Healthcare"},
    {"sym":"TORNTPOWER","yf":"TORNTPOWER.NS","sector":"Power"},
    {"sym":"TARIL","yf":"TARIL.NS","sector":"Capital Goods"},
    {"sym":"TRAVELFOOD","yf":"TRAVELFOOD.NS","sector":"Consumer Services"},
    {"sym":"TRENT","yf":"TRENT.NS","sector":"Consumer Services"},
    {"sym":"TRIDENT","yf":"TRIDENT.NS","sector":"Textiles"},
    {"sym":"TRITURBINE","yf":"TRITURBINE.NS","sector":"Capital Goods"},
    {"sym":"TIINDIA","yf":"TIINDIA.NS","sector":"Automobile and Auto Components"},
    {"sym":"UCOBANK","yf":"UCOBANK.NS","sector":"Financial Services"},
    {"sym":"UNOMINDA","yf":"UNOMINDA.NS","sector":"Automobile and Auto Components"},
    {"sym":"UPL","yf":"UPL.NS","sector":"Chemicals"},
    {"sym":"UTIAMC","yf":"UTIAMC.NS","sector":"Financial Services"},
    {"sym":"ULTRACEMCO","yf":"ULTRACEMCO.NS","sector":"Construction Materials"},
    {"sym":"UNIONBANK","yf":"UNIONBANK.NS","sector":"Financial Services"},
    {"sym":"UBL","yf":"UBL.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"UNITDSPR","yf":"UNITDSPR.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"URBANCO","yf":"URBANCO.NS","sector":"Consumer Services"},
    {"sym":"USHAMART","yf":"USHAMART.NS","sector":"Capital Goods"},
    {"sym":"VTL","yf":"VTL.NS","sector":"Textiles"},
    {"sym":"VBL","yf":"VBL.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"VEDL","yf":"VEDL.NS","sector":"Metals & Mining"},
    {"sym":"VIJAYA","yf":"VIJAYA.NS","sector":"Healthcare"},
    {"sym":"VMM","yf":"VMM.NS","sector":"Consumer Services"},
    {"sym":"IDEA","yf":"IDEA.NS","sector":"Telecommunication"},
    {"sym":"VOLTAS","yf":"VOLTAS.NS","sector":"Consumer Durables"},
    {"sym":"WAAREEENER","yf":"WAAREEENER.NS","sector":"Capital Goods"},
    {"sym":"WELCORP","yf":"WELCORP.NS","sector":"Capital Goods"},
    {"sym":"WELSPUNLIV","yf":"WELSPUNLIV.NS","sector":"Textiles"},
    {"sym":"WHIRLPOOL","yf":"WHIRLPOOL.NS","sector":"Consumer Durables"},
    {"sym":"WIPRO","yf":"WIPRO.NS","sector":"Information Technology"},
    {"sym":"WOCKPHARMA","yf":"WOCKPHARMA.NS","sector":"Healthcare"},
    {"sym":"YESBANK","yf":"YESBANK.NS","sector":"Financial Services"},
    {"sym":"ZFCVINDIA","yf":"ZFCVINDIA.NS","sector":"Automobile and Auto Components"},
    {"sym":"ZEEL","yf":"ZEEL.NS","sector":"Media Entertainment & Publication"},
    {"sym":"ZENTEC","yf":"ZENTEC.NS","sector":"Capital Goods"},
    {"sym":"ZENSARTECH","yf":"ZENSARTECH.NS","sector":"Information Technology"},
    {"sym":"ZYDUSLIFE","yf":"ZYDUSLIFE.NS","sector":"Healthcare"},
    {"sym":"ZYDUSWELL","yf":"ZYDUSWELL.NS","sector":"Fast Moving Consumer Goods"},
    {"sym":"ECLERX","yf":"ECLERX.NS","sector":"Services"},
]

# ─────────────────────────────────────────────
# INDICATOR HELPERS
# ─────────────────────────────────────────────
def ema(c, p):
    if len(c) < p: return float(c[-1])
    k = 2 / (p + 1)
    e = float(c[0])
    for v in c[1:]: e = v * k + e * (1 - k)
    return round(e, 2)

def rsi(c, p=14):
    if len(c) < p + 2: return 50.0
    d = np.diff(np.array(c, dtype=float))
    g = np.where(d > 0, d, 0.0)
    lo = np.where(d < 0, -d, 0.0)
    ag = g[-p:].mean(); al = lo[-p:].mean()
    if al == 0: return 100.0
    return round(100 - 100 / (1 + ag / al), 1)

def atr(highs, lows, closes, p=14):
    trs = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
           for i in range(1, len(closes))]
    return float(np.mean(trs[-p:])) if trs else closes[-1] * 0.02

def detect_candle(o, h, l, c, prev_o, prev_c):
    """Detect bullish reversal candles"""
    body = abs(c - o)
    total_range = h - l if h > l else 0.001
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)

    patterns = []
    # Hammer: small body upper, long lower wick (at least 2x body), at support
    if c > o and lower_wick >= body * 2 and upper_wick < body * 0.5:
        patterns.append("Hammer")
    # Bullish Engulfing: current green body engulfs previous red body
    if c > o and prev_c < prev_o and c > prev_o and o < prev_c:
        patterns.append("Bullish Engulfing")
    # Strong green candle after pullback
    if c > o and (c - o) / total_range > 0.6 and body > 0:
        patterns.append("Strong Bull Bar")
    # Doji near support (indecision → potential reversal)
    if body / total_range < 0.2 and lower_wick > upper_wick:
        patterns.append("Bullish Doji")
    return patterns[0] if patterns else None

def find_breakout_level(closes, highs):
    """Find most recent breakout / consolidation level that could act as support"""
    n = len(closes)
    if n < 60: return None
    # Find the highest close in days 30-60 ago
    past_window = closes[n-60:n-20]
    if len(past_window) == 0: return None
    return round(float(max(past_window)), 2)

# ─────────────────────────────────────────────
# CORE ANALYSIS
# ─────────────────────────────────────────────
def analyze(stock):
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 220:
            return None

        closes = df["Close"].values.tolist()
        opens  = df["Open"].values.tolist()
        highs  = df["High"].values.tolist()
        lows   = df["Low"].values.tolist()
        vols   = df["Volume"].values.tolist()
        n = len(closes)

        price = closes[-1]

        # ── EMAs ──
        ema20  = ema(closes[-60:],   20)
        ema50  = ema(closes[-100:],  50)
        ema200 = ema(closes[-200:], 200)

        # ── 1. UPTREND FILTER ──
        if not (price > ema50 and price > ema200):
            return None  # must be in uptrend

        # ── 2. PULLBACK MEASURE ──
        recent_high = max(highs[-20:])
        pullback_pct = round((recent_high - price) / recent_high * 100, 2)
        if not (2.5 <= pullback_pct <= 10.0):
            return None  # pullback must be 2.5-10%

        # ── 3. AT KEY SUPPORT ──
        dist_ema20 = abs(price - ema20) / price * 100
        dist_ema50 = abs(price - ema50) / price * 100
        bo_level   = find_breakout_level(closes, highs)
        dist_bo    = abs(price - bo_level) / price * 100 if bo_level else 999

        near_ema20 = dist_ema20 < 2.5
        near_ema50 = dist_ema50 < 3.0
        near_bo    = dist_bo < 3.5

        if not (near_ema20 or near_ema50 or near_bo):
            return None  # must be at a meaningful support

        support_level = None
        support_name  = None
        if near_ema20:
            support_level = ema20; support_name = "20 EMA"
        elif near_ema50:
            support_level = ema50; support_name = "50 EMA"
        elif near_bo:
            support_level = bo_level; support_name = "Previous Breakout Level"

        # ── 4. REVERSAL CANDLE ──
        candle_pattern = detect_candle(
            opens[-1], highs[-1], lows[-1], closes[-1],
            opens[-2], closes[-2]
        )

        # ── 5. VOLUME ANALYSIS ──
        avg_vol_20 = float(np.mean(vols[-20:]))
        avg_vol_3d = float(np.mean(vols[-4:-1]))   # last 3 days (dip)
        today_vol  = vols[-1]
        vol_dry_up   = avg_vol_3d < avg_vol_20 * 0.75   # volume drying on dip
        vol_expanding = today_vol > avg_vol_20 * 1.1    # expanding on reversal
        vol_ratio     = round(today_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0

        # ── 6. RSI ──
        rsi_now  = rsi(closes[-30:])
        rsi_3d   = rsi(closes[-33:-3])
        in_buy_zone    = 40 <= rsi_now <= 62
        rsi_divergence = closes[-1] < closes[-5] and rsi_now > rsi_3d  # price lower, rsi higher

        # ── 7. SCORING (0-10) ──
        score = 0.0
        # Trend quality
        if price > ema200: score += 1.5
        if price > ema50:  score += 1.0
        # Pullback quality
        if 3.0 <= pullback_pct <= 7.0: score += 2.0
        else: score += 1.0
        # At clean support
        if near_ema20:  score += 1.5
        elif near_ema50: score += 1.2
        elif near_bo:   score += 1.0
        # Reversal signal
        if candle_pattern in ("Bullish Engulfing", "Hammer"): score += 1.5
        elif candle_pattern: score += 0.8
        # Volume
        if vol_dry_up:     score += 0.5
        if vol_expanding:  score += 0.8
        elif vol_ratio > 0.9: score += 0.3
        # RSI
        if in_buy_zone:     score += 0.8
        if rsi_divergence:  score += 0.7
        score = min(round(score, 1), 10.0)

        if score < 5.0:
            return None

        # ── TRADE LEVELS ──
        atr_val = atr(highs, lows, closes)
        swing_low = min(lows[-5:])
        stop_loss = round(swing_low - atr_val * 0.2, 2)
        risk = price - stop_loss
        if risk <= 0: return None

        t1 = round(price + risk * 2.0, 2)
        t2 = round(price + risk * 3.5, 2)
        rr = round((t1 - price) / risk, 1)

        # ── THESIS ──
        thesis_parts = [
            f"{stock['sym']} is in a confirmed uptrend (above 50 EMA at ₹{ema50:.0f} and 200 EMA at ₹{ema200:.0f}).",
            f"Price has pulled back {pullback_pct:.1f}% from its recent high of ₹{recent_high:.0f}.",
            f"Now retesting {support_name} (₹{support_level:.0f}) — a high-interest institutional demand zone.",
        ]
        if candle_pattern:
            thesis_parts.append(f"A {candle_pattern} pattern is forming, signaling buyers stepping in.")
        if vol_dry_up:
            thesis_parts.append(f"Volume dried up during the dip (avg 3d: {avg_vol_3d/1e5:.1f}L vs 20d avg: {avg_vol_20/1e5:.1f}L) — no institutional selling.")
        if vol_expanding:
            thesis_parts.append(f"Volume is NOW expanding on the reversal ({vol_ratio}x avg) — demand confirmation.")
        if in_buy_zone:
            thesis_parts.append(f"RSI at {rsi_now} — pulled back to neutral buy zone without becoming oversold.")
        if rsi_divergence:
            thesis_parts.append("RSI bullish divergence detected: price lower, RSI higher — momentum shifting.")

        entry_strategy = (
            f"Enter on a 15-min close above ₹{round(price + atr_val * 0.2, 0):.0f} "
            f"(above today's candle high) with volume confirmation. "
            f"Alternatively, wait for a 30-min candle close above the {support_name} retest zone."
        )
        if candle_pattern in ("Bullish Engulfing", "Hammer"):
            entry_strategy = (
                f"Enter NOW on market open confirmation or a 15-min hold above ₹{round(highs[-1], 0):.0f} "
                f"(today's {candle_pattern} high) with volume. Stop is firm below ₹{stop_loss:.0f}."
            )

        return {
            "sym":           stock["sym"],
            "sector":        stock["sector"],
            "price":         round(price, 2),
            "score":         score,
            "pullback_pct":  pullback_pct,
            "recent_high":   round(recent_high, 2),
            "support_level": round(support_level, 2),
            "support_name":  support_name,
            "candle":        candle_pattern or "No clear pattern yet",
            "ema20":         ema20,
            "ema50":         ema50,
            "ema200":        ema200,
            "rsi":           rsi_now,
            "vol_ratio":     vol_ratio,
            "vol_dry_up":    vol_dry_up,
            "vol_expanding": vol_expanding,
            "entry":         round(highs[-1] + 0.1, 2),
            "stop_loss":     stop_loss,
            "t1":            t1,
            "t2":            t2,
            "rr":            rr,
            "thesis":        " ".join(thesis_parts),
            "entry_strategy":entry_strategy,
        }
    except Exception as e:
        return None

def fetch_nifty50_context():
    try:
        df = yf.Ticker("^NSEI").history(period="3mo", interval="1d", auto_adjust=True)
        c = df["Close"].values.tolist()
        price = c[-1]
        e20 = ema(c[-60:], 20)
        e50 = ema(c[-100:], 50)
        e200 = ema(c[-200:] if len(c) >= 200 else c, 200)
        pct_chg = round((c[-1] - c[-2]) / c[-2] * 100, 2) if len(c) > 1 else 0
        trend = "BULLISH" if price > e50 > e200 else "BEARISH" if price < e50 < e200 else "MIXED"
        return {
            "price":  round(price, 2),
            "pct":    pct_chg,
            "ema20":  round(e20, 2),
            "ema50":  round(e50, 2),
            "ema200": round(e200, 2),
            "trend":  trend,
            "above50": price > e50,
            "above200": price > e200,
        }
    except:
        return {"price": 0, "pct": 0, "ema20": 0, "ema50": 0, "ema200": 0, "trend": "UNKNOWN", "above50": False, "above200": False}

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────
@app.route('/api/scan', methods=['GET'])
def run_scan():
    t0 = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(analyze, s): s for s in UNIVERSE}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    # Sort by score desc, take top 3 with sector diversity
    results.sort(key=lambda x: -x["score"])
    top3 = []
    seen_sectors = set()
    for r in results:
        if r["sector"] not in seen_sectors:
            top3.append(r)
            seen_sectors.add(r["sector"])
        if len(top3) >= 3:
            break
    # Fill up to 3 even if same sector
    if len(top3) < 3:
        for r in results:
            if r not in top3:
                top3.append(r)
            if len(top3) >= 3:
                break

    nifty = fetch_nifty50_context()
    elapsed = round(time.time() - t0, 1)

    return jsonify({
        "status": "success",
        "scan_time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "elapsed": elapsed,
        "scanned": len(UNIVERSE),
        "found": len(results),
        "nifty50": nifty,
        "picks": top3,
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

if __name__ == '__main__':
    print("Elite Pullback Scanner API — Starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
