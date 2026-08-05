# Director Pattern (LangGraph-style Multi-Agent Pipeline)

> Inspired by [THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC)'s
> `lib/orchestration/director-graph.ts` — a LangGraph StateGraph that
> uses a director node to decide which agent runs next.

## Why Director Pattern?

The original Multi-Agent Pipeline was a **linear chain**:
```
researcher → data_extractor → engineer → diagram → professor_supervisor
```

This is simple but inflexible. The Director Pattern makes the pipeline
**stateful and adaptive**:

```
START → director ──(engineer)──→ engineer ──→ researcher
                    ─(professor)──→ professor_supervisor ──→ director
                    ─(END)──→ END
```

The director decides which agent to run next based on the **current
state** (not just position in the chain). This enables:

1. **Revision cycles**: REVISE → cycle back to engineer
2. **Early termination**: APPROVED → END (skip remaining agents)
3. **Error handling**: REJECT → END (don't waste cycles)
4. **Future flexibility**: insert new agents without rewriting flow

## Architecture

### StateGraph topology (mirrors OpenMAIC)

```
                ┌──────────────┐
                │   director   │  <-- Routes to next agent based on state
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ↓              ↓              ↓
    engineer      professor_      END
        │         supervisor
        │              │
        ↓              │
   researcher         │
        │              │
        ↓              │
   data_extractor     │
        │              │
        ↓              │
    diagram            │
        │              │
        └──────┬───────┘
               ↓
            director  (cycle)
```

### State Schema (mirrors LangGraph `Annotation.Root`)

`PipelineState` in `_pipeline/state.py` defines:
- **Input fields**: `course_path`, `course_code`, `course_title`
- **Agent outputs**: `brief`, `data`, `body`, `diagrams`, `review`
- **Control flow**: `current_agent`, `iteration`, `decision`, `weak_gates`
- **Stream events**: `events` (for SSE-like output)
- **Output**: `final_score`, `output_files`

Each field has a **reducer** that defines how updates are merged:
- `append_reducer` — accumulate list
- `dict_update_reducer` — merge dicts
- `replace_reducer` — overwrite

### Director Node (the key innovation)

`director_node` in `_pipeline/agents/director.py` is **pure logic** —
no LLM call. It inspects state and routes:

| State Condition | Director Routes To |
|---|---|
| `body` is empty | `engineer` |
| `review` is empty | `professor_supervisor` |
| `decision == "REVISE"` and `iteration < max_iterations` | `engineer` (cycle) |
| `decision == "APPROVED"` or `REJECT` or max iterations | `END` |

In OpenMAIC, the director is an **LLM call** that decides which agent
should speak in a real-time multi-agent conversation. Our adaptation
uses **deterministic rules** because our pipeline is more structured
(content generation, not conversation).

## Usage

```bash
# Run on a single course (with streaming output)
python3 _pipeline/director_pipeline.py --course <path> --stream

# Run on a single course (quiet, with max-iterations)
python3 _pipeline/director_pipeline.py --course <path> --max-iterations 3

# Run on all courses in current repo
python3 _pipeline/director_pipeline.py --all
```

Example output:
```
Pipeline (Director pattern): 3.091_Introduction_to_Chemistry.md
============================================================
  → director
  → engineer
  ✓ engineer: 436 lines, 6 scholars, 10 eq, 5 mm
  → researcher
  ✓ researcher: 1 sources, 13 scholar-years, 30 numbers
  → data_extractor
  ✓ data_extractor: 0 obj, 2 prereq, 10 themes
  → diagram
  ✓ diagram: 5 mermaid blocks, 5 distinct types
  → professor_supervisor
  → DECISION: APPROVED (score 102)
  → director

Final decision: APPROVED
Final score: 102
Iterations: 1
```

## Files

| File | Purpose |
|---|---|
| `_pipeline/state.py` | PipelineState dataclass + reducers (mirrors LangGraph `Annotation`) |
| `_pipeline/graph.py` | Minimal StateGraph runtime (addNode, addEdge, addConditionalEdges) |
| `_pipeline/agents/__init__.py` | Agent exports |
| `_pipeline/agents/researcher.py` | Agent 1: scan primary sources |
| `_pipeline/agents/data_extractor.py` | Agent 2: extract objectives/themes |
| `_pipeline/agents/engineer.py` | Agent 3: produce 5MM/3DG/10Q body |
| `_pipeline/agents/diagram.py` | Agent 4: ensure 5 Mermaid diagrams |
| `_pipeline/agents/professor_supervisor.py` | Agent 5: 10-gate quality review |
| `_pipeline/agents/director.py` | Director node + conditional edge |
| `_pipeline/director_pipeline.py` | Entry point: build graph + run |

## Comparison with OpenMAIC

| Aspect | OpenMAIC | Our Pipeline |
|---|---|---|
| **Director logic** | LLM-based (calls API) | Deterministic (no API) |
| **State** | LangGraph StateGraph | Custom Python dataclass + reducers |
| **Use case** | Real-time classroom discussion | Batch content generation |
| **Agents** | Dynamic (per-discussion) | Fixed 5 (researcher..supervisor) |
| **Revision** | None (each turn is independent) | Cyclic (REVISE → engineer) |
| **Streaming** | SSE via `config.writer()` | Custom writer callback |

The key abstraction we adopted: **StateGraph + reducers + director pattern**.
Even with our deterministic logic, the architecture supports
LLM-based directors in the future — just replace `director_node` body
with an LLM call.

## License

MIT — same as the project.
