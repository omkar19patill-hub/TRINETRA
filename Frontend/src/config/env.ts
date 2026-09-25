/**
 * Typed environment configuration.
 *
 * Read environment values from here rather than reaching for `import.meta.env`
 * directly in feature code, so defaults live in one place.
 *
 * VITE_API_BASE_URL defaults to `/api`, which the Vite dev server proxies to the
 * backend (see vite.config.ts). The backend itself exposes no `/api` prefix, so
 * the proxy strips it. In production, set VITE_API_BASE_URL to the backend's
 * origin, e.g. https://api.example.com
 */

const DEFAULT_API_BASE_URL = '/api'

function readApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL
  const value = typeof raw === 'string' && raw.trim() !== '' ? raw.trim() : DEFAULT_API_BASE_URL
  // Normalise away a trailing slash so callers can always pass paths as '/risk/calculate'
  return value.endsWith('/') ? value.slice(0, -1) : value
}

export const env = {
  apiBaseUrl: readApiBaseUrl(),
  isDev: import.meta.env.DEV,
} as const
