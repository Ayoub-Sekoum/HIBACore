import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MsalProvider } from '@azure/msal-react'
import { PublicClientApplication } from '@azure/msal-browser'
import { msalConfig } from './config/msalConfig'
import App from './App'
import './index.css'

// ── FORZA LIGHT MODE ──────────────────── ────────────────────
// Removes the "dark" class from <html> if the operating system
// It's in dark mode. The app always uses the light Apple style theme.
// Remove this block only if you implement a dark/light toggle.
document.documentElement.classList.remove('dark')
// ────────────────────────────────────────────────────────────

const msalInstance = new PublicClientApplication(msalConfig)

async function initializeApp() {
  await msalInstance.initialize()
  await msalInstance.handleRedirectPromise()

  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </MsalProvider>
    </React.StrictMode>,
  )
}

initializeApp().catch(console.error)
