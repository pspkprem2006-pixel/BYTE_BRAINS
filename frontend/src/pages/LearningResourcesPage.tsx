import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  AlertCircle,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  Globe,
  Loader2,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import {
  deleteSelectedResource,
  discoverLearningResources,
  getSelectedResources,
  selectLearningResource,
} from '../services/learningResources';
import { getSubjects } from '../services/subjects';
import type {
  LearningResource,
  LearningResourceSelection,
  ResourceType,
} from '../types/learningResources';
import type { Subject } from '../types/subject';

const suggestions = ['PostgreSQL', 'Python', 'React', 'SQL'];

const typeLabels: Record<ResourceType, string> = {
  official_docs: 'Official Docs',
  tutorial: 'Tutorial',
  article: 'Article',
  video: 'Video',
  practice: 'Practice',
  reference: 'Reference',
  course: 'Course',
  other: 'Resource',
};

const typeTones: Record<ResourceType, 'neutral' | 'indigo' | 'emerald' | 'amber' | 'rose'> = {
  official_docs: 'indigo',
  tutorial: 'emerald',
  article: 'neutral',
  video: 'rose',
  practice: 'amber',
  reference: 'neutral',
  course: 'indigo',
  other: 'neutral',
};

function ResourceListItem({
  resource,
  isSelected,
  isBusy,
  onToggleSelect,
}: {
  resource: LearningResource;
  isSelected: boolean;
  isBusy: boolean;
  onToggleSelect: (resource: LearningResource) => void;
}) {
  return (
    <div className="flex flex-wrap items-start gap-x-6 gap-y-2 px-5 py-4">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate text-sm font-medium text-slate-800">{resource.title}</p>
          {resource.is_official && (
            <Badge tone="emerald">
              <ShieldCheck className="h-3 w-3" aria-hidden="true" />
              Official
            </Badge>
          )}
        </div>
        {resource.description && (
          <p className="mt-1 text-sm leading-relaxed text-slate-500">{resource.description}</p>
        )}
        <p className="mt-1 text-xs text-slate-400">{resource.domain}</p>
      </div>
      <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
        <Badge tone={typeTones[resource.resource_type]}>
          {typeLabels[resource.resource_type]}
        </Badge>
        {resource.difficulty && (
          <Badge tone="neutral">{resource.difficulty}</Badge>
        )}
        <Button
          variant={isSelected ? 'primary' : 'outline'}
          size="sm"
          onClick={() => onToggleSelect(resource)}
          disabled={isSelected || isBusy}
        >
          {isSelected ? (
            <>
              <BookmarkCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Selected
            </>
          ) : (
            <>
              <Bookmark className="h-3.5 w-3.5" aria-hidden="true" />
              Select
            </>
          )}
        </Button>
        <a
          href={resource.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
        >
          Open Resource
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
        </a>
      </div>
    </div>
  );
}

function SelectedResourceCard({
  selection,
  isDeleting,
  onDelete,
}: {
  selection: LearningResourceSelection;
  isDeleting: boolean;
  onDelete: (selection: LearningResourceSelection) => void;
}) {
  return (
    <li className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-800">{selection.title}</p>
        <p className="mt-0.5 truncate text-xs text-slate-400">{selection.domain}</p>
        {selection.description && (
          <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-500">
            {selection.description}
          </p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        <a
          href={selection.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Open resource"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-300 text-slate-500 transition-colors hover:bg-slate-50"
        >
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
        </a>
        <button
          type="button"
          onClick={() => onDelete(selection)}
          aria-label="Remove selected resource"
          disabled={isDeleting}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-300 text-slate-500 transition-colors hover:border-rose-300 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"
        >
          {isDeleting ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
          )}
        </button>
      </div>
    </li>
  );
}

export function LearningResourcesPage() {
  const [query, setQuery] = useState('');
  const [resources, setResources] = useState<LearningResource[]>([]);
  const [searchedFor, setSearchedFor] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [selections, setSelections] = useState<LearningResourceSelection[]>([]);
  const [isLoadingSelections, setIsLoadingSelections] = useState(true);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [isSelectingUrl, setIsSelectingUrl] = useState<string | null>(null);
  const [deletingSelectionId, setDeletingSelectionId] = useState<string | null>(null);

  const loadSelections = useCallback(async (subjectId: string) => {
    try {
      const response = await getSelectedResources(subjectId || undefined);
      setSelections(response.resources);
    } catch (err) {
      setSelectionError(err instanceof Error ? err.message : 'Unable to load selections');
    }
  }, []);

  useEffect(() => {
    getSubjects()
      .then((data) => {
        setSubjects(data);
        if (data.length > 0) {
          setSelectedSubjectId((current) => current || data[0].id);
        }
      })
      .catch(() => setSelectionError('Unable to load subjects'))
      .finally(() => setIsLoadingSelections(false));
  }, []);

  useEffect(() => {
    if (!isLoadingSelections && subjects.length > 0 && selectedSubjectId) {
      loadSelections(selectedSubjectId);
    }
  }, [selectedSubjectId, subjects, isLoadingSelections, loadSelections]);

  const runSearch = async (topic: string) => {
    const trimmed = topic.trim();
    if (!trimmed) return;
    setQuery(trimmed);
    setSearchedFor(trimmed);
    setError(null);
    setIsLoading(true);
    setHasSearched(true);
    try {
      const response = await discoverLearningResources(trimmed);
      setResources(response.resources);
    } catch (err) {
      setResources([]);
      setError(err instanceof Error ? err.message : 'Unable to search right now.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    runSearch(query);
  };

  const handleToggleSelect = async (resource: LearningResource) => {
    if (isSelectingUrl) return;
    if (!selectedSubjectId) {
      setSelectionError('Create a subject first, then select resources for it.');
      return;
    }
    setIsSelectingUrl(resource.url);
    setSelectionError(null);
    try {
      await selectLearningResource({
        subject_id: selectedSubjectId,
        title: resource.title,
        url: resource.url,
        resource_type: resource.resource_type,
        is_official: resource.is_official,
        difficulty: resource.difficulty,
        description: resource.description,
        domain: resource.domain,
        source: resource.source,
      });
      await loadSelections(selectedSubjectId);
    } catch (err) {
      setSelectionError(err instanceof Error ? err.message : 'Unable to save this resource.');
    } finally {
      setIsSelectingUrl(null);
    }
  };

  const handleDeleteSelection = async (selection: LearningResourceSelection) => {
    if (deletingSelectionId) return;
    setDeletingSelectionId(selection.id);
    setSelectionError(null);
    try {
      await deleteSelectedResource(selection.id);
      setSelections((prev) => prev.filter((item) => item.id !== selection.id));
    } catch (err) {
      setSelectionError(err instanceof Error ? err.message : 'Unable to remove this resource.');
    } finally {
      setDeletingSelectionId(null);
    }
  };

  const selectedUrls = new Set(selections.map((selection) => selection.url));

  return (
    <>
      <PageHeader
        title="Learning Resources"
        subtitle="Discover curated resources for any topic — save them to a subject and the AI Tutor, Quiz, and Study Plan can use them."
      />

      <Card className="mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="resource-query" className="block text-sm font-medium text-slate-700">
              What do you want to learn?
            </label>
            <div className="mt-1 flex flex-col gap-3 sm:flex-row">
              <input
                id="resource-query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. PostgreSQL"
                maxLength={300}
                className="block w-full flex-1 rounded-xl border border-slate-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
                disabled={isLoading}
                autoFocus
              />
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" aria-hidden="true" />
                    Search the web
                  </>
                )}
              </Button>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400">Try:</span>
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => runSearch(suggestion)}
                disabled={isLoading}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600 transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-60"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </form>
      </Card>

      {(error || selectionError) && (
        <Card className="mb-8 border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Something went wrong.</p>
              <p className="mt-1 text-sm text-rose-600">{error ?? selectionError}</p>
            </div>
          </div>
        </Card>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-600" aria-hidden="true" />
          <span className="ml-3 text-sm text-slate-500">Finding learning resources...</span>
        </div>
      )}

      {!isLoading && !error && hasSearched && resources.length === 0 && (
        <EmptyState
          icon={Globe}
          title="No useful learning resources were found."
          description={`Try a different topic, or rephrase "${searchedFor}" with a few more words.`}
          action={
            <Button variant="outline" onClick={() => runSearch(searchedFor)}>
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              Try again
            </Button>
          }
        />
      )}

      {!isLoading && !error && resources.length > 0 && (
        <section aria-label="Found learning resources">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold">Learning Resources</h2>
            <Badge tone="neutral">{resources.length}</Badge>
            <Badge tone="indigo">{searchedFor}</Badge>
            <div className="ml-auto flex items-center gap-2">
              <label htmlFor="selection-subject" className="text-xs font-medium text-slate-500">
                Save to:
              </label>
              <select
                id="selection-subject"
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(e.target.value)}
                disabled={isSelectingUrl !== null}
                className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0 disabled:opacity-60"
              >
                {subjects.length === 0 && <option value="">No subjects yet</option>}
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
              {subjects.length === 0 && (
                <Button to="/subjects" variant="outline" size="sm">
                  Create a subject
                </Button>
              )}
            </div>
          </div>
          <Card padded={false} className="divide-y divide-slate-100">
            {resources.map((resource) => (
              <ResourceListItem
                key={resource.url}
                resource={resource}
                isSelected={selectedUrls.has(resource.url)}
                isBusy={isSelectingUrl !== null}
                onToggleSelect={handleToggleSelect}
              />
            ))}
          </Card>
          <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-400">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            Saved resources are used by the AI Tutor, Quiz Generator, and Study Plan for this
            subject. Web content is always treated as untrusted text.
          </p>
        </section>
      )}

      {!isLoading && !error && !hasSearched && (
        <EmptyState
          icon={Globe}
          title="Search the web for learning resources"
          description="No material to upload? No problem. Enter a topic and ByteBrains will find tutorials, official documentation, practice exercises, and more."
        />
      )}

      {!isLoadingSelections && (
        <section aria-label="Selected resources" className="mt-10">
          <div className="mb-4 flex items-center gap-2">
            <h2 className="text-lg font-semibold">Selected Resources</h2>
            <Badge tone="neutral">{selections.length}</Badge>
            {subjects.length > 0 && selectedSubjectId && (
              <Badge tone="indigo">
                {subjects.find((subject) => subject.id === selectedSubjectId)?.name}
              </Badge>
            )}
          </div>
          {selections.length === 0 ? (
            <Card>
              <p className="text-sm text-slate-500">
                No resources saved yet. Search above and hit Select to save a resource for this
                subject — the AI Tutor, Quiz Generator, and Study Plan will then ground their
                answers in them.
              </p>
            </Card>
          ) : (
            <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {selections.map((selection) => (
                <SelectedResourceCard
                  key={selection.id}
                  selection={selection}
                  isDeleting={deletingSelectionId === selection.id}
                  onDelete={handleDeleteSelection}
                />
              ))}
            </ul>
          )}
          {isSelectingUrl && (
            <p className="mt-3 flex items-center gap-2 text-xs text-slate-400">
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              Saving resource…
            </p>
          )}
        </section>
      )}
    </>
  );
}