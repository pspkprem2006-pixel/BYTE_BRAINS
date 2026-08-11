import { useState, useEffect, useCallback } from 'react';
import { Plus, Loader2, AlertCircle, RotateCcw, FileText, File, X, MessageSquareText, Sparkles } from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { getSubjects } from '../services/subjects';
import { uploadMaterial, listMaterials } from '../services/materials';
import type { Subject } from '../types/subject';
import type { Material } from '../types/material';

function formatFileSize(bytes: number | null): string {
  if (!bytes) return 'Unknown size';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getStatusTone(status: string): 'neutral' | 'indigo' | 'emerald' | 'amber' | 'rose' {
  switch (status) {
    case 'processed': return 'emerald';
    case 'processing': return 'indigo';
    case 'failed': return 'rose';
    default: return 'amber';
  }
}

function getFileIcon(fileType: string) {
  return fileType === 'application/pdf' ? FileText : File;
}

export function MaterialsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [materials, setMaterials] = useState<Material[]>([]);
  const [isLoadingSubjects, setIsLoadingSubjects] = useState(true);
  const [isLoadingMaterials, setIsLoadingMaterials] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSubjectSelect, setShowSubjectSelect] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const loadSubjects = useCallback(async () => {
    try {
      const data = await getSubjects();
      setSubjects(data);
      if (data.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load subjects');
    } finally {
      setIsLoadingSubjects(false);
    }
  }, [selectedSubjectId]);

  const loadMaterials = useCallback(async () => {
    if (!selectedSubjectId) {
      setMaterials([]);
      return;
    }
    setIsLoadingMaterials(true);
    setError(null);
    try {
      const data = await listMaterials(selectedSubjectId);
      setMaterials(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load materials');
    } finally {
      setIsLoadingMaterials(false);
    }
  }, [selectedSubjectId]);

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  useEffect(() => {
    loadMaterials();
  }, [loadMaterials]);

  const validateAndUpload = (file: File): void => {
    if (!selectedSubjectId) return;

    const allowedTypes = ['application/pdf', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
      alert('Only PDF and TXT files are supported.');
      return;
    }

    const maxSize = 10 * 1024 * 1024; // 10 MB
    if (file.size > maxSize) {
      alert('File size exceeds 10 MB limit.');
      return;
    }

    uploadFile(file);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    validateAndUpload(file);
    event.target.value = '';
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (!file || !selectedSubjectId) return;
    validateAndUpload(file);
  };

  const uploadFile = async (file: File) => {
    if (!selectedSubjectId) return;
    setIsUploading(true);
    setError(null);
    try {
      await uploadMaterial(selectedSubjectId, file);
      await loadMaterials();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubjectChange = (subjectId: string) => {
    setSelectedSubjectId(subjectId);
    setShowSubjectSelect(false);
  };

  const handleRetry = () => {
    loadSubjects();
    loadMaterials();
  };

  if (isLoadingSubjects) {
    return (
      <>
        <PageHeader title="Materials" subtitle="Your study document library." />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" aria-hidden="true" />
          <span className="ml-3 text-sm text-slate-500">Loading subjects…</span>
        </div>
      </>
    );
  }

  const selectedSubject = subjects.find(s => s.id === selectedSubjectId);
  const hasSubjects = subjects.length > 0;

  return (
    <>
      <PageHeader
        title="Materials"
        subtitle="Your study document library, ready for AI-powered learning."
        action={
          hasSubjects && (
            <Button
              variant="outline"
              onClick={() => setShowSubjectSelect(true)}
              disabled={isUploading}
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              Add Material
            </Button>
          )
        }
      />

      {hasSubjects && (
        <div className="mb-6 flex items-center gap-3">
          <label htmlFor="subject-select" className="text-sm font-medium text-slate-700">
            Subject:
          </label>
          <select
            id="subject-select"
            value={selectedSubjectId}
            onChange={(e) => handleSubjectChange(e.target.value)}
            className="flex-1 max-w-xs rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
            disabled={isLoadingMaterials}
          >
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>
          {showSubjectSelect && (
            <Button variant="ghost" size="sm" onClick={() => setShowSubjectSelect(false)}>
              <X className="h-4 w-4" aria-hidden="true" />
            </Button>
          )}
        </div>
      )}

      {error && (
        <Card className="mb-6 border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Unable to load materials</p>
              <p className="mt-1 text-sm text-rose-600">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                className="mt-3"
                disabled={isUploading}
              >
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Retry
              </Button>
            </div>
          </div>
        </Card>
      )}

      {hasSubjects && (
        <Card className="mb-6 border-dashed border-slate-300 bg-white">
          <div className="p-6">
            <input
              type="file"
              id="file-upload"
              accept=".pdf,.txt"
              onChange={handleFileSelect}
              className="sr-only"
              disabled={isUploading}
            />
            <label
              htmlFor="file-upload"
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center cursor-pointer transition-colors hover:border-indigo-400 hover:bg-indigo-50/60 ${
                isDragging ? 'border-indigo-500 bg-indigo-50' : ''
              }`}
            >
              <div className="flex flex-col items-center gap-2">
                <p className="text-base font-semibold text-slate-800">
                  Drag & drop or click to select a file
                </p>
                <p className="text-sm text-slate-500">
                  PDF or TXT, up to 10 MB
                </p>
              </div>
              {isUploading && (
                <div className="mt-4 flex items-center gap-2 text-sm text-indigo-600">
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Uploading and extracting text…
                </div>
              )}
            </label>
          </div>
        </Card>
      )}

      {!hasSubjects && (
        <EmptyState
          icon={Plus}
          title="No subjects yet"
          description="Create a subject first to upload materials."
          action={
            <Button variant="outline" onClick={() => window.location.href = '/subjects'}>
              <Plus className="h-4 w-4" aria-hidden="true" />
              Add Subject
            </Button>
          }
        />
      )}

      <section aria-labelledby="library-heading" className="mt-8">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h2 id="library-heading" className="text-lg font-semibold">
              Your materials
            </h2>
            {!isLoadingMaterials && materials.length > 0 && (
              <Badge tone="neutral">{materials.length}</Badge>
            )}
          </div>
          {hasSubjects && selectedSubject && (
            <Badge tone="indigo">{selectedSubject.name}</Badge>
          )}
        </div>

        {isLoadingMaterials ? (
          <Card padded={false} className="divide-y divide-slate-100">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex flex-wrap items-center gap-x-6 gap-y-2 px-5 py-4 animate-pulse">
                <div className="min-w-0 flex-1">
                  <div className="h-4 bg-slate-200 rounded w-3/4" />
                  <div className="mt-0.5 h-3 bg-slate-200 rounded w-1/4" />
                </div>
                <div className="h-5 bg-slate-200 rounded w-20" />
                <div className="h-5 bg-slate-200 rounded w-24" />
                <div className="h-5 bg-slate-200 rounded w-24" />
              </div>
            ))}
          </Card>
        ) : materials.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No study material yet."
            description="Upload a PDF or TXT file to start learning with AI."
            action={
              <label htmlFor="file-upload" className="cursor-pointer">
                <Button variant="outline" disabled={isUploading}>
                  <Plus className="h-4 w-4" aria-hidden="true" />
                  Upload Material
                </Button>
              </label>
            }
          />
        ) : (
          <Card padded={false} className="divide-y divide-slate-100">
            {materials.map((material) => {
                const FileIcon = getFileIcon(material.file_type);
                const isReady = material.processing_status === 'processed';
                return (
                  <div key={material.id} className="flex flex-wrap items-center gap-x-6 gap-y-2 px-5 py-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <FileIcon className="h-5 w-5 text-slate-400" aria-hidden="true" />
                        <p className="truncate text-sm font-medium text-slate-800">{material.original_filename}</p>
                      </div>
                      <p className="mt-0.5 text-xs text-slate-400">
                        {formatFileSize(material.file_size)} • Uploaded {new Date(material.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge tone="neutral">{material.file_type === 'application/pdf' ? 'PDF' : 'TXT'}</Badge>
                    <Badge tone={getStatusTone(material.processing_status)}>
                      {material.processing_status}
                    </Badge>
                    {isReady && (
                      <div className="flex w-full flex-wrap gap-2 sm:w-auto">
                        <Button
                          to={`/tutor?material=${material.id}`}
                          variant="outline"
                          size="sm"
                        >
                          <MessageSquareText className="h-4 w-4" aria-hidden="true" />
                          Ask Tutor
                        </Button>
                        <Button
                          to={`/quizzes?material=${material.id}`}
                          variant="outline"
                          size="sm"
                        >
                          <Sparkles className="h-4 w-4" aria-hidden="true" />
                          Generate Quiz
                        </Button>
                      </div>
                    )}
                  </div>
                );
              })}
          </Card>
        )}
      </section>
    </>
  );
}