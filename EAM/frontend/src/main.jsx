import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { checkSSOToken } from './utils/ssoAuth.js'

// Check for SSO token from Portal before rendering
// Must wait for completion to avoid race condition
const initApp = async () => {
  await checkSSOToken();
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
};

initApp();
