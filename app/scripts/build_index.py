#!/usr/bin/env python3
"""
Build course index from all 6 bootcamp repos.
Output: src/data/courses.json
"""
import os, re, json
from pathlib import Path

REPOS = {
    'civil-bootcamp': '/workspace/civil-bootcamp',
    'PhysicsSelfStudy': '/workspace/PhysicsSelfStudy',
    'HKU-Harvard-History-Self-Study': '/workspace/HKU-Harvard-History-Self-Study',
    'psych-self-study-hku': '/workspace/psych-self-study-hku',
    'mech-Eng-Bootcamp': '/workspace/mech-Eng-Bootcamp',
    'HKU-BME-Bootcamp-OpenClaw': '/workspace/HKU-BME-Bootcamp-OpenClaw',
}

# Map repo to category
REPO_CATEGORIES = {
    'civil-bootcamp': 'Engineering',
    'PhysicsSelfStudy': 'Physics',
    'HKU-Harvard-History-Self-Study': 'History',
    'psych-self-study-hku': 'Psychology',
    'mech-Eng-Bootcamp': 'Mech-Eng',
    'HKU-BME-Bootcamp-OpenClaw': 'BME',
}


def extract_course_info(path, content, repo):
    """Extract course metadata from markdown content."""
    # Title from first H1
    title_m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else os.path.basename(path).replace('.md', '')

    # 5MM — first 3 mental models from Q1
    q1_match = re.search(r'## 問題 1.*?(?=## 問題 2|---|\Z)', content, re.DOTALL)
    models = []
    if q1_match:
        items = re.findall(r'\d+\.\s+\*\*(.+?)\*\*', q1_match.group(0)[:2000])
        models = items[:5]

    # 3DG — disagreements from Q2
    q2_match = re.search(r'## 問題 2.*?(?=## 問題 3|---|\Z)', content, re.DOTALL)
    disagreements = []
    if q2_match:
        items = re.findall(r'\d+\.\s+\*\*(.+?)\*\*', q2_match.group(0)[:1500])
        disagreements = items[:3]

    # Scholars with years
    scholars = list(set(re.findall(
        r'\b(Newton|Einstein|Maxwell|Bohr|Schrödinger|Dirac|Feynman|Pauli|Heisenberg|'
        r'Boltzmann|Fermi|Bose|Hawking|Penrose|Stokes|Reynolds|von Kármán|'
        r'Braudel|Hobsbawm|Anderson|Tilly|von Ranke|Bloch|'
        r'Griffiths|Sakurai|Ashcroft|Mermin|Kittel|'
        r'Wasserman|Hastie|Boyd|Vandenberghe|'
        r'Sheffi|Daganzo|Wardrop|Newell|'
        r'Porter|Christensen|'
        r'Timoshenko|Crandall|Gere|Boresi|'
        r'Hemond|Sigmond|)\s+(\d{4})',
        content
    )))

    # Equations count
    eq_count = len(re.findall(r'\$\$.*?\$\$', content, re.DOTALL))

    # Mermaid count
    mermaid_count = len(re.findall(r'```mermaid', content))

    # Chinese character count
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', content))

    # Lines
    lines = content.count('\n')

    return {
        'id': f"{repo}/{path.replace(REPOS[repo], '')[1:]}",
        'title': title,
        'repo': repo,
        'category': REPO_CATEGORIES[repo],
        'path': f"{repo}/{path.replace(REPOS[repo], '')[1:]}",
        'url': f"https://github.com/yip-lgtm/{repo}/blob/main/{path.replace(REPOS[repo], '')[1:]}",
        'lines': lines,
        'models': models,
        'disagreements': disagreements,
        'scholars': [f"{s[0]} {s[1]}" for s in scholars[:5]],
        'equations': eq_count,
        'mermaid': mermaid_count,
        'chinese_chars': cn_chars,
    }


def main():
    all_courses = []
    for repo, base in REPOS.items():
        if not os.path.exists(base):
            print(f"Skip {repo} (not exists)")
            continue
        for root, dirs, files in os.walk(base):
            if any(x in root for x in ('.git', '_agents', '_pipeline', '__pycache__', 'old_archive', 'node_modules')):
                continue
            for f in files:
                if f.endswith('.md') and f != 'README.md' and f != 'AGENTS.md' and not f.startswith('00_'):
                    path = os.path.join(root, f)
                    try:
                        content = open(path, encoding='utf-8').read()
                        if len(content) < 500:
                            continue  # skip very short files
                        info = extract_course_info(path, content, repo)
                        all_courses.append(info)
                    except Exception as e:
                        pass

    # Sort by category then title
    all_courses.sort(key=lambda x: (x['category'], x['title']))

    out_path = Path('src/data/courses.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(all_courses),
            'by_category': {cat: sum(1 for c in all_courses if c['category'] == cat) for cat in REPO_CATEGORIES.values()},
            'courses': all_courses,
        }, f, ensure_ascii=False, indent=2)

    print(f"Indexed {len(all_courses)} courses")
    for cat, count in {cat: sum(1 for c in all_courses if c['category'] == cat) for cat in REPO_CATEGORIES.values()}.items():
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
