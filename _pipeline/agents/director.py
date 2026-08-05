"""
Agent Node: Director (LLM-based routing)

Inspired by THU-MAIC/OpenMAIC's `lib/orchestration/director-graph.ts`.

Director decides which agent to run next. Two modes:

1. **Deterministic mode** (default, no LLM):
   - If body empty: engineer
   - If review empty: professor
   - If REVISE + iteration < max: engineer (cycle)
   - Else: END

2. **LLM mode** (when API key is set):
   - The director makes an LLM call to decide:
     "Given the current state (brief, data, body, review, decision),
      which agent should run next to best advance the course toward APPROVED?"
   - This is more flexible than deterministic rules.

Output of director: dict with `current_agent`, `decision_reason`, `events`.
"""
from __future__ import annotations
from typing import Any, Dict
import json
import re

from ..state import PipelineState
from ..llm_client import complete, detect_provider
from ..graph import END


SYSTEM_PROMPT_DIRECTOR = """You are the **Director** agent in a multi-agent course-generation pipeline.

You decide WHICH agent should run next to advance a course toward APPROVED quality (≥85/100).

Available agents:
- **engineer**: produces/improves the 5MM/3DG/10Q body
- **professor_supervisor**: runs 10 quality gates (returns APPROVED/REVISE/REJECT)
- **END**: stop the pipeline

State context provided to you:
- current iteration, decision, weak gates
- whether body and review exist
- method used by previous agents (LLM or deterministic)

Your job: output JSON with the next action:
```json
{
  "next": "engineer" | "professor_supervisor" | "END",
  "reason": "Why this routing decision? (1-2 sentences)"
}
```

Default routing:
- If body is empty → engineer
- If body present but no review → professor_supervisor
- If decision == REVISE and iteration < max → engineer (cycle)
- If decision == APPROVED or REJECT or iteration >= max → END

You may override defaults if you see a more efficient path (e.g., "go straight to END if REJECT")."""


def _llm_director(state: PipelineState, config: Dict[str, Any]) -> str:
    """LLM-based director: returns next agent name or END."""
    writer = config.get("writer")
    if writer:
        writer({"type": "llm_call", "agent": "director", "phase": "start"})

    state_summary = _format_state_for_director(state)
    user_msg = (
        f"Current state:\n{state_summary}\n\n"
        f"Decide which agent should run next."
    )

    resp = complete(
        messages=[{"role": "user", "content": user_msg}],
        system=SYSTEM_PROMPT_DIRECTOR,
        max_tokens=300,
        temperature=0.1,  # very deterministic for routing
    )

    if writer:
        writer({
            "type": "llm_call", "agent": "director", "phase": "end",
            "tokens": resp.input_tokens + resp.output_tokens,
            "latency_ms": resp.latency_ms,
        })

    return resp.text


def _format_state_for_director(state: PipelineState) -> str:
    """Compact state summary for the director LLM call."""
    lines = [
        f"Course: {state.course_code}",
        f"Iteration: {state.iteration} / max {state.max_iterations}",
        f"Current decision: {state.decision}",
        f"Weak gates: {state.weak_gates}",
        f"Body present: {bool(state.body)} ({len(state.body) if state.body else 0} chars)",
        f"Review present: {bool(state.review)}",
        f"Final score so far: {state.final_score}",
    ]
    if state.brief.get("engineer_method"):
        lines.append(f"Engineer method: {state.brief['engineer_method']}")
    if state.review.get("llm_review"):
        lines.append(f"LLM review available: yes")
    return "\n".join(lines)


def _parse_director_decision(text: str, fallback: str) -> tuple[str, str]:
    """Parse LLM output to get (next_agent, reason)."""
    text = text.strip()
    # Try to parse as JSON
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    try:
        data = json.loads(text)
        next_agent = data.get("next", fallback)
        reason = data.get("reason", "")
        # Validate
        if next_agent not in ("engineer", "professor_supervisor", "END"):
            return fallback, "Invalid next, using fallback"
        return next_agent, reason
    except json.JSONDecodeError:
        # Try to find next: value
        m = re.search(r'"next"\s*:\s*"(\w+)"', text)
        if m and m.group(1) in ("engineer", "professor_supervisor", "END"):
            return m.group(1), "extracted from text"
        # Plain text fallback
        if "END" in text.upper():
            return "END", "LLM suggested END"
        if "engineer" in text.lower():
            return "engineer", "LLM suggested engineer"
        if "professor" in text.lower():
            return "professor_supervisor", "LLM suggested professor"
        return fallback, "Could not parse, using fallback"


def director_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Director: LLM-based (with deterministic fallback).
    Decides which agent to run next.
    """
    writer = config.get("writer")
    if writer:
        writer({
            "type": "agent_start", "agent": "director",
            "iteration": state.iteration, "decision": state.decision,
        })

    # Deterministic decision (always used as fallback / default)
    det_next, det_reason = _deterministic_decision(state)

    cfg = detect_provider()
    use_llm = bool(cfg.api_key) and not config.get("force_deterministic", False)

    if use_llm:
        try:
            llm_text = _llm_director(state, config)
            llm_next, llm_reason = _parse_director_decision(llm_text, det_next)
            # LLM may override deterministic, but only if it makes sense
            # Safety: if iteration is exhausted, force END
            if state.iteration >= state.max_iterations and llm_next != "END":
                next_agent = "END"
                reason = f"Max iterations reached (overriding LLM: {llm_next} → END)"
            else:
                next_agent = llm_next
                reason = llm_reason
            method = "llm"
        except Exception as e:
            if writer:
                writer({"type": "llm_error", "agent": "director", "error": str(e)[:200]})
            next_agent = det_next
            reason = det_reason
            method = "deterministic_fallback"
    else:
        next_agent = det_next
        reason = det_reason
        method = "deterministic"

    if writer:
        writer({
            "type": "agent_end", "agent": "director",
            "next": next_agent, "reason": reason, "method": method,
        })

    return {
        "current_agent": next_agent,
        "events": [{
            "type": "director_decision",
            "data": {
                "next": next_agent, "reason": reason, "method": method,
                "iteration": state.iteration, "decision": state.decision,
            },
        }],
    }


def _deterministic_decision(state: PipelineState) -> tuple[str, str]:
    """Pure-logic decision (default fallback)."""
    if not state.body:
        return "engineer", "no body yet, run engineer"
    if not state.review:
        return "professor_supervisor", "body present, no review, run professor"
    if state.decision == "REVISE" and state.iteration < state.max_iterations:
        return "engineer", f"REVISE on iteration {state.iteration}, cycle back to engineer"
    # APPROVED, REJECT, or max iterations
    if state.decision == "APPROVED":
        return "END", f"APPROVED after {state.iteration} iterations"
    if state.decision == "REJECT":
        return "END", f"REJECT after {state.iteration} iterations"
    return "END", f"max iterations ({state.max_iterations}) hit"


def director_condition(state: PipelineState) -> str:
    """Conditional edge function: maps state.current_agent to path key."""
    if state.current_agent == "__END__":
        return END
    return state.current_agent
