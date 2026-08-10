import { api } from './api';
import type {
  StudyPlanGenerateRequest,
  StudyPlanGenerateResponse,
} from '../types/studyPlan';

const STUDY_PLAN_PATH = '/api/study-plan';

export async function generateStudyPlan(
  request: StudyPlanGenerateRequest
): Promise<StudyPlanGenerateResponse> {
  return api.post<StudyPlanGenerateResponse>(`${STUDY_PLAN_PATH}/generate`, request);
}