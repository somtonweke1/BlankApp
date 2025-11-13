// API Configuration
const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'
const WS_URL = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000'

export { API_URL, WS_URL }
