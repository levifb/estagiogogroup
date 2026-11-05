import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Em desenvolvimento, /api vai para a FastAPI local (uvicorn api.index:app --port 8000).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
