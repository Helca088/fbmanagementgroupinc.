document.addEventListener("DOMContentLoaded", () => {

    const overlay = document.createElement("div");

    overlay.id = "page-loader";

    overlay.innerHTML = `
        <div id="lottie-animation"></div>
    `;

    document.body.appendChild(overlay);


    // Load Lottie
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


    function showLoader() {
        overlay.classList.add("show");
    }


    function hideLoader() {
        overlay.classList.remove("show");
    }


    // ==========================================
    // ADMIN NAVIGATION
    // ==========================================

    document.addEventListener("click", function (e) {

        const link = e.target.closest("a");

        if (!link) {
            return;
        }


        console.log("CLICKED:", link);


        // Django Unfold theme
        const xClick = link.getAttribute("x-on:click") || "";

        if (
            xClick.includes("switchTheme") ||
            xClick.includes("filterOpen")
        ) {
            return;
        }


        // Don't show loader for new tabs
        if (link.target === "_blank") {
            return;
        }


        // Don't show loader for downloads
        if (link.hasAttribute("download")) {
            return;
        }


        // Don't show loader for Ctrl/CMD/Shift click
        if (
            e.ctrlKey ||
            e.metaKey ||
            e.shiftKey ||
            e.altKey
        ) {
            return;
        }


        // Only same website
        if (link.origin !== window.location.origin) {
            return;
        }


        // Ignore #
        if (link.getAttribute("href")?.startsWith("#")) {
            return;
        }


        // ==========================================
        // ADMIN PAGE
        // ==========================================

        if (link.href.includes("/admin/")) {

            console.log("ADMIN NAVIGATION:", link.href);

            showLoader();

            // Let browser navigate normally
            return;
        }


        // Normal site links
        showLoader();

    });


    // ==========================================
    // FORM SUBMIT
    // ==========================================

    document.addEventListener("submit", function () {
        showLoader();
    });


    // ==========================================
    // PAGE RESTORED
    // ==========================================

    window.addEventListener("pageshow", function () {
        hideLoader();
    });

});