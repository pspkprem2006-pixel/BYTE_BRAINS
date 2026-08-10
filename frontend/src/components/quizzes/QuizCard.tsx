import type { Quiz } from '../../data/mockData'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

const difficultyMeta = {
  Easy: { tone: 'emerald' as const },
  Medium: { tone: 'amber' as const },
  Hard: { tone: 'rose' as const },
}

interface QuizCardProps {
  quiz: Quiz
}

export function QuizCard({ quiz }: QuizCardProps) {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold tracking-wide text-indigo-600 uppercase">
            {quiz.subject}
          </p>
          <h3 className="mt-1 font-semibold">{quiz.topic}</h3>
        </div>
        <Badge tone={difficultyMeta[quiz.difficulty].tone}>{quiz.difficulty}</Badge>
      </div>

      <p className="mt-2 text-sm text-slate-500">{quiz.questionCount} questions</p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {quiz.score !== undefined && quiz.completedAt && (
          <Badge tone="indigo">
            Score: {quiz.score}% · {quiz.completedAt}
          </Badge>
        )}
      </div>

      <div className="mt-5 flex-1" />
      <Button variant="outline" size="sm" className="w-full">
        Start Quiz
      </Button>
    </Card>
  )
}