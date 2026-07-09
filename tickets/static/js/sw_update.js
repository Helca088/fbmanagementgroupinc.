if ("serviceWorker" in navigator) {

    navigator.serviceWorker.register("/employee-sw.js", {
        scope: "/",
        updateViaCache: "none"
    })
    .then(reg => {

        console.log("SW registered");

        // Check immediately
        reg.update();

        // Check every minute
        setInterval(() => {
            reg.update();
        }, 60000);

        let updateShown = false;

        reg.addEventListener("updatefound", () => {

            if (updateShown) return;

            const newWorker = reg.installing;

            newWorker.addEventListener("statechange", () => {

                if (
                    newWorker.state === "installed" &&
                    navigator.serviceWorker.controller
                ) {

                    updateShown = true;

                    console.log("New update available");

                }

            });

        });

    });

    navigator.serviceWorker.addEventListener("controllerchange", () => {

        console.log("New service worker activated");

        window.location.reload();

    });

}