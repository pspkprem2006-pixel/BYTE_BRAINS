import { Plus } from 'lucide-react'
import { SubjectCard } from '../components/dashboard/SubjectCard'
import { Button } from '../components/ui/Button'
import { PageHeader } from '../components/ui/PageHeader'
import { subjects } from '../data/mockData'

export function SubjectsPage() {
  return (
    <>
      <PageHeader
        title="Subjects"
        subtitle="Manage the subjects you're learning. Add subject arrives with the API."
        action={
          <Button variant="outline">
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add Subject
          </Button>
        }
      />

      <section aria-label="Your subjects" className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {subjects.map((subject) => (
          <SubjectCard key={subject.id} subject={subject} variant="full" />
        ))}
      </section>
    </>
  )
}