# -*- coding: utf-8 -*-
"""
fetch_project.py — 抓取单个 GitHub 仓库的深度档案
用法：venv python fetch_project.py <owner/repo 或完整 URL>
输出 project.json：
  date, repo: {full_name, owner, name, url, description, homepage, language, stars,
               forks, topics, contributors, license, created_at, pushed_at,
               open_issues, subscribers, latest_release {tag, published_at}, readme_full}
README 为全文清洗版（最长 12000 字符），供深度创作使用。
"""
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
OUT = Path(__file__).parent / "project.json"
README_MAX = 12000


def parse_repo_arg(arg):
    arg = arg.strip().rstrip("/")
    m = re.search(r"github\.com/([\w.-]+/[\w.-]+)", arg)
    full = m.group(1) if m else arg
    if "/" not in full:
        raise SystemExit(f"仓库格式不对：{arg}（应为 owner/repo）")
    return full


def api_get(url, raw=False, retries=2):
    for i in range(retries):
        try:
            h = dict(HEADERS)
            if raw:
                h["Accept"] = "application/vnd.github.raw+json"
            r = requests.get(url, headers=h, timeout=25)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
            if r.status_code == 403:
                print(f"[api] 限流({url})", file=sys.stderr)
                return None
        except Exception as e:
            print(f"[api] {url} 失败: {e}", file=sys.stderr)
        time.sleep(2 * (i + 1))
    return None


def clean_readme(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)          # 图片
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)        # 链接留文字
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[#*`>|_{}\[\]()]", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:README_MAX]


def fetch_repo(full):
    repo = {
        "full_name": full, "owner": full.split("/", 1)[0], "name": full.split("/", 1)[1],
        "url": f"https://github.com/{full}", "description": "", "homepage": "",
        "language": "", "stars": 0, "forks": 0, "topics": [], "contributors": 0,
        "license": "", "created_at": "", "pushed_at": "", "open_issues": 0,
        "subscribers": 0, "latest_release": {"tag": "", "published_at": ""},
        "readme_full": "",
    }
    r = api_get(f"https://api.github.com/repos/{full}")
    if not r:
        raise RuntimeError(f"仓库 {full} 抓取失败（不存在/限流/网络），不输出半成品")
    j = r.json()
    repo["description"] = j.get("description") or ""
    repo["homepage"] = j.get("homepage") or ""
    repo["language"] = j.get("language") or ""
    repo["stars"] = j.get("stargazers_count", 0)
    repo["forks"] = j.get("forks_count", 0)
    repo["topics"] = (j.get("topics") or [])[:6]
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

    rr = api_get(f"https://api.github.com/repos/{full}/releases/latest")
    if rr:
        j = rr.json()
        repo["latest_release"] = {"tag": j.get("tag_name") or "",
                                  "published_at": (j.get("published_at") or "")[:10]}

    rd = api_get(f"https://api.github.com/repos/{full}/readme", raw=True)
    if rd:
        repo["readme_full"] = clean_readme(rd.text)
    else:
        print("[readme] README 抓取失败，创作时依据 description/事实字段", file=sys.stderr)
    return repo


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法：python fetch_project.py <owner/repo 或 URL>")
    full = parse_repo_arg(sys.argv[1])
    print(f"抓取 {full} 深度档案 ...")
    repo = fetch_repo(full)
    data = {"date": date.today().isoformat(), "repo": repo}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成 → {OUT}")
    print(f"  {repo['full_name']}  ★{repo['stars']}  {repo['language']}  "
          f"贡献者 {repo['contributors']}  release {repo['latest_release']['tag'] or '-'}  "
          f"README {len(repo['readme_full'])} 字符")


if __name__ == "__main__":
    main()
