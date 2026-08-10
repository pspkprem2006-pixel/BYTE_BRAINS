import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { X } from 'lucide-react'
import { SidebarContent } from './Sidebar'
import { Topbar } from './Topbar'

/**
 * Shared application shell: fixed sidebar on desktop, slide-in drawer on
 * mobile, sticky top bar, and a scrollable main content area.
 */
export function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  // Close the mobile drawer with the Escape key.
  useEffect(() => {
    if (!mobileNavOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileNavOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [mobileNavOpen])

  // Prevent background scrolling while the drawer is open.
  useEffect(() => {
    document.body.style.overflow = mobileNavOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [mobileNavOpen])

  return (
    <div className="min-h-screen">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <SidebarContent />
      </aside>

      {/* Mobile drawer */}
      <div
        className={`fixed inset-0 z-50 lg:hidden ${mobileNavOpen ? '' : 'pointer-events-none'}`}
      >
        <div
          className={`absolute inset-0 bg-slate-900/50 transition-opacity ${
            mobileNavOpen ? 'opacity-100' : 'opacity-0'
          }`}
          onClick={() => setMobileNavOpen(false)}
          aria-hidden="true"
        />
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
          className={`absolute inset-y-0 left-0 flex w-72 max-w-[85%] flex-col bg-white shadow-xl transition-transform ${
            mobileNavOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <SidebarContent onNavigate={() => setMobileNavOpen(false)} />
          <button
            type="button"
            onClick={() => setMobileNavOpen(false)}
            aria-label="Close navigation"
            autoFocus
            className="absolute top-4 right-4 rounded-lg p-2 text-slate-500 hover:bg-slate-100"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* Main column */}
      <div className="lg:pl-64">
        <Topbar onMenuClick={() => setMobileNavOpen(true)} />
        <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}