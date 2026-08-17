import coursesData from '../data/courses.json'

export interface CategoryInfo {
  value: string
  label: string
  icon: string
  color: string
  count: number
}

// Stable icon and color map per category
const CATEGORY_META: Record<string, { icon: string; label: string; color: string }> = {
  'Civil Engineering':          { icon: '🏗️', label: 'Civil Engineering',          color: 'bg-amber-900/40 text-amber-300' },
  'Physics':                    { icon: '⚛️',  label: 'Physics',                    color: 'bg-purple-900/40 text-purple-300' },
  'History':                    { icon: '📚',  label: 'History',                    color: 'bg-amber-900/40 text-amber-300' },
  'Psychology':                 { icon: '🧠',  label: 'Psychology',                 color: 'bg-pink-900/40 text-pink-300' },
  'Mech-Eng':                   { icon: '⚙️',  label: 'Mech-Eng',                   color: 'bg-cyan-900/40 text-cyan-300' },
  'BME':                        { icon: '🧬',  label: 'BME',                        color: 'bg-emerald-900/40 text-emerald-300' },
  'Robotics & Structural Eng':  { icon: '🤖', label: 'Robotics & Structural Eng',  color: 'bg-indigo-900/40 text-indigo-300' },
  'Digital Economics':          { icon: '💰',  label: 'Digital Economics',          color: 'bg-yellow-900/40 text-yellow-300' },
  'Engineering':                { icon: '🛠️',  label: 'Engineering',                color: 'bg-blue-900/40 text-blue-300' },
}

const FALLBACK_META = { icon: '📖', label: '', color: 'bg-slate-800 text-slate-300' }

export function getCategories(): CategoryInfo[] {
  const byCat: Record<string, number> = (coursesData as any).by_category || {}
  return Object.keys(byCat)
    .filter(k => byCat[k] > 0) // skip zero-count cats
    .map(k => {
      const meta = CATEGORY_META[k] || { ...FALLBACK_META, label: k }
      return {
        value: k,
        label: meta.label,
        icon: meta.icon,
        color: meta.color,
        count: byCat[k],
      }
    })
    .sort((a, b) => b.count - a.count) // largest first
}

export function getCategoryColor(category: string): string {
  return CATEGORY_META[category]?.color || FALLBACK_META.color
}

export function getCategoryIcon(category: string): string {
  return CATEGORY_META[category]?.icon || FALLBACK_META.icon
}

export function getTotalCount(): number {
  return (coursesData as any).total || 0
}

export function getBootcampCount(): number {
  return getCategories().length
}

export function getLastUpdated(): string {
  return (coursesData as any).last_updated || ''
}
