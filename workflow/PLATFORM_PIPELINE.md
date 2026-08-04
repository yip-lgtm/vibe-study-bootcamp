# Platform Multi-Agent Pipeline

> Full-stack software engineering agents for building & iterating the AllBootcamp platform itself

## 哲學

Content 用 5-agent pipeline。  
**Platform 本身** 用另外一套 multi-agent + 自動迭代：

```
Supervisor → Engineer → Tester → Supervisor (loop)
```

目標：快速、有質量、可自動迭代改進 UI / feature / bug。

---

## 3 Core Agents

| Agent | 角色 | 主要輸出 |
|-------|------|----------|
| **Full Stack Engineer** | 實作 | code changes, PR-ready diff, commit message |
| **Testing Analyst** | 品質 & 測試 | test cases, bug list, regression check, coverage notes |
| **Supervisor** | 決策 & 迭代控制 | APPROVED / REVISE / REJECT + 具體 feedback |

---

## Auto-Iteration Loop

```
1. Supervisor 收到 Task / Bug / Feature
2. Supervisor 產生「工作單」(Work Order)
3. Engineer 根據 Work Order 寫 code
4. Tester 跑分析 + 寫 test / 找問題
5. Supervisor 審核：
   - APPROVED  → 結束，可以 commit / deploy
   - REVISE    → 把 feedback 交返 Engineer，繼續下一輪
   - REJECT    → 停止，記錄原因
6. 最多跑 MaxIterations 次（預設 3）
```

**不通過不合併** — 同 content pipeline 一樣嚴格。

---

## Work Order 格式（Supervisor 產出）

```markdown
## Work Order
- ID: WO-YYYYMMDD-XXX
- Priority: P0 / P1 / P2
- Type: feature | bug | refactor | ui | performance
- Goal: 一句話目標
- Acceptance Criteria:
  - [ ] ...
  - [ ] ...
- Constraints:
  - 保持 dark mode + mobile-first
  - 唔好破壞現有 follow/saved localStorage
  - 必須通過現有 Tailwind theme
- Context: (相關檔案 / 目前問題描述)
```

---

## 檔案位置

```
_agents/platform/
├── engineer/
│   └── SYSTEM.md
├── tester/
│   └── SYSTEM.md
├── supervisor/
│   └── SYSTEM.md
└── README.md

workflow/
├── PLATFORM_PIPELINE.md   ← 你而家睇緊呢份
└── AUTO_ITERATE.md
```

---

## 使用方式（Vibe Coding 風格）

### 手動單輪
1. 開 Supervisor agent，丟問題 / feature 描述
2. 拿 Work Order → 開 Engineer
3. Engineer 產出 code → 開 Tester
4. Tester 報告 → 返 Supervisor 決定

### 自動迭代（推薦）
用 `workflow/AUTO_ITERATE.md` 嘅 prompt template，一次過餵俾一個強大 model（Claude / Grok / GPT），佢會自己扮演三個角色循環。

---

## Quality Gates for Platform Code

| Gate | 檢查 |
|------|------|
| G1 | TypeScript 無 error |
| G2 | 唔破壞現有 dark / mobile layout |
| G3 | 有對應 test 或至少 manual test steps |
| G4 | 無 console.error / 明顯 runtime crash |
| G5 | 符合現有 Tailwind theme（pill-bg, text-faint 等） |
| G6 | Commit message 清晰 |

**Decision:** APPROVED ≥ 5 gates pass / REVISE / REJECT

---

*Built for 修學旅行 platform · 2026-08*
