"""
State Schema for Multi-Agent Pipeline (LangGraph-style)

Each agent in the pipeline reads from and writes to a shared state.
Reducers (similar to LangGraph's `Annotation` reducers) accumulate
results across agent invocations.

State design inspired by OpenMAIC's `lib/orchestration/director-graph.ts`
where `Annotation.Root({...})` defines the schema with named fields and
optional reducers like `(prev, update) => [...prev, ...update]`.

Reference: https://github.com/THU-MAIC/OpenMAIC
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, List, Dict, Optional


# Reducer: append new items to existing list (LangGraph default for arrays)
def append_reducer(prev: List[Any], update: List[Any]) -> List[Any]:
    """Reducer that appends new items to existing list (immutable)."""
    return list(prev) + list(update)


# Reducer: replace previous value with new (used for scalars)
def replace_reducer(prev: Any, update: Any) -> Any:
    """Reducer that replaces previous value with new."""
    return update


# Reducer: dict update (merge keys)
def dict_update_reducer(prev: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer that merges dict updates."""
    return {**prev, **update}


@dataclass
class PipelineState:
    """
    Shared state for the 5-agent course generation pipeline.

    Each field has a reducer that defines how the state is updated
    when a node returns new values. This mirrors LangGraph's
    `Annotation.Root({field: Annotation<T>(reducer=...)})` pattern.
    """

    # === Input (set once at graph entry) ===
    course_path: str = ""                           # Path to source markdown file
    course_code: str = ""                           # e.g. "PHYS_3036"
    course_title: str = ""                          # e.g. "Quantum Physics"
    target_dir: str = ""                           # Output directory for new files

    # === Mutable: agent outputs (with reducers) ===
    brief: Dict[str, Any] = field(default_factory=dict)             # Researcher output
    data: Dict[str, Any] = field(default_factory=dict)               # Data Extractor output
    body: str = ""                                                   # Engineer output (5MM/3DG/10Q/5DD/10SL/5MR)
    diagrams: List[str] = field(default_factory=list)                # Diagram node output (mermaid blocks)
    review: Dict[str, Any] = field(default_factory=dict)             # Professor Supervisor output

    # === Mutable: control flow ===
    current_agent: str = "director"                 # Which agent to run next
    iteration: int = 0                              # Revision iteration count
    max_iterations: int = 3                         # Cap on revisions
    decision: str = ""                              # APPROVED / REVISE / REJECT (from professor) — empty until professor runs
    weak_gates: List[str] = field(default_factory=list)  # Which gates failed (for re-routing)
    errors: List[str] = field(default_factory=list)        # Accumulated errors

    # === Mutable: stream events (with reducer for SSE-like output) ===
    events: List[Dict[str, Any]] = field(default_factory=list)     # Timeline of state transitions

    # === Output ===
    final_score: int = 0
    output_files: List[str] = field(default_factory=list)


def emit_event(state: PipelineState, event_type: str, data: Dict[str, Any]) -> None:
    """Helper to append an event to the state's event log (OpenMAIC pattern)."""
    state.events.append({"type": event_type, "data": data, "ts": _now_iso()})


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def apply_update(state: PipelineState, update: Dict[str, Any]) -> PipelineState:
    """
    Apply a node's return value to state, respecting reducers.

    Mirrors LangGraph's behavior: each key in the update dict triggers
    its corresponding reducer to merge the new value with the old.

    This is the Python equivalent of LangGraph's automatic state
    application via Annotation reducers.
    """
    # Field -> reducer mapping (mirror LangGraph schema)
    reducers: Dict[str, Callable[[Any, Any], Any]] = {
        "brief": dict_update_reducer,
        "data": dict_update_reducer,
        "body": replace_reducer,
        "diagrams": append_reducer,
        "review": dict_update_reducer,
        "current_agent": replace_reducer,
        "iteration": replace_reducer,
        "decision": replace_reducer,
        "weak_gates": append_reducer,
        "errors": append_reducer,
        "events": append_reducer,
        "final_score": replace_reducer,
        "output_files": append_reducer,
        # course_path, course_code, course_title, target_dir, max_iterations are inputs (no reducer)
    }

    for key, value in update.items():
        if key in reducers:
            current = getattr(state, key)
            new_value = reducers[key](current, value)
            setattr(state, key, new_value)
        else:
            # No reducer — direct set (inputs or new fields)
            setattr(state, key, value)
    return state


def snapshot(state: PipelineState) -> Dict[str, Any]:
    """Return a JSON-serializable snapshot of the state (for logging/SSE)."""
    import dataclasses
    return {k: v for k, v in dataclasses.asdict(state).items()}
