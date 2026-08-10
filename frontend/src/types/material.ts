export interface Material {
  id: string;
  subject_id: string | null;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number | null;
  processing_status: 'uploaded' | 'processing' | 'processed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface MaterialUploadResponse {
  id: string;
  subject_id: string | null;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number | null;
  processing_status: string;
  created_at: string;
  updated_at: string;
}

export interface ApiError {
  detail: string;
}