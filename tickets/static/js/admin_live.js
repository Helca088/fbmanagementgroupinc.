let socket;

function connectWS() {

    const protocol =
        window.location.protocol === "https:" ? "wss" : "ws";

    socket = new WebSocket(
        protocol + "://" + window.location.host + "/ws/tickets/"
    );

    socket.onopen = function () {
        console.log("✅ Admin WebSocket Connected");
    };

    socket.onmessage = function (event) {

        const payload = JSON.parse(event.data);

        console.log("📨 Admin received:", payload);

        handleAdminEvent(payload);
    };

    socket.onclose = function (event) {

    console.log("========== WS CLOSED ==========");
    console.log("Code:", event.code);
    console.log("Reason:", event.reason);

    console.log("Calling fetchLatestTickets()...");
    fetchLatestTickets();

    console.log("Scheduling reconnect...");
    setTimeout(() => {
        console.log("Reconnecting...");
        connectWS();
    }, 2000);
};

    socket.onerror = function (err) {

        console.log("❌ Admin WebSocket Error", err);

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

    refreshChangeList();

}

function updateTicket(ticket){

    console.log("Updated:", ticket);

    refreshChangeList();

}

function removeTicket(id){

    console.log("Deleted:", id);

    refreshChangeList();

}

function fetchLatestTickets() {

    fetch("/api/tickets/")
        .then(response => response.json())
        .then(tickets => {

            console.log("Fetched", tickets.length, "tickets");

            // For now just reload if anything changed
            refreshChangeList();

        })
        .catch(err => console.error(err));

}

function refreshChangeList() {
    fetch(window.location.href)
        .then(r => r.text())
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
