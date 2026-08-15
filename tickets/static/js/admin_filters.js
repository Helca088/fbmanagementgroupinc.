(function () {
    "use strict";

    const STORAGE_KEY = "ticket_admin_filter_states";

    function getStates() {
        try {
            return JSON.parse(
                localStorage.getItem(STORAGE_KEY)
            ) || {};
        } catch (error) {
            return {};
        }
    }

    function saveStates(states) {
        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(states)
            );
        } catch (error) {
            // Ignore localStorage errors
        }
    }

    function getFilterKey(title) {
        return title
            .trim()
            .toLowerCase()
            .replace(/^by\s+/, "")
            .replace(/\s+/g, "_");
    }

    function initFilters() {

        const headings = document.querySelectorAll(
            "h3.font-semibold.text-important"
        );

        headings.forEach(function (heading) {

            const title = heading.textContent.trim();

            if (!title.startsWith("By ")) {
                return;
            }

            // Don't add the button twice
            if (
                heading.querySelector(
                    ".admin-filter-toggle"
                )
            ) {
                return;
            }

            const key = getFilterKey(title);

            /*
             * The filter container is the parent of the H3.
             */
            const container = heading.parentElement;

            if (!container) {
                return;
            }

            /*
             * Create toggle button
             */
            const button = document.createElement("button");

            button.type = "button";
            button.className = "admin-filter-toggle";

            button.setAttribute(
                "aria-label",
                `Hide or show ${title}`
            );

            button.title = "Hide / Show filter";

            /*
             * Put arrow on the right side
             */
            button.innerHTML = "▼";

            /*
             * Make heading a flex row
             */
            heading.style.display = "flex";
            heading.style.alignItems = "center";
            heading.style.justifyContent = "space-between";
            heading.style.width = "100%";

            heading.appendChild(button);

            /*
             * Find everything inside the filter container
             * except the heading.
             */
            const contents = Array.from(
                container.children
            ).filter(function (element) {
                return element !== heading;
            });

            /*
             * Restore saved state
             */
            const states = getStates();

            let collapsed = states[key] === true;

            function applyState() {

                contents.forEach(function (element) {
                    element.style.display =
                        collapsed ? "none" : "";
                });

                button.innerHTML =
                    collapsed ? "▶" : "▼";

                button.setAttribute(
                    "aria-expanded",
                    collapsed ? "false" : "true"
                );

                container.classList.toggle(
                    "admin-filter-collapsed",
                    collapsed
                );
            }

            applyState();

            /*
             * Toggle
             */
            button.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();
                    event.stopPropagation();

                    collapsed = !collapsed;

                    const currentStates =
                        getStates();

                    currentStates[key] =
                        collapsed;

                    saveStates(
                        currentStates
                    );

                    applyState();
                }
            );
        });
    }

    /*
     * Run after page loads
     */
    document.addEventListener(
        "DOMContentLoaded",
        function () {
            setTimeout(
                initFilters,
                100
            );
        }
    );

    /*
     * Run again after everything loads
     */
    window.addEventListener(
        "load",
        function () {
            setTimeout(
                initFilters,
                300
            );
        }
    );

})();