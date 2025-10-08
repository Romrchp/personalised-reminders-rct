async function fetchMessageData() {
    const response = await fetch("/messages/stats");
    const data = await response.json();
    return data;
}

async function renderChart() {
    const messageData = await fetchMessageData();
    const labels = messageData.map(entry => entry.date);
    const assistantData = messageData.map(entry => entry.assistant_count);
    const userData = messageData.map(entry => entry.user_count);

    const ctx = document.getElementById('messageChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Assistant Messages',
                    data: assistantData,
                    borderColor: '#683b00',
                    backgroundColor: '#683b0020',
                    fill: false,
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#683b00',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#683b00',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 3
                },
                {
                    label: 'User Messages',
                    data: userData,
                    borderColor: '#de7012',
                    backgroundColor: '#de701220',
                    fill: false,
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#de7012',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#de7012',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 3
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
                        text: 'Date',
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
                            return `Date: ${context[0].label}`;
                        },
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} messages`;
                        },
                        afterBody: function(context) {
                            const totalForDay = context.reduce((sum, item) => sum + item.parsed.y, 0);
                            return `Total for day: ${totalForDay} messages`;
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

renderChart();