
async function fetchLoggingFrequencyData() {
    try {
        const response = await fetch("/meals/logging_frequency");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Fetched logging frequency data:", data);
        return data;
    } catch (error) {
        console.error("Error fetching logging frequency data:", error);
        return [];
    }
}

async function renderLoggingFrequencyChart() {
    try {
        const data = await fetchLoggingFrequencyData();
        
        if (!data || data.length === 0) {
            console.warn("No data available for logging frequency chart");
            return;
        }
        
        const labels = data.map(entry => entry.date);
        const mealCounts = data.map(entry => entry.meal_count);

        const maxCount = Math.max(...mealCounts);
        const backgroundColors = mealCounts.map(count => {
            const intensity = count / maxCount;
            const alpha = 0.3 + (intensity * 0.5);
            return `rgba(222, 112, 18, ${alpha})`;
        });

        const ctx = document.getElementById('loggingFrequencyChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Meals Logged',
                    data: mealCounts,
                    backgroundColor: backgroundColors,
                    borderColor: '#de7012',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false,
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
                            text: 'Number of Meals Logged',
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
                            }
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
                                const percentage = ((count / maxCount) * 100).toFixed(1);
                                return [
                                    `Meals logged: ${count}`,
                                    `Relative activity: ${percentage}%`
                                ];
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
        console.error("Error rendering logging frequency chart:", error);
    }
}

renderLoggingFrequencyChart();