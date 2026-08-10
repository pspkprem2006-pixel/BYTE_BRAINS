export interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: number;
  explanation: string;
  topic: string;
}

export interface QuizGenerateRequest {
  material_id: string;
  question_count: number;
}

export interface QuizGenerateResponse {
  material_id: string;
  questions: QuizQuestion[];
  question_count: number;
}

export interface ApiError {
  detail: string;
}