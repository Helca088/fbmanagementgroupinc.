const CACHE_NAME = "fb-employee-v1";

const urlsToCache = [
    "/login/",
    "/home/",
    "/static/employee-manifest.json",
    "/static/js/ws.js",
    "/static/js/sw-update.js",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );

    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
    const req = event.request;

    if (req.url.includes("/login") || req.url.includes("/admin")) {
        return;
    }

    if (req.mode === "navigate") {
        event.respondWith(
            fetch(req, { redirect: "follow" })
                .catch(() => caches.match("/login/"))
        );
        return;
    }

    event.respondWith(
        fetch(req).catch(() => caches.match(req))
    );
});
