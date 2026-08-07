import type { FC } from 'react'
import type { Course } from '../utils/storage'
import { getCategoryColor } from '../utils/categories'

export type ListMode = 'mixed' | 'daily' | 'weekly' | 'shuffle'

interface Props {
  courses: Course[]
  followed: Set<string>
  saved: Set<string>
  onCourseClick: (c: Course) => void
  onFollow: (id: string) => void
  onSave: (id: string) => void
  totalCount: number
  screen: string
  listMode: ListMode
  onListModeChange: (m: ListMode) => void
  onReshuffle?: () => void
}

const formatTimeAgo = (_repo: string) => '11m'

const formatComments = (lines: number) => Math.floor((lines * 13) % 999) + 10

const formatLikes = (lines: number) => Math.floor((lines * 7) % 100) - 30

export const CourseList: FC<Props> = ({
  courses, followed, saved, onCourseClick, onFollow, onSave,
  totalCount, screen, listMode, onListModeChange, onReshuffle,
}) => {
  // Only show ranking tabs on home screen
  const showRankingTabs = screen === 'home'

  const tabs: { id: ListMode; label: string }[] = [
    { id: 'shuffle', label: '🎲 隨機' },
    { id: 'daily', label: '今日熱門' },
    { id: 'weekly', label: '本週精選' },
  ]

  return (
    <div className="flex-1 overflow-y-auto pb-16">
      {/* Tabs row */}
      <div className="sticky top-0 bg-black z-10 flex border-b border-divider">
        {showRankingTabs ? (
          <>
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => onListModeChange(t.id)}
                className={`flex-1 text-center py-2 text-sm tap-active ${
                  listMode === t.id
                    ? 'border-b-2 border-accent text-accent'
                    : 'text-text-faint'
                }`}
              >
                {t.label}
              </button>
            ))}
            {listMode === 'shuffle' && (
              <button
                onClick={() => onReshuffle?.()}
                title="重新洗牌 Reshuffle"
                className="px-3 text-accent text-lg tap-active"
              >
                🔀
              </button>
            )}
          </>
        ) : (
          <>
            <div className="flex-1 text-center py-2 text-sm text-text-faint">
              {screen === 'following' ? '追蹤中' : screen === 'saved' ? '收藏' : '搜尋'}
            </div>
            <div className="flex-1 text-center py-2 text-sm text-accent border-b-2 border-accent">
              {screen === 'search' ? '結果' : '列表'}
            </div>
            <div className="flex-1" />
          </>
        )}
      </div>

      {/* Result count */}
      <div className="px-4 py-2 text-xs text-text-faint border-b border-divider">
        {courses.length} of {totalCount} courses
        {screen === 'search' && ' · filtered'}
        {showRankingTabs && listMode === 'daily' && ' · 今日洗牌'}
        {showRankingTabs && listMode === 'weekly' && ' · 本週洗牌'}
        {showRankingTabs && listMode === 'shuffle' && ' · 隨機洗牌'}
        {showRankingTabs && listMode === 'mixed' && ' · 混合穿插'}
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
          const catColor = getCategoryColor(c.category)
          const isFollowed = followed.has(c.id)
          const isSaved = saved.has(c.id)

          return (
            <div
              key={c.id}
              className="px-4 py-3 border-b border-divider tap-active"
              onClick={() => onCourseClick(c)}
            >
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

              <div className="flex items-center justify-end gap-3 mt-2 text-xs text-text-dim">
                <span className="flex items-center gap-1">
                  💬 {comments} <span className="text-text-faint">comment</span>
                </span>
                <span className={`flex items-center gap-1 ${likes < 0 ? 'text-red-400' : 'text-text-dim'}`}>
                  {likes < 0 ? '👎' : '👍'} {Math.abs(likes)}{' '}
                  <span className="text-text-faint">{c.lines}L</span>
                </span>
                <span className="text-text-faint text-[10px]">
                  {c.equations}eq · {c.scholars.length}sch
                </span>
              </div>

              {c.models.length > 0 && (
                <div className="mt-1.5 text-text-faint text-xs truncate">
                  <span className="text-accent">5MM:</span>{' '}
                  {c.models[0].replace(/\*+/g, '').slice(0, 80)}
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
