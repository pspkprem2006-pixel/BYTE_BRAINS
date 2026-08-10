import { useState, type ReactNode } from 'react'
import { Bell, Moon, SlidersHorizontal, User, type LucideIcon } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'

interface ToggleProps {
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

function Toggle({ label, description, checked, onChange, disabled = false }: ToggleProps) {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <div>
        <p className={`text-sm font-medium ${disabled ? 'text-slate-400' : 'text-slate-800'}`}>
          {label}
        </p>
        {description && <p className="text-xs text-slate-500">{description}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        aria-disabled={disabled}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
          disabled ? 'cursor-not-allowed bg-slate-200' : checked ? 'bg-indigo-600' : 'bg-slate-300'
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-all ${
            checked ? 'left-5.5' : 'left-0.5'
          }`}
        />
      </button>
    </div>
  )
}

function SectionCard({
  icon: Icon,
  title,
  badge,
  children,
}: {
  icon: LucideIcon
  title: string
  badge?: string
  children: ReactNode
}) {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-slate-400" aria-hidden="true" />
        <h2 className="text-base font-semibold">{title}</h2>
        {badge && <Badge tone="neutral" className="ml-auto">{badge}</Badge>}
      </div>
      <div className="mt-3">{children}</div>
    </Card>
  )
}

export function SettingsPage() {
  const [appearance, setAppearance] = useState('Light')
  const [quizReminders, setQuizReminders] = useState(true)
  const [streakReminders, setStreakReminders] = useState(true)
  const [studyGoal, setStudyGoal] = useState('2 hours')

  return (
    <>
      <PageHeader
        title="Settings"
        subtitle="Settings available today are marked below; the rest arrive in later phases."
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <SectionCard icon={User} title="Profile" badge="With account">
          <p className="text-sm text-slate-500">
            Profile details will become editable once student accounts arrive.
          </p>
          <dl className="mt-4 space-y-3">
            <div>
              <dt className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                Display name
              </dt>
              <dd className="mt-0.5 text-sm font-medium text-slate-800">Alex Student</dd>
            </div>
            <div>
              <dt className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                Email
              </dt>
              <dd className="mt-0.5 text-sm font-medium text-slate-800">
                alex.student@example.com
              </dd>
            </div>
          </dl>
        </SectionCard>

        <SectionCard icon={Moon} title="Appearance" badge="Visual only">
          <fieldset>
            <legend className="sr-only">Theme</legend>
            <div className="flex flex-wrap gap-2">
              {['Light', 'Dark', 'System'].map((theme) => (
                <button
                  key={theme}
                  type="button"
                  aria-pressed={appearance === theme}
                  onClick={() => setAppearance(theme)}
                  className={`rounded-xl border px-4 py-2 text-sm transition-colors ${
                    appearance === theme
                      ? 'border-indigo-300 bg-indigo-50 text-indigo-700'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-indigo-300 hover:bg-indigo-50'
                  }`}
                >
                  {theme}
                </button>
              ))}
            </div>
          </fieldset>
          <p className="mt-3 text-xs text-slate-400">
            Theme selection is visual only for now — dark mode arrives with the design
            system update.
          </p>
        </SectionCard>

        <SectionCard icon={Bell} title="Notifications" badge="Coming soon">
          <div className="divide-y divide-slate-100">
            <Toggle
              label="Quiz reminders"
              description="Remind me when it's time for a quiz."
              checked={quizReminders}
              onChange={setQuizReminders}
              disabled
            />
            <Toggle
              label="Streak reminders"
              description="Nudge me to keep my study streak alive."
              checked={streakReminders}
              onChange={setStreakReminders}
              disabled
            />
          </div>
          <p className="mt-3 text-xs text-slate-400">
            Notifications will be available with account support.
          </p>
        </SectionCard>

        <SectionCard icon={SlidersHorizontal} title="Study preferences" badge="Coming soon">
          <div className="space-y-4">
            <div>
              <label
                htmlFor="study-goal"
                className="block text-sm font-medium text-slate-400"
              >
                Daily study goal
              </label>
              <select
                id="study-goal"
                value={studyGoal}
                onChange={(event) => setStudyGoal(event.target.value)}
                disabled
                className="mt-1.5 w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              >
                <option value="30 minutes">30 minutes</option>
                <option value="1 hour">1 hour</option>
                <option value="2 hours">2 hours</option>
                <option value="3 hours">3 hours</option>
              </select>
            </div>
            <div>
              <label
                htmlFor="reminder-time"
                className="block text-sm font-medium text-slate-400"
              >
                Reminder time
              </label>
              <input
                id="reminder-time"
                type="time"
                defaultValue="18:00"
                disabled
                className="mt-1.5 w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-400 focus:border-indigo-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>
          </div>
        </SectionCard>
      </div>
    </>
  )
}