# -*- coding: utf-8 -*-
"""
fetch_trending.py — 抓取 GitHub Trending 每日综合榜 Top5
输出 data.json：
  date, repos[5]: {rank, full_name, owner, name, url, description, language,
                   stars, stars_today, forks, topics, contributors, readme_snippet,
                   license, created_at, pushed_at, open_issues, subscribers}
"""
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
TOP_N = 5
OUT = Path(__file__).parent / "data.json"


def fetch_trending(retries=3):
    for i in range(retries):
        try:
            r = requests.get("https://github.com/trending", headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"[trending] 第{i+1}次抓取失败: {e}", file=sys.stderr)
            time.sleep(3 * (i + 1))
    raise RuntimeError("GitHub Trending 页面连续抓取失败")


def parse_trending(html):
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("article.Box-row")
    repos = []
    for idx, art in enumerate(articles[:TOP_N]):
        a = art.select_one("h2 a")
        full_name = a["href"].strip().lstrip("/") if a else ""
        desc_el = art.select_one("p")
        desc = desc_el.get_text(strip=True) if desc_el else ""
        lang_el = art.select_one('[itemprop="programmingLanguage"]')
        lang = lang_el.get_text(strip=True) if lang_el else ""
        stars = 0
        for link in art.select('a.Link--muted'):
            href = link.get("href", "")
            m = re.search(r"/stargazers$", href)
            if m:
                stars = int(re.sub(r"[,\s]", "", link.get_text(strip=True)) or 0)
                break
        today_el = art.select_one("span.d-inline-block.float-sm-right")
        stars_today = 0
        if today_el:
            m = re.search(r"([\d,]+)\s*stars", today_el.get_text(strip=True))
            if m:
                stars_today = int(m.group(1).replace(",", ""))
        owner, name = full_name.split("/", 1) if "/" in full_name else ("", full_name)
        repos.append({
            "rank": idx + 1,
            "full_name": full_name,
            "owner": owner,
            "name": name,
            "url": f"https://github.com/{full_name}",
            "description": desc,
            "language": lang,
            "stars": stars,
            "stars_today": stars_today,
            "forks": 0,
            "topics": [],
            "contributors": 0,
            "readme_snippet": "",
            "license": "",
            "created_at": "",
            "pushed_at": "",
            "open_issues": 0,
            "subscribers": 0,
        })
    return repos


def api_get(url, retries=2):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r
            if r.status_code == 403:
                print(f"[api] 限流({url})", file=sys.stderr)
                return None
        except Exception as e:
            print(f"[api] {url} 失败: {e}", file=sys.stderr)
        time.sleep(2 * (i + 1))
    return None


def enrich_repo(repo):
    full = repo["full_name"]
    r = api_get(f"https://api.github.com/repos/{full}")
    if r:
        j = r.json()
        repo["stars"] = j.get("stargazers_count", repo["stars"])
        repo["forks"] = j.get("forks_count", 0)
        repo["topics"] = (j.get("topics") or [])[:4]
        lic = (j.get("license") or {}).get("spdx_id") or ""
        repo["license"] = "" if lic in ("NOASSERTION", "OTHER") else lic
        repo["created_at"] = j.get("created_at") or ""
        repo["pushed_at"] = j.get("pushed_at") or ""
        repo["open_issues"] = j.get("open_issues_count", 0)
        repo["subscribers"] = j.get("subscribers_count", 0)
    cr = api_get(f"https://api.github.com/repos/{full}/contributors?per_page=1&anon=true")
    if cr and cr.links and "last" in cr.links:
        m = re.search(r"[?&]page=(\d+)", cr.links["last"]["url"])
        if m:
            repo["contributors"] = int(m.group(1))
    rr = api_get(f"https://raw.githubusercontent.com/{full}/HEAD/README.md")
    if rr is None:
        rr = api_get(f"https://raw.githubusercontent.com/{full}/HEAD/README.zh-CN.md")
    if rr:
        text = re.sub(r"<[^>]+>", " ", rr.text)
        text = re.sub(r"[#*`>\[\]!|]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        repo["readme_snippet"] = text[:4000]
    return repo


def main():
    print("抓取 GitHub Trending ...")
    repos = parse_trending(fetch_trending())
    if len(repos) < TOP_N:
        raise RuntimeError(f"仅解析到 {len(repos)} 个仓库，解析器可能失效")
    for repo in repos:
        print(f"补全 #{repo['rank']} {repo['full_name']} ...")
        enrich_repo(repo)
        time.sleep(1)
    data = {"date": date.today().isoformat(), "repos": repos}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成 → {OUT}")
    for r in repos:
        print(f"  #{r['rank']} {r['full_name']}  ★{r['stars']} (+{r['stars_today']})  {r['language']}")


if __name__ == "__main__":
    main()
