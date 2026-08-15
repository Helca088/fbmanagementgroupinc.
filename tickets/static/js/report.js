/* =========================================================
   TICKET STATUS
========================================================= */
Chart.defaults.devicePixelRatio = window.devicePixelRatio || 1;
Chart.defaults.font.family = 'Inter, Arial, sans-serif';
new Chart(document.getElementById('statusChart'), {

    type: 'doughnut',

    data: {
        labels: [
            'Pending',
            'In Progress',
            'Resolved',
            'Overdue',
            'Cancelled'
        ],

        datasets: [{
            data: statusData,

            backgroundColor: [
                '#fbbf24', // Pending
                '#60a5fa', // In Progress
                '#34d399', // Resolved
                '#ef4444', // Overdue
                '#94a3b8'  // Cancelled
            ],

            borderWidth: 2,
            borderColor: '#ffffff'
        }]
    },

    options: {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                position: 'bottom',

                labels: {
                    font: {
                        size: 12
                    },

                    padding: 16,

                    boxWidth: 40
                }
            }
        },

        cutout: '65%'
    }
});


/* =========================================================
   TICKETS BY DEPARTMENT
========================================================= */

new Chart(document.getElementById('deptChart'), {

    type: 'bar',

    data: {
        labels: deptLabels,

        datasets: [{
            label: 'Tickets',

            data: deptData,

            backgroundColor: '#6366f1',

            borderRadius: 6,

            borderSkipped: false
        }]
    },

    options: {

        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                display: false
            }
        },

        scales: {

            y: {
                beginAtZero: true,

                ticks: {
                    precision: 0
                },

                grid: {
                    color: '#f1f5f9'
                }
            },

            x: {
                grid: {
                    display: false
                }
            }
        }
    }
});


/* =========================================================
   TICKETS BY CONCERN
========================================================= */

new Chart(document.getElementById('concernChart'), {

    type: 'bar',

    data: {
        labels: concernLabels,

        datasets: [{
            label: 'Tickets',

            data: concernData,

            backgroundColor: '#818cf8',

            borderRadius: 6,

            borderSkipped: false
        }]
    },

    options: {

        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                display: false
            }
        },

        scales: {

            y: {
                beginAtZero: true,

                ticks: {
                    precision: 0
                },

                grid: {
                    color: '#f1f5f9'
                }
            },

            x: {
                grid: {
                    display: false
                },

                ticks: {
                    autoSkip: true,
                    maxRotation: 45,
                    minRotation: 0
                }
            }
        }
    }
});


/* =========================================================
   TICKETS BY OUTLET
========================================================= */

new Chart(document.getElementById('outletChart'), {

    type: 'bar',

    data: {
        labels: outletLabels,

        datasets: [{
            label: 'Tickets',

            data: outletData,

            backgroundColor: '#818cf8',

            borderRadius: 6,

            borderSkipped: false
        }]
    },

    options: {

        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                display: false
            }
        },

        scales: {

            y: {
                beginAtZero: true,

                ticks: {
                    precision: 0
                },

                grid: {
                    color: '#f1f5f9'
                }
            },

            x: {
                grid: {
                    display: false
                },

                ticks: {
                    autoSkip: true,
                    maxRotation: 45,
                    minRotation: 0
                }
            }
        }
    }
});


/* =========================================================
   TECHNICIAN PERFORMANCE
========================================================= */

new Chart(document.getElementById('techChart'), {

    type: 'bar',

    data: {

        labels: techLabels,

        datasets: [

            {
                label: 'Total Assigned',

                data: techAssigned,

                backgroundColor: '#6366f1',

                borderRadius: 4,

                borderSkipped: false
            },

            {
                label: 'Resolved',

                data: techResolved,

                backgroundColor: '#34d399',

                borderRadius: 4,

                borderSkipped: false
            },

            {
                label: 'Reopened',

                data: techReopened,

                backgroundColor: '#fb923c',

                borderRadius: 4,

                borderSkipped: false
            }

        ]
    },

    options: {

        responsive: true,
        maintainAspectRatio: false,

        plugins: {

            legend: {

                position: 'bottom',

                labels: {

                    font: {
                        size: 12
                    },

                    padding: 16
                }
            }
        },

        scales: {

            y: {

                beginAtZero: true,

                ticks: {
                    precision: 0
                },

                grid: {
                    color: '#f1f5f9'
                }
            },

            x: {

                grid: {
                    display: false
                }
            }
        }
    }
});