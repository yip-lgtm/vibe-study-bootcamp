"""
Agent Node: Researcher (LLM-based)

Reads: course_path (source markdown)
Writes: brief = {primary_sources, scholars_with_years, key_numbers, key_dates, ...}

Strategy: Use LLM to produce a structured brief from the source markdown.
If no API key is available, fall back to deterministic regex-based extraction.
"""
from __future__ import annotations
from typing import Any, Dict, List
import re
import os

from ..state import PipelineState
from ..llm_client import complete, detect_provider, LLMResponse


SYSTEM_PROMPT_RESEARCHER = """You are the **Researcher** agent in a multi-agent course-generation pipeline.

Your job: read a course markdown file and produce a structured **brief** of verified primary sources, real scholars (with years), and key numbers.

Strict rules:
- ONLY cite scholars with verifiable publication years (e.g., "Newton 1687", "Stokes 1851", "Bourouiba 2021")
- ONLY cite real primary sources (MIT OCW, arXiv, university catalogs, peer-reviewed journals, ISBNs)
- Do NOT fabricate DOIs, ISBNs, or arXiv IDs
- If a claim is uncertain, omit it rather than guess

Output format (return ONLY this JSON, no commentary):
```json
{
  "primary_sources": [
    {"title": "...", "url_or_isbn": "...", "type": "OCW|arXiv|journal|textbook|catalog"}
  ],
  "scholars_with_years": ["Newton 1687", "Stokes 1851", "Bourouiba 2021"],
  "key_numbers": ["3×10^8 m/s", "6.022×10^23 /mol", "9.81 m/s²"],
  "key_dates": [1687, 1851, 1905, 1926, 2021]
}
```

Limit output to ~20 primary sources, ~30 scholars, ~30 numbers."""


def _llm_researcher(state: PipelineState, content: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """LLM-based researcher: ask LLM to produce structured brief."""
    writer = config.get("writer")
    if writer:
        writer({"type": "llm_call", "agent": "researcher", "phase": "start"})

    # Truncate content to fit context window (keep first 30K chars)
    content_for_llm = content[:30000] if len(content) > 30000 else content

    user_msg = (
        f"Course path: {state.course_path}\n"
        f"Course code: {state.course_code}\n\n"
        f"--- Source content ({len(content):,} chars, "
        f"{content.count(chr(10)):,} lines) ---\n\n"
        f"{content_for_llm}\n\n"
        f"--- End of source ---\n\n"
        f"Produce the structured brief JSON."
    )

    cfg = detect_provider()
    resp = complete(
        messages=[{"role": "user", "content": user_msg}],
        system=SYSTEM_PROMPT_RESEARCHER,
        max_tokens=4096,
        temperature=0.2,  # low for factual extraction
    )

    if writer:
        writer({
            "type": "llm_call", "agent": "researcher", "phase": "end",
            "tokens": resp.input_tokens + resp.output_tokens,
            "latency_ms": resp.latency_ms,
            "model": resp.model,
        })

    # Parse JSON response
    import json
    text = resp.text.strip()
    # Strip ```json ... ``` fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)

    try:
        brief = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                brief = json.loads(m.group(0))
            except json.JSONDecodeError:
                brief = {
                    "primary_sources": [],
                    "scholars_with_years": [],
                    "key_numbers": [],
                    "key_dates": [],
                    "_raw_response": text[:1000],
                    "_error": "Failed to parse JSON",
                }
        else:
            brief = {
                "primary_sources": [],
                "scholars_with_years": [],
                "key_numbers": [],
                "key_dates": [],
                "_raw_response": text[:1000],
                "_error": "No JSON found",
            }

    # Normalize
    brief["source_chars"] = len(content)
    brief["source_lines"] = content.count("\n")
    brief["model_used"] = resp.model
    brief["llm_tokens"] = resp.input_tokens + resp.output_tokens
    brief["llm_latency_ms"] = resp.latency_ms

    return brief


# ===== Deterministic fallback (regex-based) =====

SCHOLAR_NAMES = (
    r"Newton|Einstein|Maxwell|Bohr|Dirac|Feynman|Heisenberg|"
    r"Boltzmann|Fermi|Bose|Hawking|Penrose|Stokes|Reynolds|"
    r"Timoshenko|Terzaghi|Bernoulli|Coulomb|"
    r"Strang|Knuth|Bourouiba|"
    r"Fourier|Lagrange|Hamilton|"
    r"Watson|Crick|Darwin|Mendel|"
    r"Landau|Lifshitz|Hemond|Schwarzenbach|"
    r"Griffiths|Sakurai|Morse|Feshbach|"
    r"Arfken|Weber|Harris|Marsden|Apostol|Spivak|"
    r"Pauling|Henderson|Hasselbalch|Arrhenius|"
    r"Hubbard|"
    r"Schiff|Shankar|Napolitano|Zee|Schwartz|"
    r"Bogoliubov|Shirkov|Cheng|Li|Jackson|Zangwill|"
    r"Brillouin|Kramers|Kronig|Polchinski|Witten|"
    r"Eddington|Wald|"
    r"Shannon|Hamming|Turing|vonNeumann|"
    r"Gauss|Riemann|Lebesgue|Stieltjes|"
    r"Curie|Rontgen|Becquerel|Rutherford|"
    r"Hardy|Weinberg|"
    r"Mandelbrot|Faraday|Ohm|Kirchhoff|Joule|Watt|Hertz|"
    r"Plato|Aristotle|Euclid|Archimedes|Pythagoras|"
    r"Brahe|Kepler|Galileo|Copernicus|"
    r"Heaviside|Gibbs|"
    r"Cantor|Dedekind|Weierstrass|Abel|Galois|"
    r"Cormen|Dijkstra|Hoare|"
    r"Hestenes|Stiefel|Householder|Golub|Wilkinson|"
    r"Smagorinsky|Lilly|Deardorff|"
    r"HongKong|"
    r"HKU|MIT|UCLA|CUHK|UST|HKUST"
)
SCHOLAR_PATTERN = re.compile(r"\b(?:" + SCHOLAR_NAMES + r")\s*[\(]?(\d{4})[\)]?")


def _deterministic_researcher(state: PipelineState, content: str) -> Dict[str, Any]:
    """Deterministic fallback: regex-based extraction."""
    # Primary sources
    primary_sources = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith(">") and (
            "MIT OCW" in line or "arXiv" in line or "DOI" in line
            or "ISBN" in line or "Primary" in line or "Source" in line
        ):
            primary_sources.append(line.lstrip("> ").strip())

    # Scholars
    scholars_with_years = list(set(SCHOLAR_PATTERN.findall(content)))

    # Numbers with units
    numbers = re.findall(
        r"\b\d+\.?\d*\s*(?:m|kg|s|K|Hz|kHz|MHz|GHz|"
        r"m/s|m/s\^2|N|J|W|eV|MeV|GeV|Pa|kPa|MPa|GPa|"
        r"mol|mmol|kg/mol|g/mol)",
        content,
    )

    years = sorted(set(int(y) for y in scholars_with_years if y.isdigit()))

    return {
        "primary_sources": primary_sources[:20],
        "scholars_with_years": [f"{y}" for y in scholars_with_years[:30]],
        "key_numbers": numbers[:30],
        "key_dates": years,
        "source_chars": len(content),
        "source_lines": content.count("\n"),
        "_method": "deterministic",
    }


# ===== Main node function =====

def researcher_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Researcher node: produces a structured brief.
    - LLM-based if API key is set
    - Deterministic regex-based fallback otherwise
    """
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "researcher", "course": state.course_code})

    try:
        with open(state.course_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"errors": [f"[researcher] Cannot read {state.course_path}: {e}"]}

    cfg = detect_provider()
    use_llm = bool(cfg.api_key) and not config.get("force_deterministic", False)

    if use_llm:
        try:
            brief = _llm_researcher(state, content, config)
            method = "llm"
        except Exception as e:
            if writer:
                writer({"type": "llm_error", "agent": "researcher", "error": str(e)[:200]})
            brief = _deterministic_researcher(state, content)
            method = "deterministic_fallback"
    else:
        brief = _deterministic_researcher(state, content)
        method = "deterministic"

    if writer:
        writer({
            "type": "agent_end", "agent": "researcher",
            "method": method,
            "result": (
                f"{len(brief.get('primary_sources', []))} sources, "
                f"{len(brief.get('scholars_with_years', []))} scholars, "
                f"{len(brief.get('key_numbers', []))} numbers"
            ),
        })

    return {"brief": brief, "events": [{
        "type": "researcher_method",
        "data": {"method": method, "course": state.course_code},
    }]}
