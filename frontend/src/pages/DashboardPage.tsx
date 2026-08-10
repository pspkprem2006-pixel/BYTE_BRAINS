import { useState, useEffect, useCallback } from 'react';
import {
  BookOpen,
  CalendarDays,
  FileText,
  Flame,
  FolderOpen,
  Loader2,
  AlertCircle,
  RotateCcw,
  Target,
  Sparkles,
  MessageSquareText,
  ListChecks,
  GraduationCap,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { getDashboardSummary } from '../services/dashboard';
import type { DashboardSummary } from '../services/dashboard';

function SectionHeading({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
    </div>
  );
}

const quickActions = [
  {
    label: 'Upload Material',
    icon: FileText,
    to: '/materials',
    tone: 'bg-indigo-50 text-indigo-600',
  },
  {
    label: 'Ask Tutor',
    icon: MessageSquareText,
    to: '/tutor',
    tone: 'bg-emerald-50 text-emerald-600',
  },
  {
    label: 'Generate Quiz',
    icon: ListChecks,
    to: '/quizzes',
    tone: 'bg-amber-50 text-amber-600',
  },
  {
    label: 'Study Plan',
    icon: CalendarDays,
    to: '/study-plan',
    tone: 'bg-rose-50 text-rose-600',
  },
];

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setSummary(await getDashboardSummary());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your dashboard.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (isLoading) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Your learning command center." />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" aria-hidden="true" />
          <span className="ml-3 text-sm text-slate-500">Loading your dashboard…</span>
        </div>
      </>
    );
  }

  if (error || !summary) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Your learning command center." />
        <Card className="border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Unable to load your dashboard</p>
              <p className="mt-1 text-sm text-rose-600">{error ?? 'Something went wrong.'}</p>
              <Button variant="outline" size="sm" onClick={load} className="mt-3">
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Retry
              </Button>
            </div>
          </div>
        </Card>
      </>
    );
  }

  const quizPercent =
    summary.quiz_session && summary.quiz_session.total > 0
      ? Math.round((summary.quiz_session.score / summary.quiz_session.total) * 100)
      : null;

  const todayTasks = summary.study_plan?.days[0]?.tasks ?? [];
  const totalTasks = summary.study_plan
    ? summary.study_plan.days.reduce((acc, day) => acc + day.tasks.length, 0)
    : 0;

  return (
    <>
      <PageHeader
        title="Good morning 👋"
        subtitle="Ready to continue learning?"
      />

      <section aria-label="Your stats" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Subjects"
          value={String(summary.subjects_count)}
          hint="active subjects"
          icon={FolderOpen}
        />
        <StatCard
          label="Materials"
          value={String(summary.materials_count)}
          hint="uploaded documents"
          icon={BookOpen}
        />
        <StatCard
          label="Quizzes"
          value={summary.quiz_session ? '1' : '0'}
          hint="this session"
          icon={ListChecks}
        />
        <StatCard
          label="Latest Quiz Score"
          value={quizPercent !== null ? `${quizPercent}%` : '—'}
          hint={quizPercent !== null ? 'last completed quiz' : 'no quiz history yet'}
          icon={Target}
        />
      </section>

      {summary.subjects_count === 0 && (
        <section className="mt-10">
          <EmptyState
            icon={FolderOpen}
            title="No subjects yet"
            description="Create your first subject to start organizing your learning materials."
            action={
              <Button to="/subjects" variant="outline" size="sm">
                Create Subject
              </Button>
            }
          />
        </section>
      )}

      <section className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section aria-labelledby="weak-topics-heading">
          <SectionHeading title="🔥 Weak Topics" subtitle="Focus areas from your quiz results." />
          {summary.weak_topics.length === 0 ? (
            <EmptyState
              icon={Target}
              title="No weak topics yet"
              description="Complete a quiz and your weak topics will show up here."
              action={
                <Button to="/quizzes" variant="outline" size="sm">
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Take a Quiz
                </Button>
              }
            />
          ) : (
            <Card>
              <ul className="flex flex-wrap gap-2">
                {summary.weak_topics.map((topic) => (
                  <li key={topic}>
                    <Badge tone="rose">{topic}</Badge>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </section>

        <section aria-labelledby="recent-materials-heading">
          <SectionHeading title="📚 Recent Materials" subtitle="Your latest uploads." />
          {summary.recent_materials.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="No study materials yet"
              description="Upload a PDF or TXT document to start learning with AI."
              action={
                <Button to="/materials" variant="outline" size="sm">
                  <FileText className="h-4 w-4" aria-hidden="true" />
                  Upload Material
                </Button>
              }
            />
          ) : (
            <Card padded={false}>
              <ul className="divide-y divide-slate-100">
                {summary.recent_materials.map((material) => (
                  <li key={material.id} className="flex items-center gap-4 px-5 py-4">
                    <span className="rounded-xl bg-slate-100 p-2.5 text-slate-500">
                      <FileText className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-800">
                        {material.original_filename}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {new Date(material.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge tone={material.processing_status === 'processed' ? 'emerald' : 'neutral'}>
                      {material.processing_status}
                    </Badge>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </section>
      </section>

      <section className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section aria-labelledby="recent-activity-heading">
          <SectionHeading title="📝 Recent Activity" subtitle="Your latest quiz result." />
          {summary.quiz_session ? (
            <Card>
              <div className="flex items-center gap-4">
                <span className="rounded-2xl bg-indigo-50 p-3 text-indigo-600">
                  <GraduationCap className="h-6 w-6" aria-hidden="true" />
                </span>
                <div className="flex-1">
                  <p className="text-sm font-semibold">
                    Score: {summary.quiz_session.score} / {summary.quiz_session.total}
                    {quizPercent !== null && (
                      <span className="ml-2 text-slate-500">({quizPercent}%)</span>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Completed{' '}
                    {new Date(summary.quiz_session.completedAt).toLocaleString()}
                  </p>
                </div>
                <Badge tone="indigo">Latest quiz</Badge>
              </div>
              {summary.quiz_session.weakTopics.length > 0 && (
                <p className="mt-4 border-t border-slate-100 pt-4 text-sm text-slate-500">
                  Weak topics: {summary.quiz_session.weakTopics.join(', ')}
                </p>
              )}
            </Card>
          ) : (
            <EmptyState
              icon={GraduationCap}
              title="No quiz history yet"
              description="Complete a quiz to see your results here."
              action={
                <Button to="/quizzes" variant="outline" size="sm">
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Generate Quiz
                </Button>
              }
            />
          )}
        </section>

        <section aria-labelledby="study-plan-heading">
          <SectionHeading title="📅 Study Plan" subtitle="Today's recommended tasks." />
          {summary.study_plan ? (
            <Card padded={false}>
              <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
                <h3 className="text-sm font-semibold">Day 1 of {summary.study_plan.days.length}</h3>
                <Badge tone="indigo">
                  {totalTasks} tasks total
                </Badge>
              </div>
              {todayTasks.length === 0 ? (
                <p className="px-5 py-4 text-sm text-slate-500">No tasks scheduled for today.</p>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {todayTasks.map((task, index) => (
                    <li key={`${task.title}-${index}`} className="flex items-center gap-4 px-5 py-4">
                      <span className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600">
                        <Flame className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-slate-800">{task.title}</p>
                        <p className="mt-0.5 text-xs capitalize text-slate-500">{task.type}</p>
                      </div>
                      <span className="text-sm font-semibold text-slate-600">
                        {task.duration_minutes} min
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="border-t border-slate-100 p-4">
                <Button to="/study-plan" variant="outline" size="sm" className="w-full">
                  Continue Studying
                </Button>
              </div>
            </Card>
          ) : (
            <EmptyState
              icon={CalendarDays}
              title="No study plan yet"
              description="Generate a personalized day-by-day plan from your material and quiz results."
              action={
                <Button to="/study-plan" variant="outline" size="sm">
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Create Study Plan
                </Button>
              }
            />
          )}
        </section>
      </section>

      <section aria-labelledby="quick-actions-heading" className="mt-10">
        <SectionHeading title="QUICK ACTIONS" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Button key={action.label} to={action.to} variant="outline" className="w-full">
                <span className={`rounded-xl p-2 ${action.tone}`} aria-hidden="true">
                  <Icon className="h-5 w-5" />
                </span>
                {action.label}
              </Button>
            );
          })}
        </div>
      </section>
    </>
  );
}