import type { StudyPlanItem } from '../../data/mockData'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

interface StudyPlanPreviewProps {
  items: StudyPlanItem[]
}

export function StudyPlanPreview({ items }: StudyPlanPreviewProps) {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Today's plan</h3>
        <Badge tone="indigo">TODAY</Badge>
      </div>
      <ul className="mt-2 flex-1 divide-y divide-slate-100">
        {items.map((item) => (
          <li key={item.id} className="flex items-center gap-4 py-3">
            <span className="w-12 shrink-0 text-sm font-semibold text-slate-400">
              {item.time}
            </span>
            <span className="text-sm font-medium text-slate-800">{item.title}</span>
          </li>
        ))}
      </ul>
      <Button to="/study-plan" variant="ghost" size="sm" className="mt-2 w-full">
        View Study Plan
      </Button>
    </Card>
  )
}