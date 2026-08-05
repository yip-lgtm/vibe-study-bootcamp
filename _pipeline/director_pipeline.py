#!/usr/bin/env python3
"""
Director-Pattern Multi-Agent Pipeline (LangGraph-style)

Inspired by THU-MAIC/OpenMAIC's `lib/orchestration/director-graph.ts`.

Architecture:
  START → director ──(engineer)──→ engineer ──→ director
                    ─(professor)──→ professor_supervisor ──→ director
                    ─(END)──→ END

The director decides which agent to run next, based on the current
state. This is more powerful than a linear pipeline because:
  - It can cycle back to engineer for revision
  - It can stop early on APPROVED
  - It can route to error handling on REJECT

Run:
  python3 _pipeline/director_pipeline.py --course <path>
  python3 _pipeline/director_pipeline.py --all
  python3 _pipeline/director_pipeline.py --course <path> --stream
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path so we can import _pipeline.* modules
PIPELINE_DIR = Path(__file__).parent
sys.path.insert(0, str(PIPELINE_DIR.parent))

from _pipeline.graph import StateGraph, START, END
from _pipeline.state import PipelineState
from _pipeline.agents.researcher import researcher_node
from _pipeline.agents.data_extractor import data_extractor_node
from _pipeline.agents.engineer import engineer_node
from _pipeline.agents.diagram import diagram_node
from _pipeline.agents.professor_supervisor import professor_supervisor_node
from _pipeline.agents.director import director_node, director_condition


def build_graph() -> StateGraph:
    """
    Build the StateGraph with 5 agent nodes + 1 director node.

    Topology (LangGraph-style):
      START → director ──(engineer)────→ engineer ──→ director
                    ─(professor)──→ professor_supervisor ──→ director
                    ─(END)──→ END

    The director routes the cycle: it can call engineer, then professor,
    then route back to engineer for revision (up to max_iterations).
    """
    g = StateGraph()

    # Add nodes
    g.add_node("researcher", researcher_node)
    g.add_node("data_extractor", data_extractor_node)
    g.add_node("engineer", engineer_node)
    g.add_node("diagram", diagram_node)
    g.add_node("professor_supervisor", professor_supervisor_node)
    g.add_node("director", director_node)

    # Director starts the graph
    g.set_entry_point("director")

    # Director → next agent (conditional)
    g.add_conditional_edges(
        "director",
        director_condition,
        {
            "engineer": "engineer",
            "professor_supervisor": "professor_supervisor",
            "END": END,
            "__END__": END,
        },
    )

    # After engineer, run researcher (cheap, idempotent) + data_extractor
    # + diagram, then back to director
    g.add_edge("engineer", "researcher")
    g.add_edge("researcher", "data_extractor")
    g.add_edge("data_extractor", "diagram")
    g.add_edge("diagram", "professor_supervisor")

    # After professor, always go back to director (to decide END or cycle)
    g.add_edge("professor_supervisor", "director")

    return g.compile()


def stream_writer(state_snapshot: Dict[str, Any]) -> None:
    """Default writer: pretty-prints events to stdout."""
    pass  # Used in run() with custom logic


def run_course(course_path: str, stream: bool = False, max_iterations: int = 3) -> PipelineState:
    """Run the pipeline for one course. Returns final state."""
    course_path = str(Path(course_path).resolve())
    initial = PipelineState(
        course_path=course_path,
        course_code=Path(course_path).stem,
        course_title=Path(course_path).stem,
        target_dir=str(Path(course_path).parent),
        max_iterations=max_iterations,
    )

    graph = build_graph()

    def writer(chunk: Dict[str, Any]) -> None:
        if not stream:
            return
        ctype = chunk.get("type", "?")
        node = chunk.get("node") or chunk.get("agent", "?")
        if ctype == "node_start":
            print(f"  → {node}")
        elif ctype == "node_end":
            result = chunk.get("result", "")
            if result:
                print(f"  ✓ {node}: {result}")
        elif ctype == "agent_start":
            print(f"  → {node}")
        elif ctype == "agent_end":
            result = chunk.get("result", "")
            if result:
                print(f"  ✓ {node}: {result}")
            decision = chunk.get("decision")
            if decision:
                print(f"  → DECISION: {decision} (score {chunk.get('score')})")
        elif ctype == "node_error":
            print(f"  ✗ {node} ERROR: {chunk.get('error')}")

    return graph.invoke(initial, config={"writer": writer})


def main():
    parser = argparse.ArgumentParser(description="Director-pattern Multi-Agent Pipeline")
    parser.add_argument("--course", help="path to course markdown file")
    parser.add_argument("--all", action="store_true", help="run all courses in current repo")
    parser.add_argument("--stream", action="store_true", help="stream events to stdout")
    parser.add_argument("--max-iterations", type=int, default=3, help="max revision cycles")
    parser.add_argument("--json", action="store_true", help="output final state as JSON")
    args = parser.parse_args()

    if args.course:
        print(f"Pipeline (Director pattern): {args.course}")
        print("=" * 60)
        final = run_course(args.course, stream=args.stream,
                           max_iterations=args.max_iterations)
        print()
        print(f"Final decision: {final.decision}")
        print(f"Final score: {final.final_score}")
        print(f"Iterations: {final.iteration}")
        if args.json:
            from _pipeline.state import snapshot
            print(json.dumps(snapshot(final), ensure_ascii=False, indent=2))

    elif args.all:
        # Find all .md files in the current repo
        repo_root = Path.cwd()
        for md in repo_root.rglob("*.md"):
            if any(x in str(md) for x in (
                ".git/", "_agents/", "_pipeline/", "node_modules/"
            )):
                continue
            if md.name in ("README.md", "AGENTS.md"):
                continue
            try:
                run_course(str(md), stream=False, max_iterations=1)
            except Exception as e:
                print(f"  ✗ {md}: {e}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
