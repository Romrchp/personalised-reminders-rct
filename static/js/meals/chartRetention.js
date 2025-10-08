async function fetchCohortRetentionData() {
    try {
        const response = await fetch("/meals/cohort_retention");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Fetched cohort retention data:", data);
        return data;
    } catch (error) {
        console.error("Error fetching cohort retention data:", error);
        return [];
    }
}
  
async function renderCohortRetentionChart() {
    try {
        const data = await fetchCohortRetentionData();
        
        if (!data || data.length === 0) {
            console.warn("No data available for cohort retention chart");
            return;
        }
        
        const labels = data.map(entry => entry.date);
        const userCounts = data.map(entry => entry.user_count);

        // Create gradient for the line
        const ctx = document.getElementById('cohortRetentionChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(222, 112, 18, 0.3)');
        gradient.addColorStop(1, 'rgba(222, 112, 18, 0.05)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Active Users',
                    data: userCounts,
                    borderColor: '#de7012',
                    backgroundColor: gradient,
                    fill: true,
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#de7012',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#de7012',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 3
                }]
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
                            text: 'Number of Active Users',
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
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return `Date: ${context[0].label}`;
                            },
                            label: function(context) {
                                const count = context.parsed.y;
                                const maxUsers = Math.max(...userCounts);
                                const retentionRate = ((count / maxUsers) * 100).toFixed(1);
                                return [
                                    `Active users: ${count}`,
                                    `Retention rate: ${retentionRate}%`
                                ];
                            },
                            afterLabel: function(context) {
                                const index = context.dataIndex;
                                if (index > 0) {
                                    const previousCount = userCounts[index - 1];
                                    const currentCount = context.parsed.y;
                                    const change = currentCount - previousCount;
                                    const changeSymbol = change >= 0 ? '📈' : '📉';
                                    return `${changeSymbol} Change: ${change >= 0 ? '+' : ''}${change}`;
                                }
                                return null;
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
      
        
    } catch (error) {
        console.error("Error rendering cohort retention chart:", error);
    }
}

renderCohortRetentionChart();