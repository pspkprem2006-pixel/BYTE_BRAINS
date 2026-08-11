import { api } from './api';
import type {
  QuizAttemptSummary,
  QuizGenerateRequest,
  QuizGenerateResponse,
  QuizSubmitRequest,
  QuizSubmitResponse,
} from '../types/quiz';

const QUIZZES_PATH = '/api/quizzes';

export async function generateQuiz(
  request: QuizGenerateRequest
): Promise<QuizGenerateResponse> {
  return api.post<QuizGenerateResponse>(`${QUIZZES_PATH}/generate`, request);
}

export async function submitQuiz(
  request: QuizSubmitRequest
): Promise<QuizSubmitResponse> {
  return api.post<QuizSubmitResponse>(`${QUIZZES_PATH}/submit`, request);
}

export async function getQuizAttempts(
  limit = 10
): Promise<QuizAttemptSummary[]> {
  return api.get<QuizAttemptSummary[]>(`${QUIZZES_PATH}/attempts?limit=${limit}`);
}
