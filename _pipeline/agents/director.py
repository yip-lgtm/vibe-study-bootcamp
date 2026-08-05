"""
Agent Node: Director (LangGraph Director Pattern)

This is the KEY innovation from OpenMAIC's `lib/orchestration/director-graph.ts`.

The director doesn't generate content — it DECIDES which agent runs next
based on the current state. This makes the pipeline:
  1. Stateful (director reads accumulated outputs)
  2. Adaptive (director routes based on quality, not just position)
  3. Cyclic (director can route back to engineer for revision)

Original OpenMAIC pattern: director is a single LLM call that decides
"which agent should speak next" given the conversation history.

Our adaptation: the director uses deterministic rules (no LLM call)
because our pipeline is more structured. The rules:

  - If state.body is empty AND we have not run engineer:
      → next: engineer
  - If state.body is empty (engineer failed or no source):
      → next: professor_supervisor (to log failure)
  - If state.review is empty (professor not yet run):
      → next: professor_supervisor
  - If state.decision == "REVISE" AND state.iteration < state.max_iterations:
      → next: engineer (cycle back for revision)
  - Otherwise (APPROVED, or REJECT, or max iterations hit):
      → END

This makes our pipeline a graph rather than a linear chain.
"""
from __future__ import annotations
from typing import Any, Dict

from ..state import PipelineState


def director_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Director: pure logic (no LLM call), decides next agent.

    Returns a dict with `current_agent` and `decision` updates.
    The graph's conditional edges then route to the chosen node.
    """
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "director",
                "iteration": state.iteration, "decision": state.decision})

    decision_reason = "no decision yet"
    next_agent = None

    if not state.body:
        # No body yet — need engineer
        next_agent = "engineer"
        decision_reason = "no body yet, run engineer"
    elif not state.review:
        # Body exists, no review — run professor
        next_agent = "professor_supervisor"
        decision_reason = "body present, no review, run professor"
    elif state.decision == "REVISE" and state.iteration < state.max_iterations:
        # Need to revise
        next_agent = "engineer"
        decision_reason = f"REVISE on iteration {state.iteration}, cycle back to engineer"
    else:
        # APPROVED, REJECT, or max iterations hit
        next_agent = "__END__"
        if state.decision == "APPROVED":
            decision_reason = f"APPROVED after {state.iteration} iterations"
        elif state.decision == "REJECT":
            decision_reason = f"REJECT after {state.iteration} iterations"
        else:
            decision_reason = f"max iterations ({state.max_iterations}) hit, decision={state.decision}"

    if writer:
        writer({"type": "agent_end", "agent": "director",
                "next": next_agent, "reason": decision_reason})

    return {
        "current_agent": next_agent,
        "events": [{
            "type": "director_decision",
            "data": {"next": next_agent, "reason": decision_reason,
                     "iteration": state.iteration, "decision": state.decision},
        }],
    }


def director_condition(state: PipelineState) -> str:
    """
    Conditional edge function: maps state.current_agent to path key.
    Returns "engineer", "professor_supervisor", or END.
    """
    if state.current_agent == "__END__":
        return END
    return state.current_agent


# Import END from graph module (lazy import to avoid circular)
from ..graph import END
