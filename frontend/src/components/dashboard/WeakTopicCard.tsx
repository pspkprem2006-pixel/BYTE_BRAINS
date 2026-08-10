import { AlertTriangle, CheckCircle2, TrendingUp, type LucideIcon } from 'lucide-react'
import type { WeakTopic, WeakTopicLevel } from '../../data/mockData'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'
import { ProgressBar } from '../ui/ProgressBar'

const levelMeta: Record<
  WeakTopicLevel,
  { label: string; tone: 'rose' | 'amber' | 'emerald'; icon: LucideIcon }
> = {
  critical: { label: 'Critical', tone: 'rose', icon: AlertTriangle },
  'needs-improvement': { label: 'Needs improvement', tone: 'amber', icon: TrendingUp },
  good: { label: 'Good', tone: 'emerald', icon: CheckCircle2 },
}

export function WeakTopicCard({ topic }: { topic: WeakTopic }) {
  const meta = levelMeta[topic.level]

  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold">{topic.name}</h3>
        <Badge tone={meta.tone}>
          <meta.icon className="h-3 w-3" aria-hidden="true" />
          {meta.label}
        </Badge>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-slate-500">Mastery</span>
        <span className="font-semibold">{topic.score}%</span>
      </div>
      <ProgressBar value={topic.score} tone={meta.tone} className="mt-2" />
    </Card>
  )
}