import { useState, useEffect, useMemo } from 'react'
import { Sidebar } from './components/Sidebar'
import { FilterPanel } from './components/FilterPanel'
import { CourseList } from './components/CourseList'
import { CourseDetail } from './components/CourseDetail'
import { TopBar } from './components/TopBar'
import { BottomNav } from './components/BottomNav'
import coursesData from './data/courses.json'
import { loadFollow, loadSaved, toggleFollow, toggleSaved, type Course } from './utils/storage'

type Screen = 'home' | 'detail' | 'following' | 'saved' | 'search'
type SidePanel = 'left' | 'right' | null

export default function App() {
  const [screen, setScreen] = useState<Screen>('home')
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [sidePanel, setSidePanel] = useState<SidePanel>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)

  // Filters
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [filterSubcategory, setFilterSubcategory] = useState<string>('all')
  const [filterHasScholars, setFilterHasScholars] = useState(false)
  const [filterHasEquations, setFilterHasEquations] = useState(false)
  const [filterMinLines, setFilterMinLines] = useState(0)
  const [sortBy, setSortBy] = useState<'newest' | 'lines' | 'title' | 'category'>('category')

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

    // Sort
    if (sortBy === 'lines') {
      result = [...result].sort((a, b) => b.lines - a.lines)
    } else if (sortBy === 'title') {
      result = [...result].sort((a, b) => a.title.localeCompare(b.title))
    } else if (sortBy === 'category') {
      result = [...result].sort((a, b) => a.category.localeCompare(b.category) || a.title.localeCompare(b.title))
    }

    return result
  }, [courses, screen, searchQuery, filterCategory, filterSubcategory, filterHasScholars, filterHasEquations, filterMinLines, sortBy, followed, saved])

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

  return (
    <div className="h-full bg-black text-white overflow-hidden relative">
      {/* Status bar spacer for iOS PWA */}
      <div className="h-[env(safe-area-inset-top)]" />

      {/* Main content area */}
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

      {/* Side panels */}
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
                setSidePanel(null)
              }}
              currentScreen={screen}
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

      {/* Quick Add / Request Course Modal */}
      {showAddModal && (
        <>
          <div
            className="absolute inset-0 bg-black/70 z-50"
            onClick={() => setShowAddModal(false)}
          />
          <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 z-50 bg-card border border-divider rounded-xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-accent">＋ 快速新增 / 申請課程</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-text-dim text-2xl leading-none tap-active px-1"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <p className="text-text-dim text-sm mb-4 leading-relaxed">
              想加入新嘅 bootcamp 或課程？暫時係 placeholder。
              <br />
              之後可以喺度填表、提交 request，或者直接連結去 GitHub issue。
            </p>

            <div className="space-y-3">
              <input
                type="text"
                placeholder="課程名稱 / Course title"
                className="w-full bg-pill-bg text-text placeholder-text-faint px-3 py-2.5 rounded text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                disabled
              />
              <textarea
                placeholder="簡述原因 / Why do you need this course?"
                rows={3}
                className="w-full bg-pill-bg text-text placeholder-text-faint px-3 py-2.5 rounded text-sm focus:outline-none focus:ring-1 focus:ring-accent resize-none"
                disabled
              />
              <button
                className="w-full py-2.5 rounded font-bold text-sm bg-accent text-black opacity-60 cursor-not-allowed"
                disabled
              >
                提交申請（即將開放）
              </button>
            </div>

            <p className="text-text-faint text-xs mt-4 text-center">
              Placeholder modal · 功能稍後實作
            </p>
          </div>
        </>
      )}
    </div>
  )
}
