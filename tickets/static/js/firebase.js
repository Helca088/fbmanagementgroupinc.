import { initializeApp } from "https://www.gstatic.com/firebasejs/12.15.0/firebase-app.js";
import {
    getMessaging,
    getToken,
    onMessage
} from "https://www.gstatic.com/firebasejs/12.15.0/firebase-messaging.js";

const firebaseConfig = {
    apiKey: "AIzaSyArJoAhoegfGKVlEsDnes89G6JyhlnKaec",
    authDomain: "fbmanagement-tickets.firebaseapp.com",
    projectId: "fbmanagement-tickets",
    storageBucket: "fbmanagement-tickets.firebasestorage.app",
    messagingSenderId: "337714677840",
    appId: "1:337714677840:web:edbe7838b5df6d8b9f6955",
    measurementId: "G-8ZDVCCHW1V"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }

    return cookieValue;
}

async function initializeNotifications() {

    if (Notification.permission === "default") {
        await Notification.requestPermission();
    }

    if (Notification.permission !== "granted") {
        console.log("Notification permission denied.");
        return;
    }

    const registration = await navigator.serviceWorker.ready;

    // Get FCM token
    const token = await getToken(messaging, {
        vapidKey: "BIN_OcZGvdlEVsJkJ-pGNc9d-PWk7bMo26HE7UqFB59o8bgq6pHLSDUaaQaYy--DF4RjqX_9UQbRoSFelJ_jTdA",
        serviceWorkerRegistration: registration,
    });

    if (token) {
    console.log("FCM Token:", token);

    await fetch("/save-fcm-token/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            token: token
        })
    });
} else {
    console.log("Failed to get FCM token");
}
}
initializeNotifications();

export { messaging };

onMessage(messaging, (payload) => {

    console.log(payload);

    new Notification(
        payload.notification.title,
        {
            body: payload.notification.body,
            icon: "/static/icons/FBLG.png"
        }
    );

});