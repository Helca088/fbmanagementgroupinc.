(function () {
    "use strict";

    const STORAGE_KEY = "ticket_filter_states";

    function getStates() {
        try {
            return JSON.parse(
                localStorage.getItem(STORAGE_KEY)
            ) || {};
        } catch (e) {
            return {};
        }
    }

    function saveStates(states) {
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(states)
        );
    }

    function getKey(heading) {
        return heading.textContent
            .trim()
            .toLowerCase()
            .replace(/^by\s+/, "")
            .replace(/\s+/g, "_");
    }

    function setupFilters() {

        const headings = Array.from(
            document.querySelectorAll(
                "h3.font-semibold.text-important"
            )
        ).filter(function (heading) {

            return heading.textContent
                .trim()
                .toLowerCase()
                .startsWith("by ");

        });

        if (!headings.length) {
            return;
        }

        const states = getStates();

        headings.forEach(function (heading, index) {

            /*
             * Don't initialize twice
             */
            if (
                heading.dataset.filterInitialized === "true"
            ) {
                return;
            }

            heading.dataset.filterInitialized = "true";

            const key = getKey(heading);

            /*
             * Find everything between this heading
             * and the next "By ..." heading.
             */
            const content = [];

            let element =
                heading.nextElementSibling;

            while (element) {

                if (
                    element.matches(
                        "h3.font-semibold.text-important"
                    )
                ) {
                    break;
                }

                content.push(element);

                element =
                    element.nextElementSibling;
            }

            /*
             * Create arrow
             */
            const arrow =
                document.createElement("button");

            arrow.type = "button";

            arrow.className =
                "individual-filter-toggle";

            arrow.innerHTML = "▶";

            arrow.setAttribute(
                "aria-label",
                "Show or hide filter"
            );

            /*
             * Make heading layout
             */
            heading.style.display = "flex";
            heading.style.alignItems = "center";
            heading.style.justifyContent =
                "space-between";

            /*
             * Add arrow
             */
            heading.appendChild(arrow);

            /*
             * IMPORTANT:
             *
             * Default is COLLAPSED.
             *
             * Only restore expanded state if the user
             * previously opened this filter.
             */
            let collapsed;

           collapsed = true;

            function applyState() {

                content.forEach(function (element) {

                    element.style.display =
                        collapsed
                            ? "none"
                            : "";

                });

                arrow.textContent =
                    collapsed
                        ? "▶"
                        : "▼";

                arrow.setAttribute(
                    "aria-expanded",
                    collapsed
                        ? "false"
                        : "true"
                );

                heading.classList.toggle(
                    "filter-collapsed",
                    collapsed
                );
            }

            /*
             * Initial state
             */
            applyState();

            /*
             * Click arrow
             */
            arrow.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();
                    event.stopPropagation();

                    collapsed = !collapsed;

                    states[key] =
                        collapsed;

                    saveStates(states);

                    applyState();
                }
            );

        });
    }

    /*
     * Initial page load
     */
    document.addEventListener(
        "DOMContentLoaded",
        function () {

            setTimeout(
                setupFilters,
                300
            );

        }
    );

    /*
     * Unfold may render the filter sheet
     * after the initial page load.
     */
    setTimeout(
        setupFilters,
        800
    );

})();