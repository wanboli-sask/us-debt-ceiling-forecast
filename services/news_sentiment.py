import re
from datetime import datetime

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import NEWS_KEYWORDS, RSS_FEEDS

_analyzer = SentimentIntensityAnalyzer()


def _matches(text: str) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in NEWS_KEYWORDS)


def fetch_news(limit_per_feed: int = 25) -> list[dict]:
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit_per_feed]:
                title = entry.get("title", "")
                if _matches(title):
                    articles.append({
                        "title": title,
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "source": feed.feed.get("title", url),
                    })
        except Exception:
            continue
    return articles[:100]


def score_articles(articles: list[dict]) -> dict:
    if not articles:
        return {"score": 0.0, "count": 0, "articles": []}
    scores = []
    enriched = []
    for a in articles:
        vs = _analyzer.polarity_scores(a["title"])
        compound = vs["compound"]
        scores.append(compound)
        enriched.append({**a, "sentiment": compound})
    avg = sum(scores) / len(scores)
    return {"score": avg, "count": len(scores), "articles": enriched}


def get_sentiment_summary() -> dict:
    articles = fetch_news()
    return score_articles(articles)
