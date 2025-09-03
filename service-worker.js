// service-worker.js
const CACHE_NAME = 'etherea-os-v1';
const urlsToCache = [
  '/',                    // Root (index.html served by FastAPI)
  '/manifest.json',       // Manifest served by FastAPI
  '/settings.html',       // Settings page if you have one
  '/assets/images/etherea-character.png',
  '/assets/videos/Etherea.mp4'
];

// Install: cache core assets
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('🔧 Service Worker: Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('🔧 Service Worker: Cache failed', error);
      })
  );
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

// Fetch: serve from cache if offline, but allow API calls to go through
self.addEventListener('fetch', (event) => {
  // Don't cache API calls - let them go directly to the server
  if (event.request.url.includes('/api/')) {
    return;
  }
  
  // For everything else, try cache first, then network
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          console.log('🔧 Service Worker: Serving from cache:', event.request.url);
          return response;
        }
        
        console.log('🔧 Service Worker: Fetching from network:', event.request.url);
        return fetch(event.request)
          .then((response) => {
            // Only cache successful responses for GET requests
            if (response.status === 200 && event.request.method === 'GET') {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, responseToCache);
                });
            }
            return response;
          })
          .catch(() => {
            // If network fails and it's a navigation request, serve cached index
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
          });
      })
  );
});

// Activate: clean old caches and take control immediately
self.addEventListener('activate', (event) => {
  console.log('🔧 Service Worker: Activating...');
  const cacheWhitelist = [CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log('🔧 Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Take control of all clients immediately
      return self.clients.claim();
    })
  );
});

// Handle messages from the main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});