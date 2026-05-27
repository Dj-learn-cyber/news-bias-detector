"""
Step 1 — Collect labeled training data from two sources:
  A) RSS feeds of outlets with known AllSides bias ratings
  B) BABE dataset from HuggingFace (expert-annotated sentences)

Output: data/raw_articles.jsonl
Each line: {"text": "...", "label": "left|lean-left|center|lean-right|right", "source": "..."}
"""

import json
import time
import re
import sys
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

try:
    from newspaper import Article
    NEWSPAPER_OK = True
except ImportError:
    NEWSPAPER_OK = False

OUTPUT = Path("data/raw_articles.jsonl")
OUTPUT.parent.mkdir(exist_ok=True)

# ── Outlet RSS feeds with AllSides bias labels ────────────────────────────────
# Format: (label, outlet_name, rss_url)
RSS_SOURCES = [
    # Far-left
    ("far-left", "The Nation",        "https://www.thenation.com/feed/?post_type=article"),
    ("far-left", "Jacobin",           "https://jacobin.com/feed/"),
    ("far-left", "Common Dreams",     "https://www.commondreams.org/rss.xml"),
    ("far-left", "truthout",          "https://truthout.org/feed/"),

    # Left
    ("left", "Mother Jones",          "https://www.motherjones.com/feed/"),
    ("left", "The Intercept",         "https://theintercept.com/feed/?rss"),
    ("left", "Vox",                   "https://www.vox.com/rss/index.xml"),
    ("left", "HuffPost",              "https://www.huffpost.com/section/front-page/feed"),
    ("left", "Salon",                 "https://www.salon.com/feed/"),
    ("left", "The New Yorker",        "https://www.newyorker.com/feed/everything"),
    ("left", "New Republic",          "https://newrepublic.com/feed.rss"),
    ("left", "Raw Story",             "https://www.rawstory.com/feed/"),

    # Lean-left
    ("lean-left", "NPR",              "https://feeds.npr.org/1001/rss.xml"),
    ("lean-left", "BBC News",         "http://feeds.bbci.co.uk/news/rss.xml"),
    ("lean-left", "The Guardian",     "https://www.theguardian.com/world/rss"),
    ("lean-left", "New York Times",   "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"),
    ("lean-left", "Washington Post",  "https://feeds.washingtonpost.com/rss/national"),
    ("lean-left", "CNN",              "http://rss.cnn.com/rss/edition.rss"),
    ("lean-left", "Politico",         "https://rss.politico.com/politics-news.xml"),
    ("lean-left", "The Atlantic",     "https://www.theatlantic.com/feed/all/"),
    ("lean-left", "Bloomberg",        "https://feeds.bloomberg.com/politics/news.rss"),
    ("lean-left", "ProPublica",       "https://www.propublica.org/feeds/propublica/main"),
    ("lean-left", "The Hill (left)",  "https://thehill.com/rss/syndicator/19110"),
    ("lean-left", "Slate",            "https://slate.com/feeds/all.rss"),
    ("lean-left", "NBC News",         "https://feeds.nbcnews.com/nbcnews/public/news"),
    ("lean-left", "TIME",             "https://time.com/feed/"),

    # Center
    ("center", "Associated Press",   "https://feeds.apnews.com/rss/topnews"),
    ("center", "Reuters",             "https://feeds.reuters.com/reuters/topNews"),
    ("center", "The Economist",       "https://www.economist.com/latest/rss.xml"),
    ("center", "Financial Times",     "https://www.ft.com/rss/home"),
    ("center", "Axios",               "https://api.axios.com/feed/"),
    ("center", "The Hill",            "https://thehill.com/rss/syndicator/19110"),
    ("center", "USA Today",           "https://rss.usatoday.com/UsatodaycomNation-TopStories"),
    ("center", "Deutsche Welle",      "https://rss.dw.com/xml/rss-en-all"),
    ("center", "France 24",           "https://www.france24.com/en/rss"),
    ("center", "RealClearPolitics",   "https://www.realclearpolitics.com/index.xml"),

    # Lean-right
    ("lean-right", "Wall Street Journal", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    ("lean-right", "Forbes",          "https://www.forbes.com/most-popular/feed/"),
    ("lean-right", "Newsweek",        "https://www.newsweek.com/rss"),
    ("lean-right", "Reason",          "https://reason.com/feed/"),
    ("lean-right", "Washington Examiner", "https://www.washingtonexaminer.com/rss/news"),
    ("lean-right", "The Spectator",   "https://www.spectator.co.uk/feed/"),
    ("lean-right", "American Conservative", "https://www.theamericanconservative.com/feed/"),

    # Right
    ("right", "Fox News",             "https://moxie.foxnews.com/google-publisher/latest.xml"),
    ("right", "National Review",      "https://www.nationalreview.com/feed/"),
    ("right", "New York Post",        "https://nypost.com/feed/"),
    ("right", "Daily Caller",         "https://dailycaller.com/feed/"),
    ("right", "Washington Times",     "https://www.washingtontimes.com/rss/headlines/news/"),
    ("right", "The Telegraph",        "https://www.telegraph.co.uk/rss.xml"),

    # Far-right
    ("far-right", "Breitbart",        "https://feeds.feedburner.com/breitbart"),
    ("far-right", "The Federalist",   "https://thefederalist.com/feed/"),
    ("far-right", "Townhall",         "https://townhall.com/rss/tipsheet"),
    ("far-right", "Daily Wire",       "https://feeds.dailywire.com/author/daily-wire/feed"),
]

MAX_ARTICLES_PER_FEED = 60  # cap per outlet so no single source dominates


def fetch_article_text(url: str, timeout: int = 12) -> str | None:
    """Fetch full article text, trying newspaper4k then BeautifulSoup."""
    if NEWSPAPER_OK:
        try:
            art = Article(url)
            art.download()
            art.parse()
            if art.text and len(art.text.strip()) > 150:
                return art.text.strip()
        except Exception:
            pass

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBiasResearch/1.0)"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "figure"]):
            tag.decompose()
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
        text = " ".join(paras)
        return text.strip() if len(text) > 150 else None
    except Exception:
        return None


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"http\S+", "", text)
    return text.strip()


def load_existing() -> set[str]:
    """Return set of URLs already collected so we can resume."""
    seen: set[str] = set()
    if OUTPUT.exists():
        with open(OUTPUT, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if "url" in obj:
                        seen.add(obj["url"])
                except json.JSONDecodeError:
                    pass
    return seen


def collect_rss() -> None:
    seen_urls = load_existing()
    mode = "a" if OUTPUT.exists() else "w"

    with open(OUTPUT, mode, encoding="utf-8") as out:
        for label, outlet, rss_url in tqdm(RSS_SOURCES, desc="Outlets"):
            try:
                feed = feedparser.parse(rss_url)
            except Exception as e:
                print(f"  [SKIP] {outlet}: feed parse error — {e}")
                continue

            entries = feed.entries[:MAX_ARTICLES_PER_FEED]
            written = 0

            for entry in entries:
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue

                # Use feed summary as cheap text if full fetch fails
                summary = entry.get("summary", "") or entry.get("description", "")
                summary = BeautifulSoup(summary, "lxml").get_text(" ", strip=True)

                text = fetch_article_text(url) or summary
                text = clean_text(text)

                if len(text.split()) < 80:
                    continue

                record = {
                    "text": text[:4000],  # cap at 4000 chars (~800 tokens)
                    "label": label,
                    "source": outlet,
                    "url": url,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                seen_urls.add(url)
                written += 1
                time.sleep(0.8)  # be polite

            print(f"  {outlet}: {written} articles ({label})")


def collect_babe() -> None:
    """Download BABE dataset and label sentences by outlet name."""
    print("\nDownloading BABE dataset from HuggingFace...")
    try:
        from datasets import load_dataset
        ds_train = load_dataset("mediabiasgroup/BABE", split="train")
        ds_test  = load_dataset("mediabiasgroup/BABE", split="test")
        all_rows = list(ds_train) + list(ds_test)
    except Exception as e:
        print(f"  [SKIP] BABE not available: {e}")
        return

    # Map outlet names → political lean (BABE uses outlet, not lean label)
    outlet_map: dict[str, str] = {
        "breitbart":          "right",
        "federalist":         "right",
        "the federalist":     "right",
        "fox":                "right",
        "fox news":           "right",
        "daily wire":         "right",
        "daily caller":       "right",
        "new york post":      "right",
        "national review":    "right",
        "washington examiner":"right",
        "washington times":   "right",
        "townhall":           "right",
        "newsmax":            "right",
        "reason":             "lean-right",
        "forbes":             "lean-right",
        "wall street journal":"lean-right",
        "wsj":                "lean-right",
        "associated press":   "center",
        "ap":                 "center",
        "reuters":            "center",
        "bbc":                "lean-left",
        "bbc news":           "lean-left",
        "guardian":           "lean-left",
        "the guardian":       "lean-left",
        "nbc":                "lean-left",
        "nbc news":           "lean-left",
        "cbs":                "lean-left",
        "abc":                "lean-left",
        "cnn":                "lean-left",
        "npr":                "lean-left",
        "politico":           "lean-left",
        "washington post":    "lean-left",
        "new york times":     "lean-left",
        "nytimes":            "lean-left",
        "time":               "lean-left",
        "the atlantic":       "lean-left",
        "bloomberg":          "lean-left",
        "huffpost":           "left",
        "huffington post":    "left",
        "vox":                "left",
        "mother jones":       "left",
        "salon":              "left",
        "the intercept":      "left",
        "raw story":          "left",
        "democracy now":      "left",
        "jacobin":            "left",
        "the nation":         "left",
        "common dreams":      "left",
    }

    written = 0
    with open(OUTPUT, "a", encoding="utf-8") as out:
        for row in all_rows:
            outlet_raw = str(row.get("outlet", "")).lower().strip()
            label = None
            for key, val in outlet_map.items():
                if key in outlet_raw:
                    label = val
                    break
            if not label:
                continue

            text = str(row.get("text", "")).strip()
            if len(text.split()) < 20:
                continue

            record = {
                "text": text[:4000],
                "label": label,
                "source": f"BABE/{row.get('outlet', '')}",
                "url": str(row.get("news_link", "")),
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    print(f"  BABE: {written} samples added.")


def print_summary() -> None:
    counts: dict[str, int] = {}
    if not OUTPUT.exists():
        return
    with open(OUTPUT, encoding="utf-8") as f:
        for line in f:
            try:
                label = json.loads(line)["label"]
                counts[label] = counts.get(label, 0) + 1
            except Exception:
                pass
    total = sum(counts.values())
    print(f"\n--- Dataset summary ({total} total) ---")
    for lbl in ["far-left", "left", "lean-left", "center", "lean-right", "right", "far-right"]:
        n = counts.get(lbl, 0)
        bar = "#" * (n // 20)
        print(f"  {lbl:<12} {n:>5}  {bar}")


if __name__ == "__main__":
    print("=== Step 1: Collecting training data ===\n")
    collect_rss()
    collect_babe()
    print_summary()
    print(f"\nSaved to {OUTPUT}")
