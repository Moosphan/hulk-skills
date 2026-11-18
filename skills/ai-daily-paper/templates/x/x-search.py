#!/usr/bin/env python3
"""用 twscrape（小号登录态）搜 X，按播放量排序，输出 JSON。"""
import argparse, asyncio, json
from twscrape import API


def media_urls(t):
    m = getattr(t, "media", None)
    if not m:
        return []
    out = []
    for attr in ("videos", "animated"):
        for v in (getattr(m, attr, None) or []):
            u = getattr(v, "url", None)
            if u:
                out.append(u)
    return out


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--min-faves", type=int, default=0)
    ap.add_argument("--db", default="x_accounts.db")
    ap.add_argument("--out", default="x-results.json")
    a = ap.parse_args()

    api = API(a.db)
    rows = []
    async for t in api.search(f"{a.query} filter:videos min_faves:{a.min_faves}", limit=a.limit):
        rows.append({
            "id": str(t.id),
            "url": f"https://x.com/{t.user.username}/status/{t.id}",
            "user": t.user.username,
            "views": t.viewCount or 0,
            "likes": t.likeCount or 0,
            "retweets": t.retweetCount or 0,
            "date": str(t.date),
            "text": (t.rawContent or "")[:200].replace("\n", " "),
            "videos": media_urls(t),
        })
    rows.sort(key=lambda r: (r["views"], r["likes"]), reverse=True)
    for r in rows[:12]:
        print(f'{r["views"]:>8} 👁 {r["likes"]:>5} ❤ @{r["user"]:<16} {r["text"][:60]}')
    json.dump(rows, open(a.out, "w"), ensure_ascii=False, indent=1)
    print("wrote", a.out, len(rows))


asyncio.run(main())
