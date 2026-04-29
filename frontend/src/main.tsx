import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 3500,
        style: { fontSize: 14, borderRadius: 8 },
        success: { iconTheme: { primary: '#F26522', secondary: '#fff' } },
      }}
    />
  </StrictMode>,
)
