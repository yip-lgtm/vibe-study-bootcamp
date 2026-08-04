import type { FC } from 'react'

interface Props {
  onClose: () => void
  category: string
  setCategory: (s: string) => void
  hasScholars: boolean
  setHasScholars: (b: boolean) => void
  hasEquations: boolean
  setHasEquations: (b: boolean) => void
  minLines: number
  setMinLines: (n: number) => void
  sortBy: 'newest' | 'lines' | 'title' | 'category'
  setSortBy: (s: 'newest' | 'lines' | 'title' | 'category') => void
  counts: Record<string, number>
}

const CATEGORIES = [
  { value: 'all', label: '全部 All' },
  { value: 'Engineering', label: '⚙️ Engineering' },
  { value: 'Physics', label: '⚛️ Physics' },
  { value: 'History', label: '📚 History' },
  { value: 'Psychology', label: '🧠 Psychology' },
  { value: 'Mech-Eng', label: '🤖 Mech-Eng' },
  { value: 'BME', label: '🧬 BME' },
]

export const FilterPanel: FC<Props> = ({
  onClose, category, setCategory, hasScholars, setHasScholars,
  hasEquations, setHasEquations, minLines, setMinLines, sortBy, setSortBy, counts,
}) => {
  return (
    <div className="h-full bg-black flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-divider">
        <div className="flex items-center justify-between">
          <div className="font-bold text-accent text-lg">🔍 篩選 Filter</div>
          <button onClick={onClose} className="text-accent text-2xl tap-active px-2">×</button>
        </div>
        <div className="text-text-dim text-xs mt-1">{counts[category] ?? 0} 個 courses</div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Category */}
        <div>
          <div className="text-text-faint text-xs font-bold mb-2 uppercase">類別 Category</div>
          <div className="space-y-1">
            {CATEGORIES.map(c => (
              <button
                key={c.value}
                onClick={() => setCategory(c.value)}
                className={`w-full text-left px-3 py-2 rounded text-sm tap-active ${
                  category === c.value ? 'bg-pill-bg text-accent' : 'text-text'
                }`}
              >
                {c.label}
                {c.value !== 'all' && counts[c.value] && (
                  <span className="float-right text-text-faint text-xs">{counts[c.value]}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Quality filters */}
        <div>
          <div className="text-text-faint text-xs font-bold mb-2 uppercase">質素 Quality</div>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-text text-sm">
              <input
                type="checkbox"
                checked={hasScholars}
                onChange={(e) => setHasScholars(e.target.checked)}
                className="accent-accent"
              />
              含學者引用 (Scholars)
            </label>
            <label className="flex items-center gap-2 text-text text-sm">
              <input
                type="checkbox"
                checked={hasEquations}
                onChange={(e) => setHasEquations(e.target.checked)}
                className="accent-accent"
              />
              ≥3 LaTeX equations
            </label>
            <div className="mt-2">
              <div className="text-text text-sm mb-1">最少行數: {minLines}</div>
              <input
                type="range"
                min="0"
                max="600"
                step="50"
                value={minLines}
                onChange={(e) => setMinLines(parseInt(e.target.value))}
                className="w-full accent-accent"
              />
            </div>
          </div>
        </div>

        {/* Sort */}
        <div>
          <div className="text-text-faint text-xs font-bold mb-2 uppercase">排序 Sort</div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { v: 'category', l: '類別' },
              { v: 'lines', l: '行數' },
              { v: 'title', l: '標題' },
              { v: 'newest', l: '新' },
            ].map(s => (
              <button
                key={s.v}
                onClick={() => setSortBy(s.v as any)}
                className={`px-3 py-2 rounded text-sm tap-active ${
                  sortBy === s.v ? 'bg-accent text-black' : 'bg-pill-bg text-text'
                }`}
              >
                {s.l}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-divider">
        <button
          onClick={onClose}
          className="w-full py-3 bg-accent text-black font-bold rounded tap-active"
        >
          套用 Apply
        </button>
      </div>
    </div>
  )
}
