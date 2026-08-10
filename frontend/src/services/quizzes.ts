import { api } from './api';
import type { QuizGenerateRequest, QuizGenerateResponse } from '../types/quiz';

const QUIZZES_PATH = '/api/quizzes';

export async function generateQuiz(
  request: QuizGenerateRequest
): Promise<QuizGenerateResponse> {
  return api.post<QuizGenerateResponse>(`${QUIZZES_PATH}/generate`, request);
}