document.addEventListener("DOMContentLoaded", () => {

    // ==========================================
    // CREATE LOADER
    // ==========================================

    let overlay = document.getElementById("page-loader");

    if (!overlay) {

        overlay = document.createElement("div");

        overlay.id = "page-loader";

        overlay.innerHTML = `
            <div id="lottie-animation"></div>
        `;

        document.body.appendChild(overlay);
    }


    // ==========================================
    // START LOTTIE
    // ==========================================

    if (typeof lottie !== "undefined") {

        lottie.loadAnimation({
            container: document.getElementById("lottie-animation"),
            renderer: "svg",
            loop: true,
            autoplay: true,
            path: "/static/animations/loading.json"
        });

    } else {

        document.getElementById("lottie-animation").innerHTML = `
            <div class="simple-loader"></div>
        `;
    }


    // ==========================================
    // SHOW / HIDE
    // ==========================================

    function showLoader() {
        overlay.classList.add("show");
    }

    function hideLoader() {
        overlay.classList.remove("show");
    }


    // ==========================================
    // CHECK IF WE ARE ARRIVING FROM ANOTHER PAGE
    // ==========================================

    const pageLoading = sessionStorage.getItem("pageLoading");

    if (pageLoading === "true") {

        // Remove flag immediately
        sessionStorage.removeItem("pageLoading");

        // Show loader on the NEW page
        showLoader();

        // Keep it visible long enough to actually see it
        setTimeout(() => {
            hideLoader();
        }, 350);
    }


    // ==========================================
    // NAVIGATION
    // ==========================================

    document.addEventListener("click", (e) => {

        const link = e.target.closest("a");

        if (!link) {
            return;
        }


        // Ignore new tabs
        if (link.target === "_blank") {
            return;
        }


        // Ignore downloads
        if (link.hasAttribute("download")) {
            return;
        }


        // Ignore special clicks
        if (
            e.ctrlKey ||
            e.metaKey ||
            e.shiftKey ||
            e.altKey
        ) {
            return;
        }


        // Ignore anchors
        const href = link.getAttribute("href");

        if (!href || href.startsWith("#")) {
            return;
        }


        // Ignore external websites
        if (link.origin !== window.location.origin) {
            return;
        }


        // Ignore theme/filter buttons
        const xClick = link.getAttribute("x-on:click") || "";

        if (
            xClick.includes("switchTheme") ||
            xClick.includes("filterOpen")
        ) {
            return;
        }


        // ==========================================
        // CHECK IF THIS IS ACTUALLY A NEW PAGE
        // ==========================================

        const currentURL =
            window.location.pathname +
            window.location.search;

        const targetURL =
            link.pathname +
            link.search;

        if (currentURL === targetURL) {
            return;
        }


        // ==========================================
        // TELL THE NEXT PAGE TO SHOW LOADER
        // ==========================================

        sessionStorage.setItem("pageLoading", "true");

        console.log("PAGE NAVIGATION:", link.href);

        // Show it here too
        showLoader();

        // Allow normal browser navigation
    });


    // ==========================================
    // FORM SUBMISSION
    // ==========================================

    document.addEventListener("submit", () => {

        sessionStorage.setItem("pageLoading", "true");

        showLoader();
    });


    // ==========================================
    // BROWSER BACK / FORWARD
    // ==========================================

    window.addEventListener("pageshow", () => {

        // Don't leave loader stuck
        if (!sessionStorage.getItem("pageLoading")) {
            hideLoader();
        }
    });

});