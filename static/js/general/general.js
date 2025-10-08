document.addEventListener('DOMContentLoaded', function () {
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const confirmed = confirm('Are you sure you want to remove this meal?');
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const deleteForms = document.querySelectorAll('.confirm-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const confirmed = confirm('Are you sure you want to send a welcome message to this user ?');
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const deleteForms = document.querySelectorAll('.participation-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const confirmed = confirm('Are you sure you to update the participation status of this user?');
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});



document.addEventListener('DOMContentLoaded', () => {
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');

    navbarToggle.addEventListener('click', () => {
        navbarToggle.classList.toggle('active');
        navbarMenu.classList.toggle('active');
    });
});

function updateLiveTimer() {
    const timerElement = document.getElementById('live-timer');
    if (!timerElement) return;
    
    const startDate = timerElement.getAttribute('data-start-date');
    if (!startDate) return;
    
    const start = new Date(startDate);
    const now = new Date();
    const diffMs = now - start;
    
    if (diffMs < 0) {
        timerElement.textContent = 'Not started';
        return;
    }
    
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    let duration = '';
    if (days > 0) {
        duration += `${days}d `;
    }
    if (hours > 0 || days > 0) {
        duration += `${hours}h `;
    }
    duration += `${minutes}m`;
    
    timerElement.textContent = duration;
}

document.addEventListener('DOMContentLoaded', function() {
    updateLiveTimer();
    setInterval(updateLiveTimer, 60000);
});

