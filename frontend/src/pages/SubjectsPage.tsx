import { useState, useEffect, useCallback } from 'react';
import { Plus, Loader2, AlertCircle, RotateCcw } from 'lucide-react';
import { SubjectCard } from '../components/dashboard/SubjectCard';
import { Button } from '../components/ui/Button';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { Card } from '../components/ui/Card';
import { getSubjects, createSubject, updateSubject, deleteSubject } from '../services/subjects';
import type { Subject, SubjectCreate, SubjectUpdate } from '../types/subject';

function SubjectForm({
  subject,
  onSubmit,
  onCancel,
  isLoading,
}: {
  subject?: Subject;
  onSubmit: (data: { name: string; description?: string }) => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  const [name, setName] = useState(subject?.name ?? '');
  const [description, setDescription] = useState(subject?.description ?? '');
  const [nameError, setNameError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setNameError('Name is required');
      return;
    }
    if (trimmedName.length > 120) {
      setNameError('Name must be 120 characters or less');
      return;
    }
    setNameError('');
    onSubmit({ name: trimmedName, description: description.trim() || undefined });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-slate-700">
          Name
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={`mt-1 block w-full rounded-xl border px-3 py-2 text-sm ${
            nameError ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500' : 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-500'
          } focus:outline-none focus:ring-2 focus:ring-offset-0`}
          disabled={isLoading}
          autoFocus
        />
        {nameError && <p className="mt-1 text-sm text-rose-600">{nameError}</p>}
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-slate-700">
          Description (optional)
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="mt-1 block w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
          disabled={isLoading}
        />
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              Saving...
            </>
          ) : subject ? (
            'Save Changes'
          ) : (
            'Add Subject'
          )}
        </Button>
      </div>
    </form>
  );
}

function ConfirmDialog({
  title,
  description,
  onConfirm,
  onCancel,
  isLoading,
  variant = 'danger',
}: {
  title: string;
  description: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
  variant?: 'danger' | 'primary';
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4" role="dialog" aria-modal="true">
      <Card className="w-full max-w-md">
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-slate-500">{description}</p>
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={onCancel} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              variant={variant === 'danger' ? 'secondary' : 'primary'}
              onClick={onConfirm}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

export function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null);
  const [deletingSubject, setDeletingSubject] = useState<Subject | null>(null);

  const loadSubjects = useCallback(async () => {
    try {
      setError(null);
      const data = await getSubjects();
      setSubjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your subjects');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  const handleCreate = async (data: SubjectCreate) => {
    setIsSubmitting(true);
    try {
      const newSubject = await createSubject(data);
      setSubjects((prev) => [newSubject, ...prev]);
      setEditingSubject(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create subject';
      if (message.includes('already exists')) {
        alert('A subject with this name already exists.');
      } else {
        alert(message);
      }
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdate = async (data: SubjectUpdate) => {
    if (!editingSubject) return;
    setIsSubmitting(true);
    try {
      const updated = await updateSubject(editingSubject.id, data);
      setSubjects((prev) => prev.map((s) => (s.id === editingSubject.id ? updated : s)));
      setEditingSubject(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update subject';
      if (message.includes('already exists')) {
        alert('A subject with this name already exists.');
      } else {
        alert(message);
      }
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingSubject) return;
    setIsSubmitting(true);
    try {
      await deleteSubject(deletingSubject.id);
      setSubjects((prev) => prev.filter((s) => s.id !== deletingSubject.id));
      setDeletingSubject(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete subject';
      alert(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openCreateDialog = () => setEditingSubject({} as Subject);
  const openEditDialog = (subject: Subject) => setEditingSubject(subject);
  const openDeleteDialog = (subject: Subject) => setDeletingSubject(subject);

  if (isLoading) {
    return (
      <>
        <PageHeader title="Subjects" subtitle="Manage the subjects you're learning." />
        <section aria-label="Your subjects" className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="flex h-full flex-col animate-pulse">
              <div className="h-6 bg-slate-200 rounded w-3/4" />
              <div className="mt-1 h-4 bg-slate-200 rounded w-full" />
              <div className="mt-4 h-4 bg-slate-200 rounded w-1/2" />
              <div className="mt-2 h-3 bg-slate-200 rounded" />
              <div className="mt-5 flex-1" />
              <div className="h-10 bg-slate-200 rounded-xl" />
            </Card>
          ))}
        </section>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Subjects"
        subtitle="Manage the subjects you're learning."
        action={
          <Button variant="outline" onClick={openCreateDialog} disabled={isSubmitting}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add Subject
          </Button>
        }
      />

      {error && (
        <Card className="mb-6 border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Unable to load your subjects</p>
              <p className="mt-1 text-sm text-rose-600">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={loadSubjects}
                className="mt-3"
                disabled={isSubmitting}
              >
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Retry
              </Button>
            </div>
          </div>
        </Card>
      )}

      <section aria-label="Your subjects" className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {subjects.length === 0 && !error && (
          <EmptyState
            icon={Plus}
            title="No subjects yet"
            description="Add your first subject to start learning."
            action={
              <Button variant="outline" onClick={openCreateDialog} disabled={isSubmitting}>
                <Plus className="h-4 w-4" aria-hidden="true" />
                Add Subject
              </Button>
            }
          />
        )}
        {subjects.map((subject) => (
          <SubjectCard
            key={subject.id}
            subject={{
              id: subject.id,
              name: subject.name,
              description: subject.description ?? '',
              progress: 0,
              topicCount: 0,
              lastStudied: 'Never',
            }}
            variant="full"
            onEdit={() => openEditDialog(subject)}
            onDelete={() => openDeleteDialog(subject)}
          />
        ))}
      </section>

      {(editingSubject && !deletingSubject) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4" role="dialog" aria-modal="true">
          <Card className="w-full max-w-md">
            <div className="space-y-4 p-6">
              <h3 className="text-lg font-semibold">
                {editingSubject.id ? 'Edit Subject' : 'Add Subject'}
              </h3>
              <SubjectForm
                subject={editingSubject.id ? editingSubject : undefined}
                onSubmit={editingSubject.id ? handleUpdate : handleCreate}
                onCancel={() => setEditingSubject(null)}
                isLoading={isSubmitting}
              />
            </div>
          </Card>
        </div>
      )}

      {deletingSubject && (
        <ConfirmDialog
          title="Delete this subject?"
          description="Your associated learning data may be affected."
          onConfirm={handleDelete}
          onCancel={() => setDeletingSubject(null)}
          isLoading={isSubmitting}
        />
      )}
    </>
  );
}