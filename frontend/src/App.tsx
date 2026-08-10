function App() {
  // import.meta.env.DEV is provided by Vite:
  // true while running "npm run dev", false for production builds.
  const runningMode = import.meta.env.DEV ? 'development' : 'production'

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-800">
      <header className="bg-slate-900 text-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <h1 className="text-xl font-bold tracking-tight">ByteBrains</h1>
          <span className="rounded-full bg-slate-700 px-3 py-1 text-xs font-medium">
            Phase 1
          </span>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        <h2 className="text-4xl font-extrabold tracking-tight">
          Smarter Learning. Powered by AI.
        </h2>
        <p className="mt-4 max-w-xl text-slate-600">
          Your adaptive study companion is coming soon.
        </p>

        <section className="mt-12 w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Status
          </h3>
          <ul className="mt-4 space-y-2 text-sm">
            <li className="flex items-center justify-between">
              <span>Frontend</span>
              <span className="inline-flex items-center gap-1.5 font-medium text-emerald-600">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Running
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span>Mode</span>
              <span className="font-medium text-slate-600">{runningMode}</span>
            </li>
          </ul>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        ByteBrains &copy; {new Date().getFullYear()} &mdash; Phase 1 foundation
      </footer>
    </div>
  )
}

export default App