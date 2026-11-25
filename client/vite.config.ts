import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/analyze': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/fetch_initial': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/rerank': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/undo_feedback': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/feedback': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/trait-profile': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    }
  }
});
