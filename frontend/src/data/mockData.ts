// Temporary demo data for the Phase 2 UI shell.
// Components only receive data through these types and values, so this file
// can be swapped for real API responses in later phases without touching the UI.

export interface StudentStats {
  overallProgress: number
  topicsCompleted: number
  studyStreakDays: number
  studyTimeHours: number
}

export interface Subject {
  id: string
  name: string
  description: string
  progress: number
  topicCount: number
  lastStudied: string
}

export type WeakTopicLevel = 'critical' | 'needs-improvement' | 'good'

export interface WeakTopic {
  id: string
  name: string
  score: number
  level: WeakTopicLevel
}

export interface StudyPlanItem {
  id: string
  time: string
  title: string
}

export interface Quiz {
  id: string
  subject: string
  topic: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  questionCount: number
  score?: number
  completedAt?: string
}

export interface Material {
  id: string
  name: string
  fileType: string
  subject: string
  uploadedAt: string
  status: 'Processed' | 'Queued'
}

export interface WeeklyActivityPoint {
  day: string
  minutes: number
}

// --- Student stats -----------------------------------------------------------

export const studentStats: StudentStats = {
  overallProgress: 74,
  topicsCompleted: 24,
  studyStreakDays: 7,
  studyTimeHours: 12.5,
}

// --- Subjects ----------------------------------------------------------------

export const subjects: Subject[] = [
  {
    id: 'dbms',
    name: 'DBMS',
    description: 'Database fundamentals, SQL, transactions and normalization.',
    progress: 74,
    topicCount: 18,
    lastStudied: 'Today',
  },
  {
    id: 'python',
    name: 'Python',
    description: 'Core language concepts, data structures and practice.',
    progress: 84,
    topicCount: 12,
    lastStudied: 'Yesterday',
  },
  {
    id: 'ml',
    name: 'Machine Learning',
    description: 'Supervised learning, model evaluation and tuning.',
    progress: 61,
    topicCount: 22,
    lastStudied: '2 days ago',
  },
]

// --- Weak topics -------------------------------------------------------------

export const weakTopics: WeakTopic[] = [
  { id: 'deadlocks', name: 'Deadlocks', score: 32, level: 'critical' },
  { id: 'transactions', name: 'Transactions', score: 45, level: 'needs-improvement' },
  { id: 'normalization', name: 'Normalization', score: 68, level: 'good' },
]

export const topicPerformance: WeakTopic[] = [
  { id: 't1', name: 'SQL Basics', score: 88, level: 'good' },
  { id: 't2', name: 'Indexing', score: 71, level: 'good' },
  { id: 't3', name: 'Joins', score: 55, level: 'needs-improvement' },
  { id: 't4', name: 'Transactions', score: 45, level: 'needs-improvement' },
  { id: 't5', name: 'Normalization', score: 68, level: 'good' },
  { id: 't6', name: 'Deadlocks', score: 32, level: 'critical' },
]

// --- Study plan --------------------------------------------------------------

export const todaysStudyPlan: StudyPlanItem[] = [
  { id: 'plan-1', time: '09:00', title: 'Review Normalization' },
  { id: 'plan-2', time: '10:00', title: 'Take DBMS Quiz' },
  { id: 'plan-3', time: '18:00', title: 'Study Transactions' },
]

export const upcomingTasks = [
  { id: 'u1', title: 'Normalization revision', when: 'Tomorrow, 09:00' },
  { id: 'u2', title: 'Transactions lesson', when: 'Wednesday, 16:00' },
  { id: 'u3', title: 'SQL joins quiz', when: 'Thursday, 18:00' },
]

export const exam = {
  title: 'DBMS Exam',
  daysRemaining: 5,
  date: 'Sat, Aug 15',
}

export const studyGoals = [
  { id: 'g1', label: 'Weekly study time', current: '12.5 hrs', target: '15 hrs', percent: 83 },
  { id: 'g2', label: 'Topics per week', current: '6 of 8', target: '8 topics', percent: 75 },
]

// --- Quizzes -----------------------------------------------------------------

export const recentQuizzes: Quiz[] = [
  {
    id: 'q1',
    subject: 'DBMS',
    topic: 'Normalization',
    difficulty: 'Medium',
    questionCount: 10,
    score: 80,
    completedAt: 'Yesterday',
  },
  {
    id: 'q2',
    subject: 'Python',
    topic: 'Functions',
    difficulty: 'Easy',
    questionCount: 8,
    score: 100,
    completedAt: '2 days ago',
  },
]

export const recommendedQuizzes: Quiz[] = []

export const completedQuizzes: Quiz[] = [
  {
    id: 'q3',
    subject: 'Machine Learning',
    topic: 'Linear Regression',
    difficulty: 'Hard',
    questionCount: 12,
    score: 67,
    completedAt: 'Last week',
  },
  {
    id: 'q4',
    subject: 'DBMS',
    topic: 'SQL Basics',
    difficulty: 'Easy',
    questionCount: 10,
    score: 90,
    completedAt: 'Last week',
  },
  {
    id: 'q5',
    subject: 'DBMS',
    topic: 'ER Diagrams',
    difficulty: 'Medium',
    questionCount: 10,
    score: 70,
    completedAt: '2 weeks ago',
  },
]

// --- Materials ---------------------------------------------------------------

export const materials: Material[] = [
  {
    id: 'm1',
    name: 'Chapter 4 - Transactions.pdf',
    fileType: 'PDF',
    subject: 'DBMS',
    uploadedAt: 'Aug 5, 2026',
    status: 'Processed',
  },
  {
    id: 'm2',
    name: 'Normalization Notes.pdf',
    fileType: 'PDF',
    subject: 'DBMS',
    uploadedAt: 'Aug 3, 2026',
    status: 'Processed',
  },
  {
    id: 'm3',
    name: 'Python Cheat Sheet.pdf',
    fileType: 'PDF',
    subject: 'Python',
    uploadedAt: 'Jul 28, 2026',
    status: 'Processed',
  },
]

// --- Progress ----------------------------------------------------------------

export const weeklyActivity: WeeklyActivityPoint[] = [
  { day: 'Mon', minutes: 45 },
  { day: 'Tue', minutes: 30 },
  { day: 'Wed', minutes: 75 },
  { day: 'Thu', minutes: 50 },
  { day: 'Fri', minutes: 90 },
  { day: 'Sat', minutes: 65 },
  { day: 'Sun', minutes: 40 },
]