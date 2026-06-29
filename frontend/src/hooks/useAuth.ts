import { useEffect } from 'react';
import { useMsal, useAccount } from '@azure/msal-react';
import { useAuthStore } from '../store/authStore';
import { setMsalInstance } from '../services/api';

export const useAuth = () => {
  const { instance, accounts } = useMsal();
  const account = useAccount(accounts[0] || {});
  const { setUser, setTenantId, setIsAuthenticated } = useAuthStore();

  useEffect(() => {
    // Sincronizza l'istanza MSAL con il client API per i token
    setMsalInstance(instance);

    if (account) {
      // Estrae il Tenant ID dai claim dell'account (tid è il Tenant ID in Entra ID)
      const tenantId = (account.idTokenClaims as any)?.tid || import.meta.env.VITE_AZURE_AD_TENANT_ID;
      
      setUser({
        name: account.name,
        username: account.username,
        localAccountId: account.localAccountId,
      });
      setTenantId(tenantId);
      setIsAuthenticated(true);
    } else {
      setIsAuthenticated(false);
    }
  }, [account, instance, setUser, setTenantId, setIsAuthenticated]);

  return { account, isAuthenticated: !!account };
};
