#!/usr/bin/env python3
"""
Physics Self-Study — Professor Supervisor Quality Gate Reviewer
Reviews every course file against the 10 quality gates.
Output: APPROVED / REVISE / REJECT with rubric breakdown.
"""
import os
import re
import sys
import json
import argparse
from pathlib import Path


# Quality gate definitions
TEMPLATE_MARKERS = [
    r'\[TBD\]', r'待補充', r'placeholder', r'Lorem ipsum',
    r'CORE_DEEPDIVE_ONE', r'CORE_DEEPDIVE_TWO', r'CORE_DEEPDIVE_THREE',
    r'T0 — Core', r'T1 — Methods', r'T2 — Applications',
    r'PLACEHOLDER', r'\[TODO\]', r'Fixme', r'fixme',
    r'^\s*XXX\b', r'\$\{.*\}',
]

# Physics scholars (with rough year hints)
SCHOLAR_HINT = re.compile(
    r'\b('
    r'Newton|Euler|Lagrange|Hamilton|Maxwell|Boltzmann|Fourier|'
    r'Betti|Cauchy|Poisson|Navier|Stokes|Reynolds|Prandtl|von Kármán|'
    r'Bohr|Heisenberg|Schrödinger|Dirac|Fermi|Bose|Einstein|Planck|'
    r'Pauli|Born|Jordan|Wien|Hertz|Rutherford|Chadwick|Feynman|'
    r'Wheeler|von Neumann|Wigner|Bethe|Weisskopf|Dyson|Schwinger|'
    r'Tomonaga|Feynman|Taylor|Penrose|Hawking|Thorne|Bragg|Bohr|'
    r'Compton|Davisson|Germer|Galileo|Huygens|Young|Fresnel|Hamilton|'
    r'Gibbs|Boltzmann|Maxwell|Fermi|Dirac|Anderson|BCS|Bardeen|'
    r'Cooper|Schrieffer|Josephson|Anderson|Laughlin|Thouless|Kosterlitz|'
    r'Wen|Wilczek|Polchinski|Witten|Gross|Politzer|Wilczek|'
    r'Curie|Lorentz|Fitzgerald|Larmor|Liénard|Wiechert|Abraham|'
    r'Bohr|Sommerfeld|Heisenberg|Schrödinger|Dirac|von Neumann|'
    r'Coulomb|Ampère|Ohm|Faraday|Henry|Tesla|Weber|'
    r'Boltzmann|Maxwell|Gibbs|Planck|Einstein|Bose|Einstein|'
    r'Landau|Lifshitz|Feynman|Sakurai|Griffiths|Szego|Hassani|'
    r'Schwartz|Tong|Cohen|Tannoudji|Diu|Laloë|Sakurai|'
    r'Zee|Weinberg|Peskin|Schroeder|Srednicki|Maggiore|'
    r'Wald|Misner|Thorne|Wheeler|Penrose|Hawking|Ellis|'
    r'Stephen Hawking|Roger Penrose|Kip Thorne|'
    r'Condon|Shortley|Bethe|Salpeter|Hylleraas|Bethe|'
    r'Bohr|Mott|Wilson|Sommerfeld|Pauling|Slater|'
    r'Ashcroft|Mermin|Kittel|Simon|'
    r'Yao|Dennery|Krivine|Reichl|'
    r'Sethi|Hubbard|White|Ashcroft|Mahan|'
    r'Berry|Shapere|Wilczek|Avron|'
    r'\bSin\b|\bCao\b|\bChen\b|\bLiu\b|\bWong\b|\bTam\b'
    r')\b'
)

YEAR_HINT = re.compile(r'\b(1[6-9]\d{2}|20\d{2})\b')


def gate1_length(content: str) -> int:
    lines = content.count('\n')
    if lines >= 400:
        return 10
    if lines >= 300:
        return 7
    if lines >= 200:
        return 4
    return 0


def gate2_format(content: str) -> int:
    score = 0
    if re.search(r'問題 1|心智模型|mental model|5.*core', content, re.IGNORECASE):
        score += 3
    if re.search(r'問題 2|根本分歧|disagree|divergence', content, re.IGNORECASE):
        score += 3
    if re.search(r'問題 3|深度問題|10.*question', content, re.IGNORECASE):
        score += 3
    if re.search(r'深入|deep dive|Deep Dive', content, re.IGNORECASE):
        score += 3
    if re.search(r'解答|solution|Solution', content, re.IGNORECASE):
        score += 3
    return min(score, 15)


def gate3_citations(content: str) -> int:
    scholars = set(SCHOLAR_HINT.findall(content))
    years = YEAR_HINT.findall(content)
    if len(scholars) >= 8 and len(years) >= 5:
        return 15
    if len(scholars) >= 5 and len(years) >= 3:
        return 12
    if len(scholars) >= 3:
        return 8
    if len(scholars) >= 1:
        return 4
    return 0


def gate4_specificity(content: str) -> int:
    equations = re.findall(r'\$\$.*\$\$|\$[^$\n]+\$', content)
    numbers = re.findall(r'\b\d+\.?\d*\b', content)
    if len(equations) >= 8 and len(numbers) >= 30:
        return 15
    if len(equations) >= 5 and len(numbers) >= 15:
        return 12
    if len(equations) >= 3 and len(numbers) >= 10:
        return 8
    if len(equations) >= 1:
        return 4
    return 0


def gate5_bilingual(content: str) -> int:
    cn = re.findall(r'[\u4e00-\u9fff]', content)
    if len(cn) >= 500:
        return 10
    if len(cn) >= 200:
        return 7
    if len(cn) >= 100:
        return 4
    return 0


def gate6_no_placeholder(content: str) -> int:
    hits = 0
    for marker in TEMPLATE_MARKERS:
        if re.search(marker, content, re.IGNORECASE | re.MULTILINE):
            hits += 1
    if hits == 0:
        return 10
    if hits == 1:
        return 6
    if hits <= 3:
        return 3
    return 0


def gate7_mermaid(content: str) -> int:
    blocks = re.findall(r'```mermaid', content)
    if len(blocks) >= 5:
        return 10
    if len(blocks) >= 3:
        return 6
    if len(blocks) >= 1:
        return 3
    return 0


def gate8_solutions(content: str) -> int:
    numbered = re.findall(r'(?:^|\n)\s*\d+[\.\)、]\s+\S', content)
    if len(numbered) >= 30:
        return 10
    if len(numbered) >= 20:
        return 7
    if len(numbered) >= 12:
        return 5
    if len(numbered) >= 6:
        return 3
    return 0


def gate9_deep_dives(content: str) -> int:
    dives = re.findall(
        r'(?:深入\s*\d|Deep\s+Dive\s*[IVX\d]|##\s*\d+\.\s+\S|###\s*\d+\.\s+\S)',
        content, re.IGNORECASE
    )
    if len(dives) >= 5:
        return 5
    if len(dives) >= 3:
        return 3
    if len(dives) >= 1:
        return 1
    return 0


def gate10_no_template(content: str) -> int:
    bad = re.findall(r'T\d\s*—\s*(Core|Methods|Applications)', content)
    if len(bad) == 0:
        return 5
    if len(bad) <= 2:
        return 3
    return 0


def review(file_path: str) -> dict:
    content = Path(file_path).read_text(encoding='utf-8')
    gates = {
        'G1_length': gate1_length(content),
        'G2_format': gate2_format(content),
        'G3_citations': gate3_citations(content),
        'G4_specificity': gate4_specificity(content),
        'G5_bilingual': gate5_bilingual(content),
        'G6_no_placeholder': gate6_no_placeholder(content),
        'G7_mermaid': gate7_mermaid(content),
        'G8_solutions': gate8_solutions(content),
        'G9_deep_dives': gate9_deep_dives(content),
        'G10_no_template': gate10_no_template(content),
    }
    total = sum(gates.values())
    if total >= 85:
        decision = 'APPROVED'
    elif total >= 70:
        decision = 'REVISE'
    else:
        decision = 'REJECT'
    return {
        'file': file_path,
        'score': total,
        'decision': decision,
        'gates': gates,
        'lines': content.count('\n'),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--course', help='single course file')
    parser.add_argument('--all', action='store_true', help='review all course files')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    
    if args.course:
        result = review(args.course)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n{result['file']}")
            print(f"  Score: {result['score']}/100  Decision: {result['decision']}")
            print(f"  Lines: {result['lines']}")
            for k, v in result['gates'].items():
                print(f"    {k:25s} {v:3d}")
        return result['decision']
    
    if args.all:
        # Find all .md files in 4 phase dirs
        course_files = []
        phase_dirs = ['01_BSc_Physics', '02_MSc_DataDriven_Modeling', '03_MSc_Physics', '04_MPhil_PhD_Prep']
        for phase in phase_dirs:
            if os.path.exists(phase):
                for root, _, files in os.walk(phase):
                    for f in files:
                        if f.endswith('.md'):
                            course_files.append(os.path.join(root, f))
        
        results = []
        decision_count = {'APPROVED': 0, 'REVISE': 0, 'REJECT': 0}
        for f in sorted(course_files):
            r = review(f)
            results.append(r)
            decision_count[r['decision']] += 1
            if r['decision'] != 'APPROVED':
                marker = '⚠️' if r['decision'] == 'REVISE' else '❌'
                print(f"{marker} {r['score']:3d}  {f}  [{r['decision']}]")
        
        print(f"\n{'='*60}")
        print(f"Total: {len(results)} files")
        print(f"  APPROVED: {decision_count['APPROVED']}")
        print(f"  REVISE:   {decision_count['REVISE']}")
        print(f"  REJECT:   {decision_count['REJECT']}")
        
        if args.json:
            os.makedirs('_pipeline', exist_ok=True)
            with open('_pipeline/review.json', 'w', encoding='utf-8') as fp:
                json.dump(results, fp, indent=2, ensure_ascii=False)
            print(f"\nDetailed report: _pipeline/review.json")


if __name__ == '__main__':
    main()
