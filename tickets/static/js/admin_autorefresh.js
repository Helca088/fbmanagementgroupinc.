function loadTickets() {
    fetch('/api/tickets/')
        .then(res => res.json())
        .then(data => {
            updateTable(data); 
        });
}


setInterval(() => {
    console.log("polling running...");
}, 3000);