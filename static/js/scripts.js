// See if that works for smooth scrolling ?
document.querySelectorAll('.navbar a').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href').substring(1); // remove '#' from href
        const targetElement = document.getElementById(targetId);
        
        targetElement.scrollIntoView({ behavior: 'smooth' });
    });
});


function toggleDetails(id) {
    const details = document.getElementById(id);
    if (details.style.display === "block") {
        details.style.display = "none"; 
    } else {
        details.style.display = "block"; 
    }
}

document.querySelector(".collapsible").addEventListener("click", function () {
        var content = document.querySelector(".content");
        var icon = document.querySelector(".icon");
        
        content.classList.toggle("show");
        icon.classList.toggle("rotate");
        
        this.textContent = content.classList.contains("show") ? "Hide Users Table & Filters" : "Show Users Table & Filters";
        this.appendChild(icon);
    });

