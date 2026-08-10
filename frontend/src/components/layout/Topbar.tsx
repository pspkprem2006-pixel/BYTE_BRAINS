import { useLocation } from 'react-router-dom'
import { Bell, Menu, Search } from 'lucide-react'
import { navItems } from './navItems'

interface TopbarProps {
  onMenuClick: () => void
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const location = useLocation()
  const current = navItems.find((item) => item.to === location.pathname) ?? navItems[0]

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="flex items-center gap-3 px-4 py-3 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation"
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>

        <h1 className="min-w-0 truncate text-lg font-semibold tracking-tight">
          {current.label}
        </h1>

        <div className="ml-auto flex items-center gap-2">
          <div className="relative hidden md:block">
            <label htmlFor="global-search" className="sr-only">
              Search ByteBrains
            </label>
            <Search
              className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <input
              id="global-search"
              type="search"
              placeholder="Search topics, materials, quizzes…"
              className="w-56 rounded-xl border border-slate-200 bg-slate-50 py-2 pr-3 pl-9 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600/20 lg:w-72"
            />
          </div>

          <button
            type="button"
            aria-label="Notifications"
            className="relative rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100"
          >
            <Bell className="h-5 w-5" aria-hidden="true" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-indigo-600" />
          </button>

          <button
            type="button"
            aria-label="Open profile menu"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-xs font-bold text-slate-600 transition-colors hover:bg-slate-300"
          >
            AS
          </button>
        </div>
      </div>
    </header>
  )
}