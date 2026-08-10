import { CalendarDays, Files, Pencil, Trash2 } from 'lucide-react'
import type { Subject } from '../../types/subject'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

interface SubjectCardProps {
  subject: Subject
  materialsCount?: number
  onEdit?: () => void
  onDelete?: () => void
}

export function SubjectCard({ subject, materialsCount = 0, onEdit, onDelete }: SubjectCardProps) {
  return (
    <Card className="flex h-full flex-col transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold">{subject.name}</h3>
        <Badge tone="indigo">
          {materialsCount} {materialsCount === 1 ? 'material' : 'materials'}
        </Badge>
      </div>
      {subject.description && (
        <p className="mt-1 text-sm text-slate-500">{subject.description}</p>
      )}
      <p className="mt-3 inline-flex items-center gap-1 text-xs text-slate-400">
        <CalendarDays className="h-3.5 w-3.5" aria-hidden="true" />
        Created {new Date(subject.created_at).toLocaleDateString()}
      </p>

      <div className="mt-5 flex-1" />
      <div className="flex items-center gap-2">
        <Button to="/materials" variant="outline" size="sm" className="flex-1">
          <Files className="h-4 w-4" aria-hidden="true" />
          Manage Materials
        </Button>
        {onEdit && (
          <Button variant="ghost" size="sm" onClick={onEdit} aria-label={`Edit ${subject.name}`}>
            <Pencil className="h-4 w-4" aria-hidden="true" />
          </Button>
        )}
        {onDelete && (
          <Button variant="ghost" size="sm" onClick={onDelete} aria-label={`Delete ${subject.name}`}>
            <Trash2 className="h-4 w-4 text-rose-600" aria-hidden="true" />
          </Button>
        )}
      </div>
    </Card>
  )
}
