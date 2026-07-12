document.addEventListener("DOMContentLoaded", () => {
    // Create overlay
    const overlay = document.createElement("div");
    overlay.id = "page-loader";
    overlay.innerHTML = '<div class="loader"></div>';
    document.body.appendChild(overlay);

    // Show loader when clicking links
    document.addEventListener("click", (e) => {
        const link = e.target.closest("a");

        if (!link) return;

        // Ignore anchors, downloads, new tabs
        if (
            link.target === "_blank" ||
            link.hasAttribute("download") ||
            link.href.startsWith("#") ||
            e.ctrlKey || e.metaKey || e.shiftKey
        ) {
            return;
        }

        overlay.classList.add("show");
    });

    // Show loader when submitting forms (e.g. login)
    document.addEventListener("submit", () => {
        overlay.classList.add("show");
    });

    // Hide loader if the page is restored from browser cache
    window.addEventListener("pageshow", () => {
        overlay.classList.remove("show");
    });
});