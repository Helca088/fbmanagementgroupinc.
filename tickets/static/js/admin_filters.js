(function () {
    "use strict";

    const STORAGE_KEY = "ticket_admin_filter_states";

    function getSavedStates() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        } catch (e) {
            return {};
        }
    }

    function saveStates(states) {
        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(states)
            );
        } catch (e) {
            // Ignore localStorage errors
        }
    }

    function getFilterName(filter) {
        /*
         * Try to identify the filter using its contents.
         * This makes the code work without changing Django's
         * list_filter configuration.
         */

        const heading = filter.querySelector(
            "h2, h3, legend, [class*='font-semibold']"
        );

        if (heading) {
            const text = heading.textContent.trim();

            if (text) {
                return text
                    .toLowerCase()
                    .replace(/\s+/g, "_");
            }
        }

        return "filter_" + Array.from(
            document.querySelectorAll("[data-admin-filter]")
        ).indexOf(filter);
    }

    function getFilterSections() {
        /*
         * Unfold renders the Django filter sections inside
         * the filter sidebar/sheet.
         *
         * We look for headings that contain the familiar
         * Django filter titles.
         */

        const possible = [];

        document.querySelectorAll(
            "aside section, aside > div, aside li"
        ).forEach(function (element) {
            const text = element.textContent.trim();

            if (
                text.includes("By department") ||
                text.includes("By status") ||
                text.includes("By priority") ||
                text.includes("By assigned to") ||
                text.includes("By outlet")
            ) {
                possible.push(element);
            }
        });

        return possible;
    }

    function findHeading(filter) {
        return filter.querySelector(
            "h2, h3, legend, summary"
        );
    }

    function collapseFilter(filter, button, collapsed) {
        const heading = findHeading(filter);

        if (!heading) {
            return;
        }

        /*
         * Everything after the heading is the filter content.
         */

        let content = [];

        Array.from(filter.children).forEach(function (child) {
            if (child !== heading && child !== button) {
                content.push(child);
            }
        });

        /*
         * Sometimes Unfold puts the heading inside another
         * wrapper. In that case we hide the remaining
         * descendants instead.
         */

        if (content.length === 0) {
            content = Array.from(
                filter.querySelectorAll(
                    ":scope > div:not(:first-child)"
                )
            );
        }

        content.forEach(function (element) {
            if (element.dataset.filterToggleButton === "true") {
                return;
            }

            element.style.display = collapsed
                ? "none"
                : "";
        });

        filter.classList.toggle(
            "admin-filter-collapsed",
            collapsed
        );

        button.setAttribute(
            "aria-expanded",
            collapsed ? "false" : "true"
        );

        button.textContent = collapsed ? "▶" : "▼";
    }

    function createToggle(filter, key) {
        if (
            filter.querySelector(
                ".admin-filter-collapse-button"
            )
        ) {
            return;
        }

        const heading = findHeading(filter);

        if (!heading) {
            return;
        }

        const button = document.createElement("button");

        button.type = "button";
        button.className =
            "admin-filter-collapse-button";

        button.dataset.filterToggleButton = "true";

        button.setAttribute(
            "aria-label",
            "Show or hide " + key + " filter"
        );

        button.setAttribute(
            "title",
            "Show / Hide filter"
        );

        const states = getSavedStates();

        const collapsed = states[key] === true;

        button.textContent = collapsed
            ? "▶"
            : "▼";

        button.setAttribute(
            "aria-expanded",
            collapsed ? "false" : "true"
        );

        button.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            const currentlyCollapsed =
                filter.classList.contains(
                    "admin-filter-collapsed"
                );

            const newState = !currentlyCollapsed;

            const saved = getSavedStates();

            saved[key] = newState;

            saveStates(saved);

            collapseFilter(
                filter,
                button,
                newState
            );
        });

        heading.classList.add(
            "admin-filter-heading-with-toggle"
        );

        heading.appendChild(button);

        collapseFilter(
            filter,
            button,
            collapsed
        );
    }

    function initFilters() {
        const filters = getFilterSections();

        filters.forEach(function (filter) {
            const heading = findHeading(filter);

            if (!heading) {
                return;
            }

            const title = heading.textContent.trim();

            if (!title) {
                return;
            }

            const key = title
                .toLowerCase()
                .replace(/\s+/g, "_");

            createToggle(
                filter,
                key
            );
        });
    }

    /*
     * Initial load
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
     * Unfold/Django may update parts of the page
     * dynamically, so check again after a short delay.
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