import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MsalProvider } from '@azure/msal-react'
import { PublicClientApplication } from '@azure/msal-browser'
import { msalConfig } from './config/msalConfig'
import App from './App'
import './index.css'

// ── FORZA LIGHT MODE ────────────────────────────────────────
// Rimuove la classe "dark" da <html> se il sistema operativo
// è in dark mode. L'app usa sempre il tema light Apple style.
// Rimuovi questo blocco solo se implementi un toggle dark/light.
document.documentElement.classList.remove('dark')
// ────────────────────────────────────────────────────────────

const msalInstance = new PublicClientApplication(msalConfig)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MsalProvider instance={msalInstance}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </MsalProvider>
  </React.StrictMode>,
)
