#!/usr/bin/env node
/**
 * sync-courses.js
 * 
 * Scans all 6 bootcamp repos and generates courses.json for the web app.
 * Run: node scripts/sync-courses.js
 * 
 * Repo types:
 *   - "root": top-level .md files = courses (Civil, Physics, History)
 *   - "subdir": week subdirs with notes/readings/quiz = courses (BME)
 *   - "indexed": every .md file = course entry (Psych)
 */
const { execSync } = { execSync: require('child_process').execSync };
const fs = require('fs');
const path = require('path');

const REPOS = [
  {
    name: 'civil-bootcamp',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/civil-bootcamp.git',
    category: 'Civil Engineering',
    branch: 'main',
    type: 'glob',
    patterns: ['MIT_CEE_*/**/*.md', 'MIT_CEE_*.md', 'MIT_CEE_*/*.md'],
  },
  {
    name: 'PhysicsSelfStudy',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/PhysicsSelfStudy.git',
    category: 'Physics',
    branch: 'master',
    type: 'glob',
    patterns: [
      '01_BSc_Physics/**/*.md',
      '02_MSc_DataDriven_Modeling/**/*.md',
      '03_MSc_Physics/**/*.md',
      '04_MPhil_PhD_Prep/**/*.md',
    ],
  },
  {
    name: 'HKU-Harvard-History-Self-Study',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/HKU-Harvard-History-Self-Study.git',
    category: 'History',
    branch: 'main',
    type: 'glob',
    patterns: ['01_HKU_Courses/*.md', '01_HKU_Courses/**/*.md', '02_Harvard_Courses/**/*.md', '00_大綱/*.md', '00_大綱/**/*.md'],
  },
  {
    name: 'mech-Eng-Bootcamp',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/mech-Eng-Bootcamp.git',
    category: 'Mech-Eng',
    branch: 'main',
    type: 'glob',
    patterns: ['mae-bootcamp/*.md', 'mae-bootcamp/**/*.md'],
  },
  {
    name: 'psych-self-study-hku',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/psych-self-study-hku.git',
    category: 'Psychology',
    branch: 'main',
    type: 'indexed',
  },
  {
    name: 'HKU-BME-Bootcamp-OpenClaw',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/HKU-BME-Bootcamp-OpenClaw.git',
    category: 'BME',
    branch: 'main',
    type: 'subdir',
  },
  {
    name: 'polyu-msc-digital-economics',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/polyu-msc-digital-economics.git',
    category: 'Digital Economics',
    branch: 'main',
    type: 'glob',
    patterns: ['Week*/*.md'],
    exclude_files: [
      'Notes_Template.md',
      'Notes_Template_ANSWERS.md',
      'completion.md',
    ],
  },
  {
    name: 'MW01-RSE-Bootcamp',
    org: 'yip-lgtm',
    url: 'https://github.com/yip-lgtm/MW01-RSE-Bootcamp.git',
    category: 'Robotics & Structural Eng',
    branch: 'main',
    type: 'projects',  // Each subdir under projects/ = 1 course
  },
];

const TMP_DIR = '/tmp/bootcamp-sync';
const SKIP_DIRS = new Set(['.git', '_agents', '_pipeline', 'node_modules', '.github', '__pycache__', '.venv', 'venv', '.venv']);
const SKIP_FILES = new Set([
  'README.md', 'AGENTS.md', '._enriched_files.txt', 'review.json', '.DS_Store',
  'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE', 'FAQ.md', 'STRUCTURE.md',
  'ROADMAP.md', 'SETUP.md', 'SETUP_AUTOMATION_PROMPT.md',
  'LEARNING_TRACKER.md', 'progress_log.md', 'cron_examples.md',
  'WEEK_COMPLETION_TEMPLATES.md', '_template_completion.md',
  'Master_Tracking.md', 'polyu_msc_plan.md', 'paper_trading_results.md',
  'PULL_REQUEST_TEMPLATE.md', 'STUDY_PLAN.md',
]);

function run(cmd, opts = {}) {
  try {
    return execSync(cmd, { encoding: 'utf-8', stdio: 'pipe', ...opts });
  } catch (e) {
    if (opts.throw !== false) throw e;
    return e.stdout || '';
  }
}

function extractCourseMeta(filePath, content) {
  const lines = content.split('\n');
  const result = {
    lines: lines.length,
    models: [],
    disagreements: [],
    scholars: [],
    equations: 0,
    mermaid: 0,
    chinese_chars: 0,
  };

  // Count Chinese characters
  let cc = 0;
  for (const line of lines) {
    for (const char of line) {
      const c = char.charCodeAt(0);
      if (c >= 0x4E00 && c <= 0x9FFF) cc++;
    }
  }
  result.chinese_chars = cc;

  // Count equations (LaTeX)
  result.equations = (content.match(/\$\$[\s\S]*?\$\$/g) || []).length +
                     (content.match(/\$[^$\n]+?\$/g) || []).length;

  // Count Mermaid diagrams
  result.mermaid = (content.match(/```mermaid[\s\S]*?```/g) || []).length;

  // Extract models
  for (const line of lines) {
    const mm = line.match(/^##\s+(MM-\d+)/);
    if (mm) result.models.push(mm[1]);
    const dd = line.match(/^##\s+(DD-\d+)/);
    if (dd) result.models.push(dd[1]);
  }

  // Extract disagreements
  for (const line of lines) {
    const dg = line.match(/^#{1,3}\s+(DG-\d+)/);
    if (dg) result.disagreements.push(dg[1]);
  }

  // Extract scholars (Author Year pattern)
  const scholars = {};
  const scholarMatches = content.match(/[A-Z][A-Za-zÀ-ÿ\s.\-']+\s+\((\d{4})\)/g) || [];
  for (const m of scholarMatches) {
    const match = m.match(/^([^(]+)\s+\((\d{4})\)/);
    if (match) {
      const year = parseInt(match[2]);
      if (year >= 1800 && year <= 2025) {
        const name = match[1].trim();
        if (name.length > 3 && name.length < 60) {
          scholars[name] = true;
        }
      }
    }
  }
  result.scholars = Object.keys(scholars).slice(0, 15);

  // Extract title
  let title = path.basename(filePath, '.md').replace(/[_-]+/g, ' ');
  for (const line of lines.slice(0, 20)) {
    const h1 = line.match(/^#\s+(.+)/);
    if (h1) { title = h1[1].trim(); break; }
  }

  // Extract course code
  let courseCode = '';
  for (const line of lines.slice(0, 30)) {
    const m = line.match(/\b([A-Z]{2,10}\s*\d{4}[A-Z]?)\b/);
    if (m) { courseCode = m[1]; break; }
  }

  // Extract subcategory from path
  let subcategory = '';
  const parts = filePath.split('/');
  for (let i = 0; i < parts.length - 1; i++) {
    const p = parts[i];
    if (/^(Phase\d|Week\d+|W\d+|大綱|Core|Elective|Capstone)/i.test(p)) {
      subcategory = p.replace(/[_-]+/g, ' ');
      break;
    }
  }
  if (!subcategory && parts.length > 1) {
    subcategory = parts[parts.length - 2].replace(/[_-]+/g, ' ');
  }

  // Extract week
  let week = '';
  const weekMatch = filePath.match(/W(\d+)/i);
  if (weekMatch) week = `W${weekMatch[1]}`;
  else {
    const w = content.match(/Week\s*(\d+)/i);
    if (w) week = `W${w[1]}`;
  }

  return { title, courseCode, subcategory, week, ...result };
}

function scanRepo(repo) {
  const repoDir = path.join(TMP_DIR, repo.name);
  
  if (!fs.existsSync(repoDir)) {
    console.log(`  Cloning ${repo.name}...`);
    run(`git clone --depth=1 -b ${repo.branch} ${repo.url} ${repoDir}`);
  } else {
    console.log(`  Updating ${repo.name}...`);
    run(`git -C ${repoDir} fetch origin ${repo.branch}`);
    run(`git -C ${repoDir} pull origin ${repo.branch}`);
  }

  const courses = [];
  const seenPaths = new Set();

  function addCourse(rel, full) {
    if (seenPaths.has(rel)) return;
    seenPaths.add(rel);

    try {
      const stat = fs.statSync(full);
      if (stat.size < 500) return; // skip skeleton files
    } catch (e) {}

    try {
      const content = fs.readFileSync(full, 'utf-8');
      const meta = extractCourseMeta(rel, content);
      
      const id = `${repo.name}/${rel.replace(/\//g, '-').replace(/\.md$/, '')}`;
      
      courses.push({
        id,
        title: meta.title,
        repo: repo.name,
        category: repo.category,
        path: rel,
        url: `https://github.com/${repo.org}/${repo.name}/blob/${repo.branch}/${rel}`,
        lines: meta.lines,
        models: meta.models,
        disagreements: meta.disagreements,
        scholars: meta.scholars,
        equations: meta.equations,
        mermaid: meta.mermaid,
        chinese_chars: meta.chinese_chars,
        subcategory: meta.subcategory || repo.category,
        course_code: meta.courseCode,
        week: meta.week,
      });
    } catch (e) {}
  }

  function walkGlob(dir, patterns, excludeFiles = []) {
    function globToRegex(pat) {
      // Convert glob pattern to regex
      const parts = pat.split('/');
      const reParts = parts.map(p => {
        if (p === '**') return '.*';
        if (p === '*') return '[^/]*';
        return p.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '[^/]*');
      });
      return new RegExp('^' + reParts.join('/') + '$');
    }

    function matches(rel) {
      for (const pat of patterns) {
        const re = globToRegex(pat);
        if (re.test(rel)) return true;
      }
      return false;
    }

    function walk(d, relPath = '') {
      const entries = fs.readdirSync(d, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name === '.git') continue;
        const full = path.join(d, entry.name);
        const rel = relPath ? `${relPath}/${entry.name}` : entry.name;
        
        if (entry.isDirectory()) {
          if (!SKIP_DIRS.has(entry.name)) {
            walk(full, rel);
          }
        } else if (entry.name.endsWith('.md') && !excludeFiles.includes(entry.name)) {
          // Allow nested README.md (PhysicsSelfStudy courses live as course/README.md)
          // while still skipping root-level meta files listed in SKIP_FILES
          const isNestedReadme = entry.name === 'README.md' && rel.includes('/');
          if ((!SKIP_FILES.has(entry.name) || isNestedReadme) && matches(rel)) {
            addCourse(rel, full);
          }
        }
      }
    }
    walk(dir);
  }

  if (repo.type === 'glob') {
    walkGlob(repoDir, repo.patterns, repo.exclude_files);
  } else if (repo.type === 'subdir') {
    // BME: nested W*/notes/README.md structure
    function findWeekDirs(dir, prefix = '') {
      const results = [];
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name === '.git' || SKIP_DIRS.has(entry.name)) continue;
        if (entry.isDirectory()) {
          const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
          if (/^W\d+/.test(entry.name)) {
            results.push(rel);
          } else {
            results.push(...findWeekDirs(path.join(dir, entry.name), rel));
          }
        }
      }
      return results.sort();
    }

    const weekDirs = findWeekDirs(repoDir);
    const subdirNames = ['notes', 'readings', 'quiz', 'code', 'deliverables'];
    
    for (const weekDir of weekDirs) {
      const weekPath = path.join(repoDir, weekDir);
      const weekEntries = fs.readdirSync(weekPath, { withFileTypes: true });
      
      for (const subEntry of weekEntries) {
        if (!subdirNames.includes(subEntry.name)) continue;
        const subPath = path.join(weekPath, subEntry.name, 'README.md');
        if (fs.existsSync(subPath)) {
          const rel = path.join(weekDir, subEntry.name, 'README.md');
          addCourse(rel, subPath);
        }
      }
    }
  } else if (repo.type === 'indexed') {
    // Psych: every .md file
    function walk(dir, relPath = '') {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name === '.git') continue;
        const full = path.join(dir, entry.name);
        const rel = relPath ? `${relPath}/${entry.name}` : entry.name;

        if (entry.isDirectory()) {
          if (!SKIP_DIRS.has(entry.name)) {
            walk(full, rel);
          }
        } else if (entry.name.endsWith('.md') && !SKIP_FILES.has(entry.name)) {
          addCourse(rel, full);
        }
      }
    }
    walk(repoDir);
  } else if (repo.type === 'projects') {
    // Each subdir under projects/ = 1 course (MW01-RSE-Bootcamp)
    // Include even empty project dirs as placeholder courses
    const projectsDir = path.join(repoDir, 'projects');
    if (fs.existsSync(projectsDir)) {
      const entries = fs.readdirSync(projectsDir, { withFileTypes: true });
      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        const projectPath = path.join(projectsDir, entry.name);
        // Recursively find all .md files inside
        const mdFiles = [];
        function findMd(d) {
          const es = fs.readdirSync(d, { withFileTypes: true });
          for (const e of es) {
            if (e.isDirectory()) {
              if (!SKIP_DIRS.has(e.name)) findMd(path.join(d, e.name));
            } else if (e.name.endsWith('.md') && !SKIP_FILES.has(e.name) && e.name !== 'README.md') {
              mdFiles.push(path.join(d, e.name));
            }
          }
        }
        findMd(projectPath);
        // Combine all .md content (may be empty)
        let combined = '';
        let totalLines = 0;
        for (const f of mdFiles) {
          try {
            const c = fs.readFileSync(f, 'utf-8');
            combined += c + '\n\n';
            totalLines += c.split('\n').length;
          } catch (e) {}
        }
        // Title from first H1 or dir name
        let title = entry.name.replace(/[_-]+/g, ' ');
        const titleMatch = combined.match(/^#\s+(.+)/m);
        if (titleMatch) title = titleMatch[1].trim();
        const rel = `projects/${entry.name}`;
        if (seenPaths.has(rel)) continue;
        seenPaths.add(rel);
        const meta = extractCourseMeta(rel, combined);
        const id = `${repo.name}/${entry.name}`;
        courses.push({
          id, title, repo: repo.name, category: repo.category,
          path: rel,
          url: `https://github.com/${repo.org}/${repo.name}/blob/${repo.branch}/${rel}`,
          lines: totalLines, models: meta.models, disagreements: meta.disagreements,
          scholars: meta.scholars, equations: meta.equations, mermaid: meta.mermaid,
          chinese_chars: meta.chinese_chars, subcategory: meta.subcategory || repo.category,
          course_code: meta.courseCode, week: meta.week,
        });
      }
    }
    // Also include Technical Guidelines as a course
    const techDir = path.join(repoDir, 'MW01-Technical-Guidelines');
    if (fs.existsSync(techDir)) {
      const textFile = path.join(techDir, 'MWTGe_English_text.txt');
      if (fs.existsSync(textFile)) {
        const content = fs.readFileSync(textFile, 'utf-8');
        const totalLines = content.split('\n').length;
        const rel = 'MW01-Technical-Guidelines/MWTGe_English_text.txt';
        if (!seenPaths.has(rel)) {
          seenPaths.add(rel);
          const meta = extractCourseMeta(rel, content);
          courses.push({
            id: `${repo.name}/MW01-Technical-Guidelines`,
            title: 'MW01 Technical Guidelines (English)',
            repo: repo.name, category: repo.category,
            path: rel,
            url: `https://github.com/${repo.org}/${repo.name}/blob/${repo.branch}/${rel}`,
            lines: totalLines, models: meta.models, disagreements: meta.disagreements,
            scholars: meta.scholars, equations: meta.equations, mermaid: meta.mermaid,
            chinese_chars: meta.chinese_chars, subcategory: 'Technical Guidelines',
            course_code: meta.courseCode, week: meta.week,
          });
        }
      }
    }
    // Bundle subjects/ as a single reference course
    const subjectsDir = path.join(repoDir, 'subjects');
    if (fs.existsSync(subjectsDir)) {
      const subjFiles = fs.readdirSync(subjectsDir).filter(f => f.endsWith('.md'));
      if (subjFiles.length > 0) {
        let combined = '';
        let totalLines = 0;
        for (const f of subjFiles) {
          const c = fs.readFileSync(path.join(subjectsDir, f), 'utf-8');
          combined += `# ${f.replace(/^\d+_/, '').replace('.md', '').replace(/_/g, ' ')}\n\n${c}\n\n`;
          totalLines += c.split('\n').length;
        }
        const rel = 'subjects/';
        if (!seenPaths.has(rel)) {
          seenPaths.add(rel);
          const meta = extractCourseMeta(rel, combined);
          courses.push({
            id: `${repo.name}/subjects-bundle`,
            title: 'Robotics & Engineering Subjects (13 courses)',
            repo: repo.name, category: repo.category,
            path: rel,
            url: `https://github.com/${repo.org}/${repo.name}/tree/${repo.branch}/subjects`,
            lines: totalLines, models: meta.models, disagreements: meta.disagreements,
            scholars: meta.scholars, equations: meta.equations, mermaid: meta.mermaid,
            chinese_chars: meta.chinese_chars, subcategory: 'Subjects Reference',
            course_code: meta.courseCode, week: meta.week,
          });
        }
      }
    }
  }

  console.log(`  -> ${courses.length} courses`);
  return courses;
}

function main() {
  console.log('=== Bootcamp Course Sync ===\n');
  
  if (fs.existsSync(TMP_DIR)) fs.rmSync(TMP_DIR, { recursive: true });
  fs.mkdirSync(TMP_DIR, { recursive: true });

  const allCourses = [];
  const byCategory = {};

  for (const repo of REPOS) {
    console.log(`Scanning ${repo.name} (${repo.type})...`);
    const courses = scanRepo(repo);
    allCourses.push(...courses);
    byCategory[repo.category] = (byCategory[repo.category] || 0) + courses.length;
  }

  allCourses.sort((a, b) => {
    if (a.category !== b.category) return a.category.localeCompare(b.category);
    if (a.subcategory !== b.subcategory) return a.subcategory.localeCompare(b.subcategory);
    return a.title.localeCompare(b.title);
  });

  const output = {
    total: allCourses.length,
    by_category: byCategory,
    last_updated: new Date().toISOString(),
    courses: allCourses,
  };

  const outPath = path.join(__dirname, '..', 'app', 'src', 'data', 'courses.json');
  fs.writeFileSync(outPath, JSON.stringify(output, null, 2));
  
  console.log(`\n=== Done! ${allCourses.length} courses written`);
  for (const [cat, count] of Object.entries(byCategory)) {
    console.log(`  ${cat}: ${count}`);
  }
  
  fs.rmSync(TMP_DIR, { recursive: true });
}

main();
