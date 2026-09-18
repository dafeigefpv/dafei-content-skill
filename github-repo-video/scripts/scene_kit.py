# -*- coding: utf-8 -*-
"""
视频原生版式的设计系统（3:4 / 1440×1920）。

为什么另起一套而不是继续用 github-project-xhs 的卡片
----------------------------------------------------
卡片是为「静态图文」排的：信息密度优先，一页塞满 12 个区块，读者可以停留。
视频是「口播驱动」的：观众只能跟着声音走，一屏塞满就等于什么都没看见。
两者的最优解不同 —— 硬把卡片搬进视频，必然出现「文不对画面」。

本版规则：**一个语义块 = 一屏画面**。画面上出现的每个元素，都由那一句口播决定。

版面分区（1440×1920）
---------------------
    y    0 ..  150   顶栏 HUD      系列徽章（左） / 仓库名 + ★（右）
    y  158 ..  202   进度轨        4 段，标出当前讲到哪
    y  240 .. 1520   舞台 Stage    1224×1280，一块一屏
    y 1552 .. 1788   字幕带        独占，深色胶囊，最长 2 行（40px 时全为单行）
    y 1822 .. 1882   底栏          品牌 + 项目地址

字幕带独占是本版最重要的结构改动：卡片版字幕无处可放，只能压在内容上，
由此引出字号、折行、页脚让位一整套坑。现在字幕有 236px 专属高度，
2 行容量 —— 折行不再致命（40px 下实测 12 条全部单行）。
"""

W, H = 1440, 1920

MARGIN = 108
STAGE_W = W - MARGIN * 2          # 1224
STAGE_TOP = 240
STAGE_H = 1280                    # 240 .. 1520
CAP_TOP, CAP_H = 1552, 236        # 1552 .. 1788
FOOT_TOP = 1822

# 设计令牌（klein 克莱因蓝主题）
TOKENS = """
:root{
  --f-cjk:'Microsoft YaHei','PingFang SC',sans-serif;
  --f-num:'Bahnschrift','Segoe UI Semibold','Arial Black',Arial,sans-serif;
  --f-mono:'Cascadia Mono','Consolas','JetBrains Mono',monospace;

  --bg:#f7f8fa; --paper:#f2f4f8; --card:#ffffff;
  --ink:#10131a; --ink2:#2c313c; --sub:#5a616e; --muted:#8b92a1; --faint:#aeb4c0;
  --acc:#002fa7; --acc-s:#e7ebf9; --acc-d:#00217a;
  --warn:#ff4f28; --warn-s:#ffece7;
  --ok:#0d8a5f; --ok-s:#e4f6ee;
  --ln:#e2e6ef; --ln2:#cbd2e0;
  --cmd-bg:#0d1017; --cmd-tx:#7ad0ff;
}
"""

SHELL_CSS = """
@font-face { font-family:'Microsoft YaHei'; src:local('Microsoft YaHei'), local('微软雅黑'); }
@font-face { font-family:'PingFang SC';    src:local('PingFang SC'); }
@font-face { font-family:'Bahnschrift';    src:local('Bahnschrift'), local('Bahnschrift SemiBold'); }
@font-face { font-family:'Cascadia Mono';  src:local('Cascadia Mono'), local('Cascadia Code'); }
@font-face { font-family:'Consolas';       src:local('Consolas'); }

/* 全局 border-box：卡片都是 padding + 2px 边框，不设 border-box 的话
   高度会「内容 + padding + border」叠加，撑破舞台（实测 s2/s5 各越界 18/22px）。 */
*, *::before, *::after { box-sizing:border-box; }
html, body { margin:0; width:1440px; height:1920px; overflow:hidden; background:var(--bg); }
#stage { position:relative; width:1440px; height:1920px; overflow:hidden; }
/* 背景：极淡点阵，给 3:4 的大留白一点质感，不影响文字对比度 */
#stage::before { content:''; position:absolute; inset:0; pointer-events:none;
  background-image:
    linear-gradient(rgba(16,19,26,.032) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16,19,26,.032) 1px, transparent 1px);
  background-size:72px 72px; }
.scene { position:absolute; inset:0; overflow:hidden; }
.tm { display:inline-block; }

/* ---------------------------------------------------------------- 顶栏 */
.hud { position:absolute; left:108px; right:108px; top:62px; height:88px;
  display:flex; align-items:center; justify-content:space-between; z-index:60; }
.hud-badge { display:inline-flex; align-items:center; gap:13px;
  background:var(--ink); color:#fff; border-radius:999px; padding:14px 27px;
  font:700 27px/1 var(--f-cjk); letter-spacing:.02em; }
.hud-badge::before { content:''; width:11px; height:11px; border-radius:50%;
  background:#ff5a36; box-shadow:0 0 0 4px rgba(255,90,54,.22); }
.hud-r { display:flex; align-items:center; gap:18px; }
.hud-repo { font:700 29px/1 var(--f-mono); color:var(--ink2); letter-spacing:-.01em; }
.hud-star { display:inline-flex; align-items:center; gap:9px;
  background:var(--acc); color:#fff; border-radius:999px; padding:13px 23px;
  font:800 27px/1 var(--f-num); letter-spacing:.01em; }

/* ------------------------------------------------------------ 进度轨 */
.rail { position:absolute; left:108px; right:108px; top:160px; height:44px;
  display:flex; gap:16px; z-index:60; }
.rag { flex:1; display:flex; flex-direction:column; gap:9px; }
.rag-k { font:600 22px/1 var(--f-cjk); color:var(--faint); letter-spacing:.08em; }
.rag-b { height:5px; border-radius:3px; background:#e4e8f1; overflow:hidden; }
.rag-b > i { display:block; height:100%; width:0; background:var(--acc); border-radius:3px; }
.rag.on .rag-k { color:var(--acc); }

/* --------------------------------------------------------------- 舞台 */
.board { position:absolute; left:108px; top:240px; width:1224px; height:1280px;
  opacity:0; display:flex; flex-direction:column; justify-content:center; z-index:20; }
/* 撑满型的行容器（六宫格 / 三步 / 挑边）靠 flex:1 占满剩余高度。
   必须配 min-height:0，否则 flex 项不会缩到内容高度以下，尾部元素被顶出舞台。 */
.board > [class*="st3"], .board > [class*="prow"], .board > .grid,
.board > .pain, .board > .st3, .board > .prow { min-height:0; }
.st3 > *, .prow > *, .grid > * { min-height:0; }
.board.top { justify-content:flex-start; }
.board.bottom { justify-content:flex-end; }

/* ----------------------------------------------------- 字幕带（独占） */
#subs { position:absolute; left:0; right:0; top:1552px; height:236px; z-index:900;
  display:flex; align-items:center; justify-content:center; }
.cap { position:absolute; left:0; right:0; text-align:center; opacity:0; }
.cap > span { display:inline-block; max-width:1330px; box-sizing:border-box;
  background:rgba(13,16,24,.93); color:#fff; border-radius:22px;
  padding:15px 32px; font:600 40px/1.34 var(--f-cjk); letter-spacing:.3px;
  box-shadow:0 12px 34px rgba(13,16,24,.20); }

/* --------------------------------------------------------------- 底栏 */
.footbar { position:absolute; left:108px; right:108px; top:1822px; height:60px;
  display:flex; align-items:center; justify-content:space-between; z-index:60; }
.footbar span { font:600 25px/1 var(--f-cjk); color:var(--faint); letter-spacing:.02em; }
"""

# 各板块通用组件（供 video_boards.py 拼装）
COMP_CSS = """
/* 板块标题：编号 + 标题 */
.bh { display:flex; align-items:flex-end; gap:22px; margin-bottom:42px; }
.bh-n { font:900 78px/.86 var(--f-num); color:var(--acc); letter-spacing:-.03em; }
.bh-t { font:800 46px/1.12 var(--f-cjk); color:var(--ink);
  letter-spacing:-.01em; padding-bottom:7px; }

/* 卡片 */
.cd { background:var(--card); border:2px solid var(--ln); border-radius:26px;
  box-shadow:0 10px 30px rgba(16,19,26,.055); }
.cd-h { display:flex; align-items:center; gap:13px; font:800 31px/1 var(--f-cjk);
  color:var(--ink); }
.dot { width:14px; height:14px; border-radius:50%; flex:none; }
.dot.w { background:var(--warn); }
.dot.a { background:var(--acc); }
.dot.g { background:var(--ok); }

/* 药丸标签 */
.tg { display:inline-block; background:var(--acc-s); color:var(--acc);
  border-radius:999px; padding:11px 21px; font:700 26px/1 var(--f-cjk); }
.tg.gh { background:#eef1f7; color:var(--sub); }
.tg.wt { background:var(--warn-s); color:var(--warn); }
.tg.ok { background:var(--ok-s); color:var(--ok); }

/* 点阵 */
.dt { display:inline-block; width:19px; height:19px; border-radius:6px;
  background:#e4e8f1; }
"""

# 每块的样式都挂在 .b-<id> 下，避免板间串样式
BOARD_CSS = {
# ---------------------------------------------------------------- c1 开场
"c1": """
.b-c1 .kick { font:700 32px/1 var(--f-cjk); color:var(--acc);
  letter-spacing:.34em; margin-bottom:30px; }
.b-c1 .mega { font:900 150px/.94 var(--f-num); color:var(--ink);
  letter-spacing:-.035em; }
.b-c1 .mega .tm { display:inline-block; }
.b-c1 .repo { margin-top:34px; font:700 38px/1 var(--f-mono); color:var(--muted);
  letter-spacing:-.01em; }
.b-c1 .chips { margin-top:46px; display:flex; gap:16px; }
.b-c1 .cue { position:absolute; left:0; right:0; bottom:14px; text-align:center;
  font:700 27px/1 var(--f-cjk); color:var(--faint); letter-spacing:.2em; }
""",
# ---------------------------------------------------------------- c2 痛点
"c2": """
.b-c2 .pain { display:flex; gap:40px; height:100%; align-items:center; }
.b-c2 .pcard { flex:1; padding:44px 40px 40px; display:flex;
  flex-direction:column; height:820px; box-sizing:border-box; }
.b-c2 .pt { margin-top:30px; font:900 50px/1.16 var(--f-cjk); color:var(--ink);
  letter-spacing:-.015em; }
.b-c2 .psub { margin-top:20px; font:600 29px/1.5 var(--f-cjk); color:var(--sub); }
/* 左：按字数计费 —— 计量条不断增长 */
.b-c2 .meter { margin-top:auto; height:26px; border-radius:13px; background:#eef1f7;
  overflow:hidden; }
.b-c2 .meter > i { display:block; height:100%; width:0; border-radius:13px;
  background:linear-gradient(90deg,var(--warn),#ff8a5c); }
.b-c2 .mlab { display:flex; justify-content:space-between; margin-top:16px;
  font:700 26px/1 var(--f-num); color:var(--muted); }
/* 右：素材上传 —— 波形 + 云端 */
.b-c2 .wave { margin-top:auto; height:132px; display:flex; align-items:center;
  gap:7px; }
.b-c2 .wave > i { flex:1; border-radius:4px; background:var(--acc); height:8px; }
.b-c2 .up { margin-top:26px; display:flex; align-items:center; gap:14px;
  font:800 29px/1 var(--f-cjk); color:var(--warn); }
.b-c2 .up .ar { font-size:40px; line-height:.7; }
.b-c2 .risk { margin-top:18px; padding:16px 20px; border-radius:16px;
  background:var(--warn-s); color:var(--warn); font:700 27px/1.4 var(--f-cjk); }
""",
# ---------------------------------------------------------------- c3 数据
"c3": """
.b-c3 { align-items:center; text-align:center; }
.b-c3 .hero { display:flex; align-items:baseline; gap:20px; }
.b-c3 .star { font:900 92px/1 var(--f-num); color:#f5b023;
  transform:translateY(-10px); }
.b-c3 .num { font:900 216px/.92 var(--f-num); color:var(--ink);
  letter-spacing:-.045em; }
.b-c3 .cap2 { margin-top:6px; font:700 32px/1 var(--f-cjk); color:var(--muted);
  letter-spacing:.24em; }
.b-c3 .tl { margin-top:70px; width:1010px; display:flex; align-items:center;
  gap:24px; }
.b-c3 .tl-k { font:700 27px/1 var(--f-cjk); color:var(--sub); flex:none; }
.b-c3 .tl-b { flex:1; height:8px; border-radius:4px; background:#e4e8f1;
  overflow:hidden; }
.b-c3 .tl-b > i { display:block; height:100%; width:0; border-radius:4px;
  background:linear-gradient(90deg,var(--acc),#4b7bff); }
.b-c3 .tl-g { font:900 54px/1 var(--f-num); color:var(--acc); flex:none;
  letter-spacing:-.02em; }
.b-c3 .tl-g > small { font:800 27px/1 var(--f-cjk); color:var(--acc);
  margin-left:6px; }
.b-c3 .facts { margin-top:64px; display:flex; gap:20px; }
.b-c3 .fc { padding:26px 34px; display:flex; flex-direction:column; gap:10px;
  align-items:center; }
.b-c3 .fc > b { font:800 32px/1 var(--f-num); color:var(--ink); }
.b-c3 .fc > span { font:600 25px/1 var(--f-cjk); color:var(--muted); }
""",
# ------------------------------------------------------------ p1 不是A是B
"p1": """
.b-p1 { gap:0; }
.b-p1 .old { position:relative; padding:52px 56px; border-radius:28px;
  background:#eef1f7; border:2px dashed var(--ln2); }
.b-p1 .new { position:relative; padding:56px 56px 52px; border-radius:28px;
  background:var(--acc); color:#fff; margin-top:38px;
  box-shadow:0 22px 52px rgba(0,47,167,.26); }
.b-p1 .vtag { display:inline-block; font:800 27px/1 var(--f-cjk);
  letter-spacing:.16em; padding:10px 20px; border-radius:999px; }
.b-p1 .old .vtag { background:#dfe4ee; color:var(--sub); }
.b-p1 .new .vtag { background:rgba(255,255,255,.18); color:#fff; }
.b-p1 .vtx { margin-top:26px; font:900 62px/1.16 var(--f-cjk);
  letter-spacing:-.02em; }
.b-p1 .old .vtx { color:var(--muted); }
.b-p1 .strike { position:absolute; left:44px; right:44px; top:56%;
  height:7px; background:var(--warn); border-radius:4px;
  transform:scaleX(0); transform-origin:left center; }
.b-p1 .tags { margin-top:30px; display:flex; gap:14px; }
.b-p1 .tags > i { font:700 27px/1 var(--f-cjk); font-style:normal;
  background:rgba(255,255,255,.16); border-radius:999px; padding:12px 22px; }
.b-p1 .arrow { display:flex; align-items:center; justify-content:center;
  gap:16px; margin:26px 0 0; font:800 30px/1 var(--f-cjk); color:var(--acc); }
.b-p1 .cross { position:absolute; right:52px; top:48px; font:900 46px/1 var(--f-num);
  color:var(--warn); }
.b-p1 .tick { position:absolute; right:52px; top:52px; font:900 46px/1 var(--f-num);
  color:#8fe3bd; }
""",
# ---------------------------------------------------------------- p2 六合
"p2": """
.b-p2 .grid { display:grid; grid-template-columns:1fr 1fr; gap:24px; flex:1; }
.b-p2 .g6 { padding:34px 36px; display:flex; flex-direction:column;
  justify-content:center; gap:12px; }
.b-p2 .g6-n { font:900 44px/.9 var(--f-num); color:var(--acc);
  letter-spacing:-.02em; }
.b-p2 .g6-t { font:800 40px/1.14 var(--f-cjk); color:var(--ink);
  letter-spacing:-.015em; }
.b-p2 .g6-d { font:600 26px/1.4 var(--f-cjk); color:var(--muted); }
""",
# ---------------------------------------------------------------- p3 引擎
"p3": """
.b-p3 .eng { display:flex; gap:24px; }
.b-p3 .ec { flex:1; padding:34px 36px; }
.b-p3 .ec-v { font:900 88px/.9 var(--f-num); color:var(--acc);
  letter-spacing:-.035em; }
.b-p3 .ec-l { margin-top:10px; font:700 29px/1 var(--f-cjk); color:var(--ink); }
.b-p3 .ec-u { font:600 24px/1 var(--f-mono); color:var(--muted); margin-top:8px; }
.b-p3 .dts { margin-top:22px; display:flex; flex-wrap:wrap; gap:8px; max-width:100%; }
.b-p3 .hw { margin-top:34px; display:flex; flex-direction:column; gap:16px; }
.b-p3 .hwr { display:flex; align-items:center; gap:22px; padding:24px 32px;
  border-radius:20px; background:var(--card); border:2px solid var(--ln); }
.b-p3 .hwk { width:330px; flex:none; font:800 31px/1 var(--f-cjk); color:var(--ink); }
.b-p3 .hwv { font:700 29px/1 var(--f-cjk); color:var(--acc); }
.b-p3 .hwn { margin-left:auto; font:700 25px/1 var(--f-mono); color:var(--faint); }
""",
# ---------------------------------------------------------------- p4 本地
"p4": """
.b-p4 .viz { display:flex; align-items:center; gap:34px; }
.b-p4 .mc { flex:1; padding:40px 42px; position:relative; border-color:var(--acc); }
.b-p4 .mc-h { display:flex; align-items:center; gap:14px; font:800 34px/1 var(--f-cjk);
  color:var(--acc); }
.b-p4 .mc-h .lock { font-size:32px; }
.b-p4 .files { margin-top:28px; display:flex; flex-direction:column; gap:14px; }
.b-p4 .fl { display:flex; align-items:center; gap:16px; padding:20px 24px;
  border-radius:16px; background:var(--paper); font:700 29px/1 var(--f-cjk);
  color:var(--ink2); }
.b-p4 .fl > b { font:800 26px/1 var(--f-mono); color:var(--ok); }
.b-p4 .mc-n { margin-top:24px; font:600 26px/1.45 var(--f-cjk); color:var(--muted); }
.b-p4 .blk { width:300px; flex:none; text-align:center; }
.b-p4 .blk-x { font:900 88px/.9 var(--f-num); color:var(--warn); }
.b-p4 .blk-c { margin-top:14px; font:800 29px/1.35 var(--f-cjk); color:var(--warn); }
.b-p4 .badges { margin-top:34px; display:flex; gap:20px; }
.b-p4 .bd { flex:1; padding:28px 32px; display:flex; flex-direction:column; gap:11px;
  border-radius:22px; background:var(--acc-s); }
.b-p4 .bd > b { font:800 33px/1 var(--f-cjk); color:var(--acc); }
.b-p4 .bd > span { font:600 26px/1 var(--f-cjk); color:var(--sub); }
""",
# ---------------------------------------------------------------- s1 命令
"s1": """
.b-s1 .term { border-radius:26px; overflow:hidden; background:var(--cmd-bg);
  box-shadow:0 24px 60px rgba(13,16,23,.30); }
.b-s1 .tbar { height:62px; display:flex; align-items:center; gap:11px;
  padding:0 26px; background:#191d26; }
.b-s1 .tbar > i { width:14px; height:14px; border-radius:50%; background:#3a4150; }
.b-s1 .tbar > i:nth-child(1){background:#ff5f57;}
.b-s1 .tbar > i:nth-child(2){background:#febc2e;}
.b-s1 .tbar > i:nth-child(3){background:#28c840;}
.b-s1 .tbar > span { margin-left:12px; font:600 24px/1 var(--f-mono); color:#5d6675; }
.b-s1 .tbody { padding:40px 42px 44px; }
.b-s1 .cline { display:flex; gap:18px; align-items:flex-start; }
.b-s1 .ps { font:800 31px/1.5 var(--f-mono); color:#7ad0ff; flex:none; }
.b-s1 .cmd { font:700 28px/1.5 var(--f-mono); color:#d6e2f0;
  word-break:break-all; letter-spacing:-.01em; }
.b-s1 .tout { margin-top:26px; display:flex; align-items:center; gap:14px;
  font:700 29px/1 var(--f-mono); color:#4ee08a; }
.b-s1 .note { margin-top:38px; text-align:center; font:700 30px/1 var(--f-cjk);
  color:var(--muted); letter-spacing:.04em; }
""",
# ---------------------------------------------------------------- s2 克隆
"s2": """
.b-s2 .st3 { display:flex; gap:24px; flex:1; }
.b-s2 .st { flex:1; padding:28px 30px; display:flex; flex-direction:column;
  gap:16px; }
.b-s2 .st-n { width:62px; height:62px; border-radius:50%; background:var(--acc);
  color:#fff; font:900 34px/62px var(--f-num); text-align:center; }
.b-s2 .st-h { font:800 36px/1.2 var(--f-cjk); color:var(--ink); }
.b-s2 .st-wave { margin-top:auto; height:104px; display:flex; align-items:center;
  gap:6px; }
.b-s2 .st-wave > i { flex:1; border-radius:3px; background:var(--acc);
  height:8px; }
.b-s2 .st-time { font:900 54px/.95 var(--f-num); color:var(--warn);
  letter-spacing:-.02em; }
.b-s2 .st-time > small { font:800 27px/1 var(--f-cjk); color:var(--muted);
  margin-left:10px; letter-spacing:0; }
.b-s2 .st-box { margin-top:auto; padding:22px 24px; border-radius:16px;
  background:var(--paper); font:600 27px/1.45 var(--f-cjk); color:var(--ink2); }
.b-s2 .st-play { margin-top:auto; display:flex; align-items:center; gap:16px; }
.b-s2 .pp { width:62px; height:62px; border-radius:50%; background:var(--ok);
  color:#fff; font:700 26px/62px var(--f-num); text-align:center; flex:none; }
.b-s2 .pb { flex:1; height:10px; border-radius:5px; background:#eef1f7;
  overflow:hidden; }
.b-s2 .pb > i { display:block; height:100%; width:0; border-radius:5px;
  background:var(--ok); }
.b-s2 .done { margin-top:14px; display:flex; align-items:center;
  justify-content:center; gap:16px; font:800 36px/1 var(--f-cjk); color:var(--ok); }
""",
# ---------------------------------------------------------------- s3 金句
"s3": """
.b-s3 .veil { position:absolute; inset:-20px; border-radius:40px;
  background:linear-gradient(150deg,#002fa7 0%,#001a63 100%);
  box-shadow:0 30px 80px rgba(0,26,99,.34); z-index:-1; }
.b-s3 { align-items:center; text-align:center; padding:0 80px; }
.b-s3 .pill { display:inline-block; background:rgba(255,255,255,.16); color:#fff;
  border-radius:999px; padding:13px 26px; font:700 27px/1 var(--f-cjk);
  letter-spacing:.2em; }
.b-s3 .q1 { margin-top:60px; font:900 84px/1.2 var(--f-cjk); color:#fff;
  letter-spacing:-.025em; }
.b-s3 .q2 { margin-top:18px; font:900 84px/1.2 var(--f-cjk); color:#8fe3bd;
  letter-spacing:-.025em; }
.b-s3 .en { margin-top:56px; font:600 29px/1.5 var(--f-mono);
  color:rgba(255,255,255,.62); }
""",
# ---------------------------------------------------------------- s4 CTA
"s4": """
.b-s4 .cta { padding:48px 52px; border-radius:30px; }
.b-s4 .cta-r { font:800 44px/1 var(--f-mono); color:var(--ink);
  letter-spacing:-.02em; }
.b-s4 .cta-m { margin-top:26px; display:flex; align-items:center; gap:28px; }
.b-s4 .cta-s { display:flex; align-items:baseline; gap:12px; }
.b-s4 .cta-s > b { font:900 72px/.9 var(--f-num); color:var(--ink);
  letter-spacing:-.03em; }
.b-s4 .cta-s > span { font:900 44px/1 var(--f-num); color:#f5b023; }
.b-s4 .cta-t { margin-left:auto; display:flex; gap:12px; }
.b-s4 .follow { margin-top:44px; display:flex; align-items:center; gap:26px; }
.b-s4 .fbtn { padding:32px 56px; border-radius:999px; background:var(--acc);
  color:#fff; font:800 46px/1 var(--f-cjk); letter-spacing:.06em;
  box-shadow:0 18px 44px rgba(0,47,167,.30); }
.b-s4 .fid { font:800 38px/1.3 var(--f-cjk); color:var(--ink); }
.b-s4 .fid > small { display:block; margin-top:12px; font:600 26px/1 var(--f-cjk);
  color:var(--muted); letter-spacing:.04em; }
.b-s4 .tail { margin-top:40px; text-align:center; font:800 34px/1 var(--f-cjk);
  color:var(--muted); letter-spacing:.22em; }
""",
# ---------------------------------------------------------------- s5 投票
"s5": """
.b-s5 .prow { display:flex; align-items:stretch; gap:26px; flex:1; }
.b-s5 .po { flex:1; padding:38px 36px; border-radius:28px; display:flex;
  flex-direction:column; gap:18px; }
.b-s5 .po-a { background:var(--card); border:2px dashed var(--ln2); }
.b-s5 .po-b { background:var(--acc); border:2px solid var(--acc); color:#fff;
  box-shadow:0 22px 52px rgba(0,47,167,.26); }
.b-s5 .po-k { width:66px; height:66px; border-radius:20px;
  font:900 38px/66px var(--f-num); text-align:center; }
.b-s5 .po-a .po-k { background:#eef1f7; color:var(--sub); }
.b-s5 .po-b .po-k { background:rgba(255,255,255,.18); color:#fff; }
.b-s5 .po-t { font:900 50px/1.18 var(--f-cjk); letter-spacing:-.02em; }
.b-s5 .po-a .po-t { color:var(--ink2); }
.b-s5 .po-d { margin-top:auto; font:600 29px/1.45 var(--f-cjk); }
.b-s5 .po-a .po-d { color:var(--muted); }
.b-s5 .po-b .po-d { color:rgba(255,255,255,.8); }
.b-s5 .vs { align-self:center; font:900 40px/1 var(--f-num); color:var(--faint);
  letter-spacing:.04em; flex:none; }
.b-s5 .pft { margin-top:16px; display:flex; align-items:center;
  justify-content:center; gap:18px; font:800 40px/1 var(--f-cjk); color:var(--acc); }
.b-s5 .bb { width:58px; height:58px; border-radius:18px; background:var(--acc);
  color:#fff; font:800 30px/58px var(--f-num); text-align:center; }
""",
}

# 波形/点阵生成器（固定图案，保证每次渲染一致）
WAVE = [22, 48, 82, 128, 96, 150, 112, 68, 140, 104, 76, 132, 92, 58, 118, 84,
        146, 106, 72, 126, 98, 62, 138, 88, 54, 122, 100, 74, 130, 90, 66, 116]
WAVE2 = [30, 64, 104, 78, 136, 92, 56, 120, 146, 86, 62, 110, 74, 130, 96, 52]


def bars(heights, cls=""):
    a = f' class="{cls}"' if cls else ""
    return "".join(f'<i{a} style="height:{h}px"></i>' for h in heights)


def dots(n, cls="dt"):
    return "".join(f'<i class="{cls}"></i>' for _ in range(n))


def chars(txt):
    """拉丁字符拆成 .tm 便于逐字入场。空格必须用 NBSP —— 普通空格夹在
    inline span 之间会被 HTML 折叠，终端命令会显示成 npxskillsadd…"""
    return "".join(f'<span class="tm">{"&nbsp;" if c == " " else c}</span>' for c in txt)
