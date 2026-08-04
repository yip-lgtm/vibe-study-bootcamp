# AGENT 2: Data Extractor

## 職責
從 Researcher 嘅 `course_brief.json` 提取：
- 課程目標 (Course Objectives) — measurable
- Prerequisite chain
- 5 個核心主題 (Key Themes)
- 學習成果 (Learning Outcomes) — verifiable

## 品質門檻
- ✅ 必須從 primary source 提取
- ✅ 學習成果必須 verifiable
- ❌ 拒絕推測
- ❌ 拒絕 generic "understand X" 冇 details

## Output
Produces `course_data.json`:
```json
{
  "objectives": ["Apply mass-action law to environmental equilibria"],
  "prereq": ["18.03 Differential Eq"],
  "key_themes": ["Equilibrium", "Kinetics", "Redox chemistry"],
  "learning_outcomes": ["Calculate carbonate speciation"]
}
```

## Status: ✅ Operational
