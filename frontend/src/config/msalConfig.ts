import { Configuration, LogLevel } from "@azure/msal-browser";

/**
 * MSAL Configuration for Azure AD / Entra ID.
 * Task 6.02 — Teams Bot SSO & Enterprise Auth.
 */
export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_AD_CLIENT_ID || "",
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_AD_TENANT_ID || "common"}`,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
    navigateToLoginRequestUrl: true,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        switch (level) {
          case LogLevel.Error: console.error(message); break;
          case LogLevel.Info: console.info(message); break;
          case LogLevel.Verbose: console.debug(message); break;
          case LogLevel.Warning: console.warn(message); break;
          default: break;
        }
      },
    },
  },
};

export const loginRequest = {
  scopes: ["User.Read", "openid", "profile"],
};
