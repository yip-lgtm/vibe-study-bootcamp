"""
Agent Node: Data Extractor (LLM-based)

Reads: state.brief, source content
Writes: state.data = {objectives, prereq, key_themes, learning_outcomes, ...}

Strategy: Use LLM to extract structured course metadata.
Falls back to regex-based extraction if no API key.
"""
from __future__ import annotations
from typing import Any, Dict
import re
import os

from ..state import PipelineState
from ..llm_client import complete, detect_provider


SYSTEM_PROMPT_DATA_EXTRACTOR = """You are the **Data Extractor** agent in a multi-agent course-generation pipeline.

Your job: read a course markdown file and extract structured course metadata:
- **objectives** (5-10): measurable, action-verb-led (Apply, Compute, Derive, Solve, Design, Analyze...)
- **prereq** (3-8): courses/topics that must be completed first
- **key_themes** (5-15): the main subject areas covered
- **learning_outcomes** (5-10): what a student can do after the course

Strict rules:
- Be SPECIFIC (cite course codes, equations, theorems)
- Be VERIFIABLE (only extract what's clearly in the source)
- Be CONCISE (one line per item, no fluff)

Output format (return ONLY this JSON, no commentary):
```json
{
  "objectives": ["Apply Darcy's law to compute groundwater flow in confined aquifers", ...],
  "prereq": ["18.03 Differential Equations", "Calculus II", ...],
  "key_themes": ["Continuum mechanics", "Fluid statics", ...],
  "learning_outcomes": ["Solve PDEs governing 2D fluid flow", ...]
}
```"""


def _llm_data_extractor(state: PipelineState, content: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """LLM-based data extraction."""
    writer = config.get("writer")
    if writer:
        writer({"type": "llm_call", "agent": "data_extractor", "phase": "start"})

    content_for_llm = content[:30000] if len(content) > 30000 else content

    user_msg = (
        f"Course: {state.course_code}\n\n"
        f"--- Source content ({len(content):,} chars) ---\n\n"
        f"{content_for_llm}\n\n"
        f"--- End of source ---\n\n"
        f"Extract the structured metadata JSON."
    )

    resp = complete(
        messages=[{"role": "user", "content": user_msg}],
        system=SYSTEM_PROMPT_DATA_EXTRACTOR,
        max_tokens=3000,
        temperature=0.2,
    )

    if writer:
        writer({
            "type": "llm_call", "agent": "data_extractor", "phase": "end",
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
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                data = {
                    "objectives": [], "prereq": [], "key_themes": [],
                    "learning_outcomes": [],
                    "_error": "JSON parse failed", "_raw": text[:500],
                }
        else:
            data = {
                "objectives": [], "prereq": [], "key_themes": [],
                "learning_outcomes": [],
                "_error": "No JSON found", "_raw": text[:500],
            }

    data["source_lines"] = content.count("\n")
    data["model_used"] = resp.model
    data["llm_tokens"] = resp.input_tokens + resp.output_tokens
    return data


def _deterministic_data_extractor(state: PipelineState, content: str) -> Dict[str, Any]:
    """Deterministic fallback."""
    objectives = []
    for line in content.split("\n"):
        m = re.match(r"^\s*\d+\.\s+\*?\*?(.+?)\*?\*?$", line.strip())
        if m:
            text = m.group(1).strip()
            if any(v in text for v in [
                "Apply", "Compute", "Derive", "Solve", "Design",
                "Analyze", "Understand", "Identify", "Recognize",
                "Formulate", "Predict", "Explain", "Calculate",
            ]):
                if 10 < len(text) < 200:
                    objectives.append(text)

    prereq = []
    for line in content.split("\n"):
        m = re.search(r"[Pp]rereq[uiaq]*:?\s*(.+)", line)
        if m:
            items = re.split(r"[,，；;]", m.group(1))
            for item in items:
                item = item.strip()
                if item and len(item) < 100:
                    prereq.append(item)

    themes = []
    for m in re.finditer(r"^##\s+(.+)$", content, re.MULTILINE):
        title = m.group(1).strip()
        if title and not title.startswith("問題") and len(title) < 80:
            themes.append(title)

    outcomes = []
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

    return {
        "objectives": objectives[:10],
        "prereq": prereq[:10],
        "key_themes": themes[:15],
        "learning_outcomes": outcomes[:10],
        "source_lines": content.count("\n"),
        "_method": "deterministic",
    }


def data_extractor_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """Data Extractor: LLM-based with deterministic fallback."""
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "data_extractor", "course": state.course_code})

    try:
        with open(state.course_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"errors": [f"[data_extractor] Cannot read {state.course_path}: {e}"]}

    cfg = detect_provider()
    use_llm = bool(cfg.api_key) and not config.get("force_deterministic", False)

    if use_llm:
        try:
            data = _llm_data_extractor(state, content, config)
            method = "llm"
        except Exception as e:
            if writer:
                writer({"type": "llm_error", "agent": "data_extractor", "error": str(e)[:200]})
            data = _deterministic_data_extractor(state, content)
            method = "deterministic_fallback"
    else:
        data = _deterministic_data_extractor(state, content)
        method = "deterministic"

    if writer:
        writer({
            "type": "agent_end", "agent": "data_extractor",
            "method": method,
            "result": (
                f"{len(data.get('objectives', []))} obj, "
                f"{len(data.get('prereq', []))} prereq, "
                f"{len(data.get('key_themes', []))} themes"
            ),
        })

    return {"data": data, "events": [{
        "type": "data_extractor_method",
        "data": {"method": method, "course": state.course_code},
    }]}
