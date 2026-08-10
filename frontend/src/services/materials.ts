import { api, getApiBaseUrl } from './api';
import type { Material, MaterialUploadResponse } from '../types/material';

const MATERIALS_PATH = '/api/materials';

export async function uploadMaterial(
  subjectId: string,
  file: File
): Promise<MaterialUploadResponse> {
  const formData = new FormData();
  formData.append('subject_id', subjectId);
  formData.append('file', file);

  const response = await fetch(`${getApiBaseUrl()}${MATERIALS_PATH}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let detail = 'Upload failed';
    try {
      const error = await response.json();
      detail = error.detail ?? detail;
    } catch {
      detail = `${response.status} ${response.statusText}`;
    }
    throw new Error(detail);
  }

  return response.json();
}

export async function listMaterials(subjectId?: string): Promise<Material[]> {
  const url = subjectId
    ? `${MATERIALS_PATH}?subject_id=${subjectId}`
    : MATERIALS_PATH;
  return api.get<Material[]>(url);
}