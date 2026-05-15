document.addEventListener('DOMContentLoaded', function () {
    var canvas = document.getElementById('ratingSparkline');
    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    var labels = JSON.parse(canvas.dataset.labels || '[]');
    var ratings = JSON.parse(canvas.dataset.ratings || '[]');

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: ratings,
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.18)',
                borderWidth: 2,
                fill: true,
                tension: 0.35,
                pointRadius: 2,
                pointHoverRadius: 4,
                pointBackgroundColor: '#ffc107',
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return ctx.parsed.y.toFixed(1) + ' ★';
                        },
                    },
                },
            },
            scales: {
                x: { display: false },
                y: {
                    min: 1,
                    max: 5,
                    ticks: { stepSize: 1, color: '#999', font: { size: 10 } },
                    grid: { color: 'rgba(0,0,0,0.05)' },
                },
            },
        },
    });
});
