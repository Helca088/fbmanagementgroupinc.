let socket;

function connectWS() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";

    socket = new WebSocket(
        protocol + "://" + window.location.host + "/ws/tickets/"
    );

    socket.onopen = function () {
        console.log("🔥 WebSocket connected");
    };

    socket.onmessage = function (event) {
        const payload = JSON.parse(event.data);
        console.log("🔥 Ticket update:", payload);

        handleTicketEvent(payload);
    };

    socket.onclose = function () {
        console.log("⚠️ WebSocket closed. Reconnecting...");
        setTimeout(connectWS, 2000);
    };

    socket.onerror = function (error) {
        console.log("❌ WebSocket error", error);
    };
}

connectWS();


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


// ========================
// UPDATE EXISTING UI
// ========================
function upsertTicket(data) {

    // Remove existing rows
    document.querySelectorAll(`[data-ticket-id="${data.id}"]`).forEach(el => el.remove());
    document.getElementById(`details-${data.id}`)?.remove();

    const table = document.getElementById("ticketTable");

    // ========================
    // DESKTOP ROW
    // ========================
    if (table) {
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

        const detailsRow = document.createElement("tr");
        detailsRow.id = `details-${data.id}`;
        detailsRow.style.display = "none";
        detailsRow.innerHTML = `
            <td colspan="4" class="p-4 bg-gray-50">
                <strong>Title:</strong> ${data.title}<br><br>
                <strong>Message:</strong> ${data.message || ""}<br><br>
                <strong>User:</strong> ${data.user}<br><br>
                <strong>Section:</strong> ${data.section || ""}<br><br>
                <strong>Concern Type:</strong> ${data.concern_type || ""}<br><br>
                <strong>Status:</strong> ${data.status}<br><br>
                <strong>Date:</strong> ${data.created_at || ""}<br><br>
                ${data.attachment ? `<a href="/ticket/${data.id}/download/" class="bg-green-600 text-white px-3 py-1 rounded">Download Attachment</a>` : ""}
            </td>
        `;

        table.prepend(detailsRow);
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
}
// ========================
// UPDATE EXISTING UI
// ========================
function updateTicketUI(data) {

    // Update status cell in both desktop and mobile rows
    document.querySelectorAll(`[data-ticket-id="${data.id}"]`).forEach(row => {
        const statusCell = row.querySelector(".status");
        if (statusCell) statusCell.innerText = data.status;

        const select = row.querySelector("select");
        if (select) select.value = data.status;
    });

    // Update desktop details row
    const desktopDetails = document.getElementById(`details-${data.id}`);
    if (desktopDetails) {
        const select = desktopDetails.querySelector("select");
        if (select) select.value = data.status;
    }

    // Update mobile details
    const mobileDetails = document.getElementById(`details-${data.id}-mobile`);
    if (mobileDetails) {
        const select = mobileDetails.querySelector("select");
        if (select) select.value = data.status;
    }
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