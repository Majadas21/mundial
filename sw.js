self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || '⚽ Quiniela Mundial 2026';
  const options = {
    body: data.body || 'Hay novedades en los partidos',
    icon: 'https://majadas21.github.io/mundial/icon.png',
    badge: 'https://majadas21.github.io/mundial/icon.png',
    data: { url: data.url || 'https://majadas21.github.io/mundial/' },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.url));
});
