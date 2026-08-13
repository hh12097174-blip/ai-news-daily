"""Source credibility scoring plugin for the AI News Daily pipeline.

Scores a news item on three axes:
  1. Domain authority  (0-60): how reputable the source domain is
  2. Freshness         (0-25): penalizes old news being recycled
  3. Annotation        (0-15): rewards items that carry a real author / byline
     and penalizes red-flag patterns (clickbait, no byline, paywall-only)

Total = 0-100, mapped to a level: excellent / good / fair / poor / reject.
"""

import json
import re
from datetime import date

# Domain authority table. Anything not listed defaults to a neutral 30.
DOMAIN_SCORES = {
    # Tier A: primary tech journalism
    "techcrunch.com": 58, "theverge.com": 57, "wired.com": 56,
    "arstechnica.com": 57, "theregister.com": 55, "zdnet.com": 53,
    "36kr.com": 52, "huxiu.com": 52, "jiqizhixin.com": 53,
    "infoq.cn": 52, "ithome.com": 48,
    # Aggregators / community sources
    "news.ycombinator.com": 45, "github.com": 50, "arxiv.org": 55,
    "zhihu.com": 42, "weibo.com": 35, "toutiao.com": 32,
    # Official / corporate blogs
    "openai.com": 55, "deepmind.google": 55, "anthropic.com": 55,
    "microsoft.com": 50, "google.com": 50,
}

# Domains with a strong track record of clickbait / low signal.
BLACKLIST = {
    "sohu.com": -15, "163.com": -10, "sina.cn": -8, "baijiahao.baidu.com": -12,
    "toutiao.com": -8, "qq.com": -5,
}

CLICKBAIT_RE = re.compile(
    r"(震惊|吓尿|出大事|万万没想到|不看后悔|99%|删前速看|沸腾了|重磅!|突发!?)",
    re.IGNORECASE,
)


def _domain_of(url: str) -> str:
    m = re.search(r"https?://([^/]+)/?", url or "")
    if not m:
        return ""
    host = m.group(1).lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def score_source(title: str = "", url: str = "", source: str = "",
                 published_days_ago: int = None, byline: bool = None,
                 **kwargs):
    """Return a credibility score (0-100) with a level and reasons.

    Args:
        title: news headline (used for clickbait detection)
        url:   canonical URL of the article
        source: display name of the source (falls back to domain)
        published_days_ago: how many days since publication; None = unknown
        byline: whether the article has a named author; None = unknown
    """
    domain = _domain_of(url) or (source or "").lower()
    reasons = []

    # 1. Domain authority (0-60)
    authority = DOMAIN_SCORES.get(domain, 30)
    if domain in BLACKLIST:
        authority += BLACKLIST[domain]
        reasons.append(f"domain '{domain}' carries a blacklist penalty")
    reasons.append(f"domain authority {authority}/60")

    # 2. Freshness (0-25)
    freshness = 25
    if published_days_ago is None:
        freshness = 15
        reasons.append("publish date unknown, freshness capped at 15")
    elif published_days_ago <= 1:
        reasons.append("published within 24h")
    elif published_days_ago <= 3:
        freshness = 20
        reasons.append("published within 3 days")
    elif published_days_ago <= 7:
        freshness = 12
        reasons.append("older than 3 days, freshness reduced")
    else:
        freshness = 0
        reasons.append("older than a week - likely recycled news")

    # 3. Annotation (0-15)
    annotation = 15
    if byline is False:
        annotation -= 8
        reasons.append("no byline")
    if CLICKBAIT_RE.search(title or ""):
        annotation -= 6
        reasons.append("clickbait pattern detected in headline")
    if annotation < 0:
        annotation = 0

    total = max(0, min(100, authority + freshness + annotation))
    if total >= 80:
        level = "excellent"
    elif total >= 60:
        level = "good"
    elif total >= 40:
        level = "fair"
    elif total >= 20:
        level = "poor"
    else:
        level = "reject"

    return json.dumps({
        "score": total,
        "level": level,
        "domain": domain,
        "breakdown": {"authority": authority, "freshness": freshness,
                      "annotation": annotation},
        "reasons": reasons,
        "recommendation": "accept" if total >= 60 else (
            "review" if total >= 40 else "drop"),
    }, ensure_ascii=False)


def register(ctx):
    ctx.register_tool(
        name="score_source",
        toolset="news_pipeline",
        description=(
            "Score a news source's credibility (0-100) based on domain "
            "authority, freshness and annotation quality. Use before "
            "ranking candidate news items."
        ),
        schema={
            "name": "score_source",
            "description": "Score news source credibility 0-100",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string",
                              "description": "News headline"},
                    "url": {"type": "string",
                            "description": "Canonical article URL"},
                    "source": {"type": "string",
                               "description": "Display name of the source"},
                    "published_days_ago": {"type": "integer",
                                           "description": "Days since publication, if known"},
                    "byline": {"type": "boolean",
                               "description": "Whether a named author exists"},
                },
                "required": ["url"],
            },
        },
        handler=score_source,
    )
