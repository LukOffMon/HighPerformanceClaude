/* GeekMcON Web service worker: after the first visit the app opens and works with no connection.
   Stale-while-revalidate: answer from cache instantly, refresh the cache from the network when online. */
const CACHE = "cekmecon-web-__BUILD__";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./ui/style.css", "./ui/app.js", "./ui/mascot.js", "./ui/neurons.js", "./ui/webstore.js", "./ui/logo.svg", "./ui/icon.png"];

self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith("cekmecon-web-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(async cache => {
    const hit = await cache.match(req, { ignoreSearch: true });
    const net = fetch(req).then(res => { if (res.ok) cache.put(req, res.clone()); return res; }).catch(() => hit || cache.match("./index.html"));
    return hit || net;
  }));
});
