# Multi-Agent Pipeline Guide

> Detailed guide to using the 5-agent pipeline for content generation

## 5 Agents Overview

| Agent | 職責 | 品質門檻 |
|---|---|---|
| 1. Researcher | Primary source verification | Real URLs, scholars, dates |
| 2. Data Extractor | Extract course metadata | Verifiable, no speculation |
| 3. Engineer | Content producer (5MM/3DG/10Q) | Specific, not generic |
| 4. Diagram | 5 Mermaid diagrams per course | Distinct types, renderable |
| 5. Professor Supervisor | Quality gate | APPROVED/REVISE/REJECT |

## Quick Start

```bash
# Single course
python3 _agents/professor_supervisor/review.py --course <path>

# All courses
python3 _agents/professor_supervisor/review.py --all

# JSON output
python3 _agents/professor_supervisor/review.py --all --json
```

## Quality Gate Reference (10 gates, 100 points)

```
G1_length       (0-10): File ≥ 300 lines
G2_format       (0-15): Has 5MM/3DG/10Q/5DD/10SL sections
G3_citations    (0-15): ≥ 3 real scholars with years
G4_specificity  (0-15): ≥ 3 LaTeX equations
G5_bilingual    (0-10): ≥ 100 Chinese characters
G6_no_placeholder (0-10): No [TBD], 待補充, Lorem
G7_mermaid      (0-10): ≥ 5 Mermaid diagrams
G8_solutions    (0-10): ≥ 10 numbered solutions
G9_deep_dives   (0-5):  ≥ 5 explicit Deep Dive sections
G10_no_template (0-5):  No T0/T1/T2 template garbage
```

## Decision

| Score | Decision | Action |
|---|---|---|
| ≥ 85 | ✅ APPROVED | Push |
| 70-84 | ⚠️ REVISE | Fix weak gates |
| < 70 | ❌ REJECT | Quarantine |

## Common Issues & Fixes

### G3_citations < 12
**Fix:** Add `Newton 1687, Maxwell 1865, Einstein 1905, Bohr 1913, Schrödinger 1926`

### G4_specificity < 8
**Fix:** Wrap equations in `$$...$$`: `$$F = ma \quad (\text{Newton 1687})$$`

### G7_mermaid < 10
**Fix:** Add 5 distinct types: stateDiagram-v2, flowchart, sequenceDiagram, classDiagram, erDiagram

### G5_bilingual < 7
**Fix:** Add 中英對照 paragraphs in every section

### G6_no_placeholder < 10
**Fix:** Replace `[TBD]`, `待補充`, `Lorem ipsum` with real content

## Adding a New Bootcamp

```bash
mkdir -p my-bootcamp/courses/
cp -r _agents/ my-bootcamp/
cp -r _pipeline/ my-bootcamp/
# Add courses using 5MM/3DG/10Q format
cd my-bootcamp/
python3 _agents/professor_supervisor/review.py --all
```

---

*Last Updated: 2026-08*
