let socket;
let reconnectDelay = 2000;
let reconnectTimer = null;
let refreshTimer = null;
let heartbeatTimer = null;
let isClosingPage = false;
function connectWS() {

    if (
        socket &&
        (
            socket.readyState === WebSocket.OPEN ||
            socket.readyState === WebSocket.CONNECTING
        )
    ) {
        return;
    }

    const protocol =
        window.location.protocol === "https:" ? "wss" : "ws";

    socket = new WebSocket(
        protocol + "://" + window.location.host + "/ws/tickets/"
    );


    socket.onopen = function () {
        console.log("✅ Admin WebSocket Connected");

        reconnectDelay = 2000;
        fetchLatestTickets();

        // Start heartbeat
        clearInterval(heartbeatTimer);

        heartbeatTimer = setInterval(() => {

    try {

        if (socket.readyState === WebSocket.OPEN) {

            socket.send(JSON.stringify({
                type: "ping"
            }));

        }

    } catch (err) {

        console.error("Heartbeat failed", err);

    }

}, 30000);
    };

    socket.onmessage = function (event) {

        const payload = JSON.parse(event.data);

        if (payload.type === "pong") {
        console.log("💓 Pong received");
        return;
    }

        console.log("📨 Admin received:", payload);

        handleAdminEvent(payload);
    };

    socket.onerror = function (err) {
    console.error("❌ Admin WebSocket Error", err);
        
    if (socket.readyState !== WebSocket.CLOSED) {
        socket.close();
    }
    };

    socket.onclose = function (event) {
    
    console.log(
        "WebSocket closed:",
        event.code,
        event.reason
    );

    clearInterval(heartbeatTimer);

    if (isClosingPage) {
        return;
    }

    if (reconnectTimer) return;

    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWS();
    }, reconnectDelay);

    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
};


}

connectWS();

function handleAdminEvent(payload) {

    console.log(payload);

    if (payload.action === "create") {
        addTicket(payload.data);
    }

    if (payload.action === "update") {
        updateTicket(payload.data);
    }

    if (payload.action === "delete") {
        removeTicket(payload.data.id);
    }

}

function addTicket(ticket){

    console.log("New ticket:", ticket);

    scheduleRefresh();

}

function updateTicket(ticket){

    console.log("Updated:", ticket);

    scheduleRefresh();

}

function removeTicket(id){

    console.log("Deleted:", id);

    scheduleRefresh();

}

async function fetchLatestTickets() {
    try {
        const response = await fetch("/api/tickets/");

        if (!response.ok) {
            throw new Error("API request failed");
        }

        refreshChangeList();
    } catch (err) {
        console.error(err);
    }
}

function refreshChangeList() {
    fetch(window.location.href)
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP ${r.status}`);
            }
            return r.text();
        })
        .then(html => {

            const doc = new DOMParser().parseFromString(html, "text/html");

            const newList = doc.querySelector("#changelist");
            const currentList = document.querySelector("#changelist");

            if (newList && currentList) {
                currentList.replaceWith(newList);
            }

        })
        .catch(console.error);
}

function scheduleRefresh() {
    if (refreshTimer) return;

    refreshTimer = setTimeout(() => {
        refreshTimer = null;
        refreshChangeList();
    }, 200);
}

document.addEventListener("visibilitychange", () => {

    if (document.visibilityState !== "visible") {
        return;
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
        fetchLatestTickets();
    } else {
        connectWS();
    }
});

window.addEventListener("beforeunload", () => {
    isClosingPage = true;

    clearInterval(heartbeatTimer);

    if (socket) {
        socket.close();
    }
});