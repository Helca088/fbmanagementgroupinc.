document.addEventListener("DOMContentLoaded", function () {

    const department = document.getElementById("id_department");
    const technician = document.getElementById("id_assigned_to");
    const concern = document.getElementById("id_concern_type");

    if (!department) return;

    function loadTechnicians() {
        if (!technician) return;

        const departmentId = department.value;

        technician.innerHTML = '<option value="">Pumili ng technician</option>';

        if (!departmentId) return;

        fetch(`/get-technicians/?department=${departmentId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(function (tech) {
                    const option = document.createElement("option");
                    option.value = tech.id;
                    option.textContent = tech.name;
                    technician.appendChild(option);
                });
            });
    }

    function loadConcerns() {
        if (!concern) return;

        const departmentId = department.value;

        concern.innerHTML = '<option value="">---------</option>';

        if (!departmentId) return;

        fetch(`/admin/tickets/ticket/get-concerns/?department=${departmentId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(function (item) {
                    const option = document.createElement("option");
                    option.value = item.id;
                    option.textContent = item.name;
                    concern.appendChild(option);
                });
            });
    }

    department.addEventListener("change", function () {
        loadTechnicians();
        loadConcerns();
    });

});