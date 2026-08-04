# Contributing to vibe-study-bootcamp

> 歡迎加入！任何人都可以 contribute

## 🌟 點樣 Contribute

### Option 1: Add 新 Bootcamp
```bash
mkdir -p your-bootcamp-name/courses/
cp -r _agents/ your-bootcamp-name/
cp -r _pipeline/ your-bootcamp-name/
# Add courses using 5MM/3DG/10Q format
cd your-bootcamp-name/
python3 _agents/professor_supervisor/review.py --all
```

### Option 2: Improve 現有 Course
- Edit course with REVISE status
- Re-run review until APPROVED

### Option 3: Improve Pipeline
- Add new quality gate
- Better diagrams
- Multi-language support

### Option 4: Documentation
- Improve README
- Add tutorials
- Translate

---

## 📋 Contribution Standards

### 必須遵守 (Mandatory)
1. **Bilingual** — 中英對照 內容
2. **Real sources** — 拒 generic 廢話
3. **Scholar citations** — 真實名字 + 年份
4. **Equations** — LaTeX format
5. **Mermaid** — 5 distinct diagrams
6. **Quality gate** — 必須 APPROVED ≥ 85

### 拒絕 Garbage
- ❌ `[TBD]`, `待補充`, `placeholder`, `Lorem ipsum`
- ❌ Template placeholders (`T0 — Core concept`)
- ❌ Generic 廢話 without specifics
- ❌ Pseudocode
- ❌ 含糊 attribution

---

## 📐 Course Format 規範

```markdown
# <COURSE_CODE> — <Course Name>

## 問題 1：5 個核心心智模型
1. **Model 1 (Scholar Year)** - equation + numbers + application
2. ...

## 問題 2：3 個根本分歧
1. **Disagreement** - Position A + Position B + tension

## 問題 3：10 個深度問題
1. Probing question + detailed answer

## 5 Deep Dives (中英對照)
### 深入 1: <Title>
- Bilingual table
- Key derivation
- Engineering applications
- Mermaid diagram

## 10 Self-Test Solutions
1. Question → detailed answer

## 5 Mermaid Diagrams
```

---

## 💡 Tips

### DO ✅
- Start with primary sources (Wikipedia, MIT OCW, arXiv)
- Use real scholar names (Newton 1687, not "someone famous")
- Include specific numbers
- Write in both Chinese AND English
- Add LaTeX equations
- Include real engineering applications

### DON'T ❌
- Copy without attribution
- Use template placeholders
- Skip the Chinese version
- Use too many bullets without depth

---

## 📬 Contact

- **Issues:** [GitHub Issues](https://github.com/yip-lgtm/vibe-study-bootcamp/issues)
- **Email:** yipsaba@polyu-msc.ai

---

*Thank you for making education free for everyone! 🌐*
