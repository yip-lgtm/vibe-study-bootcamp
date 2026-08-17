import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg', 'pwa-192.png', 'icon-512.png', 'favicon.ico'],
      manifest: {
        name: '修學旅行 — Study Tour PWA',
        short_name: '修學旅行',
        description: 'Self-Study Bootcamp Hub — 905 courses across 9 bootcamps',
        start_url: './',
        scope: './',
        display: 'standalone',
        background_color: '#05070a',
        theme_color: '#3b82f6',
        orientation: 'portrait',
        lang: 'en',
        categories: ['education', 'books', 'productivity'],
        icons: [
          { src: './icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' },
          { src: './pwa-192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
          { src: './icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
        shortcuts: [
          {
            name: 'Random Course',
            short_name: 'Random',
            description: 'Jump to a random course',
            url: './?mode=shuffle',
            icons: [{ src: './icon.svg', sizes: 'any' }],
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,json,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/raw\.githubusercontent\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'github-raw-cache',
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /^https:\/\/api\.github\.com\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'github-api-cache',
              expiration: { maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 },
            },
          },
        ],
      },
    }),
  ],
  base: './',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
