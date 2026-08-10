import { CheckCircle2, Clock, Flame, Target } from 'lucide-react'
import { StudyPlanPreview } from '../components/dashboard/StudyPlanPreview'
import { SubjectCard } from '../components/dashboard/SubjectCard'
import { WeakTopicCard } from '../components/dashboard/WeakTopicCard'
import { PageHeader } from '../components/ui/PageHeader'
import { StatCard } from '../components/ui/StatCard'
import {
  studentStats,
  subjects,
  todaysStudyPlan,
  weakTopics,
} from '../data/mockData'

export function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Good morning 👋"
        subtitle="Let's continue building your knowledge today."
      />

      <section aria-label="Your stats" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Overall Progress"
          value={`${studentStats.overallProgress}%`}
          hint="+6% this week"
          icon={Target}
        />
        <StatCard
          label="Topics Completed"
          value={String(studentStats.topicsCompleted)}
          hint="of 52 topics"
          icon={CheckCircle2}
        />
        <StatCard
          label="Study Streak"
          value={`${studentStats.studyStreakDays} days`}
          hint="Keep it going!"
          icon={Flame}
        />
        <StatCard
          label="Study Time"
          value={`${studentStats.studyTimeHours} hrs`}
          hint="this week"
          icon={Clock}
        />
      </section>

      <section aria-labelledby="continue-heading" className="mt-10">
        <div className="mb-4">
          <h2 id="continue-heading" className="text-lg font-semibold">
            Continue learning
          </h2>
          <p className="text-sm text-slate-500">Pick up where you left off.</p>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {subjects.map((subject) => (
            <SubjectCard key={subject.id} subject={subject} />
          ))}
        </div>
      </section>

      <section className="mt-10 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section aria-labelledby="weak-heading">
          <div className="mb-4">
            <h2 id="weak-heading" className="text-lg font-semibold">
              Weak topics
            </h2>
            <p className="text-sm text-slate-500">
              Focus areas suggested by your performance.
            </p>
          </div>
          <div className="space-y-4">
            {weakTopics.map((topic) => (
              <WeakTopicCard key={topic.id} topic={topic} />
            ))}
          </div>
        </section>

        <StudyPlanPreview items={todaysStudyPlan} />
      </section>
    </>
  )
}