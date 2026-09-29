"""
Sentiment Bot — news-based sentiment, sourced without any Claude/LLM access.

Honesty about what this is: it runs unattended via launchd, with no connection
back to an interactive Claude session, so it cannot use WebSearch or any LLM
judgment. It uses Google News RSS (free, no API key) for headlines per stock,
and VADER (a lexicon-based sentiment scorer — fast, local, no API) to score
them. This is a genuine, real-time-ish signal (whatever's in Google News right
now), but it is mechanical headline sentiment, not analytical judgment about
WHY something matters. A deeper research layer can be added later by having
an interactive Claude session (this one, or a future one) write richer notes
into the same output file on demand — see enrich_with_notes().
"""
import json
import time
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

warnings.filterwarnings("ignore")

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"
analyzer = SentimentIntensityAnalyzer()

# VADER is a general-purpose lexicon and gets financial headlines backwards
# surprisingly often ("stock plunges" scored positive because it doesn't know
# "plunge" is bad news). Patch in finance-specific terms before scoring anything.
_FINANCE_LEXICON = {
    "plunge": -3.0, "plunges": -3.0, "plunged": -3.0, "crash": -3.5, "crashes": -3.5,
    "tumble": -2.5, "tumbles": -2.5, "tumbled": -2.5, "slump": -2.5, "slumps": -2.5,
    "tank": -2.5, "tanks": -2.5, "slide": -1.8, "slides": -1.8, "slid": -1.8,
    "sinks": -2.2, "sink": -2.2, "sinking": -2.2, "rout": -2.8, "selloff": -2.5,
    "sell-off": -2.5, "downgrade": -2.0, "downgraded": -2.0, "cut": -1.2, "slashed": -2.0,
    "miss": -1.5, "misses": -1.5, "missed": -1.5, "disappoints": -1.8, "disappointing": -1.8,
    "loss": -1.5, "losses": -1.5, "weak": -1.2, "weakness": -1.2, "underperform": -1.8,
    "bearish": -2.0, "correction": -1.2, "low": -0.8, "lows": -0.8,
    "surge": 2.8, "surges": 2.8, "surged": 2.8, "rally": 2.5, "rallies": 2.5, "rallied": 2.5,
    "soar": 3.0, "soars": 3.0, "soared": 3.0, "jump": 1.8, "jumps": 1.8, "jumped": 1.8,
    "spike": 1.8, "spikes": 1.8, "gains": 1.5, "gain": 1.5, "rebound": 1.8, "rebounds": 1.8,
    "upgrade": 2.0, "upgraded": 2.0, "beat": 1.8, "beats": 1.8, "outperform": 2.0,
    "bullish": 2.2, "buy": 1.0, "high": 0.5, "highs": 0.5,
    "profit": 1.5, "profits": 1.5, "growth": 1.2, "robust": 1.5, "strong": 1.2,
}
analyzer.lexicon.update(_FINANCE_LEXICON)

# Company name aliases — Google News works far better on company names than
# raw tickers (searching "WIPRO.NS" returns almost nothing useful).
COMPANY_NAMES = {
    "RELIANCE.NS": "Reliance Industries", "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank", "INFY.NS": "Infosys",
    "HINDUNILVR.NS": "Hindustan Unilever", "ITC.NS": "ITC Limited", "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel", "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LT.NS": "Larsen Toubro", "AXISBANK.NS": "Axis Bank", "BAJFINANCE.NS": "Bajaj Finance",
    "MARUTI.NS": "Maruti Suzuki", "SUNPHARMA.NS": "Sun Pharma", "TITAN.NS": "Titan Company",
    "ULTRACEMCO.NS": "UltraTech Cement", "NESTLEIND.NS": "Nestle India", "WIPRO.NS": "Wipro",
    "HCLTECH.NS": "HCL Technologies", "TECHM.NS": "Tech Mahindra",
    "ASIANPAINT.NS": "Asian Paints", "BRITANNIA.NS": "Britannia Industries",
    "ADANIPORTS.NS": "Adani Ports", "POWERGRID.NS": "Power Grid Corporation",
    "NTPC.NS": "NTPC Limited", "TATAPOWER.NS": "Tata Power", "ONGC.NS": "ONGC",
    "COALINDIA.NS": "Coal India", "HDFCLIFE.NS": "HDFC Life", "SBILIFE.NS": "SBI Life",
    "BAJAJFINSV.NS": "Bajaj Finserv", "INDUSINDBK.NS": "IndusInd Bank",
    "DRREDDY.NS": "Dr Reddy's Laboratories", "CIPLA.NS": "Cipla", "DIVISLAB.NS": "Divi's Laboratories",
    "APOLLOHOSP.NS": "Apollo Hospitals", "HEROMOTOCO.NS": "Hero MotoCorp",
    "EICHERMOT.NS": "Eicher Motors", "M&M.NS": "Mahindra Mahindra", "TVSMOTOR.NS": "TVS Motor",
    "JSWSTEEL.NS": "JSW Steel", "TATASTEEL.NS": "Tata Steel", "HINDALCO.NS": "Hindalco",
    "GRASIM.NS": "Grasim Industries", "DLF.NS": "DLF Limited", "SIEMENS.NS": "Siemens India",
    "HAVELLS.NS": "Havells India", "BEL.NS": "Bharat Electronics", "HAL.NS": "Hindustan Aeronautics",
    "INDIGO.NS": "InterGlobe Aviation", "DMART.NS": "Avenue Supermarts DMart",
    "TRENT.NS": "Trent Limited",
}


def fetch_headlines(ticker: str, max_items: int = 12, hours_lookback: int = 72):
    query = COMPANY_NAMES.get(ticker, ticker.replace(".NS", "")) + " stock"
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)
    items = []
    for entry in feed.entries[:max_items * 2]:
        try:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            published = datetime.now(timezone.utc)
        if published < cutoff:
            continue
        items.append({
            "title": entry.title,
            "source": entry.get("source", {}).get("title", "unknown") if isinstance(entry.get("source"), dict) else "unknown",
            "published": published.isoformat(),
            "link": entry.link,
        })
        if len(items) >= max_items:
            break
    return items


def score_headlines(headlines):
    if not headlines:
        return {"score": 0.0, "n_headlines": 0, "label": "no_data"}
    scores = [analyzer.polarity_scores(h["title"])["compound"] for h in headlines]
    avg = sum(scores) / len(scores)
    label = "bullish" if avg > 0.15 else "bearish" if avg < -0.15 else "neutral"
    return {"score": round(avg, 3), "n_headlines": len(headlines), "label": label}


def run(tickers, sleep_between=0.5):
    """Returns {ticker: {score, n_headlines, label, top_headlines: [...]}}"""
    results = {}
    for t in tickers:
        headlines = fetch_headlines(t)
        scoring = score_headlines(headlines)
        scoring["top_headlines"] = [
            {"title": h["title"], "source": h["source"],
             "sentiment": round(analyzer.polarity_scores(h["title"])["compound"], 3)}
            for h in headlines[:5]
        ]
        results[t] = scoring
        time.sleep(sleep_between)
    return results


def save(results, path=None):
    path = path or (RESULTS_DIR / "sentiment_bot_output.json")
    payload = {
        "generated_at": datetime.now().isoformat(),
        "method": "Google News RSS headlines + VADER lexicon sentiment (mechanical, no LLM judgment)",
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from wide_universe import WIDE_UNIVERSE
    print(f"Fetching news sentiment for {len(WIDE_UNIVERSE)} stocks...")
    res = run(WIDE_UNIVERSE)
    for t, r in sorted(res.items(), key=lambda x: x[1]["score"])[:5]:
        print(f"  MOST BEARISH: {t}: {r['score']} ({r['n_headlines']} headlines)")
    for t, r in sorted(res.items(), key=lambda x: -x[1]["score"])[:5]:
        print(f"  MOST BULLISH: {t}: {r['score']} ({r['n_headlines']} headlines)")
    p = save(res)
    print(f"Saved to {p}")
