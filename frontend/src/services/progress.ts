import { api } from './api';
import type { ProgressItem } from '../types/progress';

export async function getProgress(): Promise<ProgressItem[]> {
  return api.get<ProgressItem[]>('/api/progress');
}
