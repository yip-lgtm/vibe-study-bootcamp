// Type definitions
export interface Course {
  id: string
  title: string
  repo: string
  category: string
  path: string
  url: string
  lines: number
  models: string[]
  disagreements: string[]
  scholars: string[]
  equations: number
  mermaid: number
  chinese_chars: number
}

// Local storage helpers for following/saved
const FOLLOW_KEY = 'allbootcamp_follow'
const SAVED_KEY = 'allbootcamp_saved'

export function loadFollow(): Set<string> {
  try {
    const raw = localStorage.getItem(FOLLOW_KEY)
    return new Set(raw ? JSON.parse(raw) : [])
  } catch { return new Set() }
}

export function loadSaved(): Set<string> {
  try {
    const raw = localStorage.getItem(SAVED_KEY)
    return new Set(raw ? JSON.parse(raw) : [])
  } catch { return new Set() }
}

export function toggleFollow(id: string): Set<string> {
  const s = loadFollow()
  if (s.has(id)) s.delete(id)
  else s.add(id)
  localStorage.setItem(FOLLOW_KEY, JSON.stringify(Array.from(s)))
  return s
}

export function toggleSaved(id: string): Set<string> {
  const s = loadSaved()
  if (s.has(id)) s.delete(id)
  else s.add(id)
  localStorage.setItem(SAVED_KEY, JSON.stringify(Array.from(s)))
  return s
}
