import { getSubjects } from './subjects';
import { getMaterials } from './materials';
import { getWeakTopics, getQuizSession } from '../store/weakTopics';
import { getStudyPlan } from '../store/studyPlan';
import type { Subject } from '../types/subject';
import type { Material } from '../types/material';
import type { QuizSession } from '../store/weakTopics';
import type { StudyPlanGenerateResponse } from '../types/studyPlan';

export interface DashboardSummary {
  subjects_count: number;
  materials_count: number;
  weak_topics: string[];
  recent_materials: Material[];
  quiz_session: QuizSession | null;
  study_plan: StudyPlanGenerateResponse | null;
  subjects: Subject[];
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const [subjects, materials] = await Promise.all([getSubjects(), getMaterials()]);

  return {
    subjects_count: subjects.length,
    materials_count: materials.length,
    weak_topics: getWeakTopics(),
    recent_materials: [...materials]
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
      .slice(0, 4),
    quiz_session: getQuizSession(),
    study_plan: getStudyPlan(),
    subjects,
  };
}
