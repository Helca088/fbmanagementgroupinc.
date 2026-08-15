document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // CREATE LOADER
    // ==============================

    const overlay = document.createElement("div");
    overlay.id = "page-loader";

    overlay.innerHTML = `
        <div id="lottie-animation"></div>
    `;

    document.body.appendChild(overlay);


    // ==============================
    // LOAD LOTTIE IF AVAILABLE
    // ==============================

    if (typeof lottie !== "undefined") {

        lottie.loadAnimation({
            container: document.getElementById("lottie-animation"),
            renderer: "svg",
            loop: true,
            autoplay: true,
            path: "/static/animations/loading.json"
        });

    } else {

        // Lottie is not loaded.
        // Still allow the loader to work.
        console.warn("Lottie is not loaded.");

        document.getElementById("lottie-animation").innerHTML = `
            <div class="simple-loader"></div>
        `;
    }


    // ==============================
    // SHOW LOADER
    // ==============================

    function showLoader() {
        overlay.classList.add("show");
    }


    // ==============================
    // HIDE LOADER
    // ==============================

    function hideLoader() {
        overlay.classList.remove("show");
    }


    // ==============================
    // LINK CLICK
    // ==============================

    document.addEventListener("click", (e) => {

        const link = e.target.closest("a");

        if (!link) return;


        // Ignore theme switch
        const xClick = link.getAttribute("x-on:click") || "";

        if (
            xClick.includes("switchTheme") ||
            xClick.includes("filterOpen")
        ) {
            return;
        }


        // Ignore special links
        if (
            link.target === "_blank" ||
            link.hasAttribute("download") ||
            link.href.startsWith("#") ||
            link.href.startsWith("javascript:")
        ) {
            return;
        }


        // Ignore Ctrl / CMD / Shift clicks
        if (
            e.ctrlKey ||
            e.metaKey ||
            e.shiftKey ||
            e.altKey
        ) {
            return;
        }


        // Ignore external links
        if (link.origin !== window.location.origin) {
            return;
        }


        // Ignore current page
        if (
            link.pathname === window.location.pathname &&
            link.search === window.location.search
        ) {
            return;
        }


        console.log("PAGE LOADER: clicked", link.href);

        showLoader();

        // DO NOT preventDefault.
        // Let Django navigation happen normally.

    });


    // ==============================
    // FORM SUBMIT
    // ==============================

    document.addEventListener("submit", () => {
        showLoader();
    });


    // ==============================
    // PAGE LOADED
    // ==============================

    window.addEventListener("pageshow", () => {
        hideLoader();
    });

});