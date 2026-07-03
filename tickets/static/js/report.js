new Chart(document.getElementById('statusChart'), {
    type: 'doughnut',
    data: {
        labels: ['Pending', 'In Progress', 'Resolved', 'Overdue'],
        datasets: [{
            data: statusData,
            backgroundColor: ['#fbbf24', '#60a5fa', '#34d399', '#f87171'],
            borderWidth: 2,
            borderColor: '#fff',
        }]
    },
    options: {
        plugins: { legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 16 } } },
        cutout: '65%',
    }
});

new Chart(document.getElementById('deptChart'), {
    type: 'bar',
    data: {
        labels: deptLabels,
        datasets: [{
            label: 'Tickets',
            data: deptData,
            backgroundColor: '#6366f1',
            borderRadius: 6,
        }]
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } }, x: { grid: { display: false } } },
    }
});

new Chart(document.getElementById('concernChart'), {
    type: 'bar',
    data: {
        labels: concernLabels,
        datasets: [{
            label: 'Tickets',
            data: concernData,
            backgroundColor: '#818cf8',
            borderRadius: 6,
        }]
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } }, x: { grid: { display: false } } },
    }
});

new Chart(document.getElementById('techChart'), {
    type: 'bar',
    data: {
        labels: techLabels,
        datasets: [
            { label: 'Total Assigned', data: techAssigned, backgroundColor: '#6366f1', borderRadius: 4 },
            { label: 'Resolved',       data: techResolved, backgroundColor: '#34d399', borderRadius: 4 },
            { label: 'Reopened',       data: techReopened, backgroundColor: '#fb923c', borderRadius: 4 },
        ]
    },
    options: {
        plugins: { legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 16 } } },
        scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } }, x: { grid: { display: false } } },
    }
});