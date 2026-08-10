type ProgressTone = 'indigo' | 'emerald' | 'amber' | 'rose'

const barTones: Record<ProgressTone, string> = {
  indigo: 'bg-indigo-600',
  emerald: 'bg-emerald-500',
  amber: 'bg-amber-500',
  rose: 'bg-rose-500',
}

interface ProgressBarProps {
  value: number
  /** Color of the filled portion. */
  tone?: ProgressTone
  className?: string
}

export function ProgressBar({ value, tone = 'indigo', className = '' }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value))

  return (
    <div
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Progress"
      className={`h-2 w-full overflow-hidden rounded-full bg-slate-100 ${className}`}
    >
      <div
        className={`h-full rounded-full ${barTones[tone]}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  )
}