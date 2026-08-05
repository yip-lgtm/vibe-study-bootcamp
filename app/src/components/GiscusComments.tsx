import { useEffect, useRef } from 'react'

interface Props {
  /** Unique term for this discussion (use course.id) */
  term: string
  /** Optional title shown above the widget */
  title?: string
}

const REPO = 'yip-lgtm/vibe-study-bootcamp'
const REPO_ID = 'R_kgDOTt1gqQ'
const CATEGORY = 'General'
const CATEGORY_ID = 'DIC_kwDOTt1gqc4DCs88'

export function GiscusComments({ term, title = '討論 / Discussion' }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Clear previous iframe/script when term changes
    container.innerHTML = ''

    const script = document.createElement('script')
    script.src = 'https://giscus.app/client.js'
    script.async = true
    script.crossOrigin = 'anonymous'
    script.setAttribute('data-repo', REPO)
    script.setAttribute('data-repo-id', REPO_ID)
    script.setAttribute('data-category', CATEGORY)
    script.setAttribute('data-category-id', CATEGORY_ID)
    script.setAttribute('data-mapping', 'specific')
    script.setAttribute('data-term', term)
    script.setAttribute('data-strict', '0')
    script.setAttribute('data-reactions-enabled', '1')
    script.setAttribute('data-emit-metadata', '0')
    script.setAttribute('data-input-position', 'bottom')
    script.setAttribute('data-theme', 'dark')
    script.setAttribute('data-lang', 'zh-TW')
    script.setAttribute('data-loading', 'lazy')

    container.appendChild(script)

    return () => {
      container.innerHTML = ''
    }
  }, [term])

  return (
    <section className="px-4 pb-8">
      <h2 className="text-accent font-bold mb-3 flex items-center gap-2">
        💬 {title}
      </h2>
      <div className="giscus-wrapper rounded-xl overflow-hidden min-h-[120px]" ref={containerRef} />
      <p className="text-text-faint text-xs mt-3 text-center">
        討論由 GitHub Discussions 驅動 · 需要 GitHub 帳號先可以留言
      </p>
    </section>
  )
}
