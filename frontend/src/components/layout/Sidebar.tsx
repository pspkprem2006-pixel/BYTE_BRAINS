import { NavLink } from 'react-router-dom'
import { GraduationCap, LogOut } from 'lucide-react'
import { navItems } from './navItems'

function Brand() {
  return (
    <div className="flex items-center gap-3 px-5 py-5">
      <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
        <GraduationCap className="h-5 w-5" aria-hidden="true" />
      </span>
      <div>
        <p className="text-base font-bold tracking-tight text-slate-900">ByteBrains</p>
        <p className="text-xs text-slate-500">Smarter Learning. Powered by AI.</p>
      </div>
    </div>
  )
}

/**
 * Navigation list. Rendered inside both the desktop sidebar and the
 * mobile drawer, so styling lives in one place.
 */
export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <Brand />

      <nav aria-label="Primary" className="mt-4 flex-1 space-y-1 overflow-y-auto px-3">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={`h-4.5 w-4.5 shrink-0 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`}
                  aria-hidden="true"
                />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-200 p-3">
        <div className="flex items-center gap-3 rounded-xl px-2 py-2">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-bold text-slate-600">
            AS
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-900">Alex Student</p>
            <p className="truncate text-xs text-slate-500">Personal plan</p>
          </div>
          <button
            type="button"
            aria-label="Log out"
            title="Log out (arrives with authentication)"
            className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}