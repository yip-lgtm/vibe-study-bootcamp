# End-to-End Pipeline Examples

## Real LLM Test Runs (2026-08-05)

These logs document end-to-end runs of the **LangGraph-style Director Pipeline**
against real LLM calls (MiniMax Token Plan, `sk-cp-` key, `api.minimax.io`).

### Run 1: `1.036_Structural_Mechanics_and_Design.md` (21KB)
- **Decision**: ✅ APPROVED
- **Score**: 86/100
- **Iterations**: 1
- **Total time**: 3:21

| Agent | Output |
|---|---|
| Engineer | 409 lines, 4 scholars, 5 equations, 5 mermaid |
| Researcher | 10 sources, 27 scholars, 22 numbers |
| Data Extractor | 10 obj, 6 prereq, 14 themes |
| Diagram | 5 distinct types: flowchart, sequence, state, class, gantt |

### Run 2: `1.050_Solid_Mechanics.md` (36KB)
- **Decision**: ✅ APPROVED
- **Score**: 99/100
- **Iterations**: 1
- **Total time**: 3:34

| Agent | Output |
|---|---|
| Engineer | 712 lines, 6 scholars, 5 equations, 10 mermaid |
| Researcher | 12 sources, 30 scholars, 29 numbers |
| Data Extractor | 9 obj, 5 prereq, 14 themes |
| Diagram | 5 distinct types: flowchart, sequence, state, class, er |

## Reproduce

```bash
export MINIMAX_API_KEY="sk-cp-..."
python3 _pipeline/director_pipeline.py \
    --course /path/to/course.md \
    --stream
```

## Notes

- Both runs are **real LLM calls** to `api.minimax.io/anthropic/v1/messages` with model `MiniMax-M3`
- Engineer agent takes ~60s (16K max_tokens output)
- Other agents take 4-30s
- Total pipeline: ~3-4 min for 20-40KB courses
- Auth-fail cache prevents wasted calls if key is invalid
- Deterministic fallback still works when no key

## Why This Works

The pipeline mirrors [THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC)'s
director pattern but uses **structured JSON output** for reliable routing and
**deterministic fallback** for offline operation. Each agent is independent and
idempotent — the StateGraph ensures correct sequencing via the director's
conditional edges.
