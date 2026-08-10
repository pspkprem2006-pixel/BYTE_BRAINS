import { useState, type DragEvent } from 'react'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { materials } from '../data/mockData'

export function MaterialsPage() {
  const [isDragging, setIsDragging] = useState(false)

  // Visual only: real file upload is implemented in a later phase.
  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
  }

  return (
    <>
      <PageHeader
        title="Materials"
        subtitle="Your study document library, ready for AI-powered learning."
      />

      {/* Upload dropzone (visual placeholder) */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
          isDragging
            ? 'border-indigo-400 bg-indigo-50/60'
            : 'border-slate-300 bg-white'
        }`}
      >
        <p className="text-base font-semibold text-slate-800">
          Drag &amp; drop your study material here
        </p>
        <p className="mt-1 text-sm text-slate-500">
          PDFs, notes and slides will be turned into learning context.
        </p>
        <Button variant="outline" size="sm" disabled className="mt-5">
          Browse files
        </Button>
        <p className="mt-3 text-xs text-slate-400">
          Uploading arrives in the next phase — this area is visual only.
        </p>
      </div>

      {/* Material list */}
      <section aria-labelledby="library-heading" className="mt-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 id="library-heading" className="text-lg font-semibold">
            Your materials
          </h2>
          <Badge tone="neutral">Demo data</Badge>
        </div>

        <Card padded={false} className="divide-y divide-slate-100">
          {materials.map((material) => (
            <div key={material.id} className="flex flex-wrap items-center gap-x-6 gap-y-2 px-5 py-4">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-800">{material.name}</p>
                <p className="mt-0.5 text-xs text-slate-400">Uploaded {material.uploadedAt}</p>
              </div>
              <Badge tone="neutral">{material.fileType}</Badge>
              <Badge tone="indigo">{material.subject}</Badge>
              <Badge tone="emerald">{material.status}</Badge>
            </div>
          ))}
        </Card>
      </section>
    </>
  )
}