export type StudyFocus = 'Complete syllabus' | 'Improve weak topics' | 'Balanced';

export type PlanTaskType = 'study' | 'practice' | 'revision' | 'quiz';

export interface StudyPlanTask {
  title: string;
  duration_minutes: number;
  type: PlanTaskType;
}

export interface StudyPlanDay {
  day: number;
  tasks: StudyPlanTask[];
}

export interface StudyPlanGenerateRequest {
  subject_id: string;
  days_available: number;
  hours_per_day: number;
  focus: StudyFocus;
  exam_date: string | null;
  weak_topics: string[];
}

export interface StudyPlanGenerateResponse {
  subject_id: string;
  days: StudyPlanDay[];
}