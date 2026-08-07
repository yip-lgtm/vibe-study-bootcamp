import type { FC } from 'react'
import { getCategories, getTotalCount, getBootcampCount } from '../utils/categories'

interface Props {
  onClose: () => void
  onNavigate: (s: 'home' | 'following' | 'saved' | 'search') => void
  onSelectCategory: (category: string) => void
  currentScreen: string
  currentCategory: string
}

const NAV = [
  { icon: '🔍', label: '搜尋 Search', screen: 'search' as const },
  { icon: '👥', label: '追蹤中 Following', screen: 'following' as const },
  { icon: '📁', label: '收藏 Saved', screen: 'saved' as const },
  { icon: '🏠', label: '全部 All', screen: 'home' as const },
]

export const Sidebar: FC<Props> = ({
  onClose,
  onNavigate,
  onSelectCategory,
  currentScreen,
  currentCategory,
}) => {
  const categories = getCategories()
  const total = getTotalCount()
  const bootcamps = getBootcampCount()
  return (
    <div className="h-full bg-black flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-divider">
        <div className="text-3xl">📚</div>
        <div className="font-bold text-accent text-lg mt-2">修學旅行</div>
        <div className="text-text-dim text-xs mt-1">
          Self-Study Hub · {bootcamps} bootcamps · {total} courses
        </div>
      </div>

      {/* Main nav */}
      <div className="flex-1 overflow-y-auto py-2">
        {NAV.map((item) => (
          <button
            key={item.label}
            onClick={() => onNavigate(item.screen)}
            className={`w-full flex items-center gap-3 px-5 py-3 text-left tap-active ${
              currentScreen === item.screen && currentCategory === 'all' ? 'bg-pill-bg' : ''
            }`}
          >
            <span className="text-xl">{item.icon}</span>
            <span
              className={`text-sm ${
                currentScreen === item.screen && currentCategory === 'all' ? 'text-accent' : 'text-text'
              }`}
            >
              {item.label}
            </span>
          </button>
        ))}

        <div className="px-5 py-3 mt-4">
          <div className="text-text-faint text-xs font-bold uppercase tracking-wider">Bootcamps</div>
        </div>
        {categories.map((cat) => {
          const isActive = currentCategory === cat.value && currentScreen === 'home'
          return (
            <button
              key={cat.value}
              onClick={() => onSelectCategory(cat.value)}
              className={`w-full flex items-center gap-3 px-5 py-2.5 text-left tap-active ${
                isActive ? 'bg-pill-bg' : ''
              }`}
            >
              <span className="text-base">{cat.icon}</span>
              <span className={`text-sm flex-1 ${isActive ? 'text-accent' : 'text-text'}`}>
                {cat.label}
              </span>
              <span className="text-xs text-text-faint">{cat.count}</span>
            </button>
          )
        })}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-divider text-xs text-text-faint">
        <div>v1.0.0 · 100% APPROVED</div>
        <button onClick={onClose} className="mt-2 text-accent text-sm tap-active">
          關閉 Close
        </button>
      </div>
    </div>
  )
}
