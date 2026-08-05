"""
Agent Node: Professor Supervisor (LLM-augmented)

Combines:
1. Rule-based quality gates (the existing review.py) — 10 hard gates
2. LLM-based qualitative review — overall assessment, suggestions

Decision logic:
- If LLM is available: get qualitative review + use rule-based score
- If no LLM: rule-based only (existing behavior)
"""
from __future__ import annotations
from typing import Any, Dict
import subprocess
from pathlib import Path

from ..state import PipelineState
from ..llm_client import complete, detect_provider


SYSTEM_PROMPT_PROFESSOR = """You are the **Professor Supervisor** agent — a senior academic reviewer in a multi-agent course-generation pipeline.

Your job: read a course body and its quality gate report, then provide:
- An overall qualitative assessment (2-3 sentences)
- Top 3 strengths
- Top 3 specific improvements (cite the relevant section)
- For each failing gate, a concrete actionable fix

Be HONEST and CONSTRUCTIVE. If the course is excellent, say so.
If it has gaps (e.g., missing scholars, generic placeholders, few equations), name them.

Output format (return ONLY this JSON, no commentary):
```json
{
  "overall": "Brief qualitative assessment...",
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "improvements": ["Specific improvement 1", "Specific improvement 2", "Specific improvement 3"],
  "gate_fixes": {
    "G1_length": "Increase line count by adding 5DD/10SL sections",
    "G3_citations": "Add Newton 1687, Stokes 1851, etc."
  }
}
```"""


def _llm_review(state: PipelineState, body: str, rule_review: dict, config: Dict[str, Any]) -> Dict[str, Any]:
    """LLM-based qualitative review."""
    writer = config.get("writer")
    if writer:
        writer({"type": "llm_call", "agent": "professor", "phase": "start"})

    body_for_llm = body[:25000] if len(body) > 25000 else body
    gate_summary = ", ".join(f"{k}={v}" for k, v in rule_review.get("gates", {}).items())

    user_msg = (
        f"Course: {state.course_code}\n\n"
        f"Iteration: {state.iteration}\n\n"
        f"Rule-based score: {rule_review.get('score', 0)}/100\n"
        f"Gate scores: {gate_summary}\n\n"
        f"--- Course body ({len(body):,} chars) ---\n\n"
        f"{body_for_llm}\n\n"
        f"--- End ---\n\n"
        f"Provide qualitative review in the JSON format."
    )

    resp = complete(
        messages=[{"role": "user", "content": user_msg}],
        system=SYSTEM_PROMPT_PROFESSOR,
        max_tokens=2500,
        temperature=0.3,
    )

    if writer:
        writer({
            "type": "llm_call", "agent": "professor", "phase": "end",
            "tokens": resp.input_tokens + resp.output_tokens,
            "latency_ms": resp.latency_ms,
        })

    import json, re as _re
    text = resp.text.strip()
    if text.startswith("```"):
        text = _re.sub(r"^```(?:json)?\s*", "", text)
        text = _re.sub(r"```\s*$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _re.search(r"\{.*\}", text, _re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return {"_error": "JSON parse failed", "_raw": text[:500]}
        return {"_error": "No JSON found", "_raw": text[:500]}


def professor_supervisor_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """Professor Supervisor: rule-based gates + optional LLM review."""
    writer = config.get("writer")
    if writer:
        writer({
            "type": "agent_start", "agent": "professor_supervisor",
            "course": state.course_code, "iteration": state.iteration,
        })

    # Step 1: run the existing rule-based review
    pipeline_root = Path(__file__).resolve().parents[2]
    review_script = pipeline_root / "_agents" / "professor_supervisor" / "review.py"
    if not review_script.exists():
        return {"errors": [f"[professor] review.py not found at {review_script}"]}

    # The state.body may have been modified by the engineer. Save it temporarily.
    body_path = state.course_path
    body_content = state.body
    if body_content and body_path:
        # Write body to a temp file for review.py to evaluate
        # (Or we could pass it via env, but simpler: write to disk and restore)
        with open(body_path, "w", encoding="utf-8") as f:
            f.write(body_content)

    try:
        result = subprocess.run(
            ["python3", str(review_script), "--course", state.course_path, "--json"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            return {"errors": [f"[professor] review.py failed: {result.stderr}"]}
        import json
        rule_review = json.loads(result.stdout)
    except Exception as e:
        return {"errors": [f"[professor] Cannot run review: {e}"]}
    finally:
        # Note: we don't restore the original course_path because the body
        # may legitimately be an improved version. Caller can use git
        # to revert if needed.
        pass

    score = rule_review.get("score", 0)
    if score >= 85:
        decision = "APPROVED"
    elif score >= 70:
        decision = "REVISE"
    else:
        decision = "REJECT"

    weak_gates = [
        gate for gate, score_v in rule_review.get("gates", {}).items()
        if score_v < 10
    ]

    # Step 2: optional LLM-based qualitative review
    cfg = detect_provider()
    use_llm = bool(cfg.api_key) and not config.get("force_deterministic", False)
    llm_review = {}
    if use_llm:
        try:
            llm_review = _llm_review(state, body_content or "", rule_review, config)
        except Exception as e:
            if writer:
                writer({"type": "llm_error", "agent": "professor", "error": str(e)[:200]})

    review = {
        "score": score,
        "decision": decision,
        "weak_gates": weak_gates,
        "gates": rule_review.get("gates", {}),
        "lines": rule_review.get("lines", 0),
        "llm_review": llm_review,
    }

    if writer:
        writer({
            "type": "agent_end", "agent": "professor_supervisor",
            "score": score, "decision": decision,
            "weak_gates": weak_gates,
            "has_llm_review": bool(llm_review) and not llm_review.get("_error"),
        })

    return {
        "review": review,
        "decision": decision,
        "final_score": score,
        "weak_gates": weak_gates,
        "iteration": state.iteration + 1,
    }
