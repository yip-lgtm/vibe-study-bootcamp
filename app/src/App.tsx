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

  // Filters
  const [filterCategory, setFilterCategory] = useState<string>('all')
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
  }, [courses, screen, searchQuery, filterCategory, filterHasScholars, filterHasEquations, filterMinLines, sortBy, followed, saved])

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
              setCategory={setFilterCategory}
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
    </div>
  )
}
