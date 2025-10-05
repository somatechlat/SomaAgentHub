/**
 * ⚠️ WE DO NOT MOCK - Real project dashboard application
 * 
 * Features:
 * - Real-time task graph visualization
 * - WebSocket streaming for live updates
 * - Persona status tracking
 * - Artifact links and downloads
 * - Execution controls (pause/resume/cancel)
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
