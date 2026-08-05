"""
Agent Node: Data Extractor (LangGraph-style)

Reads: state.brief (from researcher)
Writes: data = {objectives, prereq, key_themes, learning_outcomes, ...}
"""
from __future__ import annotations
from typing import Any, Dict
import re

from ..state import PipelineState


def data_extractor_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """Data Extractor: parses the source for objectives, prereq, themes, outcomes."""
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "data_extractor", "course": state.course_code})

    try:
        with open(state.course_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"errors": [f"[data_extractor] Cannot read {state.course_path}: {e}"]}

    # Extract objectives (lines starting with numbered list near "## 課程目標" or
    # "## Objectives" or containing "Apply", "Compute", "Derive", "Solve", "Design")
    objectives: list[str] = []
    for line in content.split("\n"):
        m = re.match(r"^\s*\d+\.\s+\*?\*?(.+?)\*?\*?$", line.strip())
        if m:
            text = m.group(1).strip()
            # Action-verb hints
            if any(v in text for v in ["Apply", "Compute", "Derive", "Solve",
                                          "Design", "Analyze", "Understand",
                                          "Identify", "Recognize", "Formulate",
                                          "Predict", "Explain", "Calculate"]):
                if len(text) > 10 and len(text) < 200:
                    objectives.append(text)

    # Prereq: search for "Prereq:", "Prerequisite:", "Pre:"
    prereq: list[str] = []
    for line in content.split("\n"):
        m = re.search(r"[Pp]rereq[uiaq]*:?\s*(.+)", line)
        if m:
            items = re.split(r"[,，；;]", m.group(1))
            for item in items:
                item = item.strip()
                if item and len(item) < 100:
                    prereq.append(item)

    # Key themes: H2/H3 sections, especially deep dives
    themes: list[str] = []
    for m in re.finditer(r"^##\s+(.+)$", content, re.MULTILINE):
        title = m.group(1).strip()
        if title and not title.startswith("問題") and len(title) < 80:
            themes.append(title)

    # Learning outcomes: search for "Learning Outcomes", "LO:", "Outcomes:"
    outcomes: list[str] = []
    in_lo = False
    for line in content.split("\n"):
        if re.search(r"[Ll]earning [Oo]utcomes?|LOs?:", line):
            in_lo = True
            continue
        if in_lo:
            if line.startswith("#") or line.strip() == "":
                if outcomes:
                    in_lo = False
                continue
            m = re.match(r"^\s*[\-\*]\s+(.+)$", line)
            if m and len(m.group(1)) > 5:
                outcomes.append(m.group(1).strip())

    data = {
        "objectives": objectives[:10],
        "prereq": prereq[:10],
        "themes": themes[:15],
        "outcomes": outcomes[:10],
        "source_lines": content.count("\n"),
    }

    if writer:
        writer({
            "type": "agent_end", "agent": "data_extractor",
            "result": f"{len(data['objectives'])} obj, "
                       f"{len(data['prereq'])} prereq, "
                       f"{len(data['themes'])} themes",
        })

    return {"data": data}
