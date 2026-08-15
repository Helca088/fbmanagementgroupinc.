let socket;

let reconnectDelay = 2000;
let reconnectTimer = null;
let refreshTimer = null;
let heartbeatTimer = null;

let isClosingPage = false;


// ============================================================
// WEBSOCKET CONNECTION
// ============================================================

function connectWS() {

    // Prevent duplicate WebSocket connections
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
        window.location.protocol === "https:"
            ? "wss"
            : "ws";


    socket = new WebSocket(
        protocol +
        "://" +
        window.location.host +
        "/ws/tickets/"
    );


    // ========================================================
    // CONNECTED
    // ========================================================

    socket.onopen = function () {

        console.log(
            "✅ Admin WebSocket Connected"
        );


        // Reset reconnect delay
        reconnectDelay = 2000;


        // Clear old heartbeat
        clearInterval(
            heartbeatTimer
        );


        // Start heartbeat
        heartbeatTimer = setInterval(
            function () {

                try {

                    if (
                        socket &&
                        socket.readyState ===
                        WebSocket.OPEN
                    ) {

                        socket.send(
                            JSON.stringify({
                                type: "ping"
                            })
                        );

                    }

                } catch (error) {

                    console.error(
                        "❌ Heartbeat failed:",
                        error
                    );

                }

            },
            30000
        );

    };


    // ========================================================
    // MESSAGE RECEIVED
    // ========================================================

    socket.onmessage = function (event) {

        try {

            const payload =
                JSON.parse(event.data);


            // Ignore heartbeat response
            if (
                payload.type === "pong"
            ) {

                console.log(
                    "💓 Pong received"
                );

                return;
            }


            console.log(
                "📨 Admin received:",
                payload
            );


            handleAdminEvent(
                payload
            );


        } catch (error) {

            console.error(
                "❌ WebSocket message error:",
                error
            );

        }

    };


    // ========================================================
    // ERROR
    // ========================================================

    socket.onerror = function (error) {

        console.error(
            "❌ Admin WebSocket Error:",
            error
        );

    };


    // ========================================================
    // CLOSED
    // ========================================================

    socket.onclose = function (event) {

        console.log(
            "🔌 WebSocket closed:",
            event.code,
            event.reason
        );


        clearInterval(
            heartbeatTimer
        );


        // Don't reconnect while leaving page
        if (isClosingPage) {
            return;
        }


        // Prevent multiple reconnect timers
        if (reconnectTimer) {
            return;
        }


        reconnectTimer = setTimeout(
            function () {

                reconnectTimer = null;

                console.log(
                    "🔄 Reconnecting WebSocket..."
                );

                connectWS();

            },
            reconnectDelay
        );


        // Exponential reconnect delay
        reconnectDelay =
            Math.min(
                reconnectDelay * 2,
                30000
            );

    };

}


// Start WebSocket
connectWS();


// ============================================================
// HANDLE ADMIN EVENTS
// ============================================================

function handleAdminEvent(payload) {

    console.log(
        "📩 Admin event:",
        payload
    );


    // New ticket
    if (
        payload.action === "create"
    ) {

        addTicket(
            payload.data
        );

        return;
    }


    // Updated ticket
    if (
        payload.action === "update"
    ) {

        updateTicket(
            payload.data
        );

        return;
    }


    // Deleted ticket
    if (
        payload.action === "delete"
    ) {

        if (
            payload.data &&
            payload.data.id
        ) {

            removeTicket(
                payload.data.id
            );

        }

        return;
    }

}


// ============================================================
// NEW TICKET
// ============================================================

function addTicket(ticket) {

    console.log(
        "🟢 New ticket received:",
        ticket
    );


    /*
     * Refresh only the ticket table.
     *
     * We DO NOT replace:
     *
     * #changelist
     * #changelist-filter
     *
     * Therefore:
     *
     * ✅ Filters remain
     * ✅ Filter open/closed state remains
     * ✅ Search remains
     * ✅ Pagination remains
     * ✅ Scroll is restored
     */

    scheduleRefresh();

}


// ============================================================
// UPDATED TICKET
// ============================================================

function updateTicket(ticket) {

    console.log(
        "🔵 Ticket updated:",
        ticket
    );


    scheduleRefresh();

}


// ============================================================
// DELETED TICKET
// ============================================================

function removeTicket(id) {

    console.log(
        "🔴 Ticket deleted:",
        id
    );


    scheduleRefresh();

}


// ============================================================
// SCHEDULE TABLE REFRESH
// ============================================================

function scheduleRefresh() {

    // Prevent multiple refreshes
    if (refreshTimer) {
        return;
    }


    /*
     * Wait 200ms.
     *
     * This prevents multiple WebSocket events
     * arriving at almost the same time from
     * causing multiple HTTP requests.
     */

    refreshTimer = setTimeout(
        function () {

            refreshTimer = null;

            refreshTicketTable();

        },
        200
    );

}


// ============================================================
// REFRESH ONLY TICKET TABLE
// ============================================================

function refreshTicketTable() {

    const currentTable =
        document.querySelector(
            "#result_list"
        );


    // Table doesn't exist
    if (!currentTable) {

        console.warn(
            "⚠️ #result_list not found"
        );

        return;
    }


    // ========================================================
    // SAVE SCROLL POSITION
    // ========================================================

    /*
     * Unfold uses a SimpleBar scrolling container.
     *
     * Find the closest scroll container.
     */

    const scrollContainer =
        currentTable.closest(
            ".simplebar-content-wrapper"
        );


    let scrollTop = 0;
    let scrollLeft = 0;


    if (scrollContainer) {

        scrollTop =
            scrollContainer.scrollTop;

        scrollLeft =
            scrollContainer.scrollLeft;

    } else {

        scrollTop =
            window.scrollY;

        scrollLeft =
            window.scrollX;

    }


    console.log(
        "📍 Saving scroll:",
        scrollTop
    );


    // ========================================================
    // FETCH CURRENT FILTERED PAGE
    // ========================================================

    fetch(
        window.location.href,
        {
            method: "GET",

            headers: {
                "X-Requested-With":
                    "XMLHttpRequest"
            },

            credentials: "same-origin"
        }
    )
        .then(function (response) {

            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );

            }

            return response.text();

        })
        .then(function (html) {

            // =================================================
            // PARSE NEW PAGE
            // =================================================

            const parser =
                new DOMParser();


            const doc =
                parser.parseFromString(
                    html,
                    "text/html"
                );


            // =================================================
            // FIND NEW TABLE
            // =================================================

            const newTable =
                doc.querySelector(
                    "#result_list"
                );


            const oldTable =
                document.querySelector(
                    "#result_list"
                );


            if (!newTable) {

                console.warn(
                    "⚠️ New #result_list not found"
                );

                return;

            }


            if (!oldTable) {

                console.warn(
                    "⚠️ Current #result_list not found"
                );

                return;

            }


            // =================================================
            // REPLACE ONLY TABLE
            // =================================================

            oldTable.replaceWith(
                newTable
            );


            console.log(
                "🔄 Ticket table updated"
            );


            // =================================================
            // RESTORE SCROLL
            // =================================================

            requestAnimationFrame(
                function () {

                    const newScrollContainer =
                        document
                            .querySelector(
                                "#result_list"
                            )
                            ?.closest(
                                ".simplebar-content-wrapper"
                            );


                    if (
                        newScrollContainer
                    ) {

                        newScrollContainer.scrollTop =
                            scrollTop;

                        newScrollContainer.scrollLeft =
                            scrollLeft;


                        console.log(
                            "📍 Scroll restored:",
                            scrollTop
                        );

                    } else {

                        window.scrollTo(
                            scrollLeft,
                            scrollTop
                        );

                    }

                }
            );

        })
        .catch(function (error) {

            console.error(
                "❌ Ticket table refresh failed:",
                error
            );

        });

}


// ============================================================
// TAB VISIBILITY
// ============================================================

document.addEventListener(
    "visibilitychange",
    function () {

        /*
         * IMPORTANT:
         *
         * We DO NOT refresh the table simply
         * because the user returned to the tab.
         *
         * This prevents the filter UI from
         * unexpectedly changing.
         */


        if (
            document.visibilityState !==
            "visible"
        ) {

            return;

        }


        // WebSocket still connected
        if (
            socket &&
            socket.readyState ===
            WebSocket.OPEN
        ) {

            console.log(
                "👁 Admin tab visible - WebSocket still connected"
            );

            return;

        }


        // WebSocket disconnected
        console.log(
            "🔄 Admin tab visible - reconnecting WebSocket"
        );


        connectWS();

    }
);


// ============================================================
// PAGE CLOSE
// ============================================================

window.addEventListener(
    "beforeunload",
    function () {

        isClosingPage = true;


        // Stop heartbeat
        clearInterval(
            heartbeatTimer
        );


        // Stop pending refresh
        clearTimeout(
            refreshTimer
        );


        // Stop reconnect
        clearTimeout(
            reconnectTimer
        );


        // Close WebSocket
        if (socket) {

            socket.close();

        }

    }
);