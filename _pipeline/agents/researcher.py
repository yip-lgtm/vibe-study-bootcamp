"""
Agent Node: Researcher (LangGraph-style)

Reads: course_path (source markdown)
Writes: brief = {primary_sources, key_authors, key_numbers, key_dates, ...}

This is a node in the StateGraph. It takes the current state + config
and returns a dict of updates (applied via reducers by the graph runtime).

Reference: OpenMAIC's `lib/orchestration/registry/types.ts` -- AgentConfig pattern
inspired the structured brief output.
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re

from ..state import PipelineState, emit_event, snapshot


# Scholar regex: common CEE/STEM scholars with years.
# Use ASCII-only names to avoid encoding issues.
SCHOLAR_NAMES = (
    r"Newton|Einstein|Maxwell|Bohr|Dirac|Feynman|Heisenberg|"
    r"Boltzmann|Fermi|Bose|Hawking|Penrose|Stokes|Reynolds|vonKarman|"
    r"Hemond|Schwarzenbach|Stumm|Morgan|"
    r"Griffiths|Sakurai|Ashcroft|Mermin|Kittel|"
    r"Hestenes|Stiefel|Householder|Golub|Wilkinson|"
    r"Timoshenko|Crandall|Gere|Boresi|"
    r"Casagrande|Terzaghi|Darcy|Bernoulli|Coulomb|Mohr|"
    r"Mandelbrot|Faraday|Ohm|Kirchhoff|Joule|Watt|Hertz|"
    r"Plato|Aristotle|Euclid|Archimedes|Pythagoras|"
    r"Pauling|Henderson|Hasselbalch|Arrhenius|"
    r"Watson|Crick|Darwin|Mendel|"
    r"Strang|Knuth|Cormen|Dijkstra|Hoare|"
    r"Bourouiba|Wells|"
    r"Hubbard|Marsden|Apostol|Spivak|"
    r"Fourier|Lagrange|Hamilton|"
    r"Landau|Lifshitz|"
    r"Schiff|"
    r"Shankar|"
    r"Napolitano|"
    r"Zee|"
    r"Schwartz|"
    r"Bogoliubov|Shirkov|"
    r"Cheng|Li|"
    r"Jackson|"
    r"Zangwill|"
    r"Morse|Feshbach|"
    r"Arfken|Weber|Harris|"
    r"Gottfried|Yan|"
    r"Merzbacher|"
    r"Ryder|Itzykson|Zuber|"
    r"Peskin|Schroeder|"
    r"Eddington|Penrose|Wald|"
    r"Brillouin|Kramers|Kronig|"
    r"Polchinski|Witten|"
    r"Greiner|Muller|"
    r"Hardy|Weinberg|"
    r"Shannon|Hamming|Turing|vonNeumann|"
    r"Gauss|Riemann|Lebesgue|Stieltjes|"
    r"Cantor|Dedekind|Weierstrass|"
    r"Abel|Galois|Burnside|"
    r"Knuth|Steinhaus|Erdos|"
    r"Sagan|Christensen|"
    r"MITOCW|"
    r"Smith|Joule|"
    r"Hubbard|"
    r"Merzbacher|"
    r"Brahe|Kepler|Galileo|Copernicus|"
    r"Curie|Rontgen|Becquerel|Rutherford|"
    r"Heaviside|Gibbs|"
    r"Hamilton|"
    r"Taylor|Whittaker|"
    r"Hong|Kong|"
    r"HongKong|"
    r"HKU|MIT|UCLA|CUHK|UST|HKUST|"
    r"Deisenroth|Faisal|"
    r"Stroud|Boas|"
    r"Boyd|Vandenberghe|"
    r"Conway|"
    r"Shannon|"
    r"Gibbs|Boltzmann|"
    r"Keenan|"
    r"Levenspiel|"
    r"Singh|Holman|"
    r"Geankoplis|"
    "Peters|Timmermann|"
    r"Whitaker|Barron|"
    r"Zemansky|Dittman|"
    r"Reid|Sherwood|"
    r"Felder|Denny|"
    r"Perry|Green|"
    r"Cengel|Boles|"
    r"Kaviany|"
    r"Bejan|"
    r"Kays|Crawford|"
    r"Incropera|DeWitt|"
    r"Modest|"
    r"Holman|"
    r"Bergman|Lavine|"
    r"Schmidt|"
    r"Carey|"
    r"Touloukian|"
    r"Bird|Stewart|Lightfoot|"
    r"Deen|"
    r"Bruus|"
    r"Patankar|"
    r"Ferziger|Peric|"
    r"Pope|"
    r"Wilcox|"
    r"Davidson|"
    r"Monin|Yaglom|"
    r"Tennekes|Lumley|"
    r"Pope|"
    r"Davidson|"
    r"Yeung|"
    r"Kundu|Cohen|Dowling|"
    r"White|"
    r"Blevins|"
    r"Naik|Patel|"
    r"Vanka|"
    r"Shen|"
    r"Hussain|"
    r"Choudhuri|"
    r"Boyd|Sanderson|"
    r"Lee|Woods|"
    r"Higdon|"
    r"Sagani|Lee|"
    r"Socolofsky|Jorgensen|"
    r"Davis|Cornwell|"
    r"Choi|Lam|"
    r"Ferziger|"
    r"Patel|"
    r"Rey|Liou|"
    r"Zeman|"
    r"Sandberg|"
    r"Carver|"
    r"Boyd|"
    r"McCarty|"
    r"Park|Livingston|"
    r"Schetz|Bowden|"
    r"Mattingly|"
    r"Spalding|"
    r"Crowe|Elger|"
    r"Munson|"
    r"Potter|Wiggert|"
    r"Zikanov|"
    r"Kundu|"
    r"White|"
    r"Kundu|"
    r"Pozrikidis|"
    r"Trinh|"
    r"Batchelor|"
    r"Monin|"
    r"Tritton|"
    r"Landau|Lifshitz|"
    r"White|"
    r"Fox|McDonald|"
    r"McComb|"
    r"Lesieur|"
    r"Davidson|"
    r"Fernando|"
    r"Cushman-Roisin|Becker|"
    r"Pedlosky|"
    r"Vallis|"
    r"Holton|"
    r"Salby|"
    r"Salmon|"
    r"Cushman-Roisin|"
    r"Pedlosky|"
    r"Holton|"
    r"Wallace|Hobbs|"
    r"Coiffier|"
    r"Holton|"
    r"Lin|"
    r"Kundu|"
    r"Curry|"
    r"Webster|"
    r"Saltzman|"
    r"Stensrud|"
    r"Cotton|"
    r"Bluestein|"
    r"Markowski|"
    r"Raymond|"
    r"Houze|"
    r"Doswell|"
    r"Markowski|"
    r"Schultz|"
    r"Schultz|"
    r"Bohren|Baten|"
    r"Young|"
    r"Liou|"
    r"Salby|"
    r"Holton|"
    r"Danielson|"
    r"Hartmann|"
    r"Curry|"
    r"Webster|"
    r"Peixoto|"
    r"Oort|"
    r"Lorenz|"
    r"Charney|"
    r"Eady|"
    r"Smagorinsky|"
    r"Lorenz|"
    r"Palmer|"
    r"Platzman|"
    r"Wiin-Nielsen|"
    r"Smagorinsky|"
    r"Lilly|"
    r"Deardorff|"
    r"Wyngaard|"
    r"Moeng|"
    r"Sullivan|"
    r"McComb|"
    r"Monin|Yaglom|"
    r"Frisch|"
    r"Kraichnan|"
    r"Batchelor|"
    r"Townsend|"
    r"Monin|"
    r"Tennekes|Lumley|"
    r"Hinze|"
    r"McComb|"
    r"Libby|"
    r"Williams|"
    r"Pope|"
    r"Davidson|"
    r"Yeung|"
    r"Sreenivasan|"
    r"Antonia|"
    r"Dimotakis|"
    r"Bell|"
    r"Kennedy|"
    r"Chhabra|"
    r"Schmitt|"
    r"Huchet|"
    r"Tropea|"
    r"Yarin|"
    r"Foss|"
    r"Tropea|"
    r"Summer|"
    r"Foss|"
    r"Michaelides|"
    r"Patel|"
    r"Sommerfeld|"
    r"Prandtl|"
    r"Schlichting|"
    r"White|"
    r"Kays|Crawford|"
    r"Bejan|"
    r"Incropera|"
    r"Modest|"
    r"Bergman|"
    r"Kays|"
    r"Tao|"
    r"Fox|"
    r"McDonald|"
    r"White|"
    r"Tao|"
    r"Batchelor|"
    r"Landau|Lifshitz|"
    r"Happel|Brenner|"
    r"Clift|Grace|Weber|"
    r"Michaelides|"
    r"Fan|Zhu|"
    r"Kuan|"
    r"Walker|"
    r"Socolofsky|Jorgensen|"
    r"Libby|"
    r"Williams|"
    r"Zeman|"
    r"Karagozian|"
    r"Choudhuri|"
    r"Yu|Zhou|"
    r"Zhou|"
    r"Zhou|"
    r"Hill|"
    r"Yih-Hong|"
    r"Chan|"
    r"Lam|"
    r"Lam|"
    r"Li|"
    r"Zhang|"
    r"Wang|"
    r"Chen|"
    r"Liu|"
    r"Yang|"
    r"Huang|"
    r"Zhu|"
    r"Yu|"
    r"Xu|"
    r"Lin|"
    r"Ye|"
    r"HongKong|"
    r"Hong|Kong"
)
SCHOLAR_PATTERN = re.compile(r"\b(?:" + SCHOLAR_NAMES + r")\s*[\(]?(\d{4})[\)]?")


def researcher_node(state: PipelineState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Researcher node: scans source markdown for primary sources,
    real scholars with years, and key numbers.
    """
    writer = config.get("writer")
    if writer:
        writer({"type": "agent_start", "agent": "researcher", "course": state.course_code})

    # Read source file
    try:
        with open(state.course_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"errors": [f"[researcher] Cannot read {state.course_path}: {e}"]}

    # Extract primary sources: lines starting with > (blockquotes) or
    # lines containing MIT OCW / arXiv / DOI / ISBN / Primary Source
    primary_sources: List[str] = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith(">") and (
            "MIT OCW" in line or "arXiv" in line or "DOI" in line
            or "ISBN" in line or "Primary" in line or "Source" in line
        ):
            primary_sources.append(line.lstrip("> ").strip())

    # Extract scholars with years
    scholars_with_years = list(set(SCHOLAR_PATTERN.findall(content)))

    # Extract numbers with units (very rough)
    numbers = re.findall(
        r"\b\d+\.?\d*\s*(?:m|kg|s|K|Hz|kHz|MHz|GHz|"
        r"m/s|m/s\^2|N|J|W|eV|MeV|GeV|Pa|kPa|MPa|GPa|"
        r"mol|mmol|kg/mol|g/mol)",
        content,
    )

    # Extract key dates
    years = sorted(set(int(y) for y in scholars_with_years if y.isdigit()))

    brief = {
        "primary_sources": primary_sources[:20],
        "scholars_with_years": [f"{y}" for y in scholars_with_years[:30]],
        "key_numbers": numbers[:30],
        "key_years": years,
        "source_chars": len(content),
        "source_lines": content.count("\n"),
    }

    if writer:
        writer({
            "type": "agent_end", "agent": "researcher",
            "result": (
                f"{len(brief['primary_sources'])} sources, "
                f"{len(brief['scholars_with_years'])} scholar-years, "
                f"{len(brief['key_numbers'])} numbers"
            ),
        })

    return {"brief": brief}
