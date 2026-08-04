#!/usr/bin/env python3
"""
Physics Self-Study Course Generation Pipeline Orchestrator.

Pipeline (5 agents):
  1. Researcher    → course_brief.json (HKUST/MIT OCW/arXiv, scholars, dates, constants)
  2. Data Extractor → course_data.json (objectives, prereq, themes, learning outcomes)
  3. Engineer      → course_body.md (5MM + 3DG + 10Q with detailed answers + 5DD + 10SL)
  4. Diagram       → 5 Mermaid diagrams inserted into course file
  5. Professor     → Quality gate review (APPROVED/REVISE/REJECT)

Run per course:
  python3 _pipeline/run_pipeline.py --course PHYS_3036

Review all:
  python3 _agents/professor_supervisor/review.py --all
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

PIPELINE_ROOT = Path(__file__).parent
AGENTS_ROOT = PIPELINE_ROOT.parent / '_agents'


def run_agent(agent_name: str, course: str) -> bool:
    print(f"\n→ Agent: {agent_name}")
    cmd = ['python3', str(AGENTS_ROOT / agent_name / 'lookup.py'), '--course', course]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ {agent_name} failed:\n{result.stderr}")
        return False
    print(f"  ✓ {agent_name} OK")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--course', help='course code, e.g. PHYS_3036')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    
    if args.course:
        print(f"Pipeline: {args.course}")
        print('='*60)
        agents = ['researcher', 'data_extractor', 'engineer', 'diagram', 'professor_supervisor']
        for a in agents:
            if not run_agent(a, args.course):
                print(f"\nPipeline FAILED at {a}")
                sys.exit(1)
        print(f"\n✓ Pipeline complete for {args.course}")
    
    if args.all:
        cmd = ['python3', str(AGENTS_ROOT / 'professor_supervisor' / 'review.py'), '--all']
        subprocess.run(cmd)


if __name__ == '__main__':
    main()
