// API Configuration
// Use production URLs by default, fallback to localhost for development
const isProd = (import.meta as any).env?.MODE === 'production' || window.location.hostname.includes('vercel.app')

const API_URL = isProd
  ? 'https://mastery-machine-backend.onrender.com'
  : ((import.meta as any).env?.VITE_API_URL || 'http://localhost:8000')

const WS_URL = isProd
  ? 'wss://mastery-machine-backend.onrender.com'
  : ((import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000')

console.log('API Configuration:', { API_URL, WS_URL, isProd, hostname: window.location.hostname })

export { API_URL, WS_URL }
