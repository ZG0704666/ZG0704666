"""Local dev harness: render project cards + stats WITHOUT a GitHub token.

In CI, `generate.py live` fetches real data via GraphQL using GITHUB_TOKEN.
Locally (no token), this harness feeds a captured snapshot of the real repos
(from the REST API) plus a synthetic contribution calendar into the exact same
card()/stats() renderers, so you can preview layout and typography offline.

    python scripts/dev_preview.py dist
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

from generate import FEATURED, THEMES, card, stats

# Real repo snapshot (captured from api.github.com/users/ZG0704666/repos).
REPOS = {
    "Aries-AI": dict(name="Aries-AI", stargazerCount=136, forkCount=29,
                     pushedAt="2026-11-04T17:28:20Z",
                     primaryLanguage={"name": "Kotlin", "color": "#A97BFF"},
                     languages={"edges": [{"size": 5, "node": {"name": "Kotlin", "color": "#A97BFF"}},
                                          {"size": 2, "node": {"name": "Java", "color": "#b07219"}},
                                          {"size": 1, "node": {"name": "C++", "color": "#f34b7d"}}]},
                     repositoryTopics={"nodes": [{"topic": {"name": t}} for t in
                                                 ["agent", "android", "kotlin", "llm", "accessibility"]]}),
    "Label-Once": dict(name="Label-Once", stargazerCount=0, forkCount=0,
                       pushedAt="2026-11-05T04:07:26Z",
                       primaryLanguage={"name": "Python", "color": "#3572A5"},
                       languages={"edges": [{"size": 6, "node": {"name": "Python", "color": "#3572A5"}},
                                            {"size": 1, "node": {"name": "C++", "color": "#f34b7d"}}]},
                       repositoryTopics={"nodes": []}),
    "Open-Aries-AI": dict(name="Open-Aries-AI", stargazerCount=1, forkCount=0,
                          pushedAt="2026-05-30T21:14:07Z",
                          primaryLanguage={"name": "C++", "color": "#f34b7d"},
                          languages={"edges": [{"size": 4, "node": {"name": "C++", "color": "#f34b7d"}}]},
                          repositoryTopics={"nodes": []}),
    "Open-AutoGLM": dict(name="Open-AutoGLM", stargazerCount=0, forkCount=0,
                         pushedAt="2026-03-24T09:19:56Z",
                         primaryLanguage={"name": "Python", "color": "#3572A5"},
                         languages={"edges": [{"size": 3, "node": {"name": "Python", "color": "#3572A5"}}]},
                         repositoryTopics={"nodes": []}),
}


def _calendar(days: int = 371) -> dict:
    """Deterministic pseudo-random contribution calendar ending today."""
    weeks, total = [], 0
    start = date.today() - timedelta(days=days)
    # align start to Sunday so weekday layout matches GitHub's grid
    start -= timedelta(days=(start.weekday() + 1) % 7)
    d, week = start, []
    for i in range((date.today() - start).days + 1):
        # fake a believable bursty pattern
        c = (i * 7 + (i % 5) * 3) % 11
        c = max(0, c - 4) if (i % 9) else c
        week.append({"date": d.isoformat(), "contributionCount": c})
        total += c
        d += timedelta(days=1)
        if len(week) == 7:
            weeks.append({"contributionDays": week})
            week = []
    if week:
        weeks.append({"contributionDays": week})
    return {"totalContributions": total, "weeks": weeks}


def user() -> dict:
    nodes = list(REPOS.values())
    return {
        "followers": {"totalCount": 4},
        "repositories": {"totalCount": len(nodes), "nodes": nodes},
        "contributionsCollection": {"contributionCalendar": _calendar()},
    }


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    by = dict(REPOS)
    dark = THEMES["dark"]
    for i, (name, accent, en, zh, fb) in enumerate(FEATURED, 1):
        (out / f"card-{name}.svg").write_text(
            card(dark, i, by[name], accent, en, zh, fb),
            encoding="utf-8")
    (out / "stats-preview.svg").write_text(stats(dark, user()), encoding="utf-8")
    print(f"preview: {len(list(out.glob('*.svg')))} svg files in {out}/")


if __name__ == "__main__":
    main()
