const CACHE_NAME = 'kkn-app-v1';

// Saat Service Worker dipasang
self.addEventListener('install', (event) => {
    console.log('Service Worker: Terpasang');
    self.skipWaiting();
});

// Saat Service Worker diaktifkan
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Aktif');
    return self.clients.claim();
});

// Mencegat permintaan jaringan (syarat wajib PWA)
self.addEventListener('fetch', (event) => {
    event.respondWith(fetch(event.request).catch(() => {
        return new Response('Anda sedang offline. Pastikan koneksi internet aktif untuk melihat data KKN.');
    }));
});