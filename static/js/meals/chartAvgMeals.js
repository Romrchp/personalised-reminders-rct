async function fetchMealRetentionData() {
    const response = await fetch("/meals/meal_retention_by_hour");
    return await response.json();
}

async function renderMealRetentionChart() {
    const data = await fetchMealRetentionData();
    const labels = data.map(entry => entry.hour);
    const mealCounts = data.map(entry => entry.meal_count);
    
    // peak hours to highlight
    const maxCount = Math.max(...mealCounts);
    const backgroundColors = mealCounts.map(count => {
        const intensity = count / maxCount;
        if (intensity > 0.8) return 'rgba(220, 20, 60, 0.8)'; 
        if (intensity > 0.6) return 'rgba(255, 140, 0, 0.7)'; 
        if (intensity > 0.4) return 'rgba(255, 215, 0, 0.6)'; 
        if (intensity > 0.2) return 'rgba(135, 206, 250, 0.5)'; 
        return 'rgba(211, 211, 211, 0.4)'; 
    });

    const ctx = document.getElementById('mealRetentionChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Meals Logged',
                data: mealCounts,
                backgroundColor: backgroundColors,
                borderColor: '#2c3e50',
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
                        text: 'Hour of Day',
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
                            return `Time: ${context[0].label}`;
                        },
                        label: function(context) {
                            const count = context.parsed.y;
                            const percentage = ((count / maxCount) * 100).toFixed(1);
                            return [
                                `Meals logged: ${count}`,
                                `Relative activity: ${percentage}%`
                            ];
                        },
                        afterLabel: function(context) {
                            const hour = parseInt(context.label.split(':')[0]);
                            let timeOfDay = '';
                            if (hour >= 6 && hour < 12) timeOfDay = '🌅 Morning';
                            else if (hour >= 12 && hour < 17) timeOfDay = '☀️ Afternoon';
                            else if (hour >= 17 && hour < 21) timeOfDay = '🌆 Evening';
                            else timeOfDay = '🌙 Night';
                            
                            return timeOfDay;
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

renderMealRetentionChart();