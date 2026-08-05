"""
Agent Node: Engineer (LLM-based content producer)

Reads: state.brief, state.data, source content
Writes: state.body (5MM/3DG/10Q/5DD/10SL/5MR markdown)

Strategy:
- If source has 5MM/3DG/10Q structure, the LLM improves/enriches it
- If source lacks structure, the LLM creates it from scratch
- Falls back to passing source as-is if no API key
"""
from __future__ import annotations
from typing import Any, Dict, List
import re
import os

from ..state import PipelineState
from ..llm_client import complete, detect_provider


SYSTEM_PROMPT_ENGINEER = """You are the **Engineer** agent in a multi-agent course-generation pipeline.

Your job: produce a comprehensive course body in the **Deep Study Format** with the following sections:
- **5MM** (5 Mental Models) — 5 SPECIFIC mental models with equations, numbers, scholars, dates
- **3DG** (3 Disagreements) — 3 fundamental disagreements in the field, with Position A + Position B + tension
- **10Q** (10 Probing Questions) — 10 deep questions with detailed answers (≥10 lines each)
- **5DD** (5 Deep Dives) — 5 deep-dive sections in BILINGUAL (中英對照) format
- **10SL** (10 Self-Test Solutions) — 10 self-test Q&A with full derivations
- **5MR** (5 Mermaid Diagrams) — 5 distinct Mermaid diagram types (flowchart, state, class, ER, sequence)

Strict rules:
- Every claim must cite a REAL scholar with year (e.g., "Newton 1687", "Bourouiba 2021")
- Every equation must be in LaTeX format: $$...$$
- Every question must have a detailed answer (not a 1-line summary)
- Include 中英對照 (bilingual Chinese-English) at least once per section
- Use 5 distinct Mermaid diagram types (not all flowchart)

Output format: complete markdown document, ready to save as a .md file.

You will be given:
- A research brief (primary sources, scholars, key numbers)
- A data extraction (objectives, prereq, themes)
- A source content to base the body on
- Optionally: existing body to improve (revision mode)

If the source already has 5MM/3DG/10Q structure, ENRICH it (add more scholars, more equations, more depth).
If the source lacks structure, BUILD it from scratch using the brief and data."""


def _llm_engineer(state: PipelineState, content: str, brief: dict, data: dict, config: Dict[str, Any]) -> str:
    """LLM-based engineer: produce or improve the course body."""
    writer = config.get("writer")
    if writer:
        writer({"type": "llm_call", "agent": "engineer", "phase": "start"})

    # Detect if content already has 5MM/3DG/10Q structure
    has_structure = (
        "## 問題 1" in content
        and "## 問題 2" in content
        and "## 問題 3" in content
    )

    # Truncate for context
    content_for_llm = content[:50000] if len(content) > 50000 else content
    brief_str = _format_brief(brief)
    data_str = _format_data(data)

    weak_gates = state.weak_gates or []
    is_revision = state.iteration > 0 and weak_gates

    if is_revision:
        user_msg = (
            f"REVISION MODE: improve the following course body to address these weak quality gates: {weak_gates}\n\n"
            f"Course: {state.course_code}\n\n"
            f"--- Brief ---\n{brief_str}\n\n"
            f"--- Data ---\n{data_str}\n\n"
            f"--- Current body (needs improvement) ---\n{content_for_llm}\n\n"
            f"--- End ---\n\n"
            f"Produce an improved version of the body that addresses the weak gates."
        )
    elif has_structure:
        user_msg = (
            f"ENRICH MODE: improve the following course body with more scholars, equations, depth.\n\n"
            f"Course: {state.course_code}\n\n"
            f"--- Brief ---\n{brief_str}\n\n"
            f"--- Data ---\n{data_str}\n\n"
            f"--- Current body (enrich this) ---\n{content_for_llm}\n\n"
            f"--- End ---\n\n"
            f"Produce an enriched version with deeper analysis and more citations."
        )
    else:
        user_msg = (
            f"CREATE MODE: build a course body from scratch using the brief, data, and source.\n\n"
            f"Course: {state.course_code}\n\n"
            f"--- Brief ---\n{brief_str}\n\n"
            f"--- Data ---\n{data_str}\n\n"
            f"--- Source content ---\n{content_for_llm}\n\n"
            f"--- End ---\n\n"
            f"Produce the complete course body in Deep Study Format."
        )

    resp = complete(
        messages=[{"role": "user", "content": user_msg}],
        system=SYSTEM_PROMPT_ENGINEER,
        max_tokens=16000,  # larger for body generation
        temperature=0.3,  # some creativity but mostly factual
    )

    if writer:
        writer({
            "type": "llm_call", "agent": "engineer", "phase": "end",
            "tokens": resp.input_tokens + resp.output_tokens,
            "latency_ms": resp.latency_ms,
        })

    return resp.text


def _format_brief(brief: dict) -> str:
    if not brief:
        return "(no brief)"
    parts = []
    if "primary_sources" in brief:
        parts.append("Primary sources:")
        for s in brief["primary_sources"][:10]:
            parts.append(f"  - {s}")
    if "scholars_with_years" in brief:
        parts.append("\nScholars with years:")
        for s in brief["scholars_with_years"][:15]:
            parts.append(f"  - {s}")
    if "key_numbers" in brief:
        parts.append("\nKey numbers:")
        for n in brief["key_numbers"][:10]:
            parts.append(f"  - {n}")
    return "\n".join(parts)


def _format_data(data: dict) -> str:
    if not data:
        return "(no data)"
    parts = []
    for k, label in [
        ("objectives", "Objectives"),
        ("prereq", "Prerequisites"),
        ("key_themes", "Key Themes"),
        ("learning_outcomes", "Learning Outcomes"),
    ]:
        if k in data and data[k]:
            parts.append(f"\n{label}:")
            for item in data[k][:10]:
                parts.append(f"  - {item}")
    return "\n".join(parts)


def engineer_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """Engineer: produce or improve 5MM/3DG/10Q body using LLM."""
    writer = config.get("writer")
    is_revision = state.iteration > 0 and state.weak_gates
    if writer:
        writer({
            "type": "agent_start", "agent": "engineer",
            "course": state.course_code,
            "revision": is_revision,
            "weak_gates": state.weak_gates if is_revision else [],
        })

    try:
        with open(state.course_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"errors": [f"[engineer] Cannot read {state.course_path}: {e}"]}

    cfg = detect_provider()
    use_llm = bool(cfg.api_key) and not config.get("force_deterministic", False)
    brief = state.brief or {}
    data = state.data or {}

    if use_llm:
        try:
            body = _llm_engineer(state, content, brief, data, config)
            method = "llm"
        except Exception as e:
            if writer:
                writer({"type": "llm_error", "agent": "engineer", "error": str(e)[:200]})
            body = content  # pass through
            method = "deterministic_fallback"
    else:
        body = content  # pass through
        method = "deterministic"

    # Compute body stats
    body_stats = {
        "lines": body.count("\n"),
        "scholars": len(re.findall(
            r"\b(Newton|Einstein|Maxwell|Bohr|Heisenberg|Dirac|Feynman|"
            r"Stokes|Reynolds|Timoshenko|Terzaghi|Bernoulli|Coulomb|"
            r"Strang|Knuth|Bourouiba|Wells|"
            r"Schwarzenbach|Stumm|Morgan|Hemond|"
            r"Hubbard|Marsden|Pauling|"
            r"Fourier|Lagrange|Hamilton|Maxwell|"
            r"Watson|Crick|Darwin|Mendel|"
            r"Hubbard|Marsden|"
            r"Hardy|Weinberg|Watson|"
            r"Gottfried|Yan|Sakurai)\s*[\(]?\d{4}",
            body,
        )),
        "equations": len(re.findall(r"\$\$.*?\$\$", body, re.DOTALL)),
        "mermaid": body.count("```mermaid"),
        "chinese": len(re.findall(r"[\u4e00-\u9fff]", body)),
    }

    if writer:
        writer({
            "type": "agent_end", "agent": "engineer",
            "method": method,
            "result": (
                f"{body_stats['lines']} lines, "
                f"{body_stats['scholars']} scholars, "
                f"{body_stats['equations']} eq, "
                f"{body_stats['mermaid']} mm"
            ),
        })

    return {
        "body": body,
        "brief": {"body_stats": body_stats, "engineer_method": method},
        "events": [{
            "type": "engineer_method", "data": {"method": method},
        }],
    }
