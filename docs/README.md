# Documentation

> Detailed documentation for vibe-study-bootcamp

## Quick Links

- [Main README](../README.md) — Overview
- [Charter](../proposal/CHARTER.md) — Project charter
- [Roadmap](../proposal/ROADMAP.md) — Timeline
- [Contributing](../proposal/CONTRIBUTING.md) — 點樣 contribute
- [Vibe Coding Workflow](../workflow/VIBE_CODING.md) — Coding methodology
- [Pipeline Guide](../workflow/PIPELINE_GUIDE.md) — Multi-Agent pipeline

## Architecture

### Multi-Agent Pipeline

```
User Request
    ↓
1. Researcher → course_brief.json (primary sources)
    ↓
2. Data Extractor → course_data.json (objectives, themes)
    ↓
3. Engineer → course_body.md (5MM/3DG/10Q/5DD/10SL/5MR)
    ↓
4. Diagram → + 5 Mermaid diagrams
    ↓
5. Professor Supervisor → APPROVED/REVISE/REJECT
    ↓
Publish (if APPROVED)
```

### Quality Gates (10 gates, 100 points)

See [Pipeline Guide](../workflow/PIPELINE_GUIDE.md) for full reference.

## API Reference

### Review Script

```bash
python3 _agents/professor_supervisor/review.py \
    --course <path>           # Single course
    --all                     # All courses
    --json                    # JSON output
```

### Pipeline Orchestrator

```bash
python3 _pipeline/run_pipeline.py \
    --input <course_data.json>
```

---

*2026-08 · Auto-generated*
