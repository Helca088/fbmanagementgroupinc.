let socket;

function connectWS() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";

    socket = new WebSocket(
        protocol + "://" + window.location.host + "/ws/tickets/"
    );


    socket.onmessage = function (event) {
        const payload = JSON.parse(event.data);
        console.log("🔥 Ticket update:", payload);
        handleTicketEvent(payload);
    };

    socket.onclose = function(event) {
    console.log(
        "⚠️ WebSocket closed",
        event.code,
        event.reason
    );

    setTimeout(connectWS, 2000);
};

    socket.onerror = function (error) {
        console.log("❌ WebSocket error", error);
    };
}

connectWS();
fetchLatestTickets();

// ========================
// FETCH LATEST ON RECONNECT
// ========================
function fetchLatestTickets() {
    fetch("/api/tickets/")
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            return res.json();
        })
        .then(tickets => {
            tickets.reverse().forEach(ticket => upsertTicket(ticket));
        })
        .catch(err => console.error("fetch error", err));
}
// ========================
// MAIN EVENT HANDLER
// ========================
function handleTicketEvent(payload) {
    const data = payload.data || payload;

    // ------------------------
    // DELETE EVENT
    // ------------------------
    if (payload.action === "delete") {
        const id = data.id;

        document.querySelector(`[data-ticket-id="${id}"]`)?.remove();
        document.getElementById(`details-${id}`)?.remove();

        console.log("🗑️ Deleted ticket:", id);
        return;
    }

    // ------------------------
    // UPDATE EVENT
    // ------------------------
    if (payload.action === "update") {
        updateTicketUI(data);
        return;
    }

    // ------------------------
    // CREATE / NORMAL EVENT
    // ------------------------
    upsertTicket(data);
}

    function upsertTicket(data) {

    const existing = document.querySelector(`[data-ticket-id="${data.id}"]`);

    // UPDATE EXISTING
    if (existing) {
        existing.querySelector(".status").textContent = data.status;
        return;
    }

    const table = document.getElementById("ticketTable");
    if (!table) return;

    const newRow = document.createElement("tr");
    newRow.setAttribute("data-ticket-id", data.id);
    newRow.className = "border-b hover:bg-gray-100";
    newRow.style.cursor = "pointer";

    newRow.innerHTML = `
        <td class="p-4">${data.title}</td>
        <td class="p-4">${data.user}</td>
        <td class="p-4 status">${data.status}</td>
        <td class="p-4 space-x-2">
            <button onclick="toggleDetails(${data.id})" class="bg-blue-500 text-white px-3 py-1 rounded">View</button>
            <button onclick="deleteTicket(${data.id})" class="bg-red-600 text-white px-3 py-1 rounded">Delete</button>
        </td>
    `;

    table.prepend(newRow);
}
    // ========================
    // MOBILE CARD
    // ========================
    const mobileList = document.getElementById("mobileTicketList");

    if (mobileList) {
        const card = document.createElement("div");
        card.setAttribute("data-ticket-id", data.id);
        card.className = "bg-white p-4 rounded-xl shadow";
        card.innerHTML = `
            <p><strong>Title:</strong> ${data.title}</p>
            <p><strong>Outlet:</strong> ${data.user}</p>
            <p class="status"><strong>Status:</strong> ${data.status}</p>
            <div class="mt-2 space-x-2">
                <button onclick="toggleDetails(${data.id})" class="bg-blue-500 text-white px-3 py-1 rounded">View</button>
                <button onclick="deleteTicket(${data.id})" class="bg-red-600 text-white px-3 py-1 rounded">Delete</button>
            </div>
            <div id="details-${data.id}-mobile" style="display:none;" class="mt-4 border-t pt-4">
                <p><strong>Message:</strong> ${data.message || ""}</p>
                <p><strong>Section:</strong> ${data.section || ""}</p>
                <p><strong>Date:</strong> ${data.created_at || ""}</p>
                ${data.attachment ? `<a href="/ticket/${data.id}/download/" class="bg-green-600 text-white px-3 py-1 rounded">Download Attachment</a>` : ""}
            </div>
        `;
        mobileList.prepend(card);
    }

    console.log("✅ New ticket added");

// ========================
// UPDATE EXISTING UI
// ========================
function updateTicketUI(data) {

    console.log("Updating:", data.id, data.status);

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .status`)
        .forEach(el => {
            el.textContent = data.status;
        });

    document.querySelectorAll(`select[data-ticket-id="${data.id}"]`)
        .forEach(select => {
            select.value = data.status;
        });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .scheduled-date`)
        .forEach(el => el.textContent = data.scheduled_date || "-");

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .scheduled-time`)
        .forEach(el => el.textContent = data.scheduled_time || "-");

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .admin-note`)
        .forEach(el => el.textContent = data.admin_note || "-");
}


// ========================
// TOGGLE DETAILS
// ========================
window.toggleDetails = function (id) {
    // Desktop
    const desktopDetails = document.getElementById(`details-${id}`);
    if (desktopDetails && desktopDetails.tagName === "TR") {
        desktopDetails.style.display =
            desktopDetails.style.display === "none" ? "table-row" : "none";
    }

    // Mobile
    const mobileDetails = document.getElementById(`details-${id}-mobile`);
    if (mobileDetails) {
        mobileDetails.style.display =
            mobileDetails.style.display === "none" ? "block" : "none";
    }
};

// ========================
// DELETE TICKET
// ========================
window.deleteTicket = function (id) {

    if (!confirm("Delete this ticket?")) return;

    fetch(`/delete-ticket/${id}/`, {
        method: "GET"
    })
    .then(res => {
        if (res.ok) {
            console.log("🗑️ Deleted request sent");
        }
    });
};


// ========================
// CSRF HELPER
// ========================
function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}


// ========================
// UPDATE STATUS (POST)
// ========================
window.updateStatus = function (id, status) {

    console.log("CSRF:", getCookie("csrftoken"));

    fetch(`/ticket/${id}/status/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: `status=${status}`
    });
};


// ========================
// ROW CLICK TOGGLE (SAFE)
// ========================
document.addEventListener("DOMContentLoaded", () => {

    document.addEventListener("click", (e) => {

        if (
            e.target.closest("select") ||
            e.target.closest("button") ||
            e.target.closest("a")
        ) {
            return;
        }

        const row = e.target.closest("[data-ticket-id]");
        if (!row) return;

        const id = row.dataset.ticketId;
        const details = document.getElementById(`details-${id}`);

        if (!details) return;

        details.style.display =
            details.style.display === "none" ? "table-row" : "none";
    });
});