import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            '/risk': 'http://localhost:8000',
            '/financial-crq': 'http://localhost:8000',
            '/monte-carlo': 'http://localhost:8000',
            '/decision': 'http://localhost:8000',
            '/ml': 'http://localhost:8000',
            '/ai': 'http://localhost:8000',
            '/blockchain': 'http://localhost:8000',
            '/orchestration': 'http://localhost:8000',
            '/reoptimize': 'http://localhost:8000',
            '/recalculate': 'http://localhost:8000',
            '/vulnerabilities': 'http://localhost:8000',
            '/ingestion': 'http://localhost:8000',
        }
    }
});
