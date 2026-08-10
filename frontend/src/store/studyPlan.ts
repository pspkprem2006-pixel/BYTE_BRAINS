import type { StudyPlanGenerateResponse } from '../types/studyPlan';

let studyPlan: StudyPlanGenerateResponse | null = null;

export function getStudyPlan(): StudyPlanGenerateResponse | null {
  return studyPlan;
}

export function setStudyPlan(plan: StudyPlanGenerateResponse | null): void {
  studyPlan = plan;
}
