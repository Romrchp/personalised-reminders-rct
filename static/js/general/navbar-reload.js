document.addEventListener('DOMContentLoaded', function() {
    const navbarLinks = document.querySelectorAll('.navbar-menu-item');
    
    navbarLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const linkPath = new URL(this.href).pathname;
            const currentPath = window.location.pathname;
            
            if (linkPath === currentPath) {
                e.preventDefault();
                window.location.reload();
            }
        });
    });
});