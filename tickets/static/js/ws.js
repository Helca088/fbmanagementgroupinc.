let socket;
let reconnectDelay = 2000;
const RECONNECT_DELAY_MAX = 30000;
const HEARTBEAT_INTERVAL = 30000;

let heartbeatTimer = null;
let reconnectTimer = null;


function isSearchActive() {
    const params = new URLSearchParams(window.location.search);
    const search = params.get("search");
    return !!(search && search.trim());
}

function connectWS() {
    const alreadyConnecting =
        socket &&
        (socket.readyState === WebSocket.OPEN ||
            socket.readyState === WebSocket.CONNECTING);

    if (alreadyConnecting) return;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${protocol}://${window.location.host}/ws/tickets/`);

    socket.onopen = () => {
        console.log("WS connected");

        clearInterval(heartbeatTimer);
        heartbeatTimer = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: "ping" }));
            }
        }, HEARTBEAT_INTERVAL);

        reconnectDelay = 2000;

        if (!isSearchActive()) {
            fetchLatestTickets();
        }
    };

    socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);

        if (payload.type === "pong") return;

        handleTicketEvent(payload);
    };

    socket.onclose = (event) => {
        console.log("WS closed", event.code, event.reason);

        clearInterval(heartbeatTimer);

        if (reconnectTimer) return;

        reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            connectWS();
        }, reconnectDelay);

        reconnectDelay = Math.min(reconnectDelay * 2, RECONNECT_DELAY_MAX);
    };

    socket.onerror = (error) => {
        console.error("WS error", error);
    };
}

connectWS();

// ========================================================
// DATA FETCHING
// ========================================================

function fetchLatestTickets() {
    fetch("/api/tickets/")
        .then((res) => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then((tickets) => {
            tickets.reverse().forEach((ticket) => upsertTicket(ticket));
        })
        .catch((err) => console.error("fetch error", err));
}

// ========================================================
// MAIN EVENT HANDLER
// ========================================================

function handleTicketEvent(payload) {
    const data = payload.data || payload;

    if (payload.action === "delete") {
        const id = data.id;
        document.querySelector(`[data-ticket-id="${id}"]`)?.remove();
        document.getElementById(`details-${id}`)?.remove();
        document.getElementById(`details-${id}-mobile`)?.remove();
        return;
    }

    if (payload.action === "update") {
        updateTicketUI(data);
        return;
    }

    // create / normal event
    upsertTicket(data);
}

// ========================================================
// CARD CREATION / UPSERT
// ========================================================

function upsertTicket(data) {
    const existing = document.querySelector(`[data-ticket-id="${data.id}"]`);

    if (existing) {
        updateTicketUI(data);
        return;
    }

    // Desktop
    const list = document.querySelector(".ticket-list");
    if (!list) {
        console.error("ticket-list not found");
    } else {
        list.insertAdjacentHTML("afterbegin", buildTicketCard(data));
    }

    // Mobile
    const mobileList = document.getElementById("mobileTicketList");
    if (mobileList) {
        mobileList.insertAdjacentHTML("afterbegin", buildMobileTicketCard(data));
    }
}

function formatTime12Hour(timeStr) {
    if (!timeStr) return "-";

    const [hours, minutes] = timeStr.split(":");
    const date = new Date();
    date.setHours(hours, minutes);

    return date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    });
}

function formatAssignedTechnicians(data) {
    const technicians = [];

    if (data.assigned_to) {
        technicians.push(data.assigned_to);
    }

    (data.additional_technicians || []).forEach((tech) => {
        if (typeof tech === "string") {
            technicians.push(tech);
        } else if (tech.name) {
            technicians.push(tech.name);
        }
    });

    return technicians.length ? technicians.join(", ") : "-";
}

function buildTicketCard(data) {
    return `
        <div class="ticket-card department-${data.department_slug}" data-ticket-id="${data.id}">

            <div class="ticket-header">
                <span class="dept-badge department-badge-${data.department_slug}">
                    ${data.department}
                </span>
                <span class="ticket-number">#${data.outlet_ticket_no}</span>
            </div>

            <h3>${data.outlet}</h3>

            <div class="message-wrapper">
                <span class="concern-badge">${data.concern_type}</span>
                <div class="message-box">
                    <div class="message-text">${data.message || ""}</div>
                </div>
            </div>

            <select class="ticket-select status" data-current-status="${data.status}"
                onchange="openReasonModal('${data.id}', this)">
                <option value="pending" ${data.status === "pending" ? "selected" : ""}>Pending</option>
                <option value="progress" disabled ${data.status === "progress" ? "selected" : ""}>In progress</option>
                <option value="resolved" ${data.status === "resolved" ? "selected" : ""}>Resolved</option>
                <option value="cancelled" ${data.status === "cancelled" ? "selected" : ""}>Cancelled</option>
            </select>

            <br>

            <select class="ticket-select priority" onchange="updatePriority('${data.id}', this.value)">
                <option value="Low" ${data.priority === "Low" ? "selected" : ""}>Low</option>
                <option value="Medium" ${data.priority === "Medium" ? "selected" : ""}>In need</option>
                <option value="High" ${data.priority === "High" ? "selected" : ""}>Urgent</option>
            </select>

            <br>

            <div class="schedule">
                <strong>Scheduled Date:</strong>
                <span class="scheduled-date">${data.scheduled_date || "-"}</span>
                <br>
                <strong>Scheduled Time:</strong>
                <span class="scheduled-time">${formatTime12Hour(data.scheduled_time)}</span>
            </div>

            <div class="admin-note">
                <strong>Admin Notes:</strong>
                <span class="admin-note-text">${data.admin_note || "-"}</span>
            </div>

            <div class="assigned">
                <strong>Assigned To:</strong>
                <span class="assigned-to">${formatAssignedTechnicians(data)}</span>
            </div>

            <div class="deadline">
                <strong>Deadline:</strong>
                <span class="deadline-text">${data.deadline || "-"}</span>
            </div>

            <strong>Age of concern:</strong>
            <span>${data.ticket_age || "-"}</span>

            <p class="overdue-status">${data.is_overdue ? "⚠️ OVERDUE" : ""}</p>

            <div class="ticket-date">${data.created_at}</div>

            <div class="created-by">
                <strong>Created by:</strong>
                ${data.created_by}
                ${data.created_by !== "Unknown" ? `<span class="badge">${data.created_by_role}</span>` : ""}
            </div>

            ${data.attachment ? `<a href="${data.attachment_url}" class="download-btn">Download Attachment</a>` : ""}

        </div>
    `;
}

function buildMobileTicketCard(data) {
    return `
        <div class="bg-white p-4 rounded-xl shadow" data-ticket-id="${data.id}">
            <p><strong>Title:</strong> ${data.title}</p>
            <p><strong>Outlet:</strong> ${data.user}</p>
            <p class="status"><strong>Status:</strong> ${data.status}</p>
            <div class="mt-2 space-x-2">
                <button onclick="toggleDetails(${data.id})" class="bg-blue-500 text-white px-3 py-1 rounded">View</button>
                <button onclick="deleteTicket(${data.id})" class="bg-red-600 text-white px-3 py-1 rounded">Delete</button>
            </div>
            <div id="details-${data.id}-mobile" style="display:none;" class="mt-4 border-t pt-4">
                <p><strong>Message:</strong> ${data.message || ""}</p>
                <p><strong>Department:</strong> ${data.department || ""}</p>
                <p><strong>Date:</strong> ${data.created_at || ""}</p>
                ${data.attachment ? `<a href="/ticket/${data.id}/download/" class="bg-green-600 text-white px-3 py-1 rounded">Download Attachment</a>` : ""}
            </div>
        </div>
    `;
}

// ========================================================
// CARD UPDATES
// ========================================================

function updateTicketUI(data) {
    const dropdown = document.querySelector(`[data-ticket-id="${data.id}"] .status-dropdown`);
    if (dropdown) dropdown.setAttribute("data-current-status", data.status);

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .status`).forEach((el) => {
        if (el.tagName === "SELECT") {
            el.value = data.status;
        } else {
            el.textContent = data.status;
        }
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .priority`).forEach((el) => {
        if (el.tagName === "SELECT") {
            el.value = data.priority;
        } else {
            el.textContent = data.priority;
        }
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .scheduled-date`).forEach((el) => {
        el.textContent = data.scheduled_date || "-";
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .scheduled-time`).forEach((el) => {
        el.textContent = formatTime12Hour(data.scheduled_time);
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .assigned-to`).forEach((el) => {
    el.textContent = formatAssignedTechnicians(data);
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .assigned-to`).forEach((el) => {
        el.textContent = data.assigned_to || "-";
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .deadline-text`).forEach((el) => {
        el.textContent = data.deadline || "-";
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"]`).forEach((card) => {
        const overdueEl = card.querySelector(".overdue-status");
        if (!overdueEl) return;

        if (data.is_overdue) {
            overdueEl.textContent = "⚠️ OVERDUE";
            overdueEl.style.color = "red";
            overdueEl.style.fontWeight = "900";
        } else {
            overdueEl.textContent = "";
            overdueEl.style.color = "green";
            overdueEl.style.fontWeight = "normal";
        }
    });
}

// ========================================================
// UI INTERACTIONS
// ========================================================

window.toggleDetails = function (id) {
    const desktopDetails = document.getElementById(`details-${id}`);
    if (desktopDetails && desktopDetails.tagName === "TR") {
        desktopDetails.style.display = desktopDetails.style.display === "none" ? "table-row" : "none";
    }

    const mobileDetails = document.getElementById(`details-${id}-mobile`);
    if (mobileDetails) {
        mobileDetails.style.display = mobileDetails.style.display === "none" ? "block" : "none";
    }
};

window.deleteTicket = function (id) {
    if (!confirm("Delete this ticket?")) return;

    fetch(`/delete-ticket/${id}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
    })
        .then((res) => {
            if (!res.ok) throw new Error("Delete failed");
            return res.json();
        })
        .catch(console.error);
};

window.updateStatus = function (id, status, reason) {
    fetch(`/ticket/${id}/status/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: `status=${status}&reason=${encodeURIComponent(reason)}`,
    });
};

window.updatePriority = function (id, priority) {
    fetch(`/ticket/${id}/priority/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: `priority=${priority}`,
    });
};

// ========================================================
// HELPERS
// ========================================================

function getCookie(name) {
    if (!document.cookie) return null;

    const match = document.cookie
        .split(";")
        .map((c) => c.trim())
        .find((c) => c.startsWith(`${name}=`));

    return match ? decodeURIComponent(match.substring(name.length + 1)) : null;
}

// ========================================================
// GLOBAL LISTENERS
// ========================================================

document.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("click", (e) => {
        if (e.target.closest("select") || e.target.closest("button") || e.target.closest("a")) {
            return;
        }

        const row = e.target.closest("[data-ticket-id]");
        if (!row) return;

        const details = document.getElementById(`details-${row.dataset.ticketId}`);
        if (!details) return;

        details.style.display = details.style.display === "none" ? "table-row" : "none";
    });
});

document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;

    if (isSearchActive()) return;

    if (socket && socket.readyState === WebSocket.OPEN) {
        fetchLatestTickets();
    } else {
        connectWS();
    }
});
