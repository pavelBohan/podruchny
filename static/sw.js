/**
 * Service Worker «Подручный» — стратегия Cache First
 * Обеспечивает полную оффлайн-работу конструктора промптов.
 */

const CACHE_NAME = 'podruchny-v2';

// Ресурсы, обязательные для оффлайн-работы
const OFFLINE_ASSETS = [
    '/',
    '/constructor/',
    '/guide/',
    '/offline/',
    '/history/',
    '/templates/',
    '/static/core/css/main.css',
    '/static/core/js/main.js',
    '/static/core/js/constructor.js',
    '/static/core/js/history.js',
    '/static/core/js/prompt-generator.js',
    '/static/data/categories.json',
    '/static/data/templates.json',
    '/static/data/articles.json',
    '/static/manifest.json',
    '/static/img/icon-192.png',
    '/static/img/icon-512.png',
];

// Установка: кэшируем базовые ресурсы
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(OFFLINE_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Активация: удаляем устаревшие кэши
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

// Запросы: Cache First с докэшированием успешных GET-ответов того же происхождения
self.addEventListener('fetch', (event) => {
    const { request } = event;

    if (request.method !== 'GET') return;

    event.respondWith(
        caches.match(request).then((cached) => {
            if (cached) return cached;

            return fetch(request)
                .then((response) => {
                    const url = new URL(request.url);
                    const sameOrigin = url.origin === self.location.origin;
                    const isStaticData = url.pathname.startsWith('/static/');

                    if (sameOrigin && response.ok && (isStaticData || url.pathname !== '/admin/')) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
                    }
                    return response;
                })
                .catch(() => {
                    // Полное отсутствие сети: для навигации отдаём заглушку
                    if (request.mode === 'navigate') {
                        return caches.match('/offline/');
                    }
                    return Response.error();
                });
        })
    );
});
