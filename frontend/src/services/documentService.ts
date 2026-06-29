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
   * Carica un file nel backend per l'indicazione RAG.
   */
  async upload(file: File): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8095/api/v1'}/documents/upload`, {
      method: 'POST',
      body: formData,
      // Nota: non impostare Content-Type, il browser lo farà automaticamente con il boundary
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Upload fallito (HTTP ${response.status})`);
    }

    const result = await response.json();
    return result.data;
  },

  /**
   * Elenca i documenti caricati dal tenant corrente.
   */
  async list(): Promise<DocumentInfo[]> {
    const result = await apiFetch<{ data: DocumentInfo[] }>('/documents');
    return result.data;
  },

  /**
   * Elimina un documento.
   */
  async delete(documentId: string): Promise<void> {
    await apiFetch(`/documents/${documentId}`, { method: 'DELETE' });
  }
};
