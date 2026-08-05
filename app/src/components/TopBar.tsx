import type { FC } from 'react'

interface Props {
  screen: 'home' | 'detail' | 'following' | 'saved' | 'search'
  searchQuery: string
  onSearchChange: (s: string) => void
  onMenu: () => void
  onFilter: () => void
  onBack: () => void
}

export const TopBar: FC<Props> = ({ screen, searchQuery, onSearchChange, onMenu, onFilter, onBack }) => {
  if (screen === 'detail') {
    return (
      <div className="flex items-center h-12 px-2 border-b border-divider bg-black flex-shrink-0">
        <button onClick={onBack} className="px-3 py-2 text-accent text-2xl tap-active">‹</button>
        <div className="flex-1 text-center font-bold truncate text-sm">課程詳情</div>
        <button onClick={onMenu} className="px-3 py-2 text-accent text-2xl tap-active">⋯</button>
      </div>
    )
  }

  return (
    <div className="flex items-center h-12 px-2 border-b border-divider bg-black flex-shrink-0">
      <button onClick={onMenu} className="px-3 py-2 text-accent text-2xl tap-active">≡</button>
      {screen === 'search' ? (
        <div className="flex-1 relative flex items-center">
          <input
            autoFocus
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="搜尋課程、學者、模型..."
            className="w-full bg-pill-bg text-text placeholder-text-faint px-3 py-1.5 pr-8 rounded text-sm focus:outline-none focus:ring-1 focus:ring-accent"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2 text-text-dim text-lg leading-none tap-active px-1"
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>
      ) : (
        <div className="flex-1 text-center font-bold text-sm">
          <span className="text-accent">⚡</span>{' '}
          <span className="text-text">修學旅行</span>
        </div>
      )}
      <button onClick={onFilter} className="px-3 py-2 text-accent text-2xl tap-active">≡</button>
    </div>
  )
}
