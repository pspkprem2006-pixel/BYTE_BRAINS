import { useState, type FormEvent } from 'react'
import { Bot, FileText, Send, Sparkles } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { materials } from '../data/mockData'

interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
  /** Preview bubbles are clearly marked as non-AI placeholders. */
  preview?: boolean
}

const suggestionPrompts = [
  'Explain normalization simply',
  'Give me an example',
  'Quiz me on SQL',
  "Explain this like I'm a beginner",
]

const comingSoonNote =
  'The AI tutor arrives in the next phase. For now this is the conversation UI only.'

export function TutorPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [nextId, setNextId] = useState(1)

  const sendMessage = (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return

    setMessages((current) => [
      ...current,
      { id: nextId, role: 'user', text: trimmed },
      { id: nextId + 1, role: 'assistant', text: comingSoonNote, preview: true },
    ])
    setNextId((current) => current + 2)
    setInput('')
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    sendMessage(input)
  }

  return (
    <>
      <PageHeader
        title="AI Tutor"
        subtitle="Chat with your personal study assistant — answers arrive in the next phase."
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_19rem]">
        {/* Conversation */}
        <Card
          padded={false}
          className="flex h-[70vh] min-h-[30rem] flex-col overflow-hidden lg:h-[calc(100vh-11.5rem)]"
        >
          <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-semibold">ByteBrains Tutor</p>
              <p className="text-xs text-slate-500">Online · powered by RAG in later phases</p>
            </div>
            <Badge tone="amber" className="ml-auto">
              Coming next phase
            </Badge>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-6">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center px-4 text-center">
                <span className="rounded-2xl bg-indigo-50 p-4 text-indigo-600">
                  <Sparkles className="h-7 w-7" aria-hidden="true" />
                </span>
                <h2 className="mt-5 text-lg font-semibold">Hi! I'm your ByteBrains AI Tutor.</h2>
                <p className="mt-1 max-w-md text-sm text-slate-500">
                  Ask me anything about what you're studying.
                </p>
                <div className="mt-6 grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
                  {suggestionPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => sendMessage(prompt)}
                      className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) =>
                  message.role === 'user' ? (
                    <div key={message.id} className="flex justify-end">
                      <p className="max-w-[80%] rounded-2xl rounded-br-md bg-indigo-600 px-4 py-2.5 text-sm text-white">
                        {message.text}
                      </p>
                    </div>
                  ) : (
                    <div key={message.id} className="flex justify-start">
                      <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-dashed border-slate-300 bg-slate-50 px-4 py-2.5">
                        <p className="text-xs font-semibold tracking-wide text-slate-400 uppercase">
                          ByteBrains Tutor
                        </p>
                        <p className="mt-1 text-sm text-slate-600">{message.text}</p>
                      </div>
                    </div>
                  ),
                )}
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
                placeholder="Ask anything…"
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
              <button
                type="submit"
                disabled={!input.trim()}
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
          <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">
            Study context
          </h2>
          <div className="mt-3 space-y-3">
            <div>
              <p className="text-xs text-slate-400">Active subject</p>
              <Badge tone="indigo" className="mt-1">
                DBMS
              </Badge>
            </div>
            <div>
              <p className="text-xs text-slate-400">Context sources</p>
              <ul className="mt-2 space-y-2">
                {materials.slice(0, 2).map((material) => (
                  <li key={material.id} className="flex items-center gap-2 text-sm">
                    <FileText className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
                    <span className="truncate text-slate-600">{material.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="mt-4 rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-500">
            In the next phase, answers will be grounded in your uploaded materials
            using RAG.
          </p>
        </Card>
      </div>
    </>
  )
}