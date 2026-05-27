from urllib.parse import urlparse

try:
    from newspaper import Article as NewspaperArticle
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

import requests
from bs4 import BeautifulSoup


def scrape_article(url: str) -> dict:
    domain = urlparse(url).netloc.replace("www.", "")

    if NEWSPAPER_AVAILABLE:
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()
            if article.text and len(article.text) > 100:
                return {
                    "text": article.text,
                    "title": article.title,
                    "domain": domain,
                    "authors": article.authors,
                    "publish_date": str(article.publish_date) if article.publish_date else None,
                }
        except Exception:
            pass

    # Fallback: requests + BeautifulSoup
    headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBiasBot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)
    title_tag = soup.find("title")

    if not text or len(text) < 100:
        raise ValueError("Could not extract meaningful article text from URL")

    return {
        "text": text,
        "title": title_tag.get_text(strip=True) if title_tag else "",
        "domain": domain,
        "authors": [],
        "publish_date": None,
    }
