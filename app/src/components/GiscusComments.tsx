import { useEffect, useState } from 'react'
import Giscus from '@giscus/react'

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
  const [ready, setReady] = useState(false)

  // Only mount after a short delay so the SPA transition is smooth
  useEffect(() => {
    const t = setTimeout(() => setReady(true), 150)
    return () => clearTimeout(t)
  }, [term])

  if (!ready) {
    return (
      <div className="px-4 py-6 text-center text-text-faint text-sm">
        載入討論區…
      </div>
    )
  }

  return (
    <section className="px-4 pb-8">
      <h2 className="text-accent font-bold mb-3 flex items-center gap-2">
        💬 {title}
      </h2>
      <div className="giscus-wrapper rounded-xl overflow-hidden">
        <Giscus
          id={`giscus-${term}`}
          repo={REPO}
          repoId={REPO_ID}
          category={CATEGORY}
          categoryId={CATEGORY_ID}
          mapping="specific"
          term={term}
          strict="0"
          reactionsEnabled="1"
          emitMetadata="0"
          inputPosition="bottom"
          theme="dark"
          lang="zh-TW"
          loading="lazy"
        />
      </div>
      <p className="text-text-faint text-xs mt-3 text-center">
        討論由 GitHub Discussions 驅動 · 需要 GitHub 帳號先可以留言
      </p>
    </section>
  )
}
