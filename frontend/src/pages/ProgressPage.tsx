import { useState, useEffect, useCallback } from 'react';
import {
  FolderOpen,
  BookOpen,
  ListChecks,
  Target,
  CalendarDays,
  Loader2,
  AlertCircle,
  RotateCcw,
  Sparkles,
  MessageSquareText,
  Flame,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { ProgressBar } from '../components/ui/ProgressBar';
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

export function ProgressPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setSummary(await getDashboardSummary());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your progress.');
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
        <PageHeader title="Progress" subtitle="Your learning progress at a glance." />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" aria-hidden="true" />
          <span className="ml-3 text-sm text-slate-500">Loading your progress…</span>
        </div>
      </>
    );
  }

  if (error || !summary) {
    return (
      <>
        <PageHeader title="Progress" subtitle="Your learning progress at a glance." />
        <Card className="border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Unable to load your progress</p>
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

  const latestAttempt = summary.attempts[0] ?? null;
  const quizPercent = latestAttempt
    ? latestAttempt.score
    : summary.quiz_session && summary.quiz_session.total > 0
      ? Math.round((summary.quiz_session.score / summary.quiz_session.total) * 100)
      : null;

  const totalPlanDays = summary.study_plan?.days.length ?? 0;
  const totalPlanTasks = summary.study_plan
    ? summary.study_plan.days.reduce((acc, day) => acc + day.tasks.length, 0)
    : 0;

  return (
    <>
      <PageHeader title="Progress" subtitle="Your learning progress at a glance." />

      <section aria-label="Your stats" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Subjects" value={String(summary.subjects_count)} hint="active subjects" icon={FolderOpen} />
        <StatCard label="Materials" value={String(summary.materials_count)} hint="uploaded documents" icon={BookOpen} />
        <StatCard
          label="Latest Quiz Score"
          value={quizPercent !== null ? `${quizPercent}%` : '—'}
          hint={quizPercent !== null ? 'last completed quiz' : 'no quiz history yet'}
          icon={ListChecks}
        />
        <StatCard
          label="Plan Coverage"
          value={totalPlanDays > 0 ? `${totalPlanDays} days` : '—'}
          hint={totalPlanTasks > 0 ? `${totalPlanTasks} tasks planned` : 'no study plan yet'}
          icon={CalendarDays}
        />
      </section>

      <section className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section aria-labelledby="quiz-performance-heading">
          <SectionHeading
            title="Quiz performance"
            subtitle="Your most recent quiz result, saved from real attempts."
          />
          {latestAttempt ? (
            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="truncate text-sm font-medium text-slate-600">
                    {latestAttempt.quiz_title}
                  </p>
                  <p className="mt-1 text-3xl font-bold tracking-tight">
                    {latestAttempt.correct_answers}
                    <span className="text-lg font-normal text-slate-400">
                      {' '}/ {latestAttempt.total_questions}
                    </span>
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {latestAttempt.subject_name} •{' '}
                    {latestAttempt.completed_at
                      ? new Date(latestAttempt.completed_at).toLocaleString()
                      : 'completed'}
                  </p>
                </div>
                <Badge tone={latestAttempt.score >= 70 ? 'emerald' : 'amber'}>
                  {latestAttempt.score}%
                </Badge>
              </div>
              {summary.quiz_session && summary.quiz_session.weakTopics.length > 0 && (
                <div className="mt-4 border-t border-slate-100 pt-4">
                  <p className="text-sm font-medium text-slate-700">Needs improvement</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {summary.quiz_session.weakTopics.map((topic) => (
                      <Badge key={topic} tone="rose">
                        {topic}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ) : (
            <EmptyState
              icon={ListChecks}
              title="No quiz history yet"
              description="Complete quizzes to build your performance history."
              action={
                <Button to="/quizzes" variant="outline" size="sm">
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Take a Quiz
                </Button>
              }
            />
          )}
        </section>

        <section aria-labelledby="weak-topics-heading">
          <SectionHeading
            title="Weak topics"
            subtitle="Focus areas suggested by your quiz results."
          />
          {summary.weak_topics.length === 0 ? (
            <EmptyState
              icon={Target}
              title="No weak topics yet"
              description="Complete a quiz to identify topics that need extra practice."
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
      </section>

      <section className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section aria-labelledby="subject-progress-heading">
          <SectionHeading
            title="Subject-level progress"
            subtitle="Your subjects and their uploaded materials."
          />
          {summary.subjects.length === 0 ? (
            <EmptyState
              icon={FolderOpen}
              title="No subjects yet"
              description="Create a subject to start organizing your learning."
              action={
                <Button to="/subjects" variant="outline" size="sm">
                  Create Subject
                </Button>
              }
            />
          ) : (
            <Card padded={false}>
              <ul className="divide-y divide-slate-100">
                {summary.subjects.map((subject) => {
                  const subjectMaterials = summary.recent_materials.filter(
                    (m) => m.subject_id === subject.id
                  ).length;
                  return (
                    <li key={subject.id} className="flex items-center gap-4 px-5 py-4">
                      <span className="rounded-xl bg-slate-100 p-2.5 text-slate-500">
                        <FolderOpen className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-slate-800">{subject.name}</p>
                        {subject.description && (
                          <p className="mt-0.5 truncate text-xs text-slate-500">
                            {subject.description}
                          </p>
                        )}
                      </div>
                      <Badge tone="neutral">{subjectMaterials} materials</Badge>
                    </li>
                  );
                })}
              </ul>
            </Card>
          )}
        </section>

        <section aria-labelledby="study-plan-progress-heading">
          <SectionHeading
            title="Study plan progress"
            subtitle="Your current AI-generated plan."
          />
          {summary.study_plan ? (
            <Card padded={false}>
              <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
                <h3 className="text-sm font-semibold">Current plan</h3>
                <Badge tone="indigo">{totalPlanDays} days</Badge>
              </div>
              <ul className="divide-y divide-slate-100">
                {summary.study_plan.days.map((day) => (
                  <li key={day.day} className="flex items-center gap-4 px-5 py-3">
                    <span className="w-16 shrink-0 text-sm font-semibold text-indigo-600">
                      Day {day.day}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm text-slate-700">
                        {day.tasks.map((t) => t.title).join(' · ')}
                      </p>
                    </div>
                    <Badge tone="neutral">{day.tasks.length} tasks</Badge>
                  </li>
                ))}
              </ul>
              <div className="border-t border-slate-100 p-4">
                <Button to="/study-plan" variant="outline" size="sm" className="w-full">
                  View Study Plan
                </Button>
              </div>
            </Card>
          ) : (
            <EmptyState
              icon={CalendarDays}
              title="No study plan yet"
              description="Generate a plan to see your day-by-day schedule here."
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

      <section aria-labelledby="topic-mastery-heading" className="mt-10">
        <SectionHeading
          title="Topic mastery"
          subtitle="Per-topic performance averaged from your quiz attempts."
        />
        {summary.progress.length === 0 ? (
          <EmptyState
            icon={Target}
            title="No topic data yet"
            description="Submit a quiz and each topic you were tested on will appear here."
            action={
              <Button to="/quizzes" variant="outline" size="sm">
                <Sparkles className="h-4 w-4" aria-hidden="true" />
                Take a Quiz
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {summary.progress.map((item) => (
              <Card key={item.topic_id}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-800">
                      {item.topic_name}
                    </p>
                    <p className="mt-0.5 truncate text-xs text-slate-500">
                      {item.subject_name}
                    </p>
                  </div>
                  <Badge tone={item.mastery_score >= 70 ? 'emerald' : 'amber'}>
                    {item.mastery_score}%
                  </Badge>
                </div>
                <ProgressBar
                  value={item.mastery_score}
                  label={`${item.mastery_score}% mastery`}
                  className="mt-4"
                />
                <p className="mt-3 text-xs text-slate-400">
                  From {item.topics_completed} attempt
                  {item.topics_completed === 1 ? '' : 's'}
                  {item.last_studied_at
                    ? ` • last studied ${new Date(item.last_studied_at).toLocaleDateString()}`
                    : ''}
                </p>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="next-steps-heading" className="mt-10">
        <SectionHeading
          title="What should I do next?"
          subtitle="Your next best step on the learning journey."
        />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {summary.materials_count === 0 ? (
            <Card>
              <div className="flex items-start gap-4 p-5">
                <span className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600">
                  <BookOpen className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">1. Upload study material</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Start the journey by adding a PDF or TXT document.
                  </p>
                  <Button to="/materials" variant="outline" size="sm" className="mt-3">
                    Upload Material
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <Card>
              <div className="flex items-start gap-4 p-5">
                <span className="rounded-xl bg-emerald-50 p-2.5 text-emerald-600">
                  <MessageSquareText className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">1. Learn with the AI Tutor</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Ask questions about your material before testing yourself.
                  </p>
                  <Button to="/tutor" variant="outline" size="sm" className="mt-3">
                    Ask Tutor
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {!summary.quiz_session ? (
            <Card>
              <div className="flex items-start gap-4 p-5">
                <span className="rounded-xl bg-amber-50 p-2.5 text-amber-600">
                  <ListChecks className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">2. Test your knowledge</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Complete a quiz to find your weak topics.
                  </p>
                  <Button to="/quizzes" variant="outline" size="sm" className="mt-3">
                    Take a Quiz
                  </Button>
                </div>
              </div>
            </Card>
          ) : !summary.study_plan ? (
            <Card>
              <div className="flex items-start gap-4 p-5">
                <span className="rounded-xl bg-rose-50 p-2.5 text-rose-600">
                  <Target className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">2. Fix your weak topics</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Create a study plan that targets your quiz weak spots.
                  </p>
                  <Button to="/study-plan" variant="outline" size="sm" className="mt-3">
                    Create Study Plan
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <Card>
              <div className="flex items-start gap-4 p-5">
                <span className="rounded-xl bg-rose-50 p-2.5 text-rose-600">
                  <Target className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">2. Track your weak topics</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Review what needs practice and retake quizzes.
                  </p>
                  <Button to="/quizzes" variant="outline" size="sm" className="mt-3">
                    Take a Quiz
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {summary.study_plan ? (
            <Card>
              <div className="flex items-start gap-4 p-5">
                <span className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600">
                  <Flame className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">3. Follow your study plan</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Continue with today's recommended tasks.
                  </p>
                  <Button to="/study-plan" variant="outline" size="sm" className="mt-3">
                    Continue Studying
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <Card>
              <div className="flex items-start gap-4 p-5">
                <span className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600">
                  <CalendarDays className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">3. Get a study plan</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Complete a quiz to identify weak topics and create a plan.
                  </p>
                  <Button to="/study-plan" variant="outline" size="sm" className="mt-3">
                    Create Study Plan
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </section>
    </>
  );
}