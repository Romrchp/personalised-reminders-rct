async function fetchMealsPerDayData() {
    try {
        const response = await fetch("/meals/meals_per_day");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Fetched meals per day data:", data);
        return data;
    } catch (error) {
        console.error("Error fetching meals per day data:", error);
        return [];
    }
}

async function renderMealsPerDayChart() {
    try {
        const data = await fetchMealsPerDayData();
        
        if (!data || data.length === 0) {
            console.warn("No data available for meals per day chart");
            return;
        }

        const dates = [...new Set(data.map(entry => entry.date))].sort();
        const studyGroups = [...new Set(data.map(entry => entry.study_group))];

        const groupColors = {
            0: '#6c757d',
            1: '#17a2b8',
            2: '#28a745',
            3: '#7100b3'
        };

        const datasets = studyGroups.map((group, index) => {
            return {
                label: `Group ${group}`,
                data: dates.map(date => {
                    const entry = data.find(d => d.date === date && d.study_group === group);
                    return entry ? entry.meal_count : 0;
                }),
                borderColor: groupColors[group] || '#cccccc',
                backgroundColor: `${groupColors[group] || '#cccccc'}20`,
                fill: false,
                borderWidth: 3,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: groupColors[group] || '#cccccc',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointHoverBackgroundColor: groupColors[group] || '#cccccc',
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 3
            };
        });

        const ctx = document.getElementById('mealsPerDayChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: datasets
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
                                return `${context.dataset.label}: ${context.parsed.y} meals`;
                            },
                            afterBody: function(context) {
                                const totalForDay = context.reduce((sum, item) => sum + item.parsed.y, 0);
                                return `Total for day: ${totalForDay} meals`;
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
        
        const totalMeals = data.reduce((sum, entry) => sum + entry.meal_count, 0);
        const groupStats = studyGroups.map(group => {
            const groupData = data.filter(d => d.study_group === group);
            const groupTotal = groupData.reduce((sum, entry) => sum + entry.meal_count, 0);
            return { group, total: groupTotal };
        });
        
        console.log(`📊 Meals Per Day Analytics:`);
        console.log(`   Total meals across all groups: ${totalMeals}`);
        groupStats.forEach(stat => {
            console.log(`   Group ${stat.group}: ${stat.total} meals`);
        });
        
    } catch (error) {
        console.error("Error rendering meals per day chart:", error);
    }
}

renderMealsPerDayChart();
