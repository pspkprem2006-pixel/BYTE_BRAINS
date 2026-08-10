import { Sparkles } from 'lucide-react'
import { QuizCard } from '../components/quizzes/QuizCard'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'
import { completedQuizzes, recentQuizzes, recommendedQuizzes } from '../data/mockData'

function SectionHeading({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
    </div>
  )
}

export function QuizzesPage() {
  return (
    <>
      <PageHeader
        title="Quizzes"
        subtitle="Test yourself with generated quizzes — quiz engine arrives in a later phase."
      />

      <section aria-labelledby="recent-heading">
        <div id="recent-quiz-grid">
          <SectionHeading title="Recent quizzes" subtitle="Your latest attempts." />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {recentQuizzes.map((quiz) => (
              <QuizCard key={quiz.id} quiz={quiz} />
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="recommended-heading" className="mt-10">
        <div id="recommended-quiz-grid">
          <SectionHeading
            title="Recommended for you"
            subtitle="Based on your weak topics — available once the quiz engine is live."
          />
          {recommendedQuizzes.length === 0 ? (
            <EmptyState
              icon={Sparkles}
              title="No recommendations yet"
              description="Take a few quizzes and ByteBrains will suggest exactly what to practice next."
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {recommendedQuizzes.map((quiz) => (
                <QuizCard key={quiz.id} quiz={quiz} />
              ))}
            </div>
          )}
        </div>
      </section>

      <section aria-labelledby="completed-heading" className="mt-10">
        <div id="completed-quiz-grid">
          <SectionHeading title="Completed" subtitle="Your quiz history." />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {completedQuizzes.map((quiz) => (
              <QuizCard key={quiz.id} quiz={quiz} />
            ))}
          </div>
        </div>
      </section>
    </>
  )
}