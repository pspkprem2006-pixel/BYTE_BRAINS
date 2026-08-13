import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { TutorPage } from './pages/TutorPage'
import { SubjectsPage } from './pages/SubjectsPage'
import { LearningResourcesPage } from './pages/LearningResourcesPage'
import { MaterialsPage } from './pages/MaterialsPage'
import { QuizzesPage } from './pages/QuizzesPage'
import { StudyPlanPage } from './pages/StudyPlanPage'
import { SettingsPage } from './pages/SettingsPage'

// Recharts is only needed on the Progress page, so it is loaded lazily
// to keep the initial bundle small.
const ProgressPage = lazy(() =>
  import('./pages/ProgressPage').then((module) => ({ default: module.ProgressPage })),
)

export default function App() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
          Loading…
        </div>
      }
    >
      <Routes>
      {/* Every page renders inside the shared application shell. */}
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/tutor" element={<TutorPage />} />
        <Route path="/subjects" element={<SubjectsPage />} />
        <Route path="/resources" element={<LearningResourcesPage />} />
        <Route path="/materials" element={<MaterialsPage />} />
        <Route path="/quizzes" element={<QuizzesPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/study-plan" element={<StudyPlanPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
      </Routes>
    </Suspense>
  )
}