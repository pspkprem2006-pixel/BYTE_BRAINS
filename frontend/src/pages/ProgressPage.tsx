import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { WeakTopicCard } from '../components/dashboard/WeakTopicCard'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { subjects, topicPerformance, weeklyActivity } from '../data/mockData'

const subjectProgress = subjects.map((subject) => ({
  name: subject.name,
  progress: subject.progress,
}))

export function ProgressPage() {
  return (
    <>
      <PageHeader
        title="Progress"
        subtitle="Your learning analytics at a glance."
      />

      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <span className="text-4xl font-bold tracking-tight">74%</span>
          <span className="text-sm text-slate-500">overall progress</span>
        </div>
        <Badge tone="neutral">Demo data — charts will use real analytics later</Badge>
      </div>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <h2 className="text-base font-semibold">Weekly study activity</h2>
          <p className="text-sm text-slate-500">Minutes studied per day</p>
          <div className="mt-4 h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyActivity} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="minutes"
                  stroke="#4f46e5"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#4f46e5', strokeWidth: 0 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h2 className="text-base font-semibold">Subject comparison</h2>
          <p className="text-sm text-slate-500">Progress per subject (%)</p>
          <div className="mt-4 h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={subjectProgress} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip />
                <Bar dataKey="progress" fill="#4f46e5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </section>

      <section aria-labelledby="topic-performance-heading" className="mt-10">
        <div className="mb-4">
          <h2 id="topic-performance-heading" className="text-lg font-semibold">
            Topic performance
          </h2>
          <p className="text-sm text-slate-500">Mastery per topic, from weakest to strongest.</p>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {topicPerformance.map((topic) => (
            <WeakTopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      </section>
    </>
  )
}