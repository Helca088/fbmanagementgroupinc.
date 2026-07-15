document.addEventListener("DOMContentLoaded", function () {

    const department = document.getElementById("id_department");
    const technician = document.getElementById("id_assigned_to");

    if (!department || !technician) return;

    function loadTechnicians() {

        const departmentId = department.value;

        technician.innerHTML = '<option value="">Pumili ng technician</option>';

        if (!departmentId) return;

        fetch(`/get-technicians/?department=${departmentId}`)
            .then(response => response.json())
            .then(data => {

                console.log("Returned data:", data);

                data.forEach(function (tech) {

                    const option = document.createElement("option");

                    option.value = tech.id;
                    option.textContent = tech.name;

                    technician.appendChild(option);
                });

                console.log("Options count:", technician.options.length);
                console.log(technician.innerHTML);

            });

    }

    department.addEventListener("change", loadTechnicians);

});