# -*- coding: utf-8 -*-
"""
MathModelAgent 视频 —— 各块的局部样式（一屏一块，样式挂在 .b-<块id> 下，互不串扰）。
本实例基于 klein（克莱因蓝）主题 + 白色底纸。
"""

# ---------------------------------------------------------------- c1 开场
_C1 = """
.b-c1 .kick { font:700 36px/1 var(--f-cjk); color:var(--acc); letter-spacing:.34em; margin-bottom:44px; }
.b-c1 .mega { font:900 170px/.94 var(--f-num); color:var(--ink); letter-spacing:-.035em; }
.b-c1 .mega .tm { display:inline-block; }
.b-c1 .repo { margin-top:30px; font:700 44px/1 var(--f-mono); color:var(--muted); letter-spacing:-.01em; }
.b-c1 .flowbox { margin-top:58px; padding:34px 48px; }
.b-c1 .fb-h { font:700 28px/1 var(--f-cjk); color:var(--sub); letter-spacing:.18em; margin-bottom:28px; }
.b-c1 .flow { display:flex; align-items:center; justify-content:space-between; gap:18px; }
.b-c1 .fn { flex:1; padding:52px 22px 48px; display:flex; flex-direction:column; align-items:center; gap:22px; border-radius:24px; background:var(--paper); border:2px solid var(--ln); transition:border-color .3s ease, background .3s ease; }
.b-c1 .fn .tm { font:900 42px/.9 var(--f-num); letter-spacing:-.02em; color:var(--faint); transition:color .3s ease; }
.b-c1 .fn span { font:700 34px/1 var(--f-cjk); color:var(--sub); letter-spacing:.06em; transition:color .3s ease; }
.b-c1 .fn.f1 { border-color:var(--acc); background:#f0f4ff; }
.b-c1 .fn.f1 .tm { color:var(--acc); }
.b-c1 .fn.f1 span { color:var(--ink); }
.b-c1 .fn.f2 { border-color:var(--acc); background:#f0f4ff; }
.b-c1 .fn.f2 .tm { color:var(--acc); }
.b-c1 .fn.f2 span { color:var(--ink); }
.b-c1 .fn.f3 { border-color:var(--acc); background:#f0f4ff; }
.b-c1 .fn.f3 .tm { color:var(--acc); }
.b-c1 .fn.f3 span { color:var(--ink); }
.b-c1 .fn.f4 { border-color:var(--acc); background:#f0f4ff; }
.b-c1 .fn.f4 .tm { color:var(--acc); }
.b-c1 .fn.f4 span { color:var(--ink); }
.b-c1 .fn.f5 { border-color:var(--acc); background:#f0f4ff; }
.b-c1 .fn.f5 .tm { color:var(--acc); }
.b-c1 .fn.f5 span { color:var(--ink); }
.b-c1 .fn.f6 { border-color:var(--acc); background:#f0f4ff; }
.b-c1 .fn.f6 .tm { color:var(--acc); }
.b-c1 .fn.f6 span { color:var(--ink); }
.b-c1 .fa { font:800 48px/1 var(--f-num); color:var(--faint); letter-spacing:0; flex:none; }
.b-c1 .foot { margin-top:56px; display:flex; align-items:center; justify-content:space-between; }
.b-c1 .chips { display:flex; gap:16px; }
.b-c1 .cue { font:700 28px/1 var(--f-cjk); color:var(--faint); letter-spacing:.3em; }
"""

# ---------------------------------------------------------------- c2 痛点
_C2 = """
.b-c2 .pain { height:1000px; margin:auto 0; display:flex; flex-direction:column; gap:32px; min-height:0; }
.b-c2 .pcard { flex:1; min-height:0; padding:42px 48px; display:flex; flex-direction:column; }
.b-c2 .pt { margin-top:22px; font:900 58px/1.08 var(--f-cjk); color:var(--ink); letter-spacing:-.02em; }
.b-c2 .psub { margin-top:14px; font:600 30px/1.45 var(--f-cjk); color:var(--sub); }
.b-c2 .meter { margin-top:auto; height:28px; border-radius:14px; background:#eef1f7; overflow:hidden; }
.b-c2 .meter > i { display:block; height:100%; width:0; border-radius:14px; background:linear-gradient(90deg,var(--warn),#ff8a5c); }
.b-c2 .mlab { display:flex; justify-content:space-between; margin-top:16px; font:700 26px/1 var(--f-num); color:var(--muted); letter-spacing:.1em; }
.b-c2 .cmp { margin-top:auto; display:flex; flex-direction:column; gap:14px; }
.b-c2 .cr { display:flex; align-items:center; gap:16px; }
.b-c2 .ck { font:700 32px/1 var(--f-cjk); color:var(--ink); flex:none; width:148px; }
.b-c2 .cv { font:600 30px/1 var(--f-mono); color:var(--sub); }
.b-c2 .cv.bad { color:var(--warn); }
.b-c2 .cx { margin-left:auto; font:800 26px/1 var(--f-cjk); color:var(--warn); letter-spacing:.1em; }
.b-c2 .risk { margin-top:16px; padding:16px 22px; border-radius:16px; background:var(--warn-s); color:var(--warn); font:700 27px/1.4 var(--f-cjk); }
"""

# ---------------------------------------------------------------- c3 项目+标签
_C3 = """
.b-c3 { align-items:center; text-align:center; }
.b-c3 .proj { align-self:stretch; padding:42px 52px; display:flex; flex-direction:column; gap:20px; text-align:left; }
.b-c3 .proj-h { display:flex; align-items:center; gap:20px; }
.b-c3 .proj-n { font:800 50px/1 var(--f-mono); color:var(--ink); letter-spacing:-.02em; }
.b-c3 .proj-d { font:600 32px/1.4 var(--f-cjk); color:var(--sub); }
.b-c3 .proj-m { display:flex; gap:14px; }
.b-c3 .proj-m > span { font:700 27px/1 var(--f-mono); color:var(--acc); background:var(--acc-s); border-radius:999px; padding:12px 24px; }
.b-c3 .fresh { font:700 27px/1 var(--f-mono); background:var(--acc-s); color:var(--sub); border-radius:999px; padding:12px 24px; transition:background .4s ease, color .4s ease; }
.b-c3 .tags3 { margin-top:56px; display:flex; justify-content:center; gap:18px; }
.b-c3 .tg3 { font:800 36px/1 var(--f-cjk); background:var(--acc); color:#fff; border-radius:999px; padding:18px 36px; }
"""

# ---------------------------------------------------------------- c4 核心目标对比
_C4 = """
.b-c4 .sh { display:flex; align-items:flex-end; gap:22px; margin-bottom:44px; }
.b-c4 .sh-n { font:900 68px/.86 var(--f-num); color:var(--acc); letter-spacing:-.03em; }
.b-c4 .sh-t { font:800 44px/1.12 var(--f-cjk); color:var(--ink); letter-spacing:-.01em; padding-bottom:6px; }
.b-c4 .cmp3 { display:flex; align-items:center; gap:28px; }
.b-c4 .c3r { flex:1; padding:46px 52px; border-radius:28px; background:var(--card); border:2px solid var(--ln); transition:border-color .32s ease, background .32s ease, box-shadow .32s ease; }
.b-c4 .c3h { font:800 40px/1 var(--f-cjk); color:var(--sub); letter-spacing:.06em; margin-bottom:24px; }
.b-c4 .c3b { height:38px; border-radius:19px; background:#e4e8f1; overflow:hidden; }
.b-c4 .c3b > i { display:block; height:100%; width:0; border-radius:19px; background:linear-gradient(90deg,var(--warn),#ff8a5c); }
.b-c4 .c3r.bright > i { background:linear-gradient(90deg,var(--acc),#4b7bff); }
.b-c4 .c3l { margin-top:20px; font:900 96px/.9 var(--f-num); color:var(--ink); letter-spacing:-.03em; }
.b-c4 .c3r.bright .c3l { color:var(--acc); }
.b-c4 .arrow3 { font:900 72px/1 var(--f-num); color:var(--acc); letter-spacing:0; }
.b-c4 .bright { border-color:var(--acc); background:#f0f4ff; box-shadow:0 16px 40px rgba(0,47,167,.14); }
"""

# ---------------------------------------------------------------- p1 不是A是B
_P1 = """
.b-p1 .old { position:relative; padding:56px 60px; border-radius:28px; background:#eef1f7; border:2px dashed var(--ln2); }
.b-p1 .new { position:relative; padding:60px 60px 56px; border-radius:28px; background:var(--acc); color:#fff; margin-top:40px; box-shadow:0 22px 52px rgba(0,47,167,.26); }
.b-p1 .vtag { display:inline-block; font:800 27px/1 var(--f-cjk); letter-spacing:.16em; padding:10px 20px; border-radius:999px; }
.b-p1 .old .vtag { background:#dfe4ee; color:var(--sub); }
.b-p1 .new .vtag { background:rgba(255,255,255,.18); color:#fff; }
.b-p1 .vtx { margin-top:26px; font:900 68px/1.16 var(--f-cjk); letter-spacing:-.025em; }
.b-p1 .old .vtx { color:var(--muted); }
.b-p1 .strike { position:absolute; left:48px; right:48px; top:56%; height:8px; background:var(--warn); border-radius:4px; transform:scaleX(0); transform-origin:left center; }
.b-p1 .tags { margin-top:32px; display:flex; gap:14px; }
.b-p1 .tags > i { font:700 27px/1 var(--f-cjk); font-style:normal; background:rgba(255,255,255,.16); border-radius:999px; padding:13px 23px; }
.b-p1 .arrow { display:flex; align-items:center; justify-content:center; gap:16px; margin:28px 0 0; font:800 30px/1 var(--f-cjk); color:var(--acc); }
.b-p1 .cross { position:absolute; right:56px; top:52px; font:900 50px/1 var(--f-num); color:var(--warn); }
.b-p1 .tick { position:absolute; right:56px; top:56px; font:900 50px/1 var(--f-num); color:#8fe3bd; }
"""

# ---------------------------------------------------------------- p2 三角色
_P2 = """
.b-p2 .roles { display:flex; flex-direction:column; gap:18px; justify-content:center; }
.b-p2 .r3 { height:360px; padding:32px 40px; display:flex; align-items:center; gap:36px; transition:border-color .32s ease, background .32s ease, box-shadow .32s ease; }
.b-p2 .r3-n { width:68px; height:68px; flex:none; border-radius:50%; background:#e4e8f1; color:var(--faint); font:900 40px/.9 var(--f-num); text-align:center; transition:background .32s ease, color .32s ease; }
.b-p2 .r3-b { flex:1; min-width:0; display:flex; flex-direction:column; gap:12px; }
.b-p2 .r3-t { font:900 50px/1.16 var(--f-cjk); color:var(--sub); letter-spacing:-.015em; transition:color .32s ease; }
.b-p2 .r3-d { font:600 26px/1.45 var(--f-cjk); color:var(--muted); }
.b-p2 .mm { display:inline-flex; align-items:center; padding:8px 18px; border-radius:999px; background:var(--acc-s); color:var(--acc); font:700 22px/1 var(--f-cjk); letter-spacing:.06em; opacity:.3; transition:opacity .3s ease; }
.b-p2 .on .r3-n { background:var(--acc); color:#fff; }
.b-p2 .on .r3-t { color:var(--ink); }
.b-p2 .on { border-color:var(--acc); background:#f0f4ff; box-shadow:0 16px 40px rgba(0,47,167,.14); }
.b-p2 .bh { display:flex; align-items:flex-end; gap:22px; margin-bottom:28px; }
.b-p2 .bh-n { font:900 68px/.86 var(--f-num); color:var(--acc); letter-spacing:-.03em; }
.b-p2 .bh-t { font:800 40px/1.12 var(--f-cjk); color:var(--ink); letter-spacing:-.01em; padding-bottom:7px; }
.b-p2 .note2 { margin-top:24px; text-align:center; font:600 26px/1.45 var(--f-cjk); color:var(--muted); }
"""

# ---------------------------------------------------------------- p3 模板
_P3 = """
.b-p3 .tp { height:380px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:24px; border:2px solid var(--ln); transition:border-color .32s ease, background .32s ease; }
.b-p3 .tp-n { font:900 78px/.9 var(--f-cjk); color:var(--sub); letter-spacing:-.02em; transition:color .32s ease; }
.b-p3 .tp-d { font:600 30px/1.45 var(--f-cjk); color:var(--muted); text-align:center; transition:color .32s ease; }
.b-p3 .tp-k { font:800 42px/.9 var(--f-cjk); color:var(--faint); transition:color .3s ease; }
.b-p3 .on.tp { border-color:var(--acc); background:#f0f4ff; }
.b-p3 .on.tp .tp-n { color:var(--acc); }
.b-p3 .on.tp .tp-d { color:var(--ink); }
.b-p3 .on.tp .tp-k { color:var(--ok); }
.b-p3 .evs { display:flex; gap:26px; }
"""

# ---------------------------------------------------------------- p4 验收
_P4 = """
.b-p4 .chk { margin-top:28px; padding:44px 50px; display:flex; flex-direction:column; gap:22px; }
.b-p4 .ci { display:flex; align-items:flex-start; gap:22px; padding:24px 30px; border-radius:22px; background:var(--paper); }
.b-p4 .ci > b { font:800 38px/.9 var(--f-num); color:var(--ok); flex:none; opacity:.22; transition:opacity .3s ease; }
.b-p4 .ci-t { font:800 38px/1 var(--f-cjk); color:var(--ink); letter-spacing:-.01em; }
.b-p4 .ci-d { font:600 28px/1.45 var(--f-cjk); color:var(--sub); margin-top:8px; }
.b-p4 .quote { margin-top:36px; padding:34px 44px; border-radius:22px; background:var(--acc-s); font:600 34px/1.55 var(--f-cjk); color:var(--acc); line-height:1.6; }
.b-p4 .quote small { display:block; margin-top:14px; font:700 28px/1 var(--f-cjk); color:var(--muted); letter-spacing:.08em; }
"""

# ---------------------------------------------------------------- s1 命令
_S1 = """
.b-s1 .sh { display:flex; align-items:flex-end; gap:22px; margin-bottom:44px; }
.b-s1 .sh-n { font:900 84px/.86 var(--f-num); color:var(--acc); letter-spacing:-.03em; }
.b-s1 .sh-t { font:800 48px/1.12 var(--f-cjk); color:var(--ink); letter-spacing:-.01em; padding-bottom:6px; }
.b-s1 .term { align-self:stretch; border-radius:28px; overflow:hidden; background:var(--cmd-bg); box-shadow:0 24px 60px rgba(13,16,23,.30); }
.b-s1 .tbar { height:84px; display:flex; align-items:center; gap:12px; padding:0 34px; background:#191d26; }
.b-s1 .tbar > i { width:16px; height:16px; border-radius:50%; background:#3a4150; }
.b-s1 .tbar > i:nth-child(1){background:#ff5f57;}
.b-s1 .tbar > i:nth-child(2){background:#febc2e;}
.b-s1 .tbar > i:nth-child(3){background:#28c840;}
.b-s1 .tbar > span { margin-left:14px; font:600 27px/1 var(--f-mono); color:#5d6675; }
.b-s1 .tbody { padding:72px 60px 76px; }
.b-s1 .cline { display:flex; gap:22px; align-items:flex-start; }
.b-s1 .ps { font:800 38px/1.62 var(--f-mono); color:#7ad0ff; flex:none; }
.b-s1 .cmd { font:700 36px/1.62 var(--f-mono); color:#d6e2f0; word-break:break-all; letter-spacing:-.01em; }
.b-s1 .tout { margin-top:52px; display:flex; align-items:center; gap:18px; font:700 38px/1 var(--f-mono); color:#4ee08a; }
.b-s1 .note { margin-top:70px; text-align:center; font:700 34px/1 var(--f-cjk); color:var(--muted); letter-spacing:.16em; }
"""

# ---------------------------------------------------------------- s2 金句
_S2 = """
.b-s2 .veil { position:absolute; inset:-20px; border-radius:40px; background:linear-gradient(150deg,#002fa7 0%,#001a63 100%); box-shadow:0 30px 80px rgba(0,26,99,.34); z-index:-1; }
.b-s2 { align-items:center; text-align:center; padding:0 80px; }
.b-s2 .pill { display:inline-block; background:rgba(255,255,255,.16); color:#fff; border-radius:999px; padding:13px 26px; font:700 27px/1 var(--f-cjk); letter-spacing:.2em; }
.b-s2 .q1 { margin-top:62px; font:900 90px/1.2 var(--f-cjk); color:#fff; letter-spacing:-.025em; }
.b-s2 .q2 { margin-top:18px; font:900 90px/1.2 var(--f-cjk); color:#8fe3bd; letter-spacing:-.025em; }
.b-s2 .q3 { margin-top:18px; font:900 90px/1.2 var(--f-cjk); color:#8fe3bd; letter-spacing:-.025em; }
"""

# ---------------------------------------------------------------- s3 CTA
_S3 = """
.b-s3 { align-items:center; text-align:center; padding:0 80px; justify-content:center; }
.b-s3 .cta { display:flex; flex-direction:column; gap:28px; align-items:center; }
.b-s3 .ca1, .b-s3 .ca2, .b-s3 .ca3, .b-s3 .ca4 { font:900 72px/1.2 var(--f-cjk); color:var(--ink); letter-spacing:-.02em; }
.b-s3 .ca3 { font:800 68px/1.2 var(--f-cjk); color:var(--sub); }
.b-s3 .ca4 { font:700 56px/1.2 var(--f-cjk); color:var(--muted); letter-spacing:.04em; }
.b-s3 .cloop { font-size:1.2em; margin-right:12px; }
"""

# ---------------------------------------------------------------- s4 挑边
_S4 = """
.b-s4 .prow { height:960px; margin:auto 0; display:flex; align-items:stretch; gap:28px; min-height:0; }
.b-s4 .po { flex:1; min-height:0; padding:44px 42px; border-radius:28px; display:flex; flex-direction:column; gap:22px; transition:background .34s ease, border-color .34s ease, box-shadow .34s ease; }
.b-s4 .po-a { background:var(--card); border:2px dashed var(--ln2); }
.b-s4 .po-b { background:var(--card); border:2px dashed var(--ln2); }
.b-s4 .po.on { border-style:solid; }
.b-s4 .po-b.on { background:var(--acc); border-color:var(--acc); box-shadow:0 22px 52px rgba(0,47,167,.26); }
.b-s4 .po.on .po-k { background:var(--acc); color:#fff; }
.b-s4 .po-b.on .po-k { background:rgba(255,255,255,.18); }
.b-s4 .po-b.on .po-t { color:#fff; }
.b-s4 .po-k { width:72px; height:72px; border-radius:22px; font:900 40px/72px var(--f-num); text-align:center; background:#eef1f7; color:var(--sub); transition:background .34s ease, color .34s ease; }
.b-s4 .po-t { font:900 54px/1.18 var(--f-cjk); letter-spacing:-.02em; color:var(--muted); transition:color .34s ease; }
.b-s4 .po-d { margin-top:auto; font:600 30px/1.45 var(--f-cjk); color:var(--faint); transition:color .34s ease; }
.b-s4 .po-a.on .po-d { color:var(--sub); }
.b-s4 .po-b.on .po-d { color:rgba(255,255,255,.82); }
.b-s4 .vs { align-self:center; font:900 44px/1 var(--f-num); color:var(--faint); letter-spacing:.04em; flex:none; }
.b-s4 .pft { margin-top:26px; display:flex; align-items:center; justify-content:center; gap:18px; font:800 42px/1 var(--f-cjk); color:var(--acc); }
.b-s4 .bb { width:62px; height:62px; border-radius:18px; background:var(--acc); color:#fff; font:800 32px/62px var(--f-num); text-align:center; letter-spacing:1px; }
"""

BOARD_CSS = {
    "c1": _C1, "c2": _C2, "c3": _C3, "c4": _C4,
    "p1": _P1, "p2": _P2, "p3": _P3, "p4": _P4,
    "s1": _S1, "s2": _S2, "s3": _S3, "s4": _S4,
}
