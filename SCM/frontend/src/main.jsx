import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { checkSSOToken } from './utils/ssoAuth.js'

// Check for SSO token from Portal before rendering
// Must wait for completion to avoid race condition
const initApp = async () => {
  await checkSSOToken();
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
};

initApp();
