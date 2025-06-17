// Service Worker để cache và xử lý các request
const CACHE_NAME = 'static-cache-v1';
const urlsToCache = [
  '/templates/static/css/main.css',
  '/templates/static/css/components/head.css',
  '/templates/static/css/components/suggestions.css',
  '/templates/static/css/components/chat_container.css',
  '/templates/static/css/components/prompt_container.css',
  '/templates/static/css/components/image_preview.css',
  '/templates/static/css/components/dropdown.css',
  '/templates/static/css/components/iframe.css',
  '/templates/static/css/components/search.css',
  '/templates/static/css/components/responsive_chat.css',
  '/templates/static/css/components/loading_bars.css',
  '/templates/static/css/chat.css',
  '/templates/static/js/chat_module.js',
  '/templates/static/js/login.js',
];

// Install Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch resources
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response; // Trả về response từ cache nếu có
        }
        return fetch(event.request); // Nếu không có trong cache, fetch từ network
      })
  );
});
