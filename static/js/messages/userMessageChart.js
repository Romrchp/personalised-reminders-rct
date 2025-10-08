async function fetchUserMessagesPerHour() {
    const response = await fetch("/messages/per-hour");
    const data = await response.json();
    return data;
}

async function renderUserMessagesChart() {
    const messageData = await fetchUserMessagesPerHour();
    const hours = messageData.map(entry => entry.hour);
    const userData = messageData.map(entry => entry.user_count);

    const ctx = document.getElementById('userMessagesChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hours,
            datasets: [
                {
                    label: 'User Messages per Hour',
                    data: userData,
                    backgroundColor: '#de7012',
                    borderColor: '#de7012',
                    borderWidth: 2,
                    borderRadius: 4,
                    borderSkipped: false,
                    hoverBackgroundColor: '#c55a0a',
                    hoverBorderColor: '#c55a0a',
                    hoverBorderWidth: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Hour of the Day',
                        font: {
                            family: 'Arial',
                            size: 16,
                            weight: 'bold',
                            color: '#2c3e50'
                        }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#2c3e50',
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Message Count',
                        font: {
                            family: 'Arial',
                            size: 16,
                            weight: 'bold',
                            color: '#2c3e50'
                        }
                    },
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#2c3e50',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        font: {
                            family: 'Arial',
                            size: 14,
                            color: '#2c3e50'
                        },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    cornerRadius: 6,
                    callbacks: {
                        title: function(context) {
                            return `Hour: ${context[0].label}:00`;
                        },
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} messages`;
                        }
                    }
                }
            },
            animation: {
                duration: 1200,
                easing: 'easeInOutQuart'
            }
        }
    });
}

renderUserMessagesChart();