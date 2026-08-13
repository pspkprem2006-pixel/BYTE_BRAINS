export interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: number;
  explanation: string;
  topic: string;
}

export interface QuizGenerateRequest {
  material_id?: string;
  subject_id?: string;
  question_count: number;
}

export interface QuizGenerateResponse {
  material_id?: string | null;
  subject_id?: string | null;
  questions: QuizQuestion[];
  question_count: number;
}

export interface TopicResult {
  topic: string;
  correct: number;
  total: number;
}

export interface QuizSubmitRequest {
  material_id?: string;
  subject_id?: string;
  total_questions: number;
  correct_answers: number;
  topic_results: TopicResult[];
}

export interface QuizSubmitResponse {
  attempt_id: string;
  quiz_title: string;
  total_questions: number;
  correct_answers: number;
  score: number;
  completed_at: string;
}

export interface QuizAttemptSummary {
  id: string;
  quiz_title: string;
  subject_id: string;
  subject_name: string;
  total_questions: number;
  correct_answers: number;
  score: number;
  completed_at: string | null;
}

export interface ApiError {
  detail: string;
}