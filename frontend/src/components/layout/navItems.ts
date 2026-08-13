import {
  BookOpen,
  Bot,
  CalendarRange,
  FileQuestion,
  Files,
  Globe,
  LayoutDashboard,
  Settings,
  TrendingUp,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

export const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/tutor', label: 'AI Tutor', icon: Bot },
  { to: '/subjects', label: 'Subjects', icon: BookOpen },
  { to: '/resources', label: 'Learning Resources', icon: Globe },
  { to: '/materials', label: 'Materials', icon: Files },
  { to: '/quizzes', label: 'Quizzes', icon: FileQuestion },
  { to: '/progress', label: 'Progress', icon: TrendingUp },
  { to: '/study-plan', label: 'Study Plan', icon: CalendarRange },
  { to: '/settings', label: 'Settings', icon: Settings },
]