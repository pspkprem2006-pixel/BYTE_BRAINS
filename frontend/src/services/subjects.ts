import { api } from './api';
import type { Subject, SubjectCreate, SubjectUpdate } from '../types/subject';

const SUBJECTS_PATH = '/api/subjects';

export async function getSubjects(): Promise<Subject[]> {
  return api.get<Subject[]>(SUBJECTS_PATH);
}

export async function getSubject(id: string): Promise<Subject> {
  return api.get<Subject>(`${SUBJECTS_PATH}/${id}`);
}

export async function createSubject(data: SubjectCreate): Promise<Subject> {
  return api.post<Subject>(SUBJECTS_PATH, data);
}

export async function updateSubject(id: string, data: SubjectUpdate): Promise<Subject> {
  return api.put<Subject>(`${SUBJECTS_PATH}/${id}`, data);
}

export async function deleteSubject(id: string): Promise<void> {
  return api.delete<void>(`${SUBJECTS_PATH}/${id}`);
}