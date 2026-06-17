(function () {
    // refresh every 10 seconds
    setInterval(function () {
        // only refresh if user is still on page
        if (document.visibilityState === "visible") {
            location.reload();
        }
    }, 90000);
})();