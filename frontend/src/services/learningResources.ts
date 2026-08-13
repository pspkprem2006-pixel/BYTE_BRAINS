import { api } from './api';
import type {
  LearningResourceSelection,
  LearningResourcesResponse,
  SelectLearningResourceRequest,
  SelectedResourcesResponse,
} from '../types/learningResources';

const RESOURCES_PATH = '/api/learning-resources';

export async function discoverLearningResources(
  query: string,
  count?: number,
): Promise<LearningResourcesResponse> {
  return api.post<LearningResourcesResponse>(RESOURCES_PATH, {
    query,
    ...(count !== undefined ? { count } : {}),
  });
}

export async function selectLearningResource(
  request: SelectLearningResourceRequest,
): Promise<LearningResourceSelection> {
  return api.post<LearningResourceSelection>(`${RESOURCES_PATH}/select`, request);
}

export async function getSelectedResources(
  subjectId?: string,
  limit = 100,
): Promise<SelectedResourcesResponse> {
  const params = new URLSearchParams();
  if (subjectId) params.set('subject_id', subjectId);
  params.set('limit', String(limit));
  return api.get<SelectedResourcesResponse>(`${RESOURCES_PATH}/selected?${params.toString()}`);
}

export async function deleteSelectedResource(selectionId: string): Promise<void> {
  return api.delete<void>(`${RESOURCES_PATH}/selected/${selectionId}`);
}