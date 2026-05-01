document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('xpChart');
    
    // Safety check: only run if the chart canvas exists on the current page
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Create a brand-consistent gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, '#ff7e5f');
    gradient.addColorStop(1, '#feb47b');

    // Initialize the Chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['User 1', 'User 2', 'User 3', 'User 4', 'User 5'],
            datasets: [{
                label: 'XP Gained This Week',
                data: [1250, 1100, 950, 800, 750],
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
                    grid: { display: false },
                    ticks: { font: { weight: '600' } }
                } 
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
});