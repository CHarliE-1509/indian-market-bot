"""A broader liquid NIFTY 100/150-ish universe, spanning sectors, for testing
whether the original 19-stock findings hold at scale. Hand-curated (not scraped
from NSE, which blocks non-browser requests) — some tickers may fail to resolve
if renamed/delisted since; failures are dropped automatically by fetch_universe."""

WIDE_UNIVERSE = [
    # original 19 (liquid large-caps)
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "WIPRO.NS",
    # IT
    "HCLTECH.NS", "TECHM.NS", "LTIM.NS",
    # FMCG / consumer
    "ASIANPAINT.NS", "BRITANNIA.NS", "DABUR.NS", "GODREJCP.NS", "MARICO.NS",
    "COLPAL.NS", "TATACONSUM.NS", "TRENT.NS", "DMART.NS",
    # energy / PSU
    "ADANIPORTS.NS", "POWERGRID.NS", "NTPC.NS", "TATAPOWER.NS", "ONGC.NS",
    "BPCL.NS", "IOC.NS", "COALINDIA.NS", "GAIL.NS", "PETRONET.NS",
    # financials / insurance
    "HDFCLIFE.NS", "SBILIFE.NS", "ICICIPRULI.NS", "ICICIGI.NS", "BAJAJFINSV.NS",
    "BAJAJ-AUTO.NS", "HDFCAMC.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "FEDERALBNK.NS",
    "AUBANK.NS",
    # pharma / healthcare
    "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "LUPIN.NS",
    # auto
    "HEROMOTOCO.NS", "EICHERMOT.NS", "M&M.NS", "TVSMOTOR.NS", "ASHOKLEY.NS",
    "BOSCHLTD.NS", "MOTHERSON.NS", "BALKRISIND.NS",
    # metals
    "JSWSTEEL.NS", "TATASTEEL.NS", "HINDALCO.NS", "VEDANTA.NS", "JINDALSTEL.NS",
    # cement
    "GRASIM.NS", "SHREECEM.NS", "AMBUJACEM.NS", "ACC.NS",
    # realty
    "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS",
    # chemicals
    "PIDILITE.NS", "UPL.NS", "SRF.NS",
    # industrials / durables
    "SIEMENS.NS", "ABB.NS", "HAVELLS.NS", "VOLTAS.NS", "CROMPTON.NS",
    "BEL.NS", "HAL.NS",
    # aviation
    "INDIGO.NS",
]
