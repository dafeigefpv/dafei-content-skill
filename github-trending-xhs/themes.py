# -*- coding: utf-8 -*-
"""
themes.py — github-trending-xhs / github-project-xhs 共用主题库（6 套浅色 + 4 套深色，共 10 套）
语义化令牌：render.py 的 CSS 模板用 $token 占位，渲染时按主题填充。
浅色主题中 cream/klein/forest 为原创；swiss/pastel/split 参考 zarazhangrui/frontend-slides 的 STYLE_PRESETS（Swiss Modern / Pastel Geometry / Split Pastel）。
深色主题 terminal/neon/signal/botanic 参考同一库的 Terminal Green / Neon Cyber / Bold Signal / Dark Botanical。

规则：
- content.json 可写 "theme": "klein" 指定主题；缺省按日期自动轮换（day_of_year % 10，相邻两天必不同）
- 同一天封面与详情卡必须同主题（一套皮肤到底）
- 命令块终端黑底 / 语言色点 / 项目封面终端窗为跨主题固定元素，不随主题变
- 深色主题封面用 cover_bg 渐变令牌；浅色主题 cover_bg 默认等于 bg（纯色）
- 单一 ink 令牌同时用于封面与详情卡，故每套主题须同色调（整浅或整深）；Notebook Tabs 之类「深底+浅纸」双调签名无法映射，未纳入
"""

THEMES = {
    # 1. cream 奶油砖红 —— 原默认主题，保留
    "cream": dict(
        bg="#faf7f1", paper="#f5f4f1", card="#fffdf8",
        ink="#1c1b18", text2="#3d3b35", sub="#6f6b5f", muted="#8a8577", faint="#a8a396",
        accent="#c7442e", accent_text="#faf7f1", accent2="#FF5028",
        chip_bg="#f1efe8", chip_text="#3d3b35", metric_bg="#f6f2e8", comment_bg="#f6ede4",
        border="#e3ded2", border2="#d8d2c2", wm="#f0ece0",
        cmd_bg="#1c1b18", cmd_text="#e3b341",
        grid="rgba(27,27,25,.05)",
    ),
    # 2. klein 克莱因蓝 —— 纸白底，高级科技感
    "klein": dict(
        bg="#f7f8fa", paper="#f3f5f8", card="#ffffff",
        ink="#10131a", text2="#2c313c", sub="#4a505c", muted="#7a8090", faint="#9aa0ad",
        accent="#002fa7", accent_text="#f7f8fa", accent2="#FF5028",
        chip_bg="#eceef4", chip_text="#23272f", metric_bg="#eef1f7", comment_bg="#eef1f7",
        border="#dde1ea", border2="#c8cedd", wm="#e8ebf3",
        cmd_bg="#10131a", cmd_text="#7ad0ff",
        grid="rgba(16,19,26,.05)",
    ),
    # 3. forest 森野墨绿 —— 沉稳极客
    "forest": dict(
        bg="#f6f7f2", paper="#f2f4ee", card="#fdfefb",
        ink="#17211b", text2="#2c3a31", sub="#45564c", muted="#6f8177", faint="#93a39a",
        accent="#1f5c46", accent_text="#f6f7f2", accent2="#d98e2b",
        chip_bg="#e8ede7", chip_text="#24352c", metric_bg="#ebf0ea", comment_bg="#e9f0e9",
        border="#dbe1d8", border2="#c4cfc2", wm="#e6ece4",
        cmd_bg="#17211b", cmd_text="#ffd166",
        grid="rgba(23,33,27,.05)",
    ),
    # 4. swiss 瑞士现代（浅色）—— 参考 frontend-slides「Swiss Modern」：纯白底 + 纯黑字 + 红 #ff3300，包豪斯网格感，开发者/设计向
    "swiss": dict(
        bg="#ffffff", paper="#f4f4f2", card="#ffffff",
        ink="#0a0a0a", text2="#1f1f1f", sub="#454545", muted="#767676", faint="#a6a6a6",
        accent="#ff3300", accent_text="#ffffff", accent2="#0a0a0a",
        chip_bg="#efefed", chip_text="#1f1f1f", metric_bg="#f5f5f3", comment_bg="#f5f5f3",
        border="#e4e4e4", border2="#cfcfcf", wm="#eeeeec",
        cmd_bg="#0a0a0a", cmd_text="#ff5a3c",
        grid="rgba(10,10,10,.045)",
    ),
    # 5. pastel 粉彩几何（浅色）—— 参考 frontend-slides「Pastel Geometry」：粉蓝底 #c8d9e6 + 白卡 + 柔和药丸色（紫/薄荷/鼠尾草）
    "pastel": dict(
        bg="#c8d9e6", paper="#cddde9", card="#faf9f7",
        ink="#1d2a36", text2="#34434f", sub="#5b6b78", muted="#8493a0", faint="#aab6c0",
        accent="#7c6aad", accent_text="#faf9f7", accent2="#5a7c6a",
        chip_bg="#e8eef4", chip_text="#34434f", metric_bg="#eaf0f5", comment_bg="#eef3f8",
        border="#b9cad8", border2="#a6bccd", wm="#dde7ef",
        cmd_bg="#1d2a36", cmd_text="#a8d4c4",
        grid="rgba(29,42,54,.05)",
    ),
    # 6. split 双色拼接（浅色）—— 参考 frontend-slides「Split Pastel」：蜜桃 #f5e6dc 底 + 薰衣草紫强调，活泼年轻
    "split": dict(
        bg="#f5e6dc", paper="#f1ddd0", card="#fffdfb",
        ink="#3a2e26", text2="#5a4a3e", sub="#7d6a5c", muted="#a08d7d", faint="#c2b1a2",
        accent="#8a6fb0", accent_text="#fffdfb", accent2="#5e9e86",
        chip_bg="#f3e2d8", chip_text="#5a4a3e", metric_bg="#f6e9e0", comment_bg="#f5e7df",
        border="#e7d3c6", border2="#dcc4b4", wm="#efe0d4",
        cmd_bg="#3a2e26", cmd_text="#e0b3c6",
        grid="rgba(58,46,38,.05)",
    ),
    # 7. terminal 终端绿（深色）—— 参考 frontend-slides「Terminal Green」：GitHub 暗底 #0d1117 + 终端绿 #39d353，开发者原生审美
    "terminal": dict(
        bg="#0d1117", card="#161b22",
        ink="#e6edf3", text2="#c9d1d9", sub="#8b949e", muted="#6e7681", faint="#484f58",
        accent="#39d353", accent_text="#0d1117", accent2="#58a6ff",
        chip_bg="#21262d", chip_text="#c9d1d9", metric_bg="#21262d", comment_bg="#161b22",
        border="#30363d", border2="#21262d", wm="#161b22",
        cmd_bg="#010409", cmd_text="#7ee787",
        grid="rgba(240,246,252,.03)", panel_border="#30363d",
        cover_bg="linear-gradient(160deg,#0d1117 0%,#161b22 55%,#0d1117 100%)",
    ),
    # 8. neon 霓虹赛博（深色）—— 参考「Neon Cyber」：深海军蓝 #0a0f1c + 霓虹青 #00ffcc + 品红 #ff00aa
    "neon": dict(
        bg="#0a0f1c", card="#0e1726",
        ink="#eaf6ff", text2="#bcd6ee", sub="#7d9bbd", muted="#5e7aa0", faint="#3a4f6e",
        accent="#00ffcc", accent_text="#04141a", accent2="#ff00aa",
        chip_bg="#142036", chip_text="#bcd6ee", metric_bg="#122033", comment_bg="#0e1726",
        border="#1d2c45", border2="#16263d", wm="#122033",
        cmd_bg="#050a14", cmd_text="#00ffcc",
        grid="rgba(0,255,204,.04)", panel_border="#1d2c45",
        cover_bg="linear-gradient(150deg,#0a0f1c 0%,#0e2436 100%)",
    ),
    # 9. signal 高亮橙（深色）—— 参考「Bold Signal」：暗底 + 高饱和橙 #FF5722 焦点色，带 135° 暗渐变
    "signal": dict(
        bg="#1a1a1a", card="#212121",
        ink="#ffffff", text2="#e4e4e4", sub="#a8a8a8", muted="#7a7a7a", faint="#555555",
        accent="#FF5722", accent_text="#ffffff", accent2="#ffb300",
        chip_bg="#2a2a2a", chip_text="#e4e4e4", metric_bg="#262626", comment_bg="#241f1c",
        border="#333333", border2="#3a3a3a", wm="#262626",
        cmd_bg="#0d0d0d", cmd_text="#ff8a50",
        grid="rgba(255,255,255,.035)", panel_border="#3a3a3a",
        cover_bg="linear-gradient(135deg,#1a1a1a 0%,#2d2d2d 50%,#1a1a1a 100%)",
    ),
    # 10. botanic 暗夜植物（深色）—— 参考「Dark Botanical」：近黑 #0f0f0f + 暖金 #d4a574 + 赤陶，优雅杂志感
    "botanic": dict(
        bg="#0f0f0f", card="#161514",
        ink="#e8e4df", text2="#cfc9c1", sub="#9a9590", muted="#6f6a64", faint="#4a463f",
        accent="#d4a574", accent_text="#ffffff", accent2="#c9b896",
        chip_bg="#1e1c1a", chip_text="#cfc9c1", metric_bg="#1c1a18", comment_bg="#1a1714",
        border="#2a2724", border2="#36322d", wm="#1c1a18",
        cmd_bg="#0a0a0a", cmd_text="#d4a574",
        grid="rgba(232,228,223,.035)", panel_border="#2e2b27",
        cover_bg="linear-gradient(155deg,#0f0f0f 0%,#1a1714 100%)",
    ),
}

ORDER = ["cream", "klein", "forest", "swiss", "pastel", "split",
         "terminal", "neon", "signal", "botanic"]

DARK_THEMES = {"terminal", "neon", "signal", "botanic"}


def list_themes():
    return list(ORDER)


def rotate_index(date_str):
    """按日期轮换：年内第几天 % 10，相邻两天必不同主题。"""
    from datetime import date as _d
    y, m, dd = (int(x) for x in date_str.split("-"))
    return _d(y, m, dd).timetuple().tm_yday % len(ORDER)


def resolve(date_str, explicit=None):
    """返回 (主题名, 令牌 dict)。explicit 可为主题名或 None。浅色主题默认无面板描边。"""
    if explicit and explicit in THEMES:
        name = explicit
    else:
        name = ORDER[rotate_index(date_str)]
    tokens = dict(THEMES[name])
    tokens.setdefault("panel_border", "transparent")
    tokens.setdefault("paper", tokens["bg"])
    # 浅色主题无渐变，给一个同色平铺渐变，保证 cover_bg 始终是合法 background-image 图层
    tokens.setdefault("cover_bg", "linear-gradient(180deg,%s,%s)" % (tokens["bg"], tokens["bg"]))
    return name, tokens
