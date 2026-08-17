import { useState, useEffect } from 'react'

// Listen for PWA install prompt event
// Show floating "Install App" button when available
export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)
  const [showPrompt, setShowPrompt] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const [installed, setInstalled] = useState(false)

  useEffect(() => {
    // Already installed?
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setInstalled(true)
      return
    }
    if ((window.navigator as any).standalone === true) {
      setInstalled(true)
      return
    }
    // Was user already prompted / dismissed in last 7 days?
    const lastDismissed = localStorage.getItem('pwa_install_dismissed')
    if (lastDismissed) {
      const elapsed = Date.now() - parseInt(lastDismissed)
      if (elapsed < 7 * 24 * 60 * 60 * 1000) {
        setDismissed(true)
        return
      }
    }
    // Wait for the browser to fire the beforeinstallprompt event
    const handler = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e)
      // Show after 30s of app usage
      setTimeout(() => setShowPrompt(true), 30_000)
    }
    window.addEventListener('beforeinstallprompt', handler)
    window.addEventListener('appinstalled', () => setInstalled(true))
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  if (installed || dismissed || !showPrompt || !deferredPrompt) return null

  const handleInstall = async () => {
    setShowPrompt(false)
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'dismissed') {
      setDismissed(true)
      localStorage.setItem('pwa_install_dismissed', String(Date.now()))
    } else {
      setInstalled(true)
    }
  }

  const handleDismiss = () => {
    setShowPrompt(false)
    setDismissed(true)
    localStorage.setItem('pwa_install_dismissed', String(Date.now()))
  }

  return (
    <div className="fixed bottom-20 left-3 right-3 z-30 bg-card border border-accent/40 rounded-xl p-4 shadow-2xl flex items-center gap-3 fade-up">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-bold text-text">📲 加到主畫面</p>
        <p className="text-xs text-text-dim mt-0.5">離線可用 · 905 個課程 · 一 click 即開</p>
      </div>
      <button
        onClick={handleInstall}
        className="bg-accent text-black px-3 py-1.5 rounded-lg text-xs font-bold tap-active whitespace-nowrap"
      >
        Install
      </button>
      <button
        onClick={handleDismiss}
        className="text-text-faint text-lg leading-none px-1 tap-active"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  )
}
