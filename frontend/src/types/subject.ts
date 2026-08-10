export interface Subject {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubjectCreate {
  name: string;
  description?: string;
}

export interface SubjectUpdate {
  name?: string;
  description?: string;
}

export interface ApiError {
  detail: string;
}