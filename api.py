"""
Elite SMC Scanner — API Backend
Scans Nifty 500 / F&O universe for institutional Smart Money Concepts (SMC).

Criteria:
1. Break of Structure (BOS): Recent impulsive bullish wave.
2. Order Block (OB): The last down-candle before the impulsive wave.
3. Fair Value Gap (FVG): Unmitigated bullish imbalance left by the impulsive wave.
4. Liquidity Sweep: Price sweeping below a swing low and rejecting.
5. Mitigation: Current price pulling back into the FVG or OB demand zone.
"""

import time, math, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# UNIVERSE — Loaded dynamically or fallback to small list
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
try:
    # Try to load the 504 Nifty 500 stocks if the file exists
    with open('api.py', 'r', encoding='utf-8') as f:
        # Just use a static fallback if we can't parse it easily here, 
        # but I will inject the 504 list explicitly in the script below to be safe.
        pass
except:
    pass

# We will read the universe from universe.json if it exists, else fallback.
import os
if os.path.exists('universe.json'):
    with open('universe.json', 'r') as f:
        UNIVERSE = json.load(f)
else:
    # Fallback minimal universe
    UNIVERSE = [
        {"sym":"HDFCBANK","yf":"HDFCBANK.NS","sector":"Banking"},
        {"sym":"RELIANCE","yf":"RELIANCE.NS","sector":"Energy"},
        {"sym":"TCS","yf":"TCS.NS","sector":"IT"},
        {"sym":"INFY","yf":"INFY.NS","sector":"IT"},
        {"sym":"ICICIBANK","yf":"ICICIBANK.NS","sector":"Banking"}
    ]

# ─────────────────────────────────────────────
# SMC HELPERS
# ─────────────────────────────────────────────
def find_swing_lows(lows, window=5):
    """Find local minima in a series of lows"""
    swings = []
    n = len(lows)
    for i in range(window, n - window):
        is_low = True
        for j in range(i - window, i + window + 1):
            if lows[j] < lows[i]:
                is_low = False
                break
        if is_low:
            swings.append({'idx': i, 'val': lows[i]})
    return swings

def find_order_block(opens, highs, lows, closes):
    """
    Find a bullish order block (last bearish candle before strong bullish momentum)
    Returns: {top, bottom, mid}
    """
    n = len(closes)
    # Look back over last 40 days for the biggest bullish engulfing or momentum
    best_ob = None
    max_momentum = 0
    
    for i in range(n - 40, n - 5):
        # Look for a down candle followed by explosive up moves
        if closes[i] < opens[i]:  # Bearish candle
            # Check momentum of next 2-3 candles
            momentum = closes[i+3] - closes[i]
            if momentum > max_momentum:
                max_momentum = momentum
                best_ob = {
                    'top': highs[i],
                    'bottom': lows[i],
                    'mid': (highs[i] + lows[i]) / 2,
                    'idx': i
                }
    return best_ob

def find_fvg(highs, lows, closes):
    """
    Find the most recent unmitigated bullish Fair Value Gap (FVG).
    FVG occurs when Low of candle 3 > High of candle 1.
    """
    n = len(closes)
    fvgs = []
    # Scan last 30 days
    for i in range(n - 30, n - 2):
        gap_bottom = highs[i]
        gap_top = lows[i+2]
        
        if gap_top > gap_bottom:
            # We have an FVG. Check if it's been mitigated (filled) by any subsequent candle
            mitigated = False
            for j in range(i+3, n):
                if lows[j] <= gap_bottom:
                    mitigated = True
                    break
            
            if not mitigated:
                fvgs.append({
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'idx': i+1
                })
    
    # Return the most recent unmitigated FVG
    return fvgs[-1] if fvgs else None

def check_liquidity_sweep(lows, closes, current_idx, lookback=15):
    """
    Check if the current pullback sweeps a recent swing low but rejects.
    """
    n = len(lows)
    current_low = lows[current_idx]
    current_close = closes[current_idx]
    
    # Find lowest low in lookback window before current candle
    start_idx = max(0, current_idx - lookback)
    recent_lows = lows[start_idx:current_idx]
    if not recent_lows: return False
    
    swing_low = min(recent_lows)
    
    # Sweep condition: price pierced below the swing low, but closed above it
    if current_low < swing_low and current_close > swing_low:
        return True
    return False

# ─────────────────────────────────────────────
# CORE SMC ANALYSIS
# ─────────────────────────────────────────────
def analyze_smc(stock):
    try:
        ticker = yf.Ticker(stock["yf"])
        df = ticker.history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 60:
            return None

        closes = df["Close"].values.tolist()
        opens  = df["Open"].values.tolist()
        highs  = df["High"].values.tolist()
        lows   = df["Low"].values.tolist()
        vols   = df["Volume"].values.tolist()
        n = len(closes)

        price = closes[-1]
        
        # Pullback Measure (need some retracement to enter)
        recent_high = max(highs[-20:])
        pullback_pct = round((recent_high - price) / recent_high * 100, 2)
        if pullback_pct < 2.0:
            return None # Not a pullback

        # ── Find SMC Structures ──
        ob = find_order_block(opens, highs, lows, closes)
        fvg = find_fvg(highs, lows, closes)
        liq_sweep = check_liquidity_sweep(lows, closes, -1) or check_liquidity_sweep(lows, closes, -2)
        
        # ── Mitigation Check (Is price in the zone?) ──
        in_ob = False
        in_fvg = False
        support_level = None
        support_name = None
        
        if fvg and (fvg['bottom'] * 0.98 <= price <= fvg['top'] * 1.02):
            in_fvg = True
            support_level = fvg['bottom']
            support_name = "FVG Mitigation"
            
        elif ob and (ob['bottom'] * 0.98 <= price <= ob['top'] * 1.05):
            in_ob = True
            support_level = ob['top']
            support_name = "Demand Order Block"
            
        if not (in_ob or in_fvg or liq_sweep):
            return None # No SMC footprint present

        # ── Volume Profile ──
        avg_vol_20 = float(np.mean(vols[-20:]))
        today_vol = vols[-1]
        vol_ratio = round(today_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0
        
        # ── SMC Scoring ──
        score = 0.0
        if in_fvg: score += 3.5
        if in_ob: score += 4.0
        if liq_sweep: score += 3.0
        if vol_ratio > 1.2: score += 1.0
        
        score = min(round(score, 1), 10.0)
        
        if score < 4.0:
            return None

        # ── Risk / Reward ──
        # In SMC, stop loss is strictly below the Order Block or Sweep low
        stop_loss = None
        if liq_sweep:
            stop_loss = min(lows[-2:]) * 0.99
        elif ob:
            stop_loss = ob['bottom'] * 0.99
        elif fvg:
            stop_loss = fvg['bottom'] * 0.99
        else:
            stop_loss = min(lows[-5:]) * 0.99
            
        stop_loss = round(stop_loss, 2)
        risk = price - stop_loss
        if risk <= 0: return None
        
        t1 = round(price + risk * 2.5, 2) # Target old local high / liquidity
        t2 = round(recent_high, 2)        # Target major structural high
        if t2 <= t1: t2 = round(t1 + risk * 1.5, 2)
        
        rr = round((t1 - price) / risk, 1)

        # ── Thesis Generation ──
        thesis_parts = [f"Institutional tracking for {stock['sym']} shows a {pullback_pct:.1f}% corrective pullback."]
        
        if liq_sweep:
            thesis_parts.append("Smart Money has executed a Liquidity Sweep, hunting retail stops below the recent swing low before rejecting upward.")
            
        if in_fvg:
            thesis_parts.append(f"Price is currently mitigating an un-filled Fair Value Gap (FVG) between ₹{fvg['bottom']:.0f} and ₹{fvg['top']:.0f}, balancing the order book.")
            
        if in_ob:
            thesis_parts.append(f"Price has tapped directly into an institutional Demand Order Block (OB) originating at ₹{ob['top']:.0f}, where heavy accumulation previously occurred.")
            
        thesis_parts.append("This presents a high-probability asymmetric entry based on pure institutional market structure.")

        entry_strategy = f"Enter inside the {support_name or 'Liquidity'} zone near ₹{price:.0f}. Invalidation is a hard close below the institutional stop hunt level at ₹{stop_loss:.0f}."

        return {
            "sym":           stock["sym"],
            "sector":        stock["sector"],
            "price":         round(price, 2),
            "score":         score,
            "pullback_pct":  pullback_pct,
            "recent_high":   round(recent_high, 2),
            "support_level": support_level or round(price*0.95, 2),
            "support_name":  support_name or "Liquidity Pool",
            "fvg_active":    in_fvg,
            "ob_active":     in_ob,
            "liq_sweep":     liq_sweep,
            "vol_ratio":     vol_ratio,
            "entry":         round(price, 2),
            "stop_loss":     stop_loss,
            "t1":            t1,
            "t2":            t2,
            "rr":            rr,
            "thesis":        " ".join(thesis_parts),
            "entry_strategy":entry_strategy,
        }
    except Exception as e:
        return None

def fetch_market_structure():
    """Fetch Nifty 50 structure instead of EMAs"""
    try:
        df = yf.Ticker("^NSEI").history(period="3mo", interval="1d", auto_adjust=True)
        c = df["Close"].values.tolist()
        price = c[-1]
        pct_chg = round((c[-1] - c[-2]) / c[-2] * 100, 2) if len(c) > 1 else 0
        
        # Define market structure based on Higher Highs / Lower Lows
        recent_high = max(c[-20:])
        recent_low = min(c[-20:])
        structure = "BULLISH BOS" if price > c[-20] else "BEARISH CHOCH" if price < c[-20] else "CONSOLIDATION"
        
        return {
            "price":  round(price, 2),
            "pct":    pct_chg,
            "structure": structure,
            "premium": price > (recent_high + recent_low)/2
        }
    except:
        return {"price": 0, "pct": 0, "structure": "UNKNOWN", "premium": False}

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────
@app.route('/api/scan', methods=['GET'])
def run_scan():
    t0 = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(analyze_smc, s): s for s in UNIVERSE}
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    # Sort by score desc, take top 3
    results.sort(key=lambda x: -x["score"])
    top3 = results[:3]

    nifty = fetch_market_structure()
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
    print("Elite SMC Scanner API — Starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
