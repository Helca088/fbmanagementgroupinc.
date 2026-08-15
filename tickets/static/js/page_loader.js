document.addEventListener("DOMContentLoaded", () => {
    const overlay = document.createElement("div");
    overlay.id = "page-loader";
    overlay.innerHTML = '<div id="lottie-animation"></div>';
    document.body.appendChild(overlay);

    lottie.loadAnimation({
        container: document.getElementById("lottie-animation"),
        renderer: "svg",
        loop: true,
        autoplay: true,
        path: "/static/animations/loading.json"
    });

    let navigating = false;

    document.addEventListener("click", (e) => {

        const link = e.target.closest("a");

        if (!link) return;

        // Ignore Django Unfold theme switch
        if (link.matches('a[x-on\\:click^="switchTheme"]')) {
            return;
        }

        const xClick = link.getAttribute("x-on:click") || "";

        if (
            xClick.includes("switchTheme") ||
            xClick.includes("filterOpen")
        ) {
            return;
        }

        // Ignore special clicks
        if (
            link.target === "_blank" ||
            link.hasAttribute("download") ||
            link.href.startsWith("#") ||
            e.ctrlKey ||
            e.metaKey ||
            e.shiftKey
        ) {
            return;
        }

        // Ignore external links
        if (link.origin !== window.location.origin) {
            return;
        }

        // Ignore same page
        if (link.href === window.location.href) {
            return;
        }

        // Prevent double clicking
        if (navigating) {
            e.preventDefault();
            return;
        }

        navigating = true;

        // Stop normal navigation temporarily
        e.preventDefault();

        // Show loader
        overlay.classList.add("show");

        // Give browser time to actually render loader
        setTimeout(() => {
            window.location.href = link.href;
        }, 120);
    });


    // Show loader when submitting forms
    document.addEventListener("submit", () => {
        overlay.classList.add("show");
    });


    // Hide loader when page is restored
    window.addEventListener("pageshow", () => {
        overlay.classList.remove("show");
        navigating = false;
    });
});