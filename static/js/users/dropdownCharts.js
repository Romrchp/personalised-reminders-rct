document.addEventListener('DOMContentLoaded', function() {
    const dropdownBtn = document.getElementById('groupSelector');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const selectedGroupText = document.getElementById('selectedGroupText');
    const selectedGroupInfo = document.getElementById('selectedGroupInfo');
    const chartsContainer = document.getElementById('chartsContainer');
    

    const groupData = window.groupData

    // Store current chart instances for cleanup
    let currentCharts = {};

    // Toggle dropdown
    dropdownBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdownBtn.classList.toggle('active');
        dropdownMenu.classList.toggle('show');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function() {
        dropdownBtn.classList.remove('active');
        dropdownMenu.classList.remove('show');
    });

    // Handle dropdown item selection
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function() {
            const selectedGroup = this.dataset.group;
            const selectedText = this.textContent.trim();
            
            // Update button text
            selectedGroupText.textContent = selectedText;
            
            // Update selected state
            document.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
            
            // Close dropdown
            dropdownBtn.classList.remove('active');
            dropdownMenu.classList.remove('show');
            
            // Update content based on selection
            updateContent(selectedGroup);
        });
    });

    function updateContent(group) {
        chartsContainer.classList.add('loading');
        
        // Destroy existing charts to prevent memory leaks
        destroyCurrentCharts();
        updateChartCanvases(group);
        
        if (group === 'all') {
            // Hide group info for "All Groups"
            selectedGroupInfo.style.display = 'none';
            // Load charts for all groups
            loadAllGroupsCharts();
        } else {
            // Show and update group info
            selectedGroupInfo.style.display = 'block';
            selectedGroupInfo.dataset.group = group;
            updateGroupInfo(group);
            // Load charts for specific group
            loadGroupCharts(group);
        }
        
        setTimeout(() => {
            chartsContainer.classList.remove('loading');
        }, 300);
    }

    function updateGroupInfo(group) {
        const data = groupData[group];
        if (!data) return;
        
        document.getElementById('selectedGroupName').textContent = data.name;
        document.getElementById('selectedGroupDesc').textContent = data.description;
        document.getElementById('selectedGroupCount').textContent = data.count;
        
        // Update icons
        const iconsContainer = document.getElementById('selectedGroupIcons');
        iconsContainer.innerHTML = data.icons.map(iconClass => 
            `<i class="${iconClass}"></i>`
        ).join('');
    }

    function destroyCurrentCharts() {
        // Destroy all current chart instances
        Object.values(currentCharts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        currentCharts = {};
    }

    async function loadAllGroupsCharts() {
        try {
            console.log('Loading all groups charts');
            
            // Clear any group-specific chart canvases and create generic ones
            updateChartCanvases('all');
            
            // Render charts for all users (no group filter)
            await Promise.all([
                renderGenderChart('all'),
                renderAgeChart('all'),
                renderLanguageChart('all'),
                renderActiveInactiveChart('all')
            ]);
            
        } catch (error) {
            console.error('Error loading all groups charts:', error);
        }
    }

    async function loadGroupCharts(group) {
        try {
            console.log(`Loading charts for group ${group}`);
            
            // Update chart canvases for specific group
            updateChartCanvases(group);
            
            // Render charts for specific group
            await Promise.all([
                renderGenderChart(group),
                renderAgeChart(group),
                renderLanguageChart(group),
                renderActiveInactiveChart(group)
            ]);
            
        } catch (error) {
            console.error(`Error loading charts for group ${group}:`, error);
        }
    }

    function updateChartCanvases(groupId) {
        // Update canvas IDs based on selection
        const canvases = document.querySelectorAll('#chartsContainer canvas');
        
        canvases.forEach(canvas => {
            const baseId = canvas.id.replace(/Group\d+$/, ''); // Remove existing group suffix
            if (groupId === 'all') {
                canvas.id = baseId; // Use base ID for all groups
            } else {
                canvas.id = `${baseId}Group${groupId}`; // Add group suffix
            }
        });
    }

    // Chart rendering functions that integrate with your existing code
    async function renderGenderChart(groupId) {
        try {
            const url = groupId === 'all' ? '/users/gender-distrib' : `/users/gender-distrib?study_group=${groupId}`;
            const chartId = groupId === 'all' ? 'genderChart' : `genderChartGroup${groupId}`;
            
            const response = await fetch(url);
            const genderData = await response.json();

            const canvas = document.getElementById(chartId);
            if (!canvas) {
                console.warn(`Canvas with ID ${chartId} not found`);
                return;
            }

            currentCharts[chartId] = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(genderData),
                    datasets: [{
                        data: Object.values(genderData),
                        backgroundColor: ['#cf6400', '#f7c048', '#ffce56'],
                        borderColor: ['#cf6400', '#f7c048', '#ffce56'],
                        borderWidth: 3,
                        hoverBorderWidth: 4,
                        hoverBorderColor: '#ffffff',
                        hoverBackgroundColor: ['#b8560a', '#e6aa3d', '#e6b84a']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: { family: 'Arial', size: 14, color: '#2c3e50' },
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
                                title: () => 'Gender Distribution',
                                label: (context) => {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    animation: { duration: 1200, easing: 'easeInOutQuart', animateRotate: true, animateScale: true },
                    cutout: '50%'
                }
            });
        } catch (error) {
            console.error('Error rendering gender chart:', error);
        }
    }

    async function renderAgeChart(groupId) {
        try {
            const url = groupId === 'all' ? '/users/age-distrib' : `/users/age-distrib?study_group=${groupId}`;
            const chartId = groupId === 'all' ? 'ageChart' : `ageChartGroup${groupId}`;
            
            const response = await fetch(url);
            const ageData = await response.json();

            const canvas = document.getElementById(chartId);
            if (!canvas) {
                console.warn(`Canvas with ID ${chartId} not found`);
                return;
            }

            currentCharts[chartId] = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: Object.keys(ageData),
                    datasets: [{
                        label: groupId === 'all' ? 'Age Distribution - All Users' : `Age Distribution - Group ${groupId}`,
                        data: Object.values(ageData),
                        backgroundColor: '#de7012',
                        borderColor: '#de7012',
                        borderWidth: 2,
                        borderRadius: 4,
                        borderSkipped: false,
                        hoverBackgroundColor: '#c55a0a',
                        hoverBorderColor: '#c55a0a',
                        hoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    scales: {
                        x: {
                            title: { display: true, text: 'Age Range', font: { family: 'Arial', size: 16, weight: 'bold', color: '#2c3e50' } },
                            grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false },
                            ticks: { color: '#2c3e50', font: { size: 12 } }
                        },
                        y: {
                            title: { display: true, text: 'Number of Users', font: { family: 'Arial', size: 16, weight: 'bold', color: '#2c3e50' } },
                            beginAtZero: true,
                            grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false },
                            ticks: { color: '#2c3e50', font: { size: 12 } }
                        }
                    },
                    plugins: {
                        legend: { labels: { font: { family: 'Arial', size: 14, color: '#2c3e50' }, usePointStyle: true, pointStyle: 'circle' } },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: 'white',
                            bodyColor: 'white',
                            cornerRadius: 6,
                            callbacks: {
                                title: (context) => `Age Range: ${context[0].label}`,
                                label: (context) => `Users: ${context.parsed.y}`
                            }
                        }
                    },
                    animation: { duration: 1200, easing: 'easeInOutQuart' }
                }
            });
        } catch (error) {
            console.error('Error rendering age chart:', error);
        }
    }

    async function renderLanguageChart(groupId) {
        try {
            const url = groupId === 'all' ? '/users/language-distrib' : `/users/language-distrib?study_group=${groupId}`;
            const chartId = groupId === 'all' ? 'languageChart' : `languageChartGroup${groupId}`;
            
            const response = await fetch(url);
            const languageData = await response.json();

            const canvas = document.getElementById(chartId);
            if (!canvas) {
                console.warn(`Canvas with ID ${chartId} not found`);
                return;
            }

            currentCharts[chartId] = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(languageData),
                    datasets: [{
                        data: Object.values(languageData),
                        backgroundColor: ['#4caf50', '#ff9800', '#2196f3', '#9c27b0'],
                        borderColor: ['#4caf50', '#ff9800', '#2196f3', '#9c27b0'],
                        borderWidth: 3,
                        hoverBorderWidth: 4,
                        hoverBorderColor: '#ffffff',
                        hoverBackgroundColor: ['#45a049', '#e68900', '#1976d2', '#7b1fa2']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { font: { family: 'Arial', size: 14, color: '#2c3e50' }, usePointStyle: true, pointStyle: 'circle' }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: 'white',
                            bodyColor: 'white',
                            cornerRadius: 6,
                            callbacks: {
                                title: () => 'Language Distribution',
                                label: (context) => {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    animation: { duration: 1200, easing: 'easeInOutQuart', animateRotate: true, animateScale: true },
                    cutout: '50%'
                }
            });
        } catch (error) {
            console.error('Error rendering language chart:', error);
        }
    }

    async function renderActiveInactiveChart(groupId) {
        try {
            const url = '/users/active-inactive-users';
            const response = await fetch(url);
            const data = await response.json();

            let chartData;
            let chartId = 'activeInactiveUsersChart';

            if (groupId === 'all') {
                // Show all groups
                const labels = Object.keys(data).map(group => `Group ${group}`);
                const activeUsers = Object.values(data).map(pair => pair[0]);
                const inactiveUsers = Object.values(data).map(pair => pair[1]);
                const totals = activeUsers.map((active, i) => active + inactiveUsers[i]);
                const activePercent = activeUsers.map((count, i) => totals[i] ? (count / totals[i]) * 100 : 0);
                const inactivePercent = inactiveUsers.map((count, i) => totals[i] ? (count / totals[i]) * 100 : 0);

                chartData = {
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
                };
            } else {
                // Show specific group
                chartId = `activeInactiveUsersChartGroup${groupId}`;
                const groupData = data[groupId];
                if (!groupData) return;

                const [active, inactive] = groupData;
                const total = active + inactive;
                const activePercent = total ? (active / total) * 100 : 0;
                const inactivePercent = total ? (inactive / total) * 100 : 0;

                chartData = {
                    labels: [`Group ${groupId}`],
                    datasets: [
                        {
                            label: '"Has started" Users',
                            data: [activePercent],
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
                            data: [inactivePercent],
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
                };
            }

            const canvas = document.getElementById(chartId);
            if (!canvas) {
                console.warn(`Canvas with ID ${chartId} not found`);
                return;
            }

            currentCharts[chartId] = new Chart(canvas, {
                type: 'bar',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    scales: {
                        x: {
                            stacked: true,
                            title: { display: true, text: 'Study Group', font: { family: 'Arial', size: 16, weight: 'bold', color: '#2c3e50' } },
                            grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false },
                            ticks: { color: '#2c3e50', font: { size: 12 } }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            max: 100,
                            title: { display: true, text: 'Percentage of Users (%)', font: { family: 'Arial', size: 16, weight: 'bold', color: '#2c3e50' } },
                            ticks: {
                                callback: (value) => value + '%',
                                color: '#2c3e50',
                                font: { size: 12 }
                            },
                            grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false }
                        }
                    },
                    plugins: {
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: 'white',
                            bodyColor: 'white',
                            cornerRadius: 6,
                            callbacks: {
                                title: (context) => `${context[0].label}`,
                                label: (context) => {
                                    const datasetLabel = context.dataset.label || '';
                                    const percent = context.parsed.y.toFixed(2);
                                    const index = context.dataIndex;
                                    const isActive = context.datasetIndex === 0;
                                    const absolute = groupId === 'all' 
                                        ? (isActive ? Object.values(data).map(pair => pair[0])[index] : Object.values(data).map(pair => pair[1])[index])
                                        : (isActive ? data[groupId][0] : data[groupId][1]);
                                    return `${datasetLabel}: ${absolute} (${percent}%)`;
                                },
                                afterBody: (context) => {
                                    const index = context[0].dataIndex;
                                    const total = groupId === 'all'
                                        ? Object.values(data).map(pair => pair[0] + pair[1])[index]
                                        : data[groupId][0] + data[groupId][1];
                                    return `Total users: ${total}`;
                                }
                            }
                        },
                        legend: { labels: { font: { family: 'Arial', size: 14, color: '#2c3e50' }, usePointStyle: true, pointStyle: 'circle' } }
                    },
                    animation: { duration: 1200, easing: 'easeInOutQuart' }
                }
            });
        } catch (error) {
            console.error('Error rendering active/inactive chart:', error);
        }
    }

    setTimeout(() => {
        updateContent('all');
    }, 100);
});