export type ResourceType =
  | 'official_docs'
  | 'tutorial'
  | 'article'
  | 'video'
  | 'practice'
  | 'reference'
  | 'course'
  | 'other';

export interface LearningResource {
  title: string;
  url: string;
  domain: string;
  description: string;
  resource_type: ResourceType;
  is_official: boolean;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | null;
  relevance_score: number;
  source: string;
  retrieved_at: string;
  topic: string;
}

export interface LearningResourcesResponse {
  query: string;
  resources: LearningResource[];
}

export interface LearningResourceSelection {
  id: string;
  subject_id: string | null;
  title: string;
  url: string;
  domain: string;
  resource_type: ResourceType;
  is_official: boolean;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | null;
  description: string;
  source: string;
  created_at: string;
  last_used_at: string | null;
}

export interface SelectLearningResourceRequest {
  subject_id?: string | null;
  title: string;
  url: string;
  resource_type?: ResourceType;
  is_official?: boolean;
  difficulty?: 'beginner' | 'intermediate' | 'advanced' | null;
  description?: string;
  source?: string;
  domain?: string;
}

export interface SelectedResourcesResponse {
  resources: LearningResourceSelection[];
  count: number;
}