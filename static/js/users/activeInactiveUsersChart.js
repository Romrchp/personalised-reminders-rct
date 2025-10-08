async function fetchActiveInactiveUsersData() {
    const response = await fetch("/users/active-inactive-users");
    return await response.json();
}

async function renderActiveInactiveUsersChart() {
    const data = await fetchActiveInactiveUsersData();

    const labels = Object.keys(data).map(group => `Group ${group}`);
    const activeUsers = Object.values(data).map(pair => pair[0]);
    const inactiveUsers = Object.values(data).map(pair => pair[1]);
    const totals = activeUsers.map((active, i) => active + inactiveUsers[i]);

    const activePercent = activeUsers.map((count, i) => totals[i] ? (count / totals[i]) * 100 : 0);
    const inactivePercent = inactiveUsers.map((count, i) => totals[i] ? (count / totals[i]) * 100 : 0);

    const ctx = document.getElementById('activeInactiveUsersChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '"Has started" Users',
                    data: activePercent,
                    backgroundColor: '#008080',
                    borderColor: '#008080',
                    borderWidth: 2,
                    borderRadius: 4,
                    borderSkipped: false,
                    hoverBackgroundColor: '#006666',
                    hoverBorderColor: '#006666',
                    hoverBorderWidth: 3
                },
                {
                    label: '"Never started" Users',
                    data: inactivePercent,
                    backgroundColor: '#cccccc',
                    borderColor: '#cccccc',
                    borderWidth: 2,
                    borderRadius: 4,
                    borderSkipped: false,
                    hoverBackgroundColor: '#b8b8b8',
                    hoverBorderColor: '#b8b8b8',
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
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Study Group',
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
                    stacked: true,
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Percentage of Users (%)',
                        font: {
                            family: 'Arial',
                            size: 16,
                            weight: 'bold',
                            color: '#2c3e50'
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        color: '#2c3e50',
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)',
                        drawBorder: false
                    }
                }
            },
            plugins: {
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    cornerRadius: 6,
                    callbacks: {
                        title: function(context) {
                            return `${context[0].label}`;
                        },
                        label: function(context) {
                            const datasetLabel = context.dataset.label || '';
                            const percent = context.parsed.y.toFixed(2);
                            const index = context.dataIndex;
                            const isActive = context.datasetIndex === 0;
                            const absolute = isActive ? activeUsers[index] : inactiveUsers[index];
                            return `${datasetLabel}: ${absolute} (${percent}%)`;
                        },
                        afterBody: function(context) {
                            const index = context[0].dataIndex;
                            const total = totals[index];
                            return `Total users: ${total}`;
                        }
                    }
                },
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
                }
            },
            animation: {
                duration: 1200,
                easing: 'easeInOutQuart'
            }
        }
    });
}

renderActiveInactiveUsersChart();