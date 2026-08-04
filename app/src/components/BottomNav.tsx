import type { FC } from 'react'

interface Props {
  current: string
  onChange: (s: 'home' | 'following' | 'saved' | 'search') => void
  followingCount: number
  savedCount: number
}

export const BottomNav: FC<Props> = ({ current, onChange, followingCount, savedCount }) => {
  return (
    <div className="absolute bottom-0 left-0 right-0 h-14 bg-black border-t border-divider flex items-center justify-around z-30">
      <button
        onClick={() => onChange('home')}
        className={`flex flex-col items-center gap-0.5 px-3 py-1.5 tap-active ${
          current === 'home' ? 'text-accent' : 'text-text-dim'
        }`}
      >
        <span className="text-xl">☰</span>
        <span className="text-[10px]">全部</span>
      </button>
      <button
        onClick={() => onChange('search')}
        className={`flex flex-col items-center gap-0.5 px-3 py-1.5 tap-active ${
          current === 'search' ? 'text-accent' : 'text-text-dim'
        }`}
      >
        <span className="text-2xl font-light">+</span>
      </button>
      <button
        onClick={() => onChange('search')}
        className={`flex flex-col items-center gap-0.5 px-3 py-1.5 tap-active ${
          current === 'search' ? 'text-accent' : 'text-text-dim'
        }`}
      >
        <span className="text-xl">🔍</span>
        <span className="text-[10px]">搜尋</span>
      </button>
      <button
        onClick={() => onChange('saved')}
        className={`flex flex-col items-center gap-0.5 px-3 py-1.5 tap-active relative ${
          current === 'saved' ? 'text-accent' : 'text-text-dim'
        }`}
      >
        <span className="text-xl">🔖</span>
        <span className="text-[10px]">收藏 {savedCount}</span>
      </button>
      <button
        onClick={() => onChange('following')}
        className={`flex flex-col items-center gap-0.5 px-3 py-1.5 tap-active ${
          current === 'following' ? 'text-accent' : 'text-text-dim'
        }`}
      >
        <span className="text-xl">↻</span>
        <span className="text-[10px]">追蹤 {followingCount}</span>
      </button>
    </div>
  )
}
