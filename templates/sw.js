const CACHE_NAME = 'smart-area-v1';
const OFFLINE_URL = '/offline/';
const URLS_TO_CACHE = [
    '/',
    '/dashboard/',
    '/report/',
    '/map/',
    '/leaderboard/',
    '/offline/',
    '/static/style.css',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(URLS_TO_CACHE))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
        ))
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    event.respondWith(
        fetch(event.request)
            .then(response => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                return response;
            })
            .catch(() => caches.match(event.request).then(r => r || caches.match(OFFLINE_URL)))
    );
});

// Listen for online sync message
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SYNC') {
        // Client will handle the actual sync via fetch
        self.clients.matchAll().then(clients => {
            clients.forEach(client => client.postMessage({type: 'DO_SYNC'}));
        });
    }
});
