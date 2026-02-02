/**
 * Offline Mode Service Worker
 * 
 * Enables offline functionality for content drafts and key features
 */

const CACHE_NAME = 'idkit-v1';
const OFFLINE_URL = '/offline';

// Assets to cache immediately
const STATIC_ASSETS = [
    '/',
    '/offline',
    '/manifest.json',
    '/_next/static/css/app.css',
];

// API routes to cache responses
const API_CACHE_ROUTES = [
    '/api/v1/user/profile',
    '/api/v1/content/drafts',
    '/api/v1/settings',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Handle API requests with stale-while-revalidate
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }

    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(handleNavigationRequest(request));
        return;
    }

    // Handle static assets with cache-first
    event.respondWith(handleStaticRequest(request));
});

async function handleApiRequest(request) {
    const cache = await caches.open(CACHE_NAME);

    try {
        // Try network first
        const networkResponse = await fetch(request);

        // Cache successful responses for offline use
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        // Return cached response if offline
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline JSON for API requests
        return new Response(
            JSON.stringify({ error: 'offline', message: 'You are currently offline' }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

async function handleNavigationRequest(request) {
    try {
        // Try network first for navigation
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        // Return offline page if network fails
        const cache = await caches.open(CACHE_NAME);
        const offlineResponse = await cache.match(OFFLINE_URL);
        return offlineResponse || new Response('Offline', { status: 503 });
    }
}

async function handleStaticRequest(request) {
    const cache = await caches.open(CACHE_NAME);

    // Try cache first
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    // Fallback to network
    try {
        const networkResponse = await fetch(request);

        // Cache static assets
        if (networkResponse.ok && request.url.includes('/_next/static/')) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        return new Response('Offline', { status: 503 });
    }
}

// Background sync for queued actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-drafts') {
        event.waitUntil(syncDrafts());
    }
    if (event.tag === 'sync-analytics') {
        event.waitUntil(syncAnalytics());
    }
});

async function syncDrafts() {
    const db = await openDB();
    const drafts = await db.getAll('pending-drafts');

    for (const draft of drafts) {
        try {
            await fetch('/api/v1/content/drafts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(draft),
            });
            await db.delete('pending-drafts', draft.id);
        } catch (error) {
            console.error('[SW] Failed to sync draft:', draft.id);
        }
    }
}

async function syncAnalytics() {
    const db = await openDB();
    const events = await db.getAll('pending-analytics');

    if (events.length > 0) {
        try {
            await fetch('/api/v1/analytics/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ events }),
            });
            await db.clear('pending-analytics');
        } catch (error) {
            console.error('[SW] Failed to sync analytics');
        }
    }
}

// IndexedDB helper
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('idkit-offline', 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            if (!db.objectStoreNames.contains('pending-drafts')) {
                db.createObjectStore('pending-drafts', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('pending-analytics')) {
                db.createObjectStore('pending-analytics', { keyPath: 'id', autoIncrement: true });
            }
            if (!db.objectStoreNames.contains('cached-content')) {
                db.createObjectStore('cached-content', { keyPath: 'id' });
            }
        };
    });
}

// Push notifications
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: '/icons/icon-192.png',
            badge: '/icons/badge-72.png',
            data: data.url,
            actions: data.actions || [],
        })
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.notification.data) {
        event.waitUntil(
            clients.openWindow(event.notification.data)
        );
    }
});
