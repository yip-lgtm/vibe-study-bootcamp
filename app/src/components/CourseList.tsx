import type { FC } from 'react'
import type { Course } from '../utils/storage'

interface Props {
  courses: Course[]
  followed: Set<string>
  saved: Set<string>
  onCourseClick: (c: Course) => void
  onFollow: (id: string) => void
  onSave: (id: string) => void
  totalCount: number
  screen: string
}

const CATEGORY_COLORS: Record<string, string> = {
  Engineering: 'bg-blue-900/40 text-blue-300',
  Physics: 'bg-purple-900/40 text-purple-300',
  History: 'bg-amber-900/40 text-amber-300',
  Psychology: 'bg-pink-900/40 text-pink-300',
  'Mech-Eng': 'bg-cyan-900/40 text-cyan-300',
  BME: 'bg-emerald-900/40 text-emerald-300',
}

const formatTimeAgo = (repo: string) => {
  // Mock time display - "11m" style
  return '11m'
}

const formatComments = (lines: number) => {
  // Pseudo-random based on lines for stable display
  return Math.floor((lines * 13) % 999) + 10
}

const formatLikes = (lines: number) => {
  return Math.floor((lines * 7) % 100) - 30
}

export const CourseList: FC<Props> = ({
  courses, followed, saved, onCourseClick, onFollow, onSave, totalCount, screen,
}) => {
  const getHeaderText = () => {
    if (screen === 'following') return { left: '追蹤中 Following', center: '今日 Today' }
    if (screen === 'saved') return { left: '收藏 Saved', center: '今日 Today' }
    if (screen === 'search') return { left: '搜尋 Search', center: '結果 Results' }
    return { left: '即時熱門', center: '今日熱門' }
  }
  const hdr = getHeaderText()

  return (
    <div className="flex-1 overflow-y-auto pb-16">
      {/* Tabs row */}
      <div className="sticky top-0 bg-black z-10 flex border-b border-divider">
        <div className="flex-1 text-center py-2 text-sm text-text-faint">{hdr.left}</div>
        <div className="flex-1 text-center py-2 text-sm text-text-faint border-b-2 border-accent text-accent">
          {hdr.center}
        </div>
        <div className="flex-1 text-center py-2 text-sm text-text-faint">本週精選</div>
      </div>

      {/* Result count */}
      <div className="px-4 py-2 text-xs text-text-faint border-b border-divider">
        {courses.length} of {totalCount} courses
        {screen === 'search' && ' · filtered'}
      </div>

      {/* Course list */}
      {courses.length === 0 ? (
        <div className="text-center py-12 text-text-faint">
          <div className="text-4xl mb-2">📭</div>
          <div>沒有 results</div>
        </div>
      ) : (
        courses.map((c) => {
          const comments = formatComments(c.lines)
          const likes = formatLikes(c.lines)
          const catColor = CATEGORY_COLORS[c.category] || 'bg-pill-bg text-text-dim'
          const isFollowed = followed.has(c.id)
          const isSaved = saved.has(c.id)

          return (
            <div
              key={c.id}
              className="px-4 py-3 border-b border-divider tap-active"
              onClick={() => onCourseClick(c)}
            >
              {/* Top row: title + category badge */}
              <div className="flex items-start gap-2">
                <span className="text-accent text-base mt-0.5 flex-shrink-0">⚡</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`${catColor} text-xs px-1.5 py-0.5 rounded font-bold`}>
                      {c.category}
                    </span>
                    {c.subcategory && (
                      <span className="bg-zinc-800 text-zinc-400 text-[10px] px-1.5 py-0.5 rounded">
                        {c.subcategory}
                      </span>
                    )}
                    {c.course_code && (
                      <span className="text-text-faint text-[10px] font-mono">
                        {c.course_code}
                      </span>
                    )}
                    <span className="text-text-faint text-xs">· {formatTimeAgo(c.repo)}</span>
                  </div>
                  {/* Title - bilingual friendly */}
                  <div className="mt-1.5 text-text text-[15px] leading-snug font-medium">
                    {c.title}
                  </div>
                </div>
                <div className="flex flex-col gap-1 flex-shrink-0">
                  <button
                    onClick={(e) => { e.stopPropagation(); onFollow(c.id) }}
                    className="text-base tap-active"
                    title="追蹤 Follow"
                  >
                    {isFollowed ? '🟢' : '⚪'}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); onSave(c.id) }}
                    className="text-base tap-active"
                    title="收藏 Save"
                  >
                    {isSaved ? '🟡' : '⚫'}
                  </button>
                </div>
              </div>

              {/* Stats row - like 196 comments and -177 dislikes */}
              <div className="flex items-center justify-end gap-3 mt-2 text-xs text-text-dim">
                <span className="flex items-center gap-1">
                  💬 {comments} <span className="text-text-faint">comment</span>
                </span>
                <span className={`flex items-center gap-1 ${likes < 0 ? 'text-red-400' : 'text-text-dim'}`}>
                  {likes < 0 ? '👎' : '👍'} {Math.abs(likes)} <span className="text-text-faint">{c.lines}L</span>
                </span>
                <span className="text-text-faint text-[10px]">
                  {c.equations}eq · {c.scholars.length}sch
                </span>
              </div>

              {/* First model as preview */}
              {c.models.length > 0 && (
                <div className="mt-1.5 text-text-faint text-xs truncate">
                  <span className="text-accent">5MM:</span> {c.models[0].replace(/\*+/g, '').slice(0, 80)}
                </div>
              )}
            </div>
          )
        })
      )}

      <div className="text-center py-6 text-text-faint text-xs">
        — {courses.length} courses loaded —
      </div>
    </div>
  )
}
