import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Vite config for the ByteBrains frontend.
export default defineConfig({
  plugins: [react(), tailwindcss()],
})