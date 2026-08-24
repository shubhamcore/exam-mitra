/* Exam Mitra Service Worker — offline app shell + cache-first static assets.
 * Strategy:
 *   - Precache the app shell on install (HTML, CSS, JS, manifest)
 *   - Cache-first for same-origin static assets
 *   - Network-first for API (fall back to cached last response when offline)
 *   - Never cache uploads / streams
 */
const CACHE_VERSION = 'em-v2-4-0';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const RUNTIME_CACHE = `runtime-${CACHE_VERSION}`;

const PRECACHE_URLS = [
  '/',
  '/static/style.css',
  '/static/app.js',
  '/static/manifest.json',
];

// Install: pre-cache app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS)).then(() => self.skipWaiting())
  );
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== STATIC_CACHE && k !== RUNTIME_CACHE)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch handler
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle GET
  if (req.method !== 'GET') return;

  // Skip cross-origin (CDN fonts/KaTeX handled by browser HTTP cache; we don't want to SW-cache them here)
  if (url.origin !== self.location.origin) return;

  // Never cache SSE streams, photo uploads, health checks
  if (url.pathname.startsWith('/api/jobs/') && url.pathname.endsWith('/stream')) return;
  if (url.pathname === '/api/extract-syllabus') return;
  if (url.pathname === '/api/health') return;

  // API reads (job status, tutor) — network-first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const clone = res.clone();
          caches.open(RUNTIME_CACHE).then((c) => c.put(req, clone)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then((cached) => cached || caches.match('/')))
    );
    return;
  }

  // Share pages / plan pages: network-first, fall back to cache (offline viewing of last plan)
  if (url.pathname.startsWith('/plan/')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const clone = res.clone();
          caches.open(RUNTIME_CACHE).then((c) => c.put(req, clone)).catch(() => {});
          return res;
        })
        .catch(() =>
          caches.match(req).then((cached) =>
            cached ||
            new Response(
              '<html><body style="font-family:system-ui;padding:2rem;text-align:center">' +
              '<h2>📚 Exam Mitra is offline</h2><p>This plan is not available offline yet. Reconnect to the internet and open it once to cache for offline viewing.</p><p><a href="/" style="color:#4f46e5">← Back to home</a></p></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            )
          )
        )
    );
    return;
  }

  // Static assets / root: cache-first with network fallback
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        if (!res || res.status !== 200 || res.type !== 'basic') return res;
        const clone = res.clone();
        caches.open(RUNTIME_CACHE).then((c) => c.put(req, clone)).catch(() => {});
        return res;
      }).catch(() => cached);
    })
  );
});
