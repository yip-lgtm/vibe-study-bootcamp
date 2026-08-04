# AGENT 5: Professor Supervisor (Quality Gate)

## 職責
審稿每一個 course file。Decision:
- ✅ **APPROVED** — push
- ⚠️ **REVISE** — fix
- ❌ **REJECT** — quarantine

**不通過不推送** — strict enforcement.

## 10 Quality Gates (100 points)

| Gate | Check | 拒絕 if |
|---|---|---|
| G1 Length | ≥ 300 lines | < 300 |
| G2 Format | 5MM/3DG/10Q/5DD/10SL/5MR | Missing |
| G3 Citations | Real scholars + year | < 3 |
| G4 Specificity | Numbers + equations | < 3 eq |
| G5 Bilingual | 中英對照 | EN-only |
| G6 No Placeholder | No `[TBD]`, `待補充`, `Lorem` | Any |
| G7 Mermaid | 5 diagrams | < 5 |
| G8 Solutions | 10 detailed | < 10 |
| G9 Deep Dives | 5 specific | Generic |
| G10 No Template | No T0/T1/T2 | `T0 — Core` style |

## Decision

| Score | Decision |
|---|---|
| ≥ 85 | ✅ APPROVED |
| 70-84 | ⚠️ REVISE |
| < 70 | ❌ REJECT |

## Usage

```bash
python3 _agents/professor_supervisor/review.py --course <path>
python3 _agents/professor_supervisor/review.py --all --json
```

## Status: ✅ Operational (100% APPROVED enforced)
