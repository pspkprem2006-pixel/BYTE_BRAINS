import { useState, useEffect, useCallback, useRef, type FormEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Bot, FileText, Globe, Send, Sparkles, Loader2, AlertCircle, RotateCcw, ListChecks } from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { getMaterials } from '../services/materials';
import { askTutor } from '../services/tutor';
import { getSubjects } from '../services/subjects';
import { getSelectedResources } from '../services/learningResources';
import type { Material } from '../types/material';
import type { Subject } from '../types/subject';
import type { TutorMessage, TutorAskRequest } from '../types/tutor';

const suggestionPrompts = [
  'Explain this topic in simple terms',
  'Give me an example',
  'What are the key concepts?',
  "Explain this like I'm a beginner",
];

type SourceMode = 'material' | 'subject';

export function TutorPage() {
  const [searchParams] = useSearchParams();
  const materialParam = searchParams.get('material');
  const [materials, setMaterials] = useState<Material[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [mode, setMode] = useState<SourceMode>('material');
  const [selectedMaterialId, setSelectedMaterialId] = useState<string>('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [subjectResourceCount, setSubjectResourceCount] = useState(0);
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoadingMaterials, setIsLoadingMaterials] = useState(true);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Keep the newest message in view as the conversation grows.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isAsking]);

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
        setSelectedSubjectId((current) => current || data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load subjects');
    }
  }, []);

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

  const handleAsk = async (question: string) => {
    if (isAsking) return;
    const trimmed = question.trim();
    if (!trimmed) return;
    if (mode === 'material' && !selectedMaterialId) {
      setError('Please select a study material before asking the tutor.');
      return;
    }
    if (mode === 'subject' && !selectedSubjectId) {
      setError('Please select a subject before asking the tutor.');
      return;
    }

    const userMessage: TutorMessage = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsAsking(true);
    setError(null);

    try {
      const request: TutorAskRequest = {
        question: trimmed,
        ...(mode === 'material'
          ? { material_id: selectedMaterialId }
          : { subject_id: selectedSubjectId }),
      };
      const response = await askTutor(request);
      const assistantMessage: TutorMessage = { role: 'assistant', content: response.answer };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get answer';
      setError(message);
      // Add error as assistant message so it appears in chat
      const errorMessage: TutorMessage = {
        role: 'assistant',
        content: `⚠️ ${message}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    handleAsk(input);
  };

  const handleSuggestionClick = (prompt: string) => {
    handleAsk(prompt);
  };

  const handleRetry = () => {
    loadMaterials();
    loadSubjects();
  };

  const handleModeChange = (nextMode: SourceMode) => {
    if (isAsking) return;
    setMode(nextMode);
    setMessages([]);
    setError(null);
  };

  const handleMaterialChange = (materialId: string) => {
    setSelectedMaterialId(materialId);
    setMessages([]);
  };

  const handleSubjectChange = (subjectId: string) => {
    setSelectedSubjectId(subjectId);
    setMessages([]);
  };

  const selectedMaterial = materials.find(m => m.id === selectedMaterialId);
  const selectedSubject = subjects.find(s => s.id === selectedSubjectId);

  if (isLoadingMaterials) {
    return (
      <>
        <PageHeader title="AI Tutor" subtitle="Chat with your personal study assistant." />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" aria-hidden="true" />
          <span className="ml-3 text-sm text-slate-500">Loading materials…</span>
        </div>
      </>
    );
  }

  const usableMaterials = materials.filter((m) => m.processing_status === 'processed');

  return (
    <>
      <PageHeader
        title="AI Tutor"
        subtitle="Chat with your personal study assistant — grounded in your materials and web resources."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-xl border border-slate-300 bg-white p-0.5">
              <button
                type="button"
                onClick={() => handleModeChange('material')}
                disabled={isAsking}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-60 ${
                  mode === 'material'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                Material
              </button>
              <button
                type="button"
                onClick={() => handleModeChange('subject')}
                disabled={isAsking}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-60 ${
                  mode === 'subject'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                Web resources
              </button>
            </div>
            {mode === 'material' && usableMaterials.length > 0 && (
              <select
                value={selectedMaterialId}
                onChange={(e) => handleMaterialChange(e.target.value)}
                className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
                disabled={isAsking}
              >
                {usableMaterials.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.original_filename}
                  </option>
                ))}
              </select>
            )}
            {mode === 'subject' && subjects.length > 0 && (
              <select
                value={selectedSubjectId}
                onChange={(e) => handleSubjectChange(e.target.value)}
                className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
                disabled={isAsking}
              >
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
            )}
            {mode === 'material' && selectedMaterial && (
              <Button to={`/quizzes?material=${selectedMaterial.id}`}>
                <ListChecks className="h-4 w-4" aria-hidden="true" />
                Test My Knowledge
              </Button>
            )}
            {mode === 'subject' && selectedSubject && (
              <Button to={`/quizzes?subject=${selectedSubject.id}`}>
                <ListChecks className="h-4 w-4" aria-hidden="true" />
                Test My Knowledge
              </Button>
            )}
          </div>
        }
      />

      {error && (
        <Card className="mb-6 border-rose-200 bg-rose-50">
          <div className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-medium text-rose-800">Something went wrong</p>
              <p className="mt-1 text-sm text-rose-600">{error}</p>
              <Button variant="outline" size="sm" onClick={handleRetry} className="mt-3" disabled={isAsking}>
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Retry
              </Button>
            </div>
          </div>
        </Card>
      )}

      {mode === 'material' && materials.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No study material yet."
          description="Upload a PDF or TXT document first — the AI tutor answers questions grounded in your material."
          action={
            <Button to="/materials" variant="outline">
              <FileText className="h-4 w-4" aria-hidden="true" />
              Upload Material
            </Button>
          }
        />
      ) : mode === 'material' && usableMaterials.length === 0 ? (
        <EmptyState
          icon={FileText}
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
          description="Create a subject, find learning resources on the Learning Resources page, and save them — the tutor will answer grounded in them."
          action={
            <Button to="/resources" variant="outline">
              <Globe className="h-4 w-4" aria-hidden="true" />
              Find Learning Resources
            </Button>
          }
        />
      ) : (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_19rem]">
        {/* Conversation */}
        <Card padded={false} className="flex h-[70vh] min-h-[30rem] flex-col overflow-hidden lg:h-[calc(100vh-11.5rem)]">
          <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-semibold">ByteBrains Tutor</p>
              <p className="text-xs text-slate-500">
                {mode === 'material'
                  ? selectedMaterial
                    ? `Using: ${selectedMaterial.original_filename}`
                    : 'No material selected'
                  : selectedSubject
                    ? `Using: ${selectedSubject.name}${subjectResourceCount > 0 ? ` • ${subjectResourceCount} web resource${subjectResourceCount === 1 ? '' : 's'}` : ' • no web resources yet'}` 
                    : 'No subject selected'}
              </p>
            </div>
            {isAsking && (
              <Loader2 className="h-4 w-4 animate-spin text-indigo-600 ml-auto" aria-hidden="true" />
            )}
          </div>

          <div
            aria-live="polite"
            className="flex-1 overflow-y-auto px-5 py-6"
          >
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center px-4 text-center">
                <span className="rounded-2xl bg-indigo-50 p-4 text-indigo-600">
                  <Sparkles className="h-7 w-7" aria-hidden="true" />
                </span>
                <h2 className="mt-5 text-lg font-semibold">Hi! I'm your ByteBrains AI Tutor.</h2>
                <p className="mt-1 max-w-md text-sm text-slate-500">
                  {mode === 'material'
                    ? 'Select a material and ask me anything about it.'
                    : 'Select a subject and ask me anything — I use its saved web resources.'}
                </p>
                {mode === 'subject' && subjectResourceCount === 0 && (
                  <p className="mt-3 rounded-xl bg-amber-50 px-4 py-2 text-xs text-amber-700">
                    No web resources saved for this subject yet. Find resources on the Learning
                    Resources page — otherwise I can only give general guidance.
                  </p>
                )}
                {((mode === 'material' && selectedMaterial) || (mode === 'subject' && selectedSubject)) && (
                  <div className="mt-6 grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
                    {suggestionPrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => handleSuggestionClick(prompt)}
                        disabled={isAsking}
                        className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-60"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message, index) =>
                  message.role === 'user' ? (
                    <div key={index} className="flex justify-end">
                      <div className="max-w-[80%] break-words rounded-2xl rounded-br-md bg-indigo-600 px-4 py-2.5 text-sm text-white">
                        {message.content}
                      </div>
                    </div>
                  ) : (
                    <div key={index} className="flex items-start justify-start gap-2.5">
                      <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                        <Bot className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-2.5">
                        <p className="text-xs font-semibold tracking-wide text-slate-400 uppercase">
                          ByteBrains Tutor
                        </p>
                        <p className="mt-1 text-sm break-words whitespace-pre-wrap text-slate-600">{message.content}</p>
                      </div>
                    </div>
                  ),
                )}
                {isAsking && (
                  <div className="flex items-start justify-start gap-2.5">
                    <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                      <Bot className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-2.5 animate-pulse">
                      <p className="text-xs font-semibold tracking-wide text-slate-400 uppercase">
                        ByteBrains Tutor
                      </p>
                      <p className="mt-1 text-sm text-slate-400">Thinking…</p>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="border-t border-slate-200 px-4 py-3">
            <label htmlFor="tutor-input" className="sr-only">
              Ask the AI tutor a question
            </label>
            <div className="flex items-end gap-2">
              <input
                id="tutor-input"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder={
                  mode === 'material'
                    ? selectedMaterial
                      ? 'Ask anything about this material…'
                      : 'Select a material first'
                    : selectedSubject
                      ? 'Ask anything about this subject…'
                      : 'Select a subject first'
                }
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
                disabled={
                  isAsking ||
                  (mode === 'material' ? !selectedMaterialId : !selectedSubjectId)
                }
              />
              <button
                type="submit"
                disabled={
                  !input.trim() ||
                  isAsking ||
                  (mode === 'material' ? !selectedMaterialId : !selectedSubjectId)
                }
                aria-label="Send message"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Send className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          </form>
        </Card>

        {/* Study context */}
        <Card className="h-fit">
          <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">Study context</h2>
          <div className="mt-3 space-y-3">
            {mode === 'material' && (
              <div>
                <p className="text-xs text-slate-400">Selected material</p>
                {selectedMaterial ? (
                  <Badge tone="indigo" className="mt-1">{selectedMaterial.original_filename}</Badge>
                ) : (
                  <Badge tone="neutral" className="mt-1">None selected</Badge>
                )}
              </div>
            )}
            {mode === 'subject' && (
              <div>
                <p className="text-xs text-slate-400">Subject</p>
                {selectedSubject ? (
                  <Badge tone="indigo" className="mt-1">{selectedSubject.name}</Badge>
                ) : (
                  <Badge tone="neutral" className="mt-1">None selected</Badge>
                )}
                <p className="mt-2 text-xs text-slate-400">Web resources</p>
                {subjectResourceCount > 0 ? (
                  <Badge tone="emerald" className="mt-1">{subjectResourceCount} saved</Badge>
                ) : (
                  <Badge tone="neutral" className="mt-1">None saved</Badge>
                )}
              </div>
            )}
            {mode === 'material' && (
              <div>
                <p className="text-xs text-slate-400">All materials</p>
                <ul className="mt-2 space-y-2 max-h-40 overflow-y-auto">
                  {materials.length === 0 ? (
                    <li className="text-sm text-slate-500">No materials uploaded yet</li>
                  ) : (
                    materials.map((material) => (
                      <li key={material.id} className="flex items-center gap-2 text-sm">
                        <FileText className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
                        <span className="truncate text-slate-600">{material.original_filename}</span>
                        <Badge tone="emerald" className="ml-auto text-xs">{material.processing_status}</Badge>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            )}
          </div>
          <p className="mt-4 rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-500">
            {mode === 'material'
              ? 'Answers are grounded in your uploaded study materials using AI.'
              : 'Answers use your saved web resources (titles and descriptions only). Web content is treated as untrusted text.'}
          </p>
        </Card>
      </div>
      )}
    </>
  );
}