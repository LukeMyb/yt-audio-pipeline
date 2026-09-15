import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 3749,
    strictPort: true, // ポートが使用中の場合は別のポートにフォールバックせずエラーにする
    host: true,       // ネットワーク上の他の端末（iPhone等）からもアクセス可能にする
  },
  envDir: '../',
})
