# -*- coding: utf-8 -*-
"""
12 个语义块的画面定义 —— 每块一屏，内容由那一句口播决定。

═══════════════════════════════════════════════════════════════════════
本文件当前实例：jihe520/MathModelAgent（数学建模 Agent）。
═══════════════════════════════════════════════════════════════════════
"""

from scene_kit import WAVE, WAVE2, dots, bars, chars

WAVE_BIG = [int(round(h * 1.85)) for h in WAVE]

# ===================================================================== c1
C1_HTML = """
<div class="kick">今天讲</div>
<div class="mega">@@MEGA@@</div>
<div class="repo">@@REPO@@</div>
<div class="flowbox cd">
  <div class="fb-h">全流程 · 一条命令</div>
  <div class="flow">
    <div class="fn f1"><b>01</b><span>读题</span></div>
    <div class="fa">→</div>
    <div class="fn f2"><b>02</b><span>建模</span></div>
    <div class="fa">→</div>
    <div class="fn f3"><b>03</b><span>写代码</span></div>
    <div class="fa">→</div>
    <div class="fn f4"><b>04</b><span>出图</span></div>
    <div class="fa">→</div>
    <div class="fn f5"><b>05</b><span>排版</span></div>
    <div class="fa">→</div>
    <div class="fn f6"><b>06</b><span>出 PDF</span></div>
  </div>
</div>
<div class="foot">
  <div class="chips">
    <span class="tg">数学建模</span><span class="tg">自动写代码</span><span class="tg">直出论文</span>
  </div>
  <div class="cue">开源 · SKILL 驱动</div>
</div>
"""
C1_JS = """
var B='[data-b="c1"]';
tl.from(B+' .kick',{opacity:0,y:-18,duration:.4,ease:'power2.out'},@@S@@);
tl.from(B+' .mega .tm',{opacity:0,y:70,duration:.5,stagger:.022,ease:'back.out(1.6)'},@@S@@+0.1);
tl.from(B+' .repo',{opacity:0,y:20,duration:.4},@@S@@+0.45);
tl.from(B+' .flowbox',{opacity:0,y:34,duration:.5,ease:'power2.out'},@@S@@+0.5);
tl.from(B+' .flow .fa',{opacity:0,duration:.3,stagger:.06},@@S@@+0.72);
mark(B+' .f1', @@S@@+0.62);
mark(B+' .f2', @@S@@+1.12);
mark(B+' .f3', @@S@@+1.62);
mark(B+' .f4', @@S@@+2.12);
mark(B+' .f5', @@S@@+2.62);
mark(B+' .f6', @@S@@+3.12);
tl.from(B+' .foot',{opacity:0,y:22,duration:.44},@@S@@+0.95);
"""

# ===================================================================== c2
C2_HTML = """
<div class="pain">
  <div class="pcard cd">
    <div class="cd-h"><span class="dot w"></span>比赛前两天</div>
    <div class="pt">全在调代码</div>
    <div class="psub">模型改一版、代码跑一遍，时间就这么没了。</div>
    <div class="meter"><i></i></div>
    <div class="mlab"><span>第 一 天</span><span>第 二 天 · 耗 尽 ↑</span></div>
  </div>
  <div class="pcard cd">
    <div class="cd-h"><span class="dot w"></span>比赛最后一天</div>
    <div class="pt">全耗在排版</div>
    <div class="psub">公式编号、图表标题、参考文献，一条条手工对齐。</div>
    <div class="cmp">
      <div class="cr"><span class="ck">公式编号</span><span class="cv bad">(3) (3) (4)</span></div>
      <div class="cr"><span class="ck">图表标题</span><span class="cv bad">图 2 / 图 2</span></div>
    </div>
    <div class="risk">改一次正文，页码和编号全乱一遍</div>
  </div>
</div>
"""
C2_JS = """
var B='[data-b="c2"]';
tl.from(B+' .pcard',{opacity:0,y:30,duration:.52,stagger:.12,ease:'power2.out'},@@S@@+0.06);
tl.from(B+' .pcard:nth-child(1) .pt, '+B+' .pcard:nth-child(1) .psub',{opacity:0,y:18,duration:.42,stagger:.1},@@W:调代码|0.24@@);
tl.fromTo(B+' .meter > i',{width:'4%'},{width:'92%',duration:1.4,ease:'power1.out'},@@W:调代码|0.24@@+0.3);
tl.from(B+' .pcard:nth-child(1) .mlab',{opacity:0,duration:.4},@@W:调代码|0.24@@+0.46);
tl.from(B+' .pcard:nth-child(2) .pt, '+B+' .pcard:nth-child(2) .psub',{opacity:0,y:18,duration:.42,stagger:.1},@@W:排版|0.62@@);
tl.from(B+' .cmp .cr',{opacity:0,x:26,duration:.38,stagger:.12},@@W:排版|0.62@@+0.2);
tl.from(B+' .risk',{opacity:0,y:14,scale:.95,duration:.44,ease:'back.out(1.7)'},@@W:排版|0.62@@+0.78);
"""

# ===================================================================== c3
C3_HTML = """
<div class="proj cd">
  <div class="proj-h"><span class="tg ok">开源项目</span><span class="proj-n">@@REPO@@</span></div>
  <div class="proj-d">专为数学建模做的 Agent，从读题到出 PDF 一条链路。</div>
  <div class="proj-m"><span>Python</span><span>桌面版 v0.0.20</span><span class="fresh">昨天刚提交</span></div>
</div>
<div class="tags3">
  <span class="tg3">自动建模</span>
  <span class="tg3">生成论文</span>
  <span class="tg3">直出 PDF</span>
</div>
"""
C3_JS = """
var B='[data-b="c3"]';
tl.from(B+' .proj',{opacity:0,y:26,duration:.5,ease:'power2.out'},@@S@@+0.06);
tl.from(B+' .tg3',{opacity:0,y:18,duration:.38,stagger:.12,ease:'back.out(1.6)'},@@W:自动|0.2@@);
tl.to(B+' .fresh',{opacity:1,duration:.36},@@W:提交|0.72@@);
"""

# ===================================================================== c4
C4_HTML = """
<div class="sh"><span class="sh-n">核心目标</span><span class="sh-t">把比赛压成 1 小时</span></div>
<div class="cmp3">
  <div class="c3r">
    <div class="c3h">以前</div>
    <div class="c3b"><i></i></div>
    <div class="c3l">3 天</div>
  </div>
  <div class="arrow3">→</div>
  <div class="c3r bright">
    <div class="c3h">现在</div>
    <div class="c3b"><i></i></div>
    <div class="c3l">1 小时</div>
  </div>
</div>
"""
C4_JS = """
var B='[data-b="c4"]';
tl.from(B+' .sh',{opacity:0,y:-20,duration:.42,ease:'power2.out'},@@S@@);
tl.from(B+' .cmp3',{opacity:0,y:28,duration:.5,ease:'power2.out'},@@S@@+0.14);
tl.fromTo(B+' .c3r:nth-child(1) .c3b > i',{width:'0%'},{width:'100%',duration:.9,ease:'power1.inOut'},@@W:三天|0.18@@);
tl.from(B+' .arrow3',{opacity:0,scale:.5,duration:.44,ease:'back.out(2)'},@@S@@+0.44);
tl.fromTo(B+' .c3r.bright .c3b > i',{width:'0%'},{width:'18%',duration:.58,ease:'power1.inOut'},@@W:一小时|0.68@@);
mark(B+' .c3r.bright', @@W:一小时|0.68@@);
"""

# ===================================================================== p1
P1_HTML = """
<div class="old">
  <span class="vtag">你以为</span>
  <div class="vtx">又一个帮你查资料的工具</div>
  <div class="strike"></div>
  <div class="cross">✗</div>
</div>
<div class="arrow"><span>↓</span><span>其实不是</span></div>
<div class="new">
  <span class="vtag">实际上是</span>
  <div class="vtx">一个能跑完全程的建模队</div>
  <div class="tags"><i>读题定模型</i><i>写代码出图</i><i>排版成稿</i></div>
  <div class="tick">✓</div>
</div>
"""
P1_JS = """
var B='[data-b="p1"]';
tl.from(B+' .old',{opacity:0,y:-26,duration:.46},@@S@@);
tl.from(B+' .old .vtx',{opacity:0,y:18,duration:.4},@@S@@+0.22);
tl.to(B+' .strike',{scaleX:1,duration:.42,ease:'power2.inOut'},@@W:不是|0.12@@);
tl.to(B+' .old',{opacity:.4,duration:.4},@@W:全程|0.46@@);
tl.from(B+' .old .cross',{opacity:0,scale:.4,duration:.36,ease:'back.out(2)'},@@W:全程|0.46@@+0.14);
tl.from(B+' .arrow',{opacity:0,y:-10,duration:.34},@@W:全程|0.46@@+0.24);
tl.fromTo(B+' .new',{opacity:.26,scale:.985},{opacity:1,scale:1,duration:.62,ease:'power2.out'},@@W:全程|0.46@@);
tl.from(B+' .new .vtag, '+B+' .new .vtx',{opacity:0,y:22,duration:.44,stagger:.1},@@W:全程|0.46@@+0.16);
tl.from(B+' .new .tags > i',{opacity:0,y:16,duration:.38,stagger:.11},@@W:全程|0.46@@+0.66);
"""

# ===================================================================== p2
P2_HTML = """
<div class="bh"><span class="bh-n">3</span><span class="bh-t">个角色，各管一摊</span></div>
<div class="roles">
  <div class="r3 cd">
    <div class="r3-n">01</div>
    <div class="r3-b"><div class="r3-t">建模手</div><div class="r3-d">读题、选模型、写假设</div></div>
    <div class="r3-m"><span class="mm">独立配模型</span></div>
  </div>
  <div class="r3 cd">
    <div class="r3-n">02</div>
    <div class="r3-b"><div class="r3-t">代码手</div><div class="r3-d">写代码、跑数据、出图</div></div>
    <div class="r3-m"><span class="mm">独立配模型</span></div>
  </div>
  <div class="r3 cd">
    <div class="r3-n">03</div>
    <div class="r3-b"><div class="r3-t">论文手</div><div class="r3-d">排版、成稿、交稿前自检</div></div>
    <div class="r3-m"><span class="mm">独立配模型</span></div>
  </div>
</div>
<div class="note2">每个角色单独指定模型 —— 由 litellm 接入，任意模型都能用。</div>
"""
P2_JS = """
var B='[data-b="p2"]';
tl.from(B+' .bh',{opacity:0,x:-24,duration:.44},@@S@@);
tl.from(B+' .r3',{opacity:0,y:26,duration:.42,stagger:.1,ease:'power2.out'},@@S@@+0.12);
tl.from(B+' .note2',{opacity:0,duration:.4},@@S@@+0.4);
gsap.set(B+' .mm',{opacity:.3});
mark(B+' .r3:nth-child(1)', @@W:建模手|0.1@@);
mark(B+' .r3:nth-child(2)', @@W:代码手|0.36@@);
mark(B+' .r3:nth-child(3)', @@W:论文手|0.6@@);
tl.to(B+' .mm',{opacity:1,duration:.4,stagger:.14},@@W:模型|0.84@@);
"""

# ===================================================================== p3
P3_HTML = """
<div class="bh"><span class="bh-n">17</span><span class="bh-t">套论文模板</span></div>
<div class="evs">
  <div class="tp cd">
    <div class="tp-n">国赛</div>
    <div class="tp-d">CUMCM<br>中文赛事</div>
    <div class="tp-k">✓</div>
  </div>
  <div class="tp cd">
    <div class="tp-n">华数杯</div>
    <div class="tp-d">中文赛事<br>另含华为杯</div>
    <div class="tp-k">✓</div>
  </div>
  <div class="tp cd">
    <div class="tp-n">美赛</div>
    <div class="tp-d">MCM / ICM<br>英文赛事</div>
    <div class="tp-k">✓</div>
  </div>
</div>
"""
P3_JS = """
var B='[data-b="p3"]';
tl.from(B+' .bh',{opacity:0,x:-24,duration:.44},@@S@@);
tl.from(B+' .tp',{opacity:0,y:26,duration:.44,stagger:.1,ease:'power2.out'},@@S@@+0.12);
gsap.set(B+' .tp-k',{opacity:.22});
mark(B+' .tp:nth-child(1)', @@W:国赛|0.62@@);
mark(B+' .tp:nth-child(2)', @@W:华数杯|0.74@@);
mark(B+' .tp:nth-child(3)', @@W:美赛|0.86@@);
tl.to(B+' .tp-k',{opacity:1,duration:.32,stagger:.14},@@W:国赛|0.62@@+0.24);
"""

# ===================================================================== p4
P4_HTML = """
<div class="bh"><span class="bh-n">9</span><span class="bh-t">步自动验收，交稿前跑一遍</span></div>
<div class="chk cd">
  <div class="ci"><b>✓</b><span class="ci-t">文本泄漏检测</span>
    <span class="ci-d">模板残留、占位符、没替换掉的变量</span></div>
  <div class="ci"><b>✓</b><span class="ci-t">数值一致性校验</span>
    <span class="ci-d">正文里的每个数字，回头对一遍代码输出</span></div>
  <div class="ci"><b>✓</b><span class="ci-t">Typst 编译通过</span>
    <span class="ci-d">排版不报错，才轮得到出 PDF</span></div>
  <div class="ci"><b>✓</b><span class="ci-t">PDF 逐页可视化检查</span>
    <span class="ci-d">一页页看图，找错位和溢出</span></div>
</div>
<div class="quote">「AI 生成仅供参考，目前水平直接参加国赛获奖是不可能的。」
  <small>—— 项目作者写在 README 里</small></div>
"""
P4_JS = """
var B='[data-b="p4"]';
tl.from(B+' .bh',{opacity:0,x:-24,duration:.44},@@S@@);
tl.from(B+' .chk',{opacity:0,y:26,duration:.48},@@S@@+0.1);
tl.from(B+' .quote',{opacity:0,y:22,duration:.46},@@S@@+0.4);
gsap.set(B+' .ci > b',{opacity:.24});
tl.to(B+' .ci:nth-child(1) > b',{opacity:1,duration:.32},@@S@@+0.5);
tl.to(B+' .ci:nth-child(2) > b',{opacity:1,duration:.32},@@W:数字对得上|0.55@@);
tl.to(B+' .ci:nth-child(3) > b',{opacity:1,duration:.32},@@W:编译通过|0.74@@);
tl.to(B+' .ci:nth-child(4) > b',{opacity:1,duration:.32},@@W:逐页看图|0.9@@);
mark(B+' .ci:nth-child(2)', @@W:数字对得上|0.55@@);
mark(B+' .ci:nth-child(3)', @@W:编译通过|0.74@@);
mark(B+' .ci:nth-child(4)', @@W:逐页看图|0.9@@);
"""

# ===================================================================== s1
S1_HTML = """
<div class="sh"><span class="sh-n">上手</span><span class="sh-t">一行命令，装上就能跑</span></div>
<div class="term">
  <div class="tbar"><i></i><i></i><i></i><span>terminal</span></div>
  <div class="tbody">
    <div class="cline"><span class="ps">$</span><span class="cmd">@@CMDCH@@</span></div>
    <div class="tout"><span>✔</span>SKILLS 已安装 · 17 套模板 + 知识库</div>
  </div>
</div>
<div class="note">也可以直接下桌面版 —— 内置 Claude Code，填个 Key 就能开工</div>
"""
S1_JS = """
var B='[data-b="s1"]';
tl.from(B+' .sh',{opacity:0,y:-20,duration:.44,ease:'power2.out'},@@S@@);
tl.from(B+' .term',{opacity:0,y:34,scale:.97,duration:.5,ease:'power2.out'},@@S@@+0.14);
tl.from(B+' .tm',{opacity:0,duration:.01,stagger:.014},@@W:命令|0.2@@);
tl.from(B+' .tout',{opacity:0,y:14,duration:.42},@@W:命令|0.2@@+0.7);
tl.from(B+' .note',{opacity:0,duration:.4},@@W:桌面版|0.46@@);
"""

# ===================================================================== s2 金句
S2_HTML = """
<div class="veil" data-deco></div>
<span class="pill">写 给 赶 稿 的 队 伍</span>
<div class="q1">数学建模比赛</div>
<div class="q2">比的从来不是谁算得快</div>
<div class="q3">是谁最后交得出来</div>
"""
S2_JS = """
var B='[data-b="s2"]';
tl.from(B+' .veil',{opacity:0,scale:.985,duration:.5,ease:'power2.out'},@@S@@);
tl.from(B+' .pill',{opacity:0,y:-14,duration:.42},@@S@@+0.14);
tl.from(B+' .q1',{opacity:0,y:34,duration:.52,ease:'power2.out'},@@W:建模|0.18@@);
tl.from(B+' .q2',{opacity:0,y:34,duration:.52,ease:'power2.out'},@@W:算得快|0.38@@);
tl.from(B+' .q3',{opacity:0,y:34,duration:.52,ease:'power2.out'},@@W:交得出来|0.62@@);
"""

# ===================================================================== s3 CTA
S3_HTML = """
<div class="cta">
  <div class="ca1">先收藏</div>
  <div class="ca2">赛前装一遍</div>
  <div class="ca3"><span class="cloop">🔁</span>点个关注</div>
  <div class="ca4">每天一个 Github 热门项目</div>
</div>
"""
S3_JS = """
var B='[data-b="s3"]';
tl.from(B+' .ca1',{opacity:0,y:-18,duration:.44,ease:'power2.out'},@@S@@);
tl.from(B+' .ca2',{opacity:0,y:-18,duration:.44,ease:'power2.out'},@@S@@+0.2);
tl.from(B+' .ca3',{opacity:0,y:-18,duration:.44,ease:'power2.out'},@@S@@+0.4);
tl.from(B+' .ca4',{opacity:0,y:-18,duration:.44,ease:'power2.out'},@@S@@+0.6);
"""

# ===================================================================== s4 挑边
S4_HTML = """
<div class="prow">
  <div class="po po-a">
    <div class="po-k">A</div>
    <div class="po-t">跑不出结果</div>
    <div class="po-d">模型选错、代码报错，卡在第二天夜里</div>
  </div>
  <div class="vs">VS</div>
  <div class="po po-b">
    <div class="po-k">B</div>
    <div class="po-t">排不完版</div>
    <div class="po-d">数字对不上、编号全乱，卡在交稿前</div>
  </div>
</div>
<div class="pft"><span class="bb">···</span>评论区聊聊</div>
"""
S4_JS = """
var B='[data-b="s4"]';
tl.from(B+' .po',{opacity:0,y:30,duration:.48,stagger:.12,ease:'power2.out'},@@S@@+0.06);
tl.from(B+' .vs',{opacity:0,scale:.7,duration:.4,ease:'back.out(2)'},@@S@@+0.3);
mark(B+' .po-a', @@W:跑不出结果|0.06@@);
mark(B+' .po-b', @@W:排不完版|0.56@@);
tl.from(B+' .pft',{opacity:0,y:22,duration:.46,ease:'back.out(1.5)'},@@W:评论区|0.8@@);
"""

# ===================================================================== BOARDS 对照表
BOARDS = {
    "c1": dict(cls="", html=C1_HTML, js=C1_JS,
               expect=["MathModelAgent", "数学建模", "读题", "出 PDF"]),
    "c2": dict(cls="top", html=C2_HTML, js=C2_JS,
               expect=["全在调代码", "全耗在排版", "编号"]),
    "c3": dict(cls="", html=C3_HTML, js=C3_JS,
               expect=["开源项目", "自动建模", "直出论文"]),
    "c4": dict(cls="", html=C4_HTML, js=C4_JS,
               expect=["核心目标", "压成", "一小时"]),
    "p1": dict(cls="", html=P1_HTML, js=P1_JS,
               expect=["查资料", "跑完全程", "建模队"]),
    "p2": dict(cls="top", html=P2_HTML, js=P2_JS,
               expect=["建模手", "代码手", "论文手", "独立配模型"]),
    "p3": dict(cls="", html=P3_HTML, js=P3_JS,
               expect=["17", "国赛", "华数杯", "美赛"]),
    "p4": dict(cls="", html=P4_HTML, js=P4_JS,
               expect=["9", "文本泄漏检测", "数值一致性校验", "Typst 编译", "逐页可视化"]),
    "s1": dict(cls="", html=S1_HTML, js=S1_JS,
               expect=["一行命令", "npx", "Claude Code"]),
    "s2": dict(cls="", html=S2_HTML, js=S2_JS,
               expect=["算得快", "交得出来"]),
    "s3": dict(cls="", html=S3_HTML, js=S3_JS,
               expect=["收藏", "关注"]),
    "s4": dict(cls="top", html=S4_HTML, js=S4_JS,
               expect=["跑不出结果", "排不完版", "评论区"]),
}

def fill(txt: str, data: dict) -> str:
    for k, v in (
        ("@@MEGA@@", chars(data["repo_short"])),
        ("@@REPO@@", data["repo"]),
        ("@@BRAND@@", data["brand"]),
        ("@@STARS@@", str(data["stars"])),
        ("@@STARS_K@@", data["stars_k"]),
        ("@@QUOTE_EN@@", data["quote_en"]),
        ("@@WAVEB@@", bars(WAVE_BIG)),
        ("@@WAVE2@@", bars(WAVE2)),
        ("@@WAVE@@", bars(WAVE)),
        ("@@D16@@", dots(16)),
        ("@@D11@@", dots(11)),
        ("@@CMDCH@@", chars(data["cmd"])),
    ):
        txt = txt.replace(k, v)
    return txt

def build_html(block_id: str, data: dict) -> str:
    return fill(BOARDS[block_id]["html"], data)
