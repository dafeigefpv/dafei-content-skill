# 音色选择与「AI 味」调优

edge-tts 是**免费朗读接口**，只有 6 个普通话音色，且不开放风格参数 ——
这是「AI 味」的结构性来源。按投入从小到大有三条路。

---

## 一、三条路径对比

| 路径 | 成本 | 改动量 | 效果上限 | 前置条件 |
|---|---|---|---|---|
| A. edge-tts 换音色 + 调参 + 改稿 | 0 | 改 `storyboard.json` | 有限（消除播报腔 ~50%） | 无 |
| **B. Azure 官方 Speech + DragonHD Flash** | **≈¥0.05/条** | **只换 TTS 调用层** | **高（接近真人）** | Azure 国际版订阅 |
| C. 本地开源克隆（IndexTTS2 等） | 电费 / 租卡 | 重建整条 TTS 链 | 最高（可克隆本人音色） | **NVIDIA 显卡 6–8GB** |

---

## 二、路径 A：edge-tts 免费音色（实测可用清单）

`edge-tts list_voices()` 返回 322 个音色，**中文仅 14 个**，其中大陆普通话 **6 个**：

| 音色 | 性别 | 官方定位 | 自然度体感 |
|---|---|---|---|
| `zh-CN-YunjianNeural` | 男 | Sports / Passion | ✅ 起伏最大，最不像播报 |
| `zh-CN-XiaoxiaoNeural` | 女 | News, Novel / Warm | ✅ 温暖，亲和 |
| `zh-CN-XiaoyiNeural` | 女 | Cartoon, Novel / Lively | ○ 活泼，略尖 |
| `zh-CN-YunxiaNeural` | 男 | Cartoon / Cute | ○ 偏童声 |
| `zh-CN-YunxiNeural` | 男 | Novel / Lively, Sunshine | △ 小说朗读底色，播报腔重 |
| `zh-CN-YunyangNeural` | 男 | News / Professional | ❌ 标准新闻腔，最「AI」 |

方言 / 港台另有 `zh-CN-liaoning-XiaobeiNeural`（东北）、`zh-CN-shaanxi-XiaoniNeural`（陕西）、
`zh-HK-*`（3）、`zh-TW-*`（3）。

**本项目定版（2026-09-17 试听后拍板）**：`zh-CN-YunjianNeural` + `rate:"+8%"`。
原为 `YunxiNeural +18%`，用户反馈「AI 味太重」；11 款试听后选定云健 +8%。
改动代价：总时长变慢约 10%，需重估时长。

⚠️ **官方列表外的音色一律不可用**。实测探测 9 个 Azure 专属音色
（`zh-CN-XiaoshuangNeural`、`zh-CN-XiaoxiaoMultilingualNeural`、
`zh-CN-YunxiaoMultilingualNeural`、`zh-CN-XiaochenMultilingualNeural`、
`zh-CN-YunyiMultilingualNeural`、`zh-CN-XiaobeiMultilingualNeural`、
`zh-CN-XiaoxiaoDialectsNeural`、`zh-CN-XiaozhenNeural` 及方言变体）
**全部返回 `NoAudioReceived`**，无一旁路可用。

### ⚠️ 判读 `NoAudioReceived` 的干扰项

它有两种含义，**日志里无法区分**：

1. 该音色不被免费端点支持 —— 稳定复现，重试无效；
2. **频率限制** —— 错开即恢复。

实测**连续快速探测时 `zh-CN-YunxiNeural` 自身也会 `NoAudioReceived`**（限流，非不支持）。
判断某音色是否真的不可用时，**必须错开重试一次再下结论**。

### 参数杠杆

语速是第二大因素。`rate:"+18%"` 实测 5.23 字/s，明显偏快，机械感随之上升；
降到 `+8%`（4.79 字/s）或 `+0%`（4.43 字/s）会松弛不少。
`pitch:-3~-5Hz` 可略微降低「播音」的紧绷感。

### 文本杠杆（免费且幅度最大）

见 `copywriting.md` 第六节的书面稿 ↔ 口语稿对照表。
**改稿的口语化收益往往大于换音色。**

---

## 三、路径 B：Azure DragonHD Flash（推荐升级）

同样这批音色在**微软官方 Speech 服务**里有 2025–2026 年的新一代 HD 模型
（`DragonHDFlashLatestNeural`），并且**开放风格参数** `mstts:express-as` ——
这正是免费朗读接口拿不到的东西：

| 音色（SSML 写法 `名字:模型`） | 可用风格 |
|---|---|
| `zh-CN-Yunxi:DragonHDFlashLatestNeural` | angry, **chat**, cheerful, complaining, depressed, fearful, news, sad, shy, strict, voice-assistant |
| `zh-CN-Xiaoxiao:DragonHDFlashLatestNeural` | angry, **chat**, cheerful, customer-service, excited, fearful, sad, voice-assistant |
| `zh-CN-Xiaoxiao2:DragonHDFlashLatestNeural` | affectionate, cheerful, curious, **empathetic**, **encouraging**, **story**, **poetry-reading**, whispering…（20 种） |
| `zh-CN-Xiaoshuang:DragonHDFlashLatestNeural` | **仅 chat**（专为对话场景设计） |
| `zh-CN-Xiaoyou:DragonHDFlashLatestNeural` | **chat**, story, cute, poetry-reading, sad |
| `zh-CN-Yunhan:DragonHDFlashLatestNeural` | empathetic, **encouraging**, whispering, tired, curious… |

**要点**：

- **`style="chat"` 就是「去播报腔」的开关** —— HD 模型会先理解文本再预测说话模式，
  不是逐字拼接韵律。
- **字级时间戳照常可用**：HD voices 支持 word boundary events，返回 `Text` +
  `AudioOffset`，`voice_synth.py` 的块边界定位逻辑**无需改动**，仅替换合成调用。
- **成本可忽略**：Neural HD 自 2026-03 起 $22 / 100 万字符。单条视频约 320 字
  → **≈$0.007（不到 5 分钱）**。
- 区域：East US / West Europe / Southeast Asia / West US 2 / Canada Central /
  France Central / Sweden Central 等；需 **Azure 国际版**订阅（世纪互联版音色不同）。
- 接入方式：替换 `synth_scene()` 为 Azure Speech SDK
  （`speechsynthesis` + `SSML` + `word_boundary` 事件），其余流水线不动。

---

## 四、路径 C：本地开源克隆（本机不可行）

中文自然度第一梯队是 **IndexTTS2**（B 站开源，1.5B，中文 CER 1.03%、SIM 76.5%，
音色-情感解耦、字级时长可控），其次是 **CosyVoice2**（阿里，情感控制好）。
但**全部要求 NVIDIA 显卡 6–8GB 显存**。

⚠️ **本机无独显**（Intel 集显 + Honor 虚拟显示器，Intel Core 5 220H / 16 核 / 31.7G），
CPU 推理 1.5B 模型慢到不可用。要用这条路得租云 GPU（如 AutoDL 4090，约 ¥2/小时）。
`GPT-SoVITS` 虽名气大，但零样本基本不可用、必须训练音色，不适合本场景。

---

## 五、试听台（skill 自带）

换音色时用，别凭感觉选：

```bash
PY=<venv python>
"$PY" scripts/voice/lab.py probe      # 探测哪些音色名可用（含 Azure 专属，预期全 FAIL）
"$PY" scripts/voice/lab.py render     # 同句台词 × 11 个音色/参数组合
"$PY" scripts/voice/stitch.py         # 拼成带语音报幕的合集便于试听
"$PY" scripts/voice/text_lab.py       # 书面稿 vs 口语稿对照（音色固定）
```

产物落在 `<project>/audio/lab/` 与 `audio/textlab/`。
`lab.py render` 会把「音色 + 语速 + pitch」的组合固定成可复现的标签（`B1-yunjian-8` 这类），
选定后在 `storyboard.json` 里写回对应的 `voice` / `rate`。
