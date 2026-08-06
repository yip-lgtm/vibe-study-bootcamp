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
import subprocess
import sys
import time
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

    final = graph.invoke(initial, config={"writer": writer})

    # Write enhanced body back to course file (only for APPROVED courses)
    if final.decision == "APPROVED" and final.body:
        try:
            with open(course_path, "w", encoding="utf-8") as f:
                f.write(final.body)
        except Exception as e:
            pass  # Don't fail the run if write fails

    return final


def main():
    parser = argparse.ArgumentParser(description="Director-pattern Multi-Agent Pipeline")
    parser.add_argument("--course", help="path to course markdown file")
    parser.add_argument("--all", action="store_true", help="run all courses in current repo")
    parser.add_argument("--stream", action="store_true", help="stream events to stdout")
    parser.add_argument("--max-iterations", type=int, default=3, help="max revision cycles")
    parser.add_argument("--json", action="store_true", help="output final state as JSON")
    # GitHub Actions / server-mode arguments
    parser.add_argument("--repo", help="path to repo root (for GitHub Actions incremental mode)")
    parser.add_argument("--batch", type=int, default=20, help="courses per run in repo mode (default 20)")
    parser.add_argument("--branch", default="main", help="branch for --repo mode (default main)")
    args = parser.parse_args()

    if args.course:
        print(f"Pipeline (Director pattern): {args.course}")
        print("=" * 60)
        # Reset token usage tracker for this run
        from _pipeline.llm_client import reset_usage_tracking, get_usage_report
        reset_usage_tracking()
        final = run_course(args.course, stream=args.stream,
                           max_iterations=args.max_iterations)
        print()
        print(f"Final decision: {final.decision}")
        print(f"Final score: {final.final_score}")
        print(f"Iterations: {final.iteration}")
        # Print token usage
        usage = get_usage_report()
        print(f"\nToken usage:")
        print(f"  LLM calls: {usage['calls']}")
        print(f"  Input tokens:  {usage['input_tokens']:>10,}")
        print(f"  Output tokens: {usage['output_tokens']:>10,}")
        print(f"  Total tokens:  {usage['total_tokens']:>10,}")
        if usage['by_model']:
            print(f"  By model:")
            for model, stats in usage['by_model'].items():
                print(f"    - {model}: {stats['calls']} calls, "
                      f"{stats['input_tokens']:,} in + {stats['output_tokens']:,} out")
        if args.json:
            from _pipeline.state import snapshot
            print(json.dumps(snapshot(final), ensure_ascii=False, indent=2))

    elif args.repo:
        # Server/CRON mode: incremental batch processing
        from _pipeline.llm_client import reset_usage_tracking, get_usage_report

        repo_root = Path(args.repo)
        branch = args.branch
        skip_dirs = {'.git', '_agents', '_pipeline', 'node_modules', '.github', '__pycache__'}

        # Get already-modified files (already processed)
        result = subprocess.run(
            ['git', 'status', '--porcelain'], cwd=repo_root, capture_output=True, text=True
        )
        modified = set()
        for line in result.stdout.strip().split('\n'):
            if line.startswith('M ') or line.startswith('?? '):
                path = line[3:].strip()
                if path.endswith('.md') and '_pipeline' not in path and 'review.json' not in path:
                    modified.add(path)

        # Find all courses
        all_courses = []
        for md in repo_root.rglob('*.md'):
            parts = md.parts[len(repo_root.parts):]
            if any(s in parts for s in skip_dirs):
                continue
            if md.name in ('README.md', 'AGENTS.md'):
                continue
            rel = str(Path(*parts))
            all_courses.append((md, rel))

        remaining = [(p, r) for p, r in all_courses if r not in modified]
        done = len(all_courses) - len(remaining)
        print(f'[{repo_root.name}] {done}/{len(all_courses)} done, {len(remaining)} remaining')

        if not remaining:
            print(f'[{repo_root.name}] All done!')
            sys.exit(0)

        batch = remaining[:args.batch]
        total_in = total_out = 0
        start = time.time()

        for i, (course_path, rel) in enumerate(batch, 1):
            print(f'[{i}/{len(batch)}] {rel}')
            reset_usage_tracking()
            t0 = time.time()
            try:
                final = run_course(str(course_path), stream=False, max_iterations=1)
                elapsed = time.time() - t0
                usage = get_usage_report()
                total_in += usage['input_tokens']
                total_out += usage['output_tokens']
                wrote = "✓" if (final.decision == 'APPROVED' and final.body) else ""
                status = f'APPROVED {final.final_score}' if final.decision == 'APPROVED' else f'{final.decision} {final.final_score}'
                print(f'  -> {status} ({elapsed:.0f}s, {usage["total_tokens"]:,} tok) {wrote}')
            except Exception as e:
                print(f'  -> ERROR: {e}')

        print(f'[{repo_root.name}] Batch: {len(batch)} processed in {time.time()-start:.0f}s')
        print(f'[{repo_root.name}] Tokens: {total_in:,}+{total_out:,}={total_in+total_out:,}')

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
