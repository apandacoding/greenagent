// API Configuration
// Use environment variable or fallback to localhost
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
export const WS_URL = import.meta.env.VITE_WS_URL || `ws://localhost:8001`;

// Helper to convert HTTP URL to WebSocket URL
export function getWebSocketUrl(path: string = ''): string {
  const baseUrl = import.meta.env.VITE_WS_URL || API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
  return `${baseUrl}${path}`;
}

// Helper to get API endpoint
export function getApiUrl(path: string = ''): string {
  return `${API_URL}${path}`;
}

