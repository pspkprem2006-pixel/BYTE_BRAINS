import { ArrowRight, Clock, Pencil, Trash2 } from 'lucide-react'
import type { Subject } from '../../data/mockData'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { ProgressBar } from '../ui/ProgressBar'

interface SubjectCardProps {
  subject: Subject
  /** "full" also shows topic count and last-studied meta rows. */
  variant?: 'overview' | 'full'
  onEdit?: () => void
  onDelete?: () => void
}

export function SubjectCard({ subject, variant = 'overview', onEdit, onDelete }: SubjectCardProps) {
  return (
    <Card className="flex h-full flex-col">
      <h3 className="font-semibold">{subject.name}</h3>
      <p className="mt-1 text-sm text-slate-500">{subject.description}</p>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-slate-500">Progress</span>
        <span className="font-semibold">{subject.progress}%</span>
      </div>
      <ProgressBar value={subject.progress} className="mt-2" />

      {variant === 'full' && (
        <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
          <span>{subject.topicCount} topics</span>
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" aria-hidden="true" />
            {subject.lastStudied}
          </span>
        </div>
      )}

      <div className="mt-5 flex-1" />
      <div className="flex items-center gap-2">
        <Button to="/tutor" variant="outline" size="sm" className="flex-1">
          Continue
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Button>
        {onEdit && (
          <Button variant="ghost" size="sm" onClick={onEdit} aria-label="Edit subject">
            <Pencil className="h-4 w-4" aria-hidden="true" />
          </Button>
        )}
        {onDelete && (
          <Button variant="ghost" size="sm" onClick={onDelete} aria-label="Delete subject">
            <Trash2 className="h-4 w-4 text-rose-600" aria-hidden="true" />
          </Button>
        )}
      </div>
    </Card>
  )
}