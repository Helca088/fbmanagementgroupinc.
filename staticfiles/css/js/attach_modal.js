function openImageModal(src) {
    let modal =document.getElementById("imageModal");

    if(!modal){
        modal = document.createElement("div");
        modal.id = "imageModal";
        modal.innerHTML = `
        <div id="imageModalContent">
             <span id="closeModal">&times;</span>
             <img id="modalImage" src="" />
             </div>
             `;
             
    document.body.appendChild(modal);

    modal.style.position ="fixed";
    modal.style.top = "0";
    modal.style.left = "0";
    modal.style.width = "100%";
    modal.style.height = "100%";
    modal.style.background = "rgba(0.0.0.0.8)";
    modal.style.display = "flex";
    modal.style.alignItems = "center";
    modal.style.justifyContent = "center";
    modal.style.zIndex = "9999";

    document.getElementById("closeModal").onclick = () => {
        modal.style.display = "none";
    };
    modal.onclick = (e) => {
        if (e.target === modal){
            modal.style.display = "none";
        }
    };
    }

    document.getElementById("modalImage").src = src;
    modal.style.display = "flex";
}