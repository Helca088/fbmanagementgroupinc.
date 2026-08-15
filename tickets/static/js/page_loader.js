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

    let hideTimeout;

    function showLoader() {
        overlay.classList.add("show");
        // Safety net: never let it hang forever if navigation stalls/gets cancelled
        clearTimeout(hideTimeout);
        hideTimeout = setTimeout(() => overlay.classList.remove("show"), 8000);
    }

    document.addEventListener("click", (e) => {
        const link = e.target.closest("a");
        if (!link) return;

        // Ignore any Alpine-driven interaction, not just named ones
        // (sidebar toggle, dropdowns, tabs, theme switch, filters, etc.)
        if (link.hasAttribute("x-on:click") || link.hasAttribute("@click")) {
            return;
        }

        const hrefAttr = link.getAttribute("href");

        // Use the raw attribute, not link.href, to catch real anchor/JS/empty links
        if (
            !hrefAttr ||
            hrefAttr.startsWith("#") ||
            hrefAttr.startsWith("javascript:") ||
            hrefAttr.startsWith("mailto:") ||
            hrefAttr.startsWith("tel:")
        ) {
            return;
        }

        if (
            link.target === "_blank" ||
            link.hasAttribute("download") ||
            e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0
        ) {
            return;
        }

        showLoader();
    });

    document.addEventListener("submit", showLoader);

    window.addEventListener("pageshow", () => {
        clearTimeout(hideTimeout);
        overlay.classList.remove("show");
    });
});