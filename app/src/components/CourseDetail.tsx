import type { FC } from 'react'
import type { Course } from '../utils/storage'

interface Props {
  course: Course
  isFollowed: boolean
  isSaved: boolean
  onFollow: () => void
  onSave: () => void
}

export const CourseDetail: FC<Props> = ({ course, isFollowed, isSaved, onFollow, onSave }) => {
  const handleSuggestCorrection = () => {
    const title = encodeURIComponent(`[Correction] ${course.title}`)
    const body = encodeURIComponent(
      `## 內容修正建議 / Content Correction\n\n` +
      `**課程 / Course:** ${course.title}\n` +
      `**ID:** \`${course.id}\`\n` +
      `**Path:** \`${course.path}\`\n` +
      `**GitHub:** ${course.url}\n\n` +
      `### 問題類型\n` +
      `- [ ] 事實錯誤 / Factual error\n` +
      `- [ ] 方程式錯誤 / Equation error\n` +
      `- [ ] 引用錯誤 / Citation / scholar error\n` +
      `- [ ] 中英翻譯問題 / Translation issue\n` +
      `- [ ] 內容過時 / Outdated content\n` +
      `- [ ] 其他 / Other\n\n` +
      `### 詳細說明\n` +
      `（請寫清楚位置、而家寫咗咩、建議改成咩、有冇來源）\n\n` +
      `---\n` +
      `*Submitted via AllBootcamp Course Detail · ${new Date().toISOString().slice(0, 10)}*`
    )
    window.open(
      `https://github.com/yip-lgtm/vibe-study-bootcamp/issues/new?title=${title}&body=${body}&labels=correction`,
      '_blank'
    )
  }

  return (
    <div className="flex-1 overflow-y-auto pb-16">
      {/* Hero */}
      <div className="px-4 py-4 bg-gradient-to-b from-pill-bg to-black border-b border-divider">
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <span className="text-accent text-xs font-bold px-2 py-0.5 bg-pill-bg rounded">
            {course.category}
          </span>
          <span className="text-text-faint text-xs">{course.repo}</span>
        </div>
        <h1 className="text-xl font-bold text-text leading-tight">{course.title}</h1>
        <div className="flex items-center gap-3 mt-3 text-xs text-text-dim">
          <span>📏 {course.lines} lines</span>
          <span>📐 {course.equations} equations</span>
          <span>📊 {course.mermaid} diagrams</span>
          <span>👤 {course.scholars.length} scholars</span>
        </div>
        <div className="flex gap-2 mt-3">
          <button
            onClick={onFollow}
            className={`flex-1 py-2 rounded text-sm font-bold tap-active ${
              isFollowed ? 'bg-accent text-black' : 'bg-pill-bg text-accent'
            }`}
          >
            {isFollowed ? '✓ 追蹤中' : '+ 追蹤 Follow'}
          </button>
          <button
            onClick={onSave}
            className={`flex-1 py-2 rounded text-sm font-bold tap-active ${
              isSaved ? 'bg-accent text-black' : 'bg-pill-bg text-accent'
            }`}
          >
            {isSaved ? '★ 已收藏' : '☆ 收藏 Save'}
          </button>
        </div>
      </div>

      {/* 5MM — 5 Mental Models */}
      {course.models.length > 0 && (
        <section className="px-4 py-3 border-b border-divider">
          <h2 className="text-accent font-bold mb-2 flex items-center gap-2">
            <span className="text-accent">⚡</span> 5 個核心心智模型
          </h2>
          {course.models.map((m, i) => (
            <div key={i} className="mb-2 text-text text-sm leading-relaxed">
              <span className="text-accent font-bold mr-1">{i + 1}.</span>
              {m.replace(/\*+/g, '').trim()}
            </div>
          ))}
        </section>
      )}

      {/* 3DG — 3 Disagreements */}
      {course.disagreements.length > 0 && (
        <section className="px-4 py-3 border-b border-divider">
          <h2 className="text-accent font-bold mb-2 flex items-center gap-2">
            <span className="text-accent">⚡</span> 3 個根本分歧
          </h2>
          {course.disagreements.map((d, i) => (
            <div key={i} className="mb-2 text-text text-sm leading-relaxed">
              <span className="text-accent font-bold mr-1">{i + 1}.</span>
              {d.replace(/\*+/g, '').trim()}
            </div>
          ))}
        </section>
      )}

      {/* Scholars */}
      {course.scholars.length > 0 && (
        <section className="px-4 py-3 border-b border-divider">
          <h2 className="text-accent font-bold mb-2 flex items-center gap-2">
            <span className="text-accent">⚡</span> 引用學者
          </h2>
          <div className="flex flex-wrap gap-2">
            {course.scholars.map((s, i) => (
              <span key={i} className="bg-pill-bg text-text text-xs px-2 py-1 rounded">
                {s}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Chinese content indicator */}
      <section className="px-4 py-3 border-b border-divider">
        <h2 className="text-accent font-bold mb-2 flex items-center gap-2">
          <span className="text-accent">⚡</span> 中英對照
        </h2>
        <div className="text-text-dim text-sm">
          中文字符: <span className="text-accent font-bold">{course.chinese_chars}</span>
        </div>
        <div className="w-full bg-divider h-1 rounded mt-2">
          <div
            className="bg-accent h-1 rounded transition-all"
            style={{ width: `${Math.min(100, (course.chinese_chars / 2000) * 100)}%` }}
          />
        </div>
      </section>

      {/* Action: open in GitHub */}
      <div className="px-4 py-4 space-y-3">
        <a
          href={course.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-3 bg-pill-bg text-accent text-center font-bold rounded tap-active"
        >
          喺 GitHub 開啟 Open in GitHub ↗
        </a>
        <div className="text-text-faint text-xs text-center break-all">
          {course.path}
        </div>
      </div>

      {/* 公眾修正 / Public Correction */}
      <section className="px-4 pb-6">
        <div className="border border-divider rounded-xl p-4 bg-card">
          <h2 className="text-accent font-bold mb-1 flex items-center gap-2">
            ✏️ 公眾修正
          </h2>
          <p className="text-text-dim text-xs mb-3 leading-relaxed">
            發現錯誤、過時內容或翻譯問題？歡迎提出修正，會直接變成 GitHub Issue 俾 multi-agent 處理。
          </p>
          <button
            onClick={handleSuggestCorrection}
            className="w-full py-2.5 rounded font-bold text-sm bg-accent text-black tap-active"
          >
            提出修正 Suggest a Correction →
          </button>
        </div>
      </section>
    </div>
  )
}
