// src/services/api.ts
import { IPublicClientApplication } from '@azure/msal-browser';

import { useAuthStore } from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

let msalInstance: IPublicClientApplication | null = null;

export function setMsalInstance(instance: IPublicClientApplication) {
  msalInstance = instance;
}

export async function getAuthHeader(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};
  
  // 1. Tenant ID from Store
  const { tenantId } = useAuthStore.getState();
  if (tenantId) headers['X-Tenant-Id'] = tenantId;

  // 2. JWT from MSAL
  if (!msalInstance) return headers;
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length === 0) return headers;
  
  try {
    const result = await msalInstance.acquireTokenSilent({
      scopes: ['openid', 'profile'],
      account: accounts[0],
    });
    headers['Authorization'] = `Bearer ${result.accessToken}`;
  } catch (error) {
    console.warn("MSAL silent token acquisition failed:", error);
  }
  
  return headers;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const authHeaders = await getAuthHeader();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export { API_BASE_URL };
