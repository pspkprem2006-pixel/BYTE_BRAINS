import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  CalendarDays,
  Loader2,
  AlertCircle,
  RotateCcw,
  Sparkles,
  BookOpen,
  PenLine,
  RefreshCw,
  ListChecks,
  Target,
  Clock,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { getSubjects } from '../services/subjects';
import { generateStudyPlan } from '../services/studyPlan';
import { getWeakTopics, getQuizSession } from '../store/weakTopics';
import { setStudyPlan } from '../store/studyPlan';
import type { Subject } from '../types/subject';
import type {
  StudyFocus,
  PlanTaskType,
  StudyPlanDay,
  StudyPlanGenerateResponse,
} from '../types/studyPlan';

const FOCUS_OPTIONS: StudyFocus[] = ['Complete syllabus', 'Improve weak topics', 'Balanced'];

const taskTypeMeta: Record<PlanTaskType, { label: string; icon: typeof BookOpen; tone: string }> = {
  study: { label: 'Study', icon: BookOpen, tone: 'bg-indigo-50 text-indigo-600' },
  practice: { label: 'Practice', icon: PenLine, tone: 'bg-emerald-50 text-emerald-600' },
  revision: { label: 'Revision', icon: RefreshCw, tone: 'bg-amber-50 text-amber-600' },
  quiz: { label: 'Quiz', icon: ListChecks, tone: 'bg-rose-50 text-rose-600' },
};

export function StudyPlanPage() {
  const [searchParams] = useSearchParams();
  const subjectParam = searchParams.get('subject');
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [daysAvailable, setDaysAvailable] = useState<number>(5);
  const [hoursPerDay, setHoursPerDay] = useState<number>(2);
  const [focus, setFocus] = useState<StudyFocus>('Balanced');
  const [examDate, setExamDate] = useState<string>('');
  const [weakTopics, setWeakTopicsState] = useState<string[]>([]);
  const [isLoadingSubjects, setIsLoadingSubjects] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<StudyPlanGenerateResponse | null>(null);

  const loadSubjects = useCallback(async () => {
    try {
      setError(null);
      const data = await getSubjects();
      setSubjects(data);
      if (data.length > 0) {
        setSelectedSubjectId((current) => {
          if (subjectParam && data.some((s) => s.id === subjectParam)) {
            return subjectParam;
          }
          const sessionSubjectId = getQuizSession()?.subject_id;
          if (sessionSubjectId && data.some((s) => s.id === sessionSubjectId)) {
            return sessionSubjectId;
          }
          return current || data[0].id;
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load subjects');
    } finally {
      setIsLoadingSubjects(false);
    }
  }, [subjectParam]);

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  useEffect(() => {
    setWeakTopicsState(getWeakTopics());
  }, []);

  const handleGenerate = async () => {
    if (!selectedSubjectId) return;
    setIsGenerating(true);
    setError(null);
    try {
      const response = await generateStudyPlan({
        subject_id: selectedSubjectId,
        days_available: daysAvailable,
        hours_per_day: hoursPerDay,
        focus,
        exam_date: examDate ? examDate : null,
        weak_topics: weakTopics,
      });
      setPlan(response);
      setStudyPlan(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate study plan');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerate = () => {
    setPlan(null);
    setStudyPlan(null);
    handleGenerate();
  };

  if (isLoadingSubjects) {
    return (
      <>
        <PageHeader title="Study Plan" subtitle="Your adaptive AI study planner." />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" aria-hidden="true" />
          <span className="ml-3 text-sm text-slate-500">Loading subjects…</span>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Study Plan"
        subtitle="Generate a personalized day-by-day plan from your material and quiz results."
      />

      {error && (
        <Card className="mb-6 border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Something went wrong</p>
              <p className="mt-1 text-sm text-rose-600">{error}</p>
              <Button variant="outline" size="sm" onClick={loadSubjects} className="mt-3">
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Retry
              </Button>
            </div>
          </div>
        </Card>
      )}

      {subjects.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No subjects yet"
          description="Create a subject first, then generate a study plan for it."
          action={
            <Button to="/subjects" variant="outline">
              Create Subject
            </Button>
          }
        />
      ) : (
        <Card className="mx-auto max-w-xl">
          <div className="space-y-5">
            <div>
              <label htmlFor="plan-subject" className="block text-sm font-medium text-slate-700">
                Subject
              </label>
              <select
                id="plan-subject"
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(e.target.value)}
                className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="plan-days" className="block text-sm font-medium text-slate-700">
                  Days available
                </label>
                <input
                  id="plan-days"
                  type="number"
                  min={1}
                  max={30}
                  value={daysAvailable}
                  onChange={(e) => setDaysAvailable(Number(e.target.value))}
                  className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label htmlFor="plan-hours" className="block text-sm font-medium text-slate-700">
                  Hours per day
                </label>
                <input
                  id="plan-hours"
                  type="number"
                  min={0.5}
                  max={12}
                  step={0.5}
                  value={hoursPerDay}
                  onChange={(e) => setHoursPerDay(Number(e.target.value))}
                  className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Focus</label>
              <div className="mt-2 flex flex-wrap gap-2">
                {FOCUS_OPTIONS.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setFocus(option)}
                    className={`rounded-xl border px-4 py-2 text-sm font-medium transition-colors ${
                      focus === option
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-indigo-300'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label htmlFor="plan-exam-date" className="block text-sm font-medium text-slate-700">
                Exam date <span className="font-normal text-slate-400">(optional)</span>
              </label>
              <input
                id="plan-exam-date"
                type="date"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
                className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {weakTopics.length > 0 && (
              <div className="rounded-xl border border-rose-100 bg-rose-50 p-4">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-rose-600" aria-hidden="true" />
                  <p className="text-sm font-medium text-rose-800">Based on your recent quiz</p>
                </div>
                <p className="mt-1 text-xs text-rose-600">
                  These weak topics will be included in your plan.
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {weakTopics.map((topic) => (
                    <Badge key={topic} tone="rose">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <Button onClick={handleGenerate} disabled={isGenerating} className="w-full">
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Creating plan…
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Create Study Plan
                </>
              )}
            </Button>
          </div>
        </Card>
      )}

      {plan && (
        <section className="mt-10">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">
              Your plan —{' '}
              {subjects.find((s) => s.id === plan.subject_id)?.name ?? 'selected subject'}
            </h2>
            <Button variant="outline" size="sm" onClick={handleRegenerate}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Regenerate Plan
            </Button>
          </div>

          <div className="space-y-6">
            {plan.days.map((day: StudyPlanDay) => (
              <Card
                key={day.day}
                padded={false}
                className={day.day === 1 ? 'border-indigo-200 shadow-md ring-1 ring-indigo-100' : ''}
              >
                <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-3">
                  <CalendarDays className="h-4 w-4 text-indigo-600" aria-hidden="true" />
                  <h3 className="text-sm font-semibold">Day {day.day}</h3>
                  {day.day === 1 && <Badge tone="indigo">Today</Badge>}
                  {day.day === 1 && (
                    <span className="ml-auto text-xs text-slate-400">Start here</span>
                  )}
                </div>
                <ul className="divide-y divide-slate-100">
                  {day.tasks.map((task, index) => {
                    const meta = taskTypeMeta[task.type] ?? taskTypeMeta.study;
                    const TaskIcon = meta.icon;
                    const isWeakTopic = weakTopics.some(
                      (topic) => topic.toLowerCase() === task.title.toLowerCase()
                    );
                    const isFirstTask = day.day === 1 && index === 0;
                    return (
                      <li
                        key={`${day.day}-${index}`}
                        className={`flex items-center gap-4 px-5 py-4 ${isFirstTask ? 'bg-indigo-50/50' : ''}`}
                      >
                        <span
                          className={`rounded-xl p-2.5 ${meta.tone}`}
                          aria-hidden="true"
                        >
                          <TaskIcon className="h-4 w-4" />
                        </span>
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-medium text-slate-800">{task.title}</p>
                            {isWeakTopic && <Badge tone="rose">Weak Topic</Badge>}
                            {isFirstTask && <Badge tone="emerald">Up Next</Badge>}
                          </div>
                          <p className="mt-0.5 text-xs text-slate-500">{meta.label}</p>
                        </div>
                        <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-slate-600">
                          <Clock className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
                          {task.duration_minutes} min
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </Card>
            ))}
          </div>
        </section>
      )}
    </>
  );
}