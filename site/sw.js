// Reçoit les notifications et ouvre la fiche du jeu quand on touche la notif.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

self.addEventListener("push", e => {
  const n = e.data ? e.data.json() : { title: "Actu jeux", body: "Du nouveau." };
  e.waitUntil(self.registration.showNotification(n.title, {
    body: n.body, tag: n.tag, icon: "icone-192.png", badge: "icone-192.png", data: { url: n.url || "" },
  }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  const url = new URL("./" + (e.notification.data.url || ""), self.registration.scope).href;
  e.waitUntil(self.clients.matchAll({ type: "window" }).then(fenetres => {
    const ouverte = fenetres.find(f => f.url.startsWith(self.registration.scope));
    return ouverte ? ouverte.navigate(url).then(f => f && f.focus()) : self.clients.openWindow(url);
  }));
});
