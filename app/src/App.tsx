import { useState, useEffect, useMemo } from 'react'
import { Sidebar } from './components/Sidebar'
import { FilterPanel } from './components/FilterPanel'
import { CourseList } from './components/CourseList'
import { CourseDetail } from './components/CourseDetail'
import { TopBar } from './components/TopBar'
import { BottomNav } from './components/BottomNav'
import coursesData from './data/courses.json'
import { loadFollow, loadSaved, toggleFollow, toggleSaved, type Course } from './utils/storage'
import { seededShuffle, getDailySeed, getWeeklySeed } from './utils/shuffle'
import type { ListMode } from './components/CourseList'

type Screen = 'home' | 'detail' | 'following' | 'saved' | 'search'
type SidePanel = 'left' | 'right' | null

export default function App() {
  const [screen, setScreen] = useState<Screen>('home')
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [sidePanel, setSidePanel] = useState<SidePanel>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)

  // Quick Add form state
  const [addTitle, setAddTitle] = useState('')
  const [addReason, setAddReason] = useState('')
  const [addSubmitted, setAddSubmitted] = useState(false)

  // Filters
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [filterSubcategory, setFilterSubcategory] = useState<string>('all')
  const [filterHasScholars, setFilterHasScholars] = useState(false)
  const [filterHasEquations, setFilterHasEquations] = useState(false)
  const [filterMinLines, setFilterMinLines] = useState(0)
  const [sortBy, setSortBy] = useState<'newest' | 'lines' | 'title' | 'category' | 'mixed'>('mixed')
  const [listMode, setListMode] = useState<ListMode>('mixed')

  // Following / Saved
  const [followed, setFollowed] = useState<Set<string>>(new Set())
  const [saved, setSaved] = useState<Set<string>>(new Set())

  useEffect(() => {
    setFollowed(loadFollow())
    setSaved(loadSaved())
  }, [])

  const courses = coursesData.courses as Course[]

  const filteredCourses = useMemo(() => {
    let result = courses

    // Screen filter
    if (screen === 'following') {
      result = result.filter(c => followed.has(c.id))
    } else if (screen === 'saved') {
      result = result.filter(c => saved.has(c.id))
    } else if (screen === 'search') {
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        result = result.filter(c =>
          c.title.toLowerCase().includes(q) ||
          c.category.toLowerCase().includes(q) ||
          c.repo.toLowerCase().includes(q) ||
          c.models.some(m => m.toLowerCase().includes(q)) ||
          c.scholars.some(s => s.toLowerCase().includes(q))
        )
      }
    }

    // Category filter
    if (filterCategory !== 'all') {
      result = result.filter(c => c.category === filterCategory)
    }

    // Subcategory filter (drill-down within category)
    if (filterSubcategory !== 'all') {
      result = result.filter(c => c.subcategory === filterSubcategory)
    }

    // Quality filters
    if (filterHasScholars) {
      result = result.filter(c => c.scholars.length > 0)
    }
    if (filterHasEquations) {
      result = result.filter(c => c.equations > 3)
    }
    if (filterMinLines > 0) {
      result = result.filter(c => c.lines >= filterMinLines)
    }

    // Ranking / sort
    result = [...result]

    // On home screen, ranking tabs control order
    if (screen === 'home' && filterCategory === 'all' && !searchQuery) {
      if (listMode === 'daily') {
        result = seededShuffle(result, getDailySeed())
      } else if (listMode === 'weekly') {
        result = seededShuffle(result, getWeeklySeed())
      } else {
        // mixed: interleave categories
        const byCat: Record<string, Course[]> = {}
        for (const c of result) {
          const k = c.category || 'Other'
          if (!byCat[k]) byCat[k] = []
          byCat[k].push(c)
        }
        for (const k of Object.keys(byCat)) {
          byCat[k].sort((a, b) => a.title.localeCompare(b.title) || a.id.localeCompare(b.id))
        }
        const catKeys = Object.keys(byCat).sort()
        const interleaved: Course[] = []
        let i = 0
        let added = true
        while (added) {
          added = false
          for (const k of catKeys) {
            if (i < byCat[k].length) {
              interleaved.push(byCat[k][i])
              added = true
            }
          }
          i++
        }
        result = interleaved
      }
    } else {
      // Filter panel sort (when filtered / other screens)
      if (sortBy === 'lines') {
        result.sort((a, b) => b.lines - a.lines || a.id.localeCompare(b.id))
      } else if (sortBy === 'title') {
        result.sort((a, b) => a.title.localeCompare(b.title) || a.id.localeCompare(b.id))
      } else if (sortBy === 'newest') {
        result.sort((a, b) => b.id.localeCompare(a.id))
      } else if (sortBy === 'category') {
        result.sort(
          (a, b) =>
            a.category.localeCompare(b.category) ||
            a.title.localeCompare(b.title) ||
            a.id.localeCompare(b.id)
        )
      } else {
        // mixed interleave
        const byCat: Record<string, Course[]> = {}
        for (const c of result) {
          const k = c.category || 'Other'
          if (!byCat[k]) byCat[k] = []
          byCat[k].push(c)
        }
        for (const k of Object.keys(byCat)) {
          byCat[k].sort((a, b) => a.title.localeCompare(b.title) || a.id.localeCompare(b.id))
        }
        const catKeys = Object.keys(byCat).sort()
        const interleaved: Course[] = []
        let i = 0
        let added = true
        while (added) {
          added = false
          for (const k of catKeys) {
            if (i < byCat[k].length) {
              interleaved.push(byCat[k][i])
              added = true
            }
          }
          i++
        }
        result = interleaved
      }
    }

    return result
  }, [courses, screen, searchQuery, filterCategory, filterSubcategory, filterHasScholars, filterHasEquations, filterMinLines, sortBy, listMode, followed, saved])

  // Compute available subcategories for current category
  const subcategoryCounts = useMemo(() => {
    const map: Record<string, number> = { all: 0 }
    const pool = filterCategory === 'all' ? courses : courses.filter(c => c.category === filterCategory)
    for (const c of pool) {
      const sub = c.subcategory || 'Other'
      map[sub] = (map[sub] || 0) + 1
    }
    map.all = pool.length
    return map
  }, [courses, filterCategory])

  const handleCourseClick = (course: Course) => {
    setSelectedCourse(course)
    setScreen('detail')
    setSidePanel(null)
  }

  const handleFollow = (id: string) => {
    setFollowed(toggleFollow(id))
  }

  const handleSave = (id: string) => {
    setSaved(toggleSaved(id))
  }

  const closeAddModal = () => {
    setShowAddModal(false)
    setAddTitle('')
    setAddReason('')
    setAddSubmitted(false)
  }

  const handleAddSubmit = () => {
    const title = addTitle.trim()
    if (!title) return

    try {
      const key = 'study_tour_requests'
      const prev = JSON.parse(localStorage.getItem(key) || '[]')
      prev.unshift({
        title,
        reason: addReason.trim(),
        ts: new Date().toISOString(),
      })
      localStorage.setItem(key, JSON.stringify(prev.slice(0, 20)))
    } catch {}

    const issueTitle = encodeURIComponent(`[Course Request] ${title}`)
    const body = encodeURIComponent(
      `## 課程申請 / Course Request\n\n` +
      `**課程名稱 / Course title:** ${title}\n\n` +
      `**原因 / Why needed:**\n${addReason.trim() || '(未填寫)'}\n\n` +
      `---\n` +
      `*Submitted via AllBootcamp Quick Add Modal · ${new Date().toISOString().slice(0, 10)}*`
    )
    window.open(
      `https://github.com/yip-lgtm/vibe-study-bootcamp/issues/new?title=${issueTitle}&body=${body}&labels=course-request`,
      '_blank'
    )

    setAddSubmitted(true)
    setTimeout(() => {
      closeAddModal()
    }, 1800)
  }

  return (
    <div className="h-full bg-black text-white overflow-hidden relative">
      <div className="h-[env(safe-area-inset-top)]" />

      <div className="h-full flex flex-col">
        <TopBar
          screen={screen}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onMenu={() => setSidePanel(sidePanel === 'left' ? null : 'left')}
          onFilter={() => setSidePanel(sidePanel === 'right' ? null : 'right')}
          onBack={() => setScreen('home')}
        />

        {screen === 'detail' && selectedCourse ? (
          <CourseDetail
            course={selectedCourse}
            isFollowed={followed.has(selectedCourse.id)}
            isSaved={saved.has(selectedCourse.id)}
            onFollow={() => handleFollow(selectedCourse.id)}
            onSave={() => handleSave(selectedCourse.id)}
          />
        ) : (
          <CourseList
            courses={filteredCourses}
            followed={followed}
            saved={saved}
            onCourseClick={handleCourseClick}
            onFollow={handleFollow}
            onSave={handleSave}
            totalCount={courses.length}
            screen={screen}
            listMode={listMode}
            onListModeChange={setListMode}
          />
        )}

        <BottomNav
          current={screen}
          onChange={(s) => {
            setScreen(s)
            setSidePanel(null)
          }}
          onAdd={() => setShowAddModal(true)}
          followingCount={followed.size}
          savedCount={saved.size}
        />
      </div>

      {sidePanel === 'left' && (
        <>
          <div
            className="absolute inset-0 bg-black/60 z-40"
            onClick={() => setSidePanel(null)}
          />
          <div className="absolute left-0 top-0 bottom-0 w-72 z-50 slide-in-left">
            <Sidebar
              onClose={() => setSidePanel(null)}
              onNavigate={(s) => {
                setScreen(s)
                setFilterCategory('all')
                setFilterSubcategory('all')
                setSidePanel(null)
              }}
              onSelectCategory={(cat) => {
                setFilterCategory(cat)
                setFilterSubcategory('all')
                setScreen('home')
                setSidePanel(null)
              }}
              currentScreen={screen}
              currentCategory={filterCategory}
            />
          </div>
        </>
      )}

      {sidePanel === 'right' && (
        <>
          <div
            className="absolute inset-0 bg-black/60 z-40"
            onClick={() => setSidePanel(null)}
          />
          <div className="absolute right-0 top-0 bottom-0 w-72 z-50 slide-in-right">
            <FilterPanel
              onClose={() => setSidePanel(null)}
              category={filterCategory}
              setCategory={(s) => { setFilterCategory(s); setFilterSubcategory('all') }}
              subcategory={filterSubcategory}
              setSubcategory={setFilterSubcategory}
              subcategoryCounts={subcategoryCounts}
              hasScholars={filterHasScholars}
              setHasScholars={setFilterHasScholars}
              hasEquations={filterHasEquations}
              setHasEquations={setFilterHasEquations}
              minLines={filterMinLines}
              setMinLines={setFilterMinLines}
              sortBy={sortBy}
              setSortBy={setSortBy}
              counts={coursesData.by_category as Record<string, number>}
            />
          </div>
        </>
      )}

      {showAddModal && (
        <>
          <div
            className="absolute inset-0 bg-black/70 z-50"
            onClick={closeAddModal}
          />
          <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 z-50 bg-card border border-divider rounded-xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-accent">＋ 快速新增 / 申請課程</h2>
              <button
                onClick={closeAddModal}
                className="text-text-dim text-2xl leading-none tap-active px-1"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            {addSubmitted ? (
              <div className="py-8 text-center">
                <div className="text-3xl mb-3">✅</div>
                <p className="text-accent font-bold mb-1">已開啟 GitHub Issue</p>
                <p className="text-text-dim text-sm">請喺新分頁完成提交</p>
              </div>
            ) : (
              <>
                <p className="text-text-dim text-sm mb-4 leading-relaxed">
                  想加入新嘅 bootcamp 或課程？填寫下面，會直接開啟 GitHub Issue 提交申請。
                </p>

                <div className="space-y-3">
                  <input
                    type="text"
                    value={addTitle}
                    onChange={(e) => setAddTitle(e.target.value)}
                    placeholder="課程名稱 / Course title *"
                    className="w-full bg-pill-bg text-text placeholder-text-faint px-3 py-2.5 rounded text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                    autoFocus
                  />
                  <textarea
                    value={addReason}
                    onChange={(e) => setAddReason(e.target.value)}
                    placeholder="簡述原因 / Why do you need this course?"
                    rows={3}
                    className="w-full bg-pill-bg text-text placeholder-text-faint px-3 py-2.5 rounded text-sm focus:outline-none focus:ring-1 focus:ring-accent resize-none"
                  />
                  <button
                    onClick={handleAddSubmit}
                    disabled={!addTitle.trim()}
                    className={`w-full py-2.5 rounded font-bold text-sm ${
                      addTitle.trim()
                        ? 'bg-accent text-black tap-active'
                        : 'bg-accent text-black opacity-40 cursor-not-allowed'
                    }`}
                  >
                    提交申請 → GitHub Issue
                  </button>
                </div>

                <p className="text-text-faint text-xs mt-4 text-center">
                  會開啟新分頁 · 需要 GitHub 帳號登入先可以提交
                </p>
              </>
            )}
          </div>
        </>
      )}
    </div>
  )
}
