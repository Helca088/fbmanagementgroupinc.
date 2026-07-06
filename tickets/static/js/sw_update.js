if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/employee-sw.js", { scope: '/' })
        .then(reg => {
            console.log("SW registered");

            let updateShown = false;

            reg.addEventListener("updatefound", () => {
                if (updateShown) return;

                const newWorker = reg.installing;

                newWorker.addEventListener("statechange", () => {
                    if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
                        updateShown = true;
                        console.log("New update available");
                        // optional UI instead of alert
                    }
                });
            });
        });

    navigator.serviceWorker.addEventListener("controllerchange", () => {
        window.location.reload();
    });
}