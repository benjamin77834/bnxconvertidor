import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Sello de build: se inyecta en el bundle para mostrar en el header. Asi, al
  // mirar la UI, se sabe si el navegador cargo la version nueva o una cacheada.
  define: {
    __BUILD_ID__: JSON.stringify(new Date().toISOString().slice(5, 16).replace('T', ' ')),
  },
  server: {
    port: 3000,
    proxy: {
      '/compile': 'http://localhost:8000',
      '/cobol': 'http://localhost:8000',
      '/plan': 'http://localhost:8000'
    }
  }
})
