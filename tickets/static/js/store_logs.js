// Store Logs JS
// No WebSocket
// No fetch("/api/tickets/")

let selectedTicketId = null;
let selectedStatus = null;
let selectedDropdown = null;
let previousStatus = null;

function openReasonModal(ticketId, dropdown) {
    selectedTicketId = ticketId;
    selectedDropdown = dropdown;

    selectedStatus = dropdown.value;
    previousStatus = dropdown.getAttribute("data-current-status");

    document.getElementById("statusReason").value = "";
    document.getElementById("reasonModal").style.display = "block";
}

function closeReasonModal() {
    document.getElementById("reasonModal").style.display = "none";

    if (selectedDropdown) {
        selectedDropdown.value = previousStatus;
    }
}

function submitStatusReason() {
    const reason = document.getElementById("statusReason").value.trim();

    if (!reason) {
        alert("Please enter a reason");
        return;
    }

    updateStatus(
        selectedTicketId,
        selectedStatus,
        reason
    );

    document.getElementById("reasonModal").style.display = "none";
}

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

function updateStatus(id, status, reason) {
    fetch(`/ticket/${id}/status/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: `status=${status}&reason=${encodeURIComponent(reason)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && selectedDropdown) {
            selectedDropdown.setAttribute(
                "data-current-status",
                data.status
            );
        }
    });
}

function updatePriority(id, priority) {
    fetch(`/ticket/${id}/priority/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: `priority=${priority}`
    });
}

document.addEventListener("DOMContentLoaded", () => {

    document.addEventListener("click", function(e){

        if(
            e.target.closest("select") ||
            e.target.closest("button") ||
            e.target.closest("a")
        ){
            return;
        }

        const card = e.target.closest("[data-ticket-id]");

        if(!card) return;

        const details = card.querySelector(".ticket-details");

        if(details){
            details.classList.toggle("show");
        }
    });

});