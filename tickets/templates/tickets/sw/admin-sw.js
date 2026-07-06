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
            icon: "/static/icons/icon-192.png"
        }
    );
});

self.addEventListener("install", () => {
    self.skipWaiting();
});

self.addEventListener("fetch", () => {});

self.addEventListener("notificationclick", function(event) {

    event.notification.close();

    const url =
        event.notification.data?.url || "/";

    event.waitUntil(
        clients.openWindow(url)
    );
});