document.addEventListener('DOMContentLoaded', function () {
    const xpCanvas =
        document.getElementById('xpChart');

    if (xpCanvas) {
        const xpCtx = xpCanvas.getContext('2d');
        const gradient =
            xpCtx.createLinearGradient(0, 0, 0, 400);

        gradient.addColorStop(0, '#ff7e5f');
        gradient.addColorStop(1, '#feb47b');

        new Chart(xpCtx, {
            type: 'bar',
            data: {

                labels: window.topUserLabels,
                datasets: [{
                    label: 'XP Gained This Week',
                    data: window.topUserXp,
                    backgroundColor: gradient,
                    borderRadius: 8
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {

                    y: {

                        beginAtZero: true,
                        display: false
                    },

                    x: {

                        grid: {
                            display: false
                        },

                        ticks: {
                            font: {
                                weight: '600'
                            }
                        }
                    }
                },

                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    const suburbCanvas =
        document.getElementById('suburbChart');

    if (suburbCanvas) {

        const suburbCtx =
            suburbCanvas.getContext('2d');

        new Chart(suburbCtx, {

            type: 'doughnut',

            data: {

                labels: window.suburbLabels,
                datasets: [{

                    label: 'Reviews Per Suburb',
                    data: window.suburbCounts,
                    borderWidth: 1
                }]
            },

            options: {

                responsive: true,
                maintainAspectRatio: false,
                plugins: {

                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

});