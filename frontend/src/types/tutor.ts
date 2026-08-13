export interface TutorAskRequest {
  material_id?: string;
  subject_id?: string;
  question: string;
}

export interface TutorAskResponse {
  material_id?: string | null;
  question: string;
  answer: string;
}

export interface TutorMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ApiError {
  detail: string;
}