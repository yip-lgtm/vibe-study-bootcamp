"""
Agent Node: Diagram (LangGraph-style)

Reads: state.body (engineer output)
Writes: state.diagrams (list of Mermaid block identifiers, ensures 5 distinct diagrams)
"""
from __future__ import annotations
from typing import Any, Dict, List
import re

from ..state import PipelineState


# Mermaid diagram types we want to see
DIAGRAM_TYPES = [
    "flowchart",
    "sequenceDiagram",
    "stateDiagram",
    "classDiagram",
    "erDiagram",
    "graph",
    "pie",
    "gantt",
]


def diagram_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diagram node: ensures the body has 5 distinct Mermaid diagrams.
    Returns a list of detected diagram types.
    """
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "diagram", "course": state.course_code})

    body = state.body
    if not body:
        return {"errors": ["[diagram] No body content from engineer"]}

    # Detect mermaid blocks
    mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", body, re.DOTALL)
    detected_types: List[str] = []
    for block in mermaid_blocks:
        for t in DIAGRAM_TYPES:
            if t in block:
                detected_types.append(t)
                break

    if writer:
        writer({
            "type": "agent_end", "agent": "diagram",
            "result": f"{len(mermaid_blocks)} mermaid blocks, "
                       f"{len(set(detected_types))} distinct types: {set(detected_types)}",
        })

    return {"diagrams": detected_types}
