import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.API_PROXY_TARGET || 'http://127.0.0.1:8080';
  return {
    server: { proxy: { '/api': { target }, '/uploads': { target } } },
    preview: { proxy: { '/api': { target }, '/uploads': { target } } },
    esbuild: { jsx: 'automatic' },
  };
});
