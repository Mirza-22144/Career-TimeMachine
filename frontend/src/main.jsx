import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import LandingPage from './screens/LandingPage.jsx'

// Temporarily rendering the screen under test directly (App.jsx is left
// untouched). Swap this back to <App /> or wire up routing once there's
// more than one screen to navigate between.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <LandingPage />
  </StrictMode>,
)
