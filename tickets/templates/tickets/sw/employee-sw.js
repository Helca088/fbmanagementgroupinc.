importScripts("https://www.gstatic.com/firebasejs/12.15.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/12.15.0/firebase-messaging-compat.js");

firebase.initializeApp({
    apiKey: "AIzaSyArJoAhoegfGKVlEsDnes89G6JyhlnKaec",
    authDomain: "fbmanagement-tickets.firebaseapp.com",
    projectId: "fbmanagement-tickets",
    storageBucket: "fbmanagement-tickets.firebasestorage.app",
    messagingSenderId: "337714677840",
    appId: "1:337714677840:web:edbe7838b5df6d8b9f6955",
    measurementId: "G-8ZDVCCHW1V"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    self.registration.showNotification(
        payload.notification.title,
        {
            body: payload.notification.body,
            icon: "/static/icons/Phmt.png",

            data: {
                url: payload.data?.url || "https://fbmanagement.onrender.com/home/"
            }
        }
    );
});

const CACHE_NAME = "fb-employee-v1";

const urlsToCache = [
    "/static/employee-manifest.json",
    "/static/js/ws.js",
    "/static/js/sw_update.js",  
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
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});

self.addEventListener("notificationclick", function(event) {

    event.notification.close();

    const url =
        event.notification.data?.url || "https://fbmanagement.onrender.com/home/";

    event.waitUntil(
        clients.openWindow(url)
    );
});