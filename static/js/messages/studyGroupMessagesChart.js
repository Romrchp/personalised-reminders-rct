async function fetchMessagesPerDayAndStudyGroup() {
    const response = await fetch("/messages/per-day-and-study-group");
    const data = await response.json();
    return data.study_groups;
}

async function renderStudyGroupMessagesChart() {
    const messagesData = await fetchMessagesPerDayAndStudyGroup();
    const studyGroupLabels = [];
    const datasets = [];
    const groupColors = {
        0: '#6c757d',
        1: '#17a2b8',
        2: '#28a745',
        3: '#7100b3'
    };

    Object.keys(messagesData).forEach(studyGroup => {
        const studyGroupData = messagesData[studyGroup];
        const studyGroupMessages = studyGroupData.map(entry => entry.user_count);
        const studyGroupDates = studyGroupData.map(entry => entry.date);

        studyGroupLabels.push(...studyGroupDates);
        datasets.push({
            label: `Study Group ${studyGroup}`,
            data: studyGroupMessages,
            borderColor: groupColors[studyGroup] || '#cccccc',
            backgroundColor: `${groupColors[studyGroup] || '#cccccc'}20`,
            fill: false,
            borderWidth: 3,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: groupColors[studyGroup] || '#cccccc',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointHoverBackgroundColor: groupColors[studyGroup] || '#cccccc',
            pointHoverBorderColor: '#ffffff',
            pointHoverBorderWidth: 3
        });
    });

    const uniqueLabels = [...new Set(studyGroupLabels)];

    const ctx = document.getElementById('studyGroupMessagesChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: uniqueLabels,
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

renderStudyGroupMessagesChart();