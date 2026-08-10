import { api } from './api';
import type { TutorAskRequest, TutorAskResponse } from '../types/tutor';

const TUTOR_PATH = '/api/tutor';

export async function askTutor(request: TutorAskRequest): Promise<TutorAskResponse> {
  return api.post<TutorAskResponse>(`${TUTOR_PATH}/ask`, request);
}