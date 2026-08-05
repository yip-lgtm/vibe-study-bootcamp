"""
Agent Node: Professor Supervisor (LangGraph-style)

Reads: state.body, state.brief, state.data, state.diagrams
Writes: state.review = {score, decision, weak_gates, ...}

The professor is the QUALITY GATE. Its decision determines the
flow control: APPROVED → END, REVISE → cycle back to engineer.

Uses the existing review.py for the actual scoring (single source of truth).
"""
from __future__ import annotations
from typing import Any, Dict
import subprocess
from pathlib import Path

from ..state import PipelineState


def professor_supervisor_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Professor Supervisor: runs the 10-gate quality review on the body.
    Decides: APPROVED / REVISE / REJECT.

    Re-uses the existing _agents/professor_supervisor/review.py script
    to keep the scoring logic DRY (single source of truth).
    """
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "professor_supervisor",
                "course": state.course_code, "iteration": state.iteration})

    # Resolve the review.py path
    pipeline_root = Path(__file__).resolve().parents[2]  # /workspace/<repo>/
    review_script = pipeline_root / "_agents" / "professor_supervisor" / "review.py"

    if not review_script.exists():
        return {"errors": [f"[professor] review.py not found at {review_script}"]}

    # Run review.py
    try:
        result = subprocess.run(
            ["python3", str(review_script), "--course", state.course_path, "--json"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            return {"errors": [f"[professor] review.py failed: {result.stderr}"]}
        import json
        review_data = json.loads(result.stdout)
    except Exception as e:
        return {"errors": [f"[professor] Cannot run review: {e}"]}

    score = review_data.get("score", 0)
    if score >= 85:
        decision = "APPROVED"
    elif score >= 70:
        decision = "REVISE"
    else:
        decision = "REJECT"

    # Identify weak gates
    weak_gates = [
        gate for gate, score_v in review_data.get("gates", {}).items()
        if score_v < 10
    ]

    review = {
        "score": score,
        "decision": decision,
        "weak_gates": weak_gates,
        "gates": review_data.get("gates", {}),
        "lines": review_data.get("lines", 0),
    }

    if writer:
        writer({
            "type": "agent_end", "agent": "professor_supervisor",
            "score": score, "decision": decision,
            "weak_gates": weak_gates,
        })

    return {
        "review": review,
        "decision": decision,
        "final_score": score,
        "weak_gates": weak_gates,
        "iteration": state.iteration + 1,  # Increment iteration
    }
