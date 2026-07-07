import { useEffect } from 'react';
import { useMsal, useAccount } from '@azure/msal-react';
import { useAuthStore } from '../store/authStore';
import { setMsalInstance } from '../services/api';

export const useAuth = () => {
  const { instance, accounts } = useMsal();
  const account = useAccount(accounts[0] || {});
  const { setUser, setTenantId, setIsAuthenticated } = useAuthStore();

  useEffect(() => {
    // Synchronize the MSAL instance with the API client for tokens
    setMsalInstance(instance);

    if (account) {
      // Extracts the Tenant ID from the account claims (tid is the Tenant ID in Entra ID)
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
