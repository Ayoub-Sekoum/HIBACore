import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig } from "../config/msalConfig";

const msalInstance = new PublicClientApplication(msalConfig);

async function get_token() {
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
        const response = await msalInstance.acquireTokenSilent({
            scopes: ["User.Read"], // O gli scope necessari per la tua API
            account: accounts[0]
        });
        return response.accessToken;
    }
    return null;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const adminService = {
    // Super Admin APIs
    async super_list_tenants() {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/super/tenants`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response.json();
    },

    async super_get_tenant_detail(tenant_id: string) {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/super/tenants/${tenant_id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response.json();
    },

    async super_update_policy(tenant_id: string, updates: any) {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/super/tenants/${tenant_id}/policy`, {
            method: 'PATCH',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });
        return response.json();
    },

    async super_suspend_tenant(tenant_id: string, reason: string) {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/super/tenants/${tenant_id}/suspend`, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason })
        });
        return response.json();
    },

    async super_get_audit(limit = 50, offset = 0) {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/super/audit?limit=${limit}&offset=${offset}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response.json();
    },

    // Tenant Admin APIs
    async tenant_get_policy() {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/tenant/policy`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response.json();
    },

    async tenant_update_policy(updates: any) {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/tenant/policy`, {
            method: 'PATCH',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });
        return response.json();
    },

    async tenant_get_audit(limit = 50, offset = 0) {
        const token = await get_token();
        const response = await fetch(`${API_BASE_URL}/admin/tenant/audit?limit=${limit}&offset=${offset}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response.json();
    }
};
