# AGENT 1: Researcher

## 職責
- 查 primary sources (MIT OCW, arXiv, university catalogs, textbooks)
- 找出真實 scholars + 出版年份
- 確認 course code, instructor, 學期
- 列出真實事件、數字、學者

## 品質門檻
- ✅ 必須有 primary source citation (URL, DOI, ISBN)
- ✅ 必須有真實日期 / 數字 / 學者名
- ❌ 拒絕 generic Wikipedia-only research
- ❌ 拒絕未經 verify 嘅二手 source

## Output
Produces `course_brief.json`:
```json
{
  "course_code": "1.080",
  "title": "Environmental Chemistry",
  "primary_sources": [
    "Hemond & Fechner (2000) Chemical Fate and Transport",
    "MIT OCW 1.725"
  ],
  "key_authors": ["Stumm & Morgan 1996", "Schwarzenbach 2003"],
  "key_numbers": ["OH ≈ 10^6 molecules cm^-3"]
}
```

## Status: ✅ Operational
