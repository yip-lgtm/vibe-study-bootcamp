"""
Minimal StateGraph Runtime for Multi-Agent Pipeline

Python port of LangGraph's StateGraph + addNode + addEdge + addConditionalEdges.

This is a deliberately small implementation (~200 lines) that captures
the essential LangGraph pattern: a directed graph of nodes with state
flow, conditional branching, and a single "START"/"END" sentinel.

Reference: LangGraph Python + OpenMAIC's `lib/orchestration/director-graph.ts`
https://langchain-ai.github.io/langgraph/
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set
import inspect

from .state import PipelineState, apply_update, emit_event, snapshot


# Sentinel strings for graph topology (LangGraph uses `START` / `END` constants)
START = "__START__"
END = "__END__"


# A node takes the current state and a config dict (with optional writer), and
# returns either:
#   - a dict of state updates (applied via reducers), OR
#   - a partial state object whose fields are also applied
NodeFn = Callable[[PipelineState, Dict[str, Any]], Dict[str, Any]]


# Conditional edge function takes the state and returns a string key
# that maps to one of the `path_map` values (a node name or END)
ConditionFn = Callable[[PipelineState], str]


@dataclass
class _Edge:
    """Internal representation of a graph edge."""
    source: str
    target: str  # node name, START, or END


@dataclass
class _ConditionalEdge:
    """Internal representation of a conditional edge."""
    source: str
    condition: ConditionFn
    path_map: Dict[str, str]  # condition-return-value -> next-node-name (or END)


class StateGraph:
    """
    Minimal StateGraph: nodes + edges + conditional edges + start point.

    Usage (mirrors LangGraph TypeScript API):
        g = StateGraph(PipelineState)
        g.add_node("researcher", researcher_fn)
        g.add_node("director", director_fn)
        g.add_edge(START, "researcher")
        g.add_conditional_edges("director", director_condition, {
            "engineer": "engineer",
            END: END,
        })
        app = g.compile()
        final_state = app.invoke(initial_state, config={"writer": print})
    """

    def __init__(self, state_schema=None):
        self._nodes: Dict[str, NodeFn] = {}
        self._edges: List[_Edge] = []
        self._cond_edges: List[_ConditionalEdge] = []
        self._start: Optional[str] = None
        self._state_schema = state_schema

    # ----- Public API -----

    def add_node(self, name: str, fn: NodeFn) -> "StateGraph":
        """Add a node with a name and function (like LangGraph addNode)."""
        if name in (START, END):
            raise ValueError(f"Cannot use reserved name: {name}")
        self._nodes[name] = fn
        return self

    def add_edge(self, source: str, target: str) -> "StateGraph":
        """Add a direct edge (like LangGraph addEdge)."""
        if source == END:
            raise ValueError("Cannot add edge FROM END")
        if target == START:
            raise ValueError("Cannot add edge TO START")
        if source not in (START,) and source not in self._nodes:
            raise ValueError(f"Unknown source node: {source}")
        if target not in (END,) and target not in self._nodes:
            raise ValueError(f"Unknown target node: {target}")
        self._edges.append(_Edge(source=source, target=target))
        return self

    def add_conditional_edges(
        self,
        source: str,
        condition: ConditionFn,
        path_map: Dict[str, str],
    ) -> "StateGraph":
        """Add a conditional edge (like LangGraph addConditionalEdges)."""
        if source not in self._nodes:
            raise ValueError(f"Unknown source node: {source}")
        for key, target in path_map.items():
            if target not in (END,) and target not in self._nodes:
                raise ValueError(f"Unknown target {target!r} in path_map key {key!r}")
        self._cond_edges.append(_ConditionalEdge(
            source=source, condition=condition, path_map=path_map,
        ))
        return self

    def set_entry_point(self, name: str) -> "StateGraph":
        """Set the entry point (like LangGraph setEntryPoint)."""
        if name not in self._nodes:
            raise ValueError(f"Unknown node: {name}")
        self._start = name
        return self

    def set_finish_point(self, name: str) -> "StateGraph":
        """Add a finish edge from node to END."""
        return self.add_edge(name, END)

    def compile(self) -> "CompiledGraph":
        """Compile the graph into a runnable form (returns CompiledGraph)."""
        if not self._start:
            raise ValueError("Entry point not set (use set_entry_point)")
        if START not in {e.source for e in self._edges} and not any(
            e.source == START for e in self._edges
        ):
            # Auto-add START -> entry
            self._edges.append(_Edge(source=START, target=self._start))
        return CompiledGraph(
            nodes=dict(self._nodes),
            edges=list(self._edges),
            cond_edges=list(self._cond_edges),
            start=self._start,
        )


class CompiledGraph:
    """A compiled, runnable StateGraph. Use .invoke() to run."""

    def __init__(self, nodes, edges, cond_edges, start):
        self._nodes = nodes
        self._edges = edges
        self._cond_edges = cond_edges
        self._start = start
        # Build adjacency for direct edges: source -> [target]
        self._direct: Dict[str, List[str]] = {}
        for e in edges:
            self._direct.setdefault(e.source, []).append(e.target)
        # Build cond adjacency: source -> (cond, path_map)
        self._cond: Dict[str, _ConditionalEdge] = {}
        for ce in cond_edges:
            self._cond[ce.source] = ce

    def invoke(
        self,
        initial_state: PipelineState,
        config: Optional[Dict[str, Any]] = None,
    ) -> PipelineState:
        """
        Run the graph to completion. Returns the final state.
        config may include a `writer(chunk)` callable for streaming events.
        """
        config = config or {}
        writer = config.get("writer")
        state = initial_state
        current = self._start

        # Loop until we reach END
        max_steps = 100  # safety cap
        steps = 0
        while current != END and steps < max_steps:
            steps += 1

            if current == START:
                # Direct edge from START
                targets = self._direct.get(START, [])
                if not targets:
                    break
                current = targets[0]
                continue

            if current not in self._nodes:
                raise RuntimeError(f"Reached unknown node: {current}")

            node_fn = self._nodes[current]
            # Stream a "node_start" event
            if writer:
                writer({"type": "node_start", "node": current})

            # Run the node
            try:
                update = node_fn(state, config) or {}
            except Exception as e:
                update = {"errors": [f"[{current}] {type(e).__name__}: {e}"]}
                if writer:
                    writer({"type": "node_error", "node": current, "error": str(e)})

            # Apply update to state (using reducers)
            state = apply_update(state, update)

            # Stream a "node_end" event
            if writer:
                writer({"type": "node_end", "node": current, "state": snapshot(state)})

            # Determine next node
            if current in self._cond:
                # Conditional edge: run condition, look up path_map
                cond_edge = self._cond[current]
                key = cond_edge.condition(state)
                if key not in cond_edge.path_map:
                    raise RuntimeError(
                        f"Condition returned {key!r}, not in path_map {list(cond_edge.path_map.keys())}"
                    )
                current = cond_edge.path_map[key]
            elif current in self._direct:
                # Direct edge: take the first one (LangGraph supports multiple
                # but our simple model uses one)
                current = self._direct[current][0]
            else:
                # No outgoing edge: stop
                current = END

        return state
