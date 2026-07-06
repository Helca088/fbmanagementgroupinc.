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

    console.log("Background payload:", payload);

    self.registration.showNotification(
        payload.data.title,
        {
            body: payload.data.body,
            icon: "/static/icons/icon-192.png",

            data: {
                url: payload.data.url
            }
        }
    );

});

self.addEventListener("notificationclick", (event) => {

    event.notification.close();

    const url = event.notification.data?.url || "https://fbmanagement.onrender.com/admin/tickets/ticket/";

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        }).then((clientList) => {

            for (const client of clientList) {

                if (client.url.includes(new URL(url).pathname) && "focus" in client) {
                    return client.focus();
                }

            }

            return clients.openWindow(url);
        })
    );

});