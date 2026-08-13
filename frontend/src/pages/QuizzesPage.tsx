import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Loader2,
  AlertCircle,
  RotateCcw,
  ArrowRight,
  ArrowLeft,
  Trophy,
  RefreshCw,
  Sparkles,
  FileText,
  Globe,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { ProgressBar } from '../components/ui/ProgressBar';
import { getMaterials } from '../services/materials';
import { generateQuiz, submitQuiz } from '../services/quizzes';
import { getSubjects } from '../services/subjects';
import { getSelectedResources } from '../services/learningResources';
import { setWeakTopics, setQuizSession } from '../store/weakTopics';
import type { Material } from '../types/material';
import type { Subject } from '../types/subject';
import type { QuizQuestion, TopicResult } from '../types/quiz';

type SourceMode = 'material' | 'subject';

export function QuizzesPage() {
  const [searchParams] = useSearchParams();
  const materialParam = searchParams.get('material');
  const subjectParam = searchParams.get('subject');
  const [materials, setMaterials] = useState<Material[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [mode, setMode] = useState<SourceMode>(materialParam ? 'material' : 'subject');
  const [selectedMaterialId, setSelectedMaterialId] = useState<string>('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [subjectResourceCount, setSubjectResourceCount] = useState(0);
  const [questionCount, setQuestionCount] = useState<number>(5);
  const [isLoadingMaterials, setIsLoadingMaterials] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [quiz, setQuiz] = useState<QuizQuestion[] | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const loadMaterials = useCallback(async () => {
    try {
      setError(null);
      const data = await getMaterials();
      setMaterials(data);
      const usable = data.filter((m) => m.processing_status === 'processed');
      if (usable.length > 0) {
        setSelectedMaterialId((current) => {
          if (materialParam && usable.some((m) => m.id === materialParam)) {
            return materialParam;
          }
          return current || usable[0].id;
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load materials');
    } finally {
      setIsLoadingMaterials(false);
    }
  }, [materialParam]);

  const loadSubjects = useCallback(async () => {
    try {
      const data = await getSubjects();
      setSubjects(data);
      if (data.length > 0) {
        setSelectedSubjectId((current) => {
          if (subjectParam && data.some((s) => s.id === subjectParam)) {
            return subjectParam;
          }
          return current || data[0].id;
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load subjects');
    }
  }, [subjectParam]);

  useEffect(() => {
    loadMaterials();
    loadSubjects();
  }, [loadMaterials, loadSubjects]);

  useEffect(() => {
    if (!selectedSubjectId) return;
    let cancelled = false;
    getSelectedResources(selectedSubjectId)
      .then((response) => {
        if (!cancelled) setSubjectResourceCount(response.count);
      })
      .catch(() => {
        if (!cancelled) setSubjectResourceCount(0);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSubjectId]);

  const handleGenerate = async () => {
    if (mode === 'material' && !selectedMaterialId) {
      setError('Please select a study material before generating a quiz.');
      return;
    }
    if (mode === 'subject' && !selectedSubjectId) {
      setError('Please select a subject before generating a quiz.');
      return;
    }
    setIsGenerating(true);
    setError(null);
    try {
      const response = await generateQuiz({
        question_count: questionCount,
        ...(mode === 'material'
          ? { material_id: selectedMaterialId }
          : { subject_id: selectedSubjectId }),
      });
      if (response.questions.length === 0) {
        setError('The quiz generator returned an empty quiz. Please try again.');
        return;
      }
      setQuiz(response.questions);
      setAnswers(Array(response.questions.length).fill(null));
      setCurrentIndex(0);
      setSubmitted(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate quiz');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    loadMaterials();
    loadSubjects();
  };

  const handleTryAgain = () => {
    setQuiz(null);
    setAnswers([]);
    setCurrentIndex(0);
    setSubmitted(false);
    setSaveError(null);
  };

  const handleSelectOption = (optionIndex: number) => {
    if (submitted) return;
    setAnswers((prev) => {
      const next = [...prev];
      next[currentIndex] = optionIndex;
      return next;
    });
  };

  const score =
    submitted && quiz
      ? quiz.reduce(
          (acc, q, i) => acc + (answers[i] === q.correct_answer ? 1 : 0),
          0
        )
      : 0;

  const weakTopics =
    submitted && quiz
      ? [
          ...new Set(
            quiz
              .filter((q, i) => answers[i] !== q.correct_answer)
              .map((q) => q.topic)
          ),
        ]
      : [];

  const buildTopicResults = (
    questions: QuizQuestion[],
    answersList: (number | null)[]
  ): TopicResult[] => {
    const byTopic = new Map<string, { correct: number; total: number }>();
    questions.forEach((question, index) => {
      const entry = byTopic.get(question.topic) ?? { correct: 0, total: 0 };
      entry.total += 1;
      if (answersList[index] === question.correct_answer) {
        entry.correct += 1;
      }
      byTopic.set(question.topic, entry);
    });
    return Array.from(byTopic, ([topic, counts]) => ({ topic, ...counts }));
  };

  const handleSubmitQuiz = async () => {
    if (!quiz) return;

    // Compute the outcome directly from the answers. The derived
    // `score`/`weakTopics` constants below still read the pre-submit
    // state inside this handler, so they must not be used here.
    const correctCount = quiz.reduce(
      (acc, q, i) => acc + (answers[i] === q.correct_answer ? 1 : 0),
      0
    );
    const weak = [
      ...new Set(
        quiz
          .filter((q, i) => answers[i] !== q.correct_answer)
          .map((q) => q.topic)
      ),
    ];

    setSubmitted(true);
    const material = materials.find((m) => m.id === selectedMaterialId) ?? null;
    const subject = subjects.find((s) => s.id === selectedSubjectId) ?? null;
    const subjectId =
      mode === 'subject' ? subject?.id ?? null : material?.subject_id ?? null;
    setQuizSession(correctCount, quiz.length, weak, subjectId);
    setWeakTopics(weak);

    // Persist the real attempt outcome (score derived from answers). The
    // request carries the material (when material mode) or the subject
    // (when web-resource mode).
    try {
      await submitQuiz({
        ...(mode === 'material'
          ? { material_id: material?.id }
          : { subject_id: subject?.id }),
        total_questions: quiz.length,
        correct_answers: correctCount,
        topic_results: buildTopicResults(quiz, answers),
      });
      setSaveError(null);
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : 'Failed to save quiz result'
      );
    }
  };

  const strongTopics =
    submitted && quiz
      ? [
          ...new Set(
            quiz
              .filter((q, i) => answers[i] === q.correct_answer)
              .map((q) => q.topic)
          ),
        ]
      : [];

  if (isLoadingMaterials) {
    return (
      <>
        <PageHeader title="Quizzes" subtitle="Test yourself with AI-generated quizzes." />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" aria-hidden="true" />
          <span className="ml-3 text-sm text-slate-500">Loading materials…</span>
        </div>
      </>
    );
  }

  const usableMaterials = materials.filter((m) => m.processing_status === 'processed');

  if (quiz && !submitted) {
    const currentQuestion = quiz[currentIndex];
    const isLast = currentIndex === quiz.length - 1;
    const allAnswered = answers.every((a) => a !== null);

    return (
      <>
        <PageHeader
          title="Quiz"
          subtitle={`Question ${currentIndex + 1} of ${quiz.length}`}
        />

        <Card className="mx-auto max-w-2xl">
          <div className="mb-4 flex items-center justify-between">
            <Badge tone="indigo">{currentQuestion.topic}</Badge>
            <span className="text-sm text-slate-500">
              Question {currentIndex + 1} of {quiz.length}
            </span>
          </div>
          <ProgressBar
            value={((currentIndex + 1) / quiz.length) * 100}
            label={`Question ${currentIndex + 1} of ${quiz.length}`}
            className="mb-6"
          />

          <h2 className="text-lg font-semibold">{currentQuestion.question}</h2>

          <div className="mt-6 space-y-3">
            {currentQuestion.options.map((option, optionIndex) => {
              const selected = answers[currentIndex] === optionIndex;
              return (
                <button
                  key={optionIndex}
                  type="button"
                  onClick={() => handleSelectOption(optionIndex)}
                  className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm transition-colors ${
                    selected
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-900'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-indigo-300 hover:bg-indigo-50/50'
                  }`}
                >
                  <span
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                      selected ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {String.fromCharCode(65 + optionIndex)}
                  </span>
                  {option}
                </button>
              );
            })}
          </div>

          <div className="mt-6 flex items-center justify-between">
            <Button
              variant="outline"
              onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
              disabled={currentIndex === 0}
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Previous
            </Button>
            {isLast ? (
              <Button onClick={handleSubmitQuiz} disabled={!allAnswered}>
                Submit Quiz
              </Button>
            ) : (
              <Button
                onClick={() => setCurrentIndex((i) => Math.min(quiz.length - 1, i + 1))}
              >
                Next
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            )}
          </div>
        </Card>
      </>
    );
  }

  if (quiz && submitted) {
    const percent = quiz.length > 0 ? Math.round((score / quiz.length) * 100) : 0;

    return (
      <>
        <PageHeader title="Quiz Complete" subtitle="Here's how you did." />

        <Card className="mx-auto max-w-2xl">
          <div className="flex flex-col items-center py-8 text-center">
            <span className="rounded-2xl bg-emerald-50 p-4 text-emerald-600">
              <Trophy className="h-8 w-8" aria-hidden="true" />
            </span>
            <p className="mt-5 text-xs font-semibold tracking-widest text-slate-400 uppercase">
              Your Score
            </p>
            <p className="mt-1 text-4xl font-bold tracking-tight">
              {percent}
              <span className="text-lg font-normal text-slate-400">%</span>
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {score} of {quiz.length} questions correct
            </p>
          </div>

          <div className="grid gap-6 border-t border-slate-100 px-6 pt-6 pb-8 sm:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold text-emerald-700">Strong Topics</h3>
              {strongTopics.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">None yet — keep practicing!</p>
              ) : (
                <ul className="mt-2 space-y-1">
                  {strongTopics.map((topic) => (
                    <li key={topic} className="text-sm text-slate-600">
                      • {topic}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-rose-700">Needs Improvement</h3>
              {weakTopics.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">Nothing — perfect score!</p>
              ) : (
                <ul className="mt-2 space-y-1">
                  {weakTopics.map((topic) => (
                    <li key={topic} className="text-sm text-slate-600">
                      🔥 {topic}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-3 border-t border-slate-100 px-6 py-5">
            <Button to="/study-plan">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Create Study Plan
            </Button>
            <Button variant="outline" onClick={handleTryAgain}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Try Again
            </Button>
          </div>

          {saveError && (
            <div className="border-t border-slate-100 px-6 py-4">
              <p className="flex items-start gap-2 text-sm text-amber-700">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>
                  Your result was shown but could not be saved to your progress history:
                  {saveError}
                </span>
              </p>
            </div>
          )}
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Quizzes"
        subtitle="Generate an AI quiz from your uploaded study material or saved web resources."
        action={
          (mode === 'material' && usableMaterials.length > 0) ||
          (mode === 'subject' && subjects.length > 0) ? (
            <Button onClick={handleGenerate} disabled={isGenerating || !selectedMaterialId && mode === 'material' || !selectedSubjectId && mode === 'subject'}>
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Generating…
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Generate Quiz
                </>
              )}
            </Button>
          ) : undefined
        }
      />

      {error && (
        <Card className="mb-6 border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Something went wrong</p>
              <p className="mt-1 text-sm text-rose-600">{error}</p>
              <Button variant="outline" size="sm" onClick={handleRetry} className="mt-3">
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Retry
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="mb-6 flex justify-center">
        <div className="flex rounded-xl border border-slate-300 bg-white p-0.5">
          <button
            type="button"
            onClick={() => setMode('material')}
            disabled={isGenerating}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-60 ${
              mode === 'material'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            Material
          </button>
          <button
            type="button"
            onClick={() => setMode('subject')}
            disabled={isGenerating}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-60 ${
              mode === 'subject'
                ? 'bg-indigo-600 text-white'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            Web resources
          </button>
        </div>
      </div>

      {mode === 'material' && materials.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No study material yet."
          description="Test yourself after studying your material — upload a PDF or TXT first."
          action={
            <Button to="/materials" variant="outline">
              <FileText className="h-4 w-4" aria-hidden="true" />
              Upload Material
            </Button>
          }
        />
      ) : mode === 'material' && usableMaterials.length === 0 ? (
        <EmptyState
          icon={Loader2}
          title="No processed study material yet."
          description="Your uploaded materials are still being processed or failed to extract text. Try uploading a text-based PDF or TXT file."
          action={
            <Button to="/materials" variant="outline">
              <FileText className="h-4 w-4" aria-hidden="true" />
              Go to Materials
            </Button>
          }
        />
      ) : mode === 'subject' && subjects.length === 0 ? (
        <EmptyState
          icon={Globe}
          title="No subjects yet."
          description="Create a subject, save learning resources for it, and quizzes will be generated from those web resources."
          action={
            <Button to="/resources" variant="outline">
              <Globe className="h-4 w-4" aria-hidden="true" />
              Find Learning Resources
            </Button>
          }
        />
      ) : (
        <Card className="mx-auto max-w-xl">
          <div className="space-y-5">
            <div>
              <label htmlFor="quiz-source" className="block text-sm font-medium text-slate-700">
                {mode === 'material' ? 'Study material' : 'Subject'}
              </label>
              {mode === 'material' ? (
                <select
                  id="quiz-source"
                  value={selectedMaterialId}
                  onChange={(e) => setSelectedMaterialId(e.target.value)}
                  className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
                >
                  {usableMaterials.map((material) => (
                    <option key={material.id} value={material.id}>
                      {material.original_filename}
                    </option>
                  ))}
                </select>
              ) : (
                <select
                  id="quiz-source"
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value)}
                  className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
                >
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              )}
              {mode === 'subject' && subjectResourceCount === 0 && (
                <p className="mt-1 text-xs text-amber-600">
                  No web resources saved for this subject yet — the quiz can only cover its
                  uploaded materials.
                </p>
              )}
              {mode === 'material' && !selectedMaterialId && (
                <p className="mt-1 text-xs text-amber-600">
                  Select a study material above to enable quiz generation.
                </p>
              )}
              {mode === 'subject' && !selectedSubjectId && (
                <p className="mt-1 text-xs text-amber-600">
                  Select a subject above to enable quiz generation.
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Number of questions</label>
              <div className="mt-2 flex gap-2">
                {[5, 10].map((count) => (
                  <button
                    key={count}
                    type="button"
                    onClick={() => setQuestionCount(count)}
                    className={`flex-1 rounded-xl border px-4 py-2.5 text-sm font-medium transition-colors ${
                      questionCount === count
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-indigo-300'
                    }`}
                  >
                    {count} questions
                  </button>
                ))}
              </div>
            </div>

            <Button
              onClick={handleGenerate}
              disabled={
                isGenerating ||
                (mode === 'material' ? !selectedMaterialId : !selectedSubjectId)
              }
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Generating quiz…
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Generate Quiz
                </>
              )}
            </Button>
          </div>
        </Card>
      )}
    </>
  );
}