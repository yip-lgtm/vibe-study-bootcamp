"""
Agent Node: Diagram (LLM-based Mermaid generator)

Reads: state.body
Writes: state.diagrams (list of Mermaid blocks)

Strategy: Use LLM to suggest 5 distinct Mermaid diagrams based on body content.
Falls back to regex-based detection.
"""
from __future__ import annotations
from typing import Any, Dict, List
import re
import os

from ..state import PipelineState
from ..llm_client import complete, detect_provider


DIAGRAM_TYPES = [
    "flowchart", "sequenceDiagram", "stateDiagram",
    "classDiagram", "erDiagram", "graph", "pie", "gantt",
]


SYSTEM_PROMPT_DIAGRAM = """You are the **Diagram** agent in a multi-agent course-generation pipeline.

Your job: read a course body and suggest 5 **distinct Mermaid diagram types** that best illustrate the course concepts.

Required: 5 distinct types from:
  - flowchart (TD/LR)
  - sequenceDiagram
  - stateDiagram-v2
  - classDiagram
  - erDiagram
  - pie
  - gantt

For each diagram, output:
- The diagram type
- A 1-line description of what it shows
- The actual Mermaid code block (must be valid syntax, GitHub-renderable)

Output format (return ONLY this JSON):
```json
{
  "diagrams": [
    {
      "type": "flowchart",
      "description": "Process flow of X",
      "code": "flowchart TD\\n  A[Start] --> B[Step 1]\\n  B --> C[End]"
    },
    ...
  ]
}
```

Each code block must be SYNTACTICALLY VALID and renderable in GitHub markdown."""


def _llm_diagram(state: PipelineState, body: str, config: Dict[str, Any]) -> List[Dict[str, str]]:
    """LLM-based diagram generation."""
    writer = config.get("writer")
    if writer:
        writer({"type": "llm_call", "agent": "diagram", "phase": "start"})

    body_for_llm = body[:25000] if len(body) > 25000 else body

    user_msg = (
        f"Course: {state.course_code}\n\n"
        f"--- Course body ({len(body):,} chars) ---\n\n"
        f"{body_for_llm}\n\n"
        f"--- End ---\n\n"
        f"Generate 5 distinct Mermaid diagrams for this course."
    )

    resp = complete(
        messages=[{"role": "user", "content": user_msg}],
        system=SYSTEM_PROMPT_DIAGRAM,
        max_tokens=4000,
        temperature=0.3,
    )

    if writer:
        writer({
            "type": "llm_call", "agent": "diagram", "phase": "end",
            "tokens": resp.input_tokens + resp.output_tokens,
            "latency_ms": resp.latency_ms,
        })

    import json
    text = resp.text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    try:
        data = json.loads(text)
        diagrams = data.get("diagrams", [])
        return diagrams
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                return data.get("diagrams", [])
            except json.JSONDecodeError:
                return []
        return []


def _deterministic_diagram(body: str) -> List[str]:
    """Detect Mermaid blocks deterministically."""
    mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", body, re.DOTALL)
    detected: List[str] = []
    for block in mermaid_blocks:
        for t in DIAGRAM_TYPES:
            if t in block:
                detected.append(t)
                break
    return detected


def diagram_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """Diagram: 5 distinct Mermaid diagrams via LLM or regex detection."""
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "diagram", "course": state.course_code})

    body = state.body
    if not body:
        return {"errors": ["[diagram] No body content from engineer"]}

    cfg = detect_provider()
    use_llm = bool(cfg.api_key) and not config.get("force_deterministic", False)

    if use_llm:
        try:
            diagrams = _llm_diagram(state, body, config)
            method = "llm"
        except Exception as e:
            if writer:
                writer({"type": "llm_error", "agent": "diagram", "error": str(e)[:200]})
            diagrams = [{"type": t} for t in _deterministic_diagram(body)]
            method = "deterministic_fallback"
    else:
        diagrams = [{"type": t} for t in _deterministic_diagram(body)]
        method = "deterministic"

    if writer:
        writer({
            "type": "agent_end", "agent": "diagram",
            "method": method,
            "result": f"{len(diagrams)} diagrams: {[d.get('type', '?') for d in diagrams]}",
        })

    return {
        "diagrams": diagrams,
        "events": [{
            "type": "diagram_method",
            "data": {"method": method, "count": len(diagrams)},
        }],
    }
