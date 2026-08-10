import { useState, useEffect, useCallback } from 'react';
import {
  Loader2,
  AlertCircle,
  RotateCcw,
  ArrowRight,
  ArrowLeft,
  Trophy,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { getMaterials } from '../services/materials';
import { generateQuiz } from '../services/quizzes';
import { setWeakTopics } from '../store/weakTopics';
import type { Material } from '../types/material';
import type { QuizQuestion } from '../types/quiz';

export function QuizzesPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState<string>('');
  const [questionCount, setQuestionCount] = useState<number>(5);
  const [isLoadingMaterials, setIsLoadingMaterials] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [quiz, setQuiz] = useState<QuizQuestion[] | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const loadMaterials = useCallback(async () => {
    try {
      setError(null);
      const data = await getMaterials();
      setMaterials(data);
      if (data.length > 0 && !selectedMaterialId) {
        setSelectedMaterialId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load materials');
    } finally {
      setIsLoadingMaterials(false);
    }
  }, [selectedMaterialId]);

  useEffect(() => {
    loadMaterials();
  }, [loadMaterials]);

  const handleGenerate = async () => {
    if (!selectedMaterialId) return;
    setIsGenerating(true);
    setError(null);
    try {
      const response = await generateQuiz({
        material_id: selectedMaterialId,
        question_count: questionCount,
      });
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
    loadMaterials();
  };

  const handleTryAgain = () => {
    setQuiz(null);
    setAnswers([]);
    setCurrentIndex(0);
    setSubmitted(false);
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

  const handleSubmitQuiz = () => {
    setSubmitted(true);
    setWeakTopics(weakTopics);
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
              {currentIndex + 1} / {quiz.length}
            </span>
          </div>

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
          <div className="flex flex-col items-center py-4 text-center">
            <span className="rounded-2xl bg-emerald-50 p-4 text-emerald-600">
              <Trophy className="h-8 w-8" aria-hidden="true" />
            </span>
            <h2 className="mt-4 text-2xl font-bold">
              Score: {score} / {quiz.length}
            </h2>
            <p className="mt-1 text-sm text-slate-500">{percent}%</p>
          </div>

          <div className="mt-6 grid gap-6 sm:grid-cols-2">
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
                      • {topic}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button to="/study-plan">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Create Study Plan
            </Button>
            <Button variant="outline" onClick={handleTryAgain}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Try Again
            </Button>
          </div>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Quizzes"
        subtitle="Generate an AI quiz from your uploaded study material."
        action={
          materials.length > 0 && (
            <Button onClick={handleGenerate} disabled={isGenerating || !selectedMaterialId}>
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
          )
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

      {materials.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No materials yet"
          description="Upload study material first, then generate a quiz from it."
        />
      ) : (
        <Card className="mx-auto max-w-xl">
          <div className="space-y-5">
            <div>
              <label htmlFor="quiz-material" className="block text-sm font-medium text-slate-700">
                Study material
              </label>
              <select
                id="quiz-material"
                value={selectedMaterialId}
                onChange={(e) => setSelectedMaterialId(e.target.value)}
                className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
              >
                {materials.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.original_filename} ({material.processing_status})
                  </option>
                ))}
              </select>
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

            <Button onClick={handleGenerate} disabled={isGenerating} className="w-full">
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