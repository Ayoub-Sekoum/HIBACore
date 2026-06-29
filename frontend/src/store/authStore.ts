import { create } from 'zustand';

interface AuthState {
  user: any | null;
  token: string | null;
  tenantId: string | null;
  isAuthenticated: boolean;
  
  // Actions
  setUser: (user: any | null) => void;
  setToken: (token: string | null) => void;
  setTenantId: (tenantId: string | null) => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  tenantId: null,
  isAuthenticated: false,

  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  setTenantId: (tenantId) => set({ tenantId }),
  setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
  logout: () => set({ user: null, token: null, tenantId: null, isAuthenticated: false }),
}));
