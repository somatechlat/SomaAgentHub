import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const devPort = Number(process.env.ADMIN_CONSOLE_PORT ?? '10018');
const gatewayTarget = process.env.GATEWAY_API_URL ?? 'http://localhost:10000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: devPort,
    proxy: {
      '/v1': {
        target: gatewayTarget,
        changeOrigin: true,
      },
    },
  },
});
