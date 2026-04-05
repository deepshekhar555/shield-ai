// Shield AI — Service Worker v1.0
// Required for PWA / Play Store publishing

const CACHE_NAME = 'shield-ai-v1';
const ASSETS_TO_CACHE = [
  '/ui/login.html',
  '/ui/dashboard.html',
  '/ui/index.html',
  '/ui/styles.css',
  '/ui/script.js',
  '/ui/shield_logo.png',
];

// INSTALL: Cache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// ACTIVATE: Remove old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  clients.claim();
});

// FETCH: Network-first for API calls, cache-first for static assets
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Always hit the network for API calls
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/predict')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Cache-first for static assets
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      });
    }).catch(() => caches.match('/ui/login.html'))
  );
});
