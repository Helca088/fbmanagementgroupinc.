function openImageModal(src) {
    let modal =document.getElementById("imageModal");

    if(!modal){
        modal = document.createElement("div");
        modal.id = "imageModal";
        modal.innerHTML = `<img id="modalImage" style="max-width:90vw; max-height:90vh;">`;

             
    document.body.appendChild(modal);

    modal.style.position ="fixed";
    modal.style.top = "0";
    modal.style.left = "0";
    modal.style.width = "100vw";
    modal.style.height = "100vh";
    modal.style.background = "rgba(0.0.0.0.85)";
    modal.style.display = "flex";
    modal.style.alignItems = "center";
    modal.style.justifyContent = "center";
    modal.style.zIndex = "9999";

    modal.onclick = () => modal.style.display = "none";
    }

    document.getElementById("modalImage").src = src;
    modal.style.display = "flex";
}

window.downloadSelectedAttachments = function () {
    console.log("clicked download");
    const checked =
        document.querySelectorAll(
             'input[name="attachments"]:checked'
        );

    if (checked.length === 0) {
        alert("Select at least one attachment.");
        return;
    }
    
    checked.forEach(cb => {
        window.open(
            `/attachment/${cb.value}/download/` ,
            "_blank"
        );
    });
}