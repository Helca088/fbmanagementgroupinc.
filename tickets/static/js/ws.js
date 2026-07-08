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
    socket.onopen = function(){

        console.log("✅ WS OPEN");

        fetchLatestTickets();
    };

    socket.onerror = function (error) {
        console.log("❌ WebSocket error", error);
    };
}

connectWS();
fetchLatestTickets();


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

      const existing = document.querySelector(
        `[data-ticket-id="${data.id}"]`
    );

    if (existing) {
        updateTicketUI(data);
        return;
    }

    const list = document.querySelector(".ticket-list");

    if (!list) return;

    list.insertAdjacentHTML(
        "afterbegin",
        buildTicketCard(data)
    );
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

function formatTime12Hour(timeStr) {
    if (!timeStr) return "-";

    const [hours, minutes] = timeStr.split(":");

    const date = new Date();
    date.setHours(hours, minutes);

    return date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        hour12: true
    });
}

function buildTicketCard(data){

    return `
        <div class="ticket-card section-${data.section_slug}"
         data-ticket-id="${data.id}">

        <span class="dept-badge section-badge-${data.section_slug}">
            ${data.section}
        </span>

        <h3>${data.outlet}</h3>

        <p>${data.message}</p>

        <select
            class="ticket-select status"
            data-current-status="${data.status}"
            onchange="openReasonModal('${data.id}', this)">

            <option value="pending"
                ${data.status === "pending" ? "selected" : ""}>
                Pending
            </option>

            <option value="progress"
                disabled
                ${data.status === "progress" ? "selected" : ""}>
                In progress
            </option>

            <option value="resolved"
                ${data.status === "resolved" ? "selected" : ""}>
                Resolved
            </option>

        </select>

        <br>

        <select
            class="ticket-select priority"
            onchange="updatePriority('${data.id}', this.value)">

            <option value="Low"
                ${data.priority === "Low" ? "selected" : ""}>
                Low
            </option>

            <option value="Medium"
                ${data.priority === "Medium" ? "selected" : ""}>
                In need
            </option>

            <option value="High"
                ${data.priority === "High" ? "selected" : ""}>
                Urgent
            </option>

        </select>

        <br>

        <div class="schedule">
            <strong>Scheduled Date:</strong>
            <span class="scheduled-date">
                ${data.scheduled_date || "-"}
            </span>

            <br>

            <strong>Scheduled Time:</strong>
            <span class="scheduled-time">
                ${formatTime12Hour(data.scheduled_time)}
            </span>
        </div>

        <div class="admin-note">
            <strong>Admin Notes:</strong>
            <span class="admin-note-text">
                ${data.admin_note || "-"}
            </span>
        </div>

        <div class="assigned">
            <strong>Assigned To:</strong>
            <span class="assigned-to">
                ${data.assigned_to || "-"}
            </span>
        </div>

        <div class="deadline">
            <strong>Deadline:</strong>
            <span class="deadline-text">
                ${data.deadline || "-"}
            </span>
        </div>

        <strong>Age of concern:</strong>
        <span>${data.ticket_age || "-"}</span>

        <p class="overdue-status">
            ${data.is_overdue ? "⚠️ OVERDUE" : ""}
        </p>

        <div class="ticket-date">
            ${data.created_at}
        </div>

        ${data.attachment ? `
            <a
                href="${data.attachment_url}"
                class="download-btn">
                Download Attachment
            </a>
        ` : ""}

    </div>
    `;
}

function updateTicketUI(data) {

    console.log("FULL DATA:", data);

    const dropdown = document.querySelector(
    `[data-ticket-id="${data.id}"] .status-dropdown`
    );

    if (dropdown) {
        dropdown.setAttribute(
        "data-current-status",
        data.status
    );
    }

    console.log("Updating:", data.id, data.status);

    console.log(
        "Card:",
        document.querySelector(`[data-ticket-id="${data.id}"]`)
    );

    console.log(
        "Date:",
        document.querySelector(`[data-ticket-id="${data.id}"] .scheduled-date`)
    );

    console.log(
        "Time:",
        document.querySelector(`[data-ticket-id="${data.id}"] .scheduled-time`)
    );

    console.log(
        "Note:",
        document.querySelector(`[data-ticket-id="${data.id}"] .admin-note-text`)
    );

    console.log("Setting date:", data.scheduled_date);
    console.log("Setting time:", data.scheduled_time);
    console.log("Setting note:", data.admin_note);
    console.log("Setting deadline:", data.deadline);

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .status`)
        .forEach(el => {
            if (el.tagName === "SELECT") {
            el.value = data.status;
        } 
        
        else {
            el.textContent = data.status;
        }
        });
    

    document.querySelectorAll(
        `[data-ticket-id="${data.id}"] .priority`
    ).forEach(el => {

        if (el.tagName === "SELECT") {
            el.value = data.priority;
        }
        else{
            el.textContent = data.priority;
        }
        });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .scheduled-date`)
        .forEach(el => {
            el.textContent = data.scheduled_date || "-";
        });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .scheduled-time`)
        .forEach(el => {
            el.textContent = formatTime12Hour(data.scheduled_time);
        });

    document.querySelectorAll(`[data-ticket-id="${data.id}"] .admin-note-text`)
        .forEach(el => {
            el.textContent = data.admin_note || "-";
        });
    
    document.querySelectorAll(
        `[data-ticket-id="${data.id}"] .assigned-to`
        ).forEach(el => {
          el.textContent = data.assigned_to || "-";
        });


    document.querySelectorAll(
        `[data-ticket-id="${data.id}"] .deadline-text`
    ).forEach(el => {
        el.textContent = data.deadline || "-";
    });

    document.querySelectorAll(`[data-ticket-id="${data.id}"]`).forEach(card => {

        const overdueEl = card.querySelector(".overdue-status");

        if (overdueEl){
            if (data.is_overdue){
                overdueEl.textContent = "⚠️ OVERDUE";
                overdueEl.style.color = "red";
                overdueEl.style.fontWeight = "900";

            } else {
                overdueEl.textContent = "";
                overdueEl.style.color = "green";
                overdueEl.style.fontWeight = "normal";   
            }
        }
    })
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
window.updateStatus = function (id, status, reason) {

    console.log("CSRF:", getCookie("csrftoken"));

    fetch(`/ticket/${id}/status/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: `status=${status}&reason=${encodeURIComponent(reason)}`
    });
};
window.updatePriority = function (id, priority) {

    console.log("CSRF:", getCookie("csrftoken"));

    fetch(`/ticket/${id}/priority/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: `priority=${priority}`
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