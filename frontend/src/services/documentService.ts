// src/services/documentService.ts
import { apiFetch } from './api';

export interface DocumentInfo {
  id: string;
  name: string;
  size: number;
  type: string;
  uploaded_at: string;
}

export const documentService = {
  /**
   * Load a file in the backend for RAG indication.
   */
  async upload(file: File): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8095/api/v1'}/documents/upload`, {
      method: 'POST',
      body: formData,
      // Note: do not set Content-Type, the browser will do it automatically with the boundary
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Upload fallito (HTTP ${response.status})`);
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Lists documents uploaded by the current tenant.
   */
  async list(): Promise<DocumentInfo[]> {
    const result = await apiFetch<{ data: DocumentInfo[] }>('/documents');
    return result.data;
  },

  /**
   * Delete a document.
   */
  async delete(documentId: string): Promise<void> {
    await apiFetch(`/documents/${documentId}`, { method: 'DELETE' });
  }
};
