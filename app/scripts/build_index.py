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

# Optional subcategory mappings per repo (for better UI differentiation)
REPO_SUBCATEGORIES = {
    'HKU-BME-Bootcamp-OpenClaw': {
        '01_Phase1_LifeSciences': 'Phase 1: Life Sciences',
        '02_Phase2_Quantitative': 'Phase 2: Quantitative',
        '03_Phase3_Applications': 'Phase 3: Core BME Applications',
        '04_Phase4_Advanced_Research': 'Phase 4: Advanced Research',
        'Agents': 'OpenClaw Agents',
        '00_Planning': 'Planning',
    },
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

        # Special handling for HKU-BME-Bootcamp: each W01-W24 week folder
        # contains a notes/README.md that IS the course content
        if repo == 'HKU-BME-Bootcamp-OpenClaw':
            for top_dir in sorted(os.listdir(base)):
                if not os.path.isdir(os.path.join(base, top_dir)):
                    continue
                for week_dir in sorted(os.listdir(os.path.join(base, top_dir))):
                    if not (week_dir.startswith('W') and '_' in week_dir):
                        continue
                    week_path = os.path.join(base, top_dir, week_dir)
                    # Look for notes/README.md or {week_dir}.md
                    candidates = [
                        os.path.join(week_path, 'notes', 'README.md'),
                        os.path.join(week_path, 'readings', 'README.md'),
                        os.path.join(week_path, f'{week_dir}.md'),
                        os.path.join(week_path, 'COURSE.md'),
                    ]
                    for cand in candidates:
                        if os.path.isfile(cand):
                            try:
                                content = open(cand, encoding='utf-8').read()
                                if len(content) < 500:
                                    continue
                                info = extract_course_info(cand, content, repo)
                                # Override ID/title with week folder name
                                info['id'] = f"{repo}/{week_dir}"
                                # Extract clean title: remove "Week N Notes —" / "Readings —"
                                clean_title = info['title']
                                for prefix in ['Week ' + week_dir.split('_')[0][1:] + ' Notes — ',
                                               'Week ' + week_dir.split('_')[0][1:] + ' Readings — ']:
                                    clean_title = clean_title.replace(prefix, '')
                                # Extract course code from folder name (e.g., BMED1207 from W01_Intro_Chemistry_BMED1207)
                                import re as _re
                                code_match = _re.search(r'((?:BMED|BIOC|ENGG|BME)\d*)', week_dir)
                                course_code = code_match.group(1) if code_match else ''
                                # Parse title parts: W01_Intro_Chemistry_BMED1207 → "Intro Chemistry"
                                parts = week_dir.split('_')
                                # parts[0] = W01, parts[1..-2] = subject, parts[-1] = code
                                subject_parts = parts[1:-1] if len(parts) > 2 else parts[1:]
                                subject = ' '.join(subject_parts)
                                # Phase mapping
                                phase_map = {
                                    '01_Phase1_LifeSciences': 'Phase 1: Life Sciences',
                                    '02_Phase2_Quantitative': 'Phase 2: Quantitative',
                                    '03_Phase3_Applications': 'Phase 3: Core BME Applications',
                                    '04_Phase4_Advanced_Research': 'Phase 4: Advanced Research',
                                }
                                subcategory = phase_map.get(top_dir, top_dir)
                                # Build proper title (strip duplicate course code from subject)
                                if course_code:
                                    subject = subject.replace(course_code, '').strip()
                                subject = subject.replace('_', ' ').strip()
                                # Map common abbreviations
                                subject = subject.replace('Adv ', 'Advanced ').replace('TissueEng', 'Tissue Engineering')
                                info['title'] = f"{course_code} — {subject} (W{parts[0][1:]})" if course_code else f"{subject} (W{parts[0][1:]})"
                                info['subcategory'] = subcategory
                                info['course_code'] = course_code
                                info['week'] = f"W{parts[0][1:]}"
                                info['path'] = f"{repo}/{cand.replace(base, '')[1:]}"
                                info['url'] = f"https://github.com/yip-lgtm/{repo}/blob/main/{cand.replace(base, '')[1:]}"
                                all_courses.append(info)
                            except Exception as e:
                                pass
                            break  # one course per week

        # Generic: walk all .md files (except README.md, AGENTS.md, 00_*, agents/)
        for root, dirs, files in os.walk(base):
            if any(x in root for x in ('.git', '_agents', '_pipeline', '__pycache__', 'old_archive', 'node_modules', '/Agents/', '/00_Planning/')):
                continue
            # Skip BME week subfolder notes (already indexed above)
            if repo == 'HKU-BME-Bootcamp-OpenClaw' and '/W' in root and ('/notes' in root or '/readings' in root or '/code' in root or '/quiz' in root or '/deliverables' in root):
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
