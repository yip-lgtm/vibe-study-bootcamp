import type { FC } from 'react'

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

const CATS = [
  { icon: '⚙️', label: 'Engineering', value: 'Engineering' },
  { icon: '⚛️', label: 'Physics', value: 'Physics' },
  { icon: '📚', label: 'History', value: 'History' },
  { icon: '🧠', label: 'Psychology', value: 'Psychology' },
  { icon: '🤖', label: 'Mech-Eng', value: 'Mech-Eng' },
  { icon: '🧬', label: 'BME', value: 'BME' },
]

export const Sidebar: FC<Props> = ({
  onClose,
  onNavigate,
  onSelectCategory,
  currentScreen,
  currentCategory,
}) => {
  return (
    <div className="h-full bg-black flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-divider">
        <div className="text-3xl">📚</div>
        <div className="font-bold text-accent text-lg mt-2">修學旅行</div>
        <div className="text-text-dim text-xs mt-1">Self-Study Hub · 6 bootcamps · 519 courses</div>
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
        {CATS.map((item) => {
          const isActive = currentCategory === item.value && currentScreen === 'home'
          return (
            <button
              key={item.label}
              onClick={() => onSelectCategory(item.value)}
              className={`w-full flex items-center gap-3 px-5 py-2.5 text-left tap-active ${
                isActive ? 'bg-pill-bg' : ''
              }`}
            >
              <span className="text-base">{item.icon}</span>
              <span className={`text-sm ${isActive ? 'text-accent' : 'text-text'}`}>
                {item.label}
              </span>
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
