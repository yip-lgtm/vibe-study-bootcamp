# 🌐 vibe-study-bootcamp

> **Open-source Vibe Coding × Self-Study Hub**
> Multi-Agent pipeline for generating research-based bilingual (中英對照) course content

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Multi-Agent](https://img.shields.io/badge/Pipeline-Multi--Agent-orange)](./_agents/)
[![100% APPROVED](https://img.shields.io/badge/Quality-100%25_APPROVED-brightgreen)](./_pipeline/)
[![HK](https://img.shields.io/badge/Built_in-Hong_Kong-red)](./proposal/)

---

## 🎯 Mission

我哋相信 **vibe coding + self-study + multi-agent AI = 21 世紀最有效嘅自學方法**。

呢個 project 係一個**完全 open-source** 嘅 framework，幫助任何人：

1. 📚 **系統性自學** — 由中學到大學到博士嘅 path
2. 🤖 **用 AI multi-agent** 自動生成高質量 research-based 課程
3. 🌍 **Bilingual (中英對照)** 內容 — 香港/國際雙語用戶友善
4. ✅ **嚴格品質控制** — 不通過不推送
5. 💯 **完全免費** — MIT License，公眾自學

---

## 🗂️ Repo 結構

```
vibe-study-bootcamp/
├── proposal/                  # Open-source 提案 (charter, roadmap)
├── docs/                      # Documentation
├── _agents/                   # Multi-Agent Pipeline (5 agents)
│   ├── researcher/            # Primary source verification
│   ├── data_extractor/        # Course metadata extraction
│   ├── engineer/              # Content producer
│   ├── diagram/               # 5 Mermaid diagrams per course
│   └── professor_supervisor/  # Quality gate reviewer
├── _pipeline/                 # Pipeline orchestrator
├── app/                       # AllBootcamp PWA (showcase app)
├── workflow/                  # Vibe coding workflow guides
└── LICENSE                    # MIT
```

---

## 🌟 Showcase — AllBootcamp App

**495+ courses** from 6 bootcamps, all 100% APPROVED:

| Bootcamp | Courses | Status |
|---|---|---|
| `civil-bootcamp` (MIT CEE) | 85 | ✅ 100% |
| `PhysicsSelfStudy` (HKUST) | 18 | ✅ 100% |
| `HKU-Harvard-History-Self-Study` | 155 | ✅ 100% |
| `psych-self-study-hku` | 131 | ✅ 100% |
| `mech-Eng-Bootcamp` (CUHK MAE) | 100 | ✅ 100% |
| `HKU-BME-Bootcamp-OpenClaw` | 6 | ✅ 100% |
| **Total** | **495+** | **✅ 100%** |

**App:** [`app/`](./app/) — Mobile-first PWA in dark mode with HK forum design

---

## 🤖 Multi-Agent Pipeline (5 Agents)

```
1. Researcher    →  查 primary sources
2. Data Extractor →  提取 objectives / themes
3. Engineer       →  5MM/3DG/10Q/5DD/10SL/5MR 內容
4. Diagram        →  5 Mermaid 圖
5. Professor Supervisor →  10 quality gates (APPROVED/REVISE/REJECT)
```

**不通過不推送** strictly enforced.

---

## 📊 Quality Gates (10 gates, 100 points)

| Gate | Check | Min |
|---|---|---|
| G1 Length | 內容行數 | ≥ 300 |
| G2 Format | 5MM/3DG/10Q 結構 | All present |
| G3 Citations | 真實學者 + 年份 | ≥ 3 |
| G4 Specificity | 方程式 + 數字 | ≥ 3 eq |
| G5 Bilingual | 中英對照 | ≥ 100 字 |
| G6 No Placeholder | 無 `[TBD]` / `Lorem` | 0 |
| G7 Mermaid | 圖表 | ≥ 5 |
| G8 Solutions | 詳解 | ≥ 10 |
| G9 Deep Dives | 深度 dive | ≥ 5 |
| G10 No Template | 無 T0/T1/T2 | 0 |

**Decision:** APPROVED ≥85 / REVISE 70-84 / REJECT <70

---

## 🚀 快速開始

```bash
# 1. 跑 AllBootcamp App
cd app/
npm install
npm run dev

# 2. 驗證 Pipeline
python3 _agents/professor_supervisor/review.py --all

# 3. 加入新 bootcamp
mkdir -p your-bootcamp/courses/
cp -r _agents/ your-bootcamp/
cp -r _pipeline/ your-bootcamp/
cd your-bootcamp/
python3 _agents/professor_supervisor/review.py --all
```

---

## 📜 Open Source 提案

- [CHARTER.md](./proposal/CHARTER.md) — Project charter
- [ROADMAP.md](./proposal/ROADMAP.md) — 2026-2027 roadmap
- [CONTRIBUTING.md](./proposal/CONTRIBUTING.md) — 點樣 contribute
- [LICENSE](./LICENSE) — MIT License

---

## 📬 Contact

- **Author:** Saba (葉) Yip
- **Email:** yipsaba@polyu-msc.ai
- **GitHub:** [@yip-lgtm](https://github.com/yip-lgtm)

---

🇭🇰 Built in Hong Kong · 🌍 For the world · 💯 100% Open Source
