document.addEventListener("DOMContentLoaded", function () {

    const department = document.getElementById("id_department");
    const technician = document.getElementById("id_assigned_to");
    const additionalTechnicians = document.getElementById("id_additional_technicians");
    const concern = document.getElementById("id_concern_type");

    if (!department) return;

    function loadTechnicians() {
        if (!technician) return;

        const departmentId = department.value;

        // Remember current selections
        const selectedTechnician = technician.value;
        const selectedAdditional = additionalTechnicians
            ? Array.from(additionalTechnicians.selectedOptions).map(option => option.value)
            : [];

        // Clear existing options
        technician.innerHTML = '<option value="">Pumili ng technician</option>';
        if (additionalTechnicians) additionalTechnicians.innerHTML = "";

        if (!departmentId) return;

        fetch(`/get-technicians/?department=${departmentId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(function (tech) {

                    // Primary technician
                    const option1 = document.createElement("option");
                    option1.value = String(tech.id);
                    option1.textContent = tech.name;

                    if (option1.value === selectedTechnician) {
                        option1.selected = true;
                    }

                    technician.appendChild(option1);

                    // Additional technicians
                    if (additionalTechnicians) {
                        const option2 = document.createElement("option");
                        option2.value = String(tech.id);
                        option2.textContent = tech.name;

                        if (selectedAdditional.includes(option2.value)) {
                            option2.selected = true;
                        }

                        additionalTechnicians.appendChild(option2);
                    }
                });
            })
            .catch(error => {
                console.error("Error loading technicians:", error);
            });
    }

    function loadConcerns() {
        if (!concern) return;

        const departmentId = department.value;

        // Remember current selection
        const selectedConcern = concern.value;

        concern.innerHTML = '<option value="">Pumili ng concern</option>';

        if (!departmentId) return;

        fetch(`/admin/tickets/ticket/get-concerns/?department=${departmentId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(function (item) {
                    const option = document.createElement("option");
                    option.value = String(item.id);
                    option.textContent = item.name;

                    if (option.value === selectedConcern) {
                        option.selected = true;
                    }

                    concern.appendChild(option);
                });
            })
            .catch(error => {
                console.error("Error loading concerns:", error);
            });
    }

    department.addEventListener("change", function () {
        loadTechnicians();
        loadConcerns();
    });

    // Load automatically when editing an existing ticket
    if (department.value) {
        loadTechnicians();
        loadConcerns();
    }

});