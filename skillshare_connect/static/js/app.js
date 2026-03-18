/* =========================
   JS - FORM TOGGLE & THEME
========================= */

function switchAuth(type) {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const loginTab = document.getElementById('loginTab');
    const signupTab = document.getElementById('signupTab');
    
    if (type === 'login') {
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
        loginTab.classList.add('bg-white', 'text-blue-600', 'shadow-sm');
        loginTab.classList.remove('text-gray-600');
        signupTab.classList.remove('bg-white', 'text-blue-600', 'shadow-sm');
        signupTab.classList.add('text-gray-600');
    } else {
        signupForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
        signupTab.classList.add('bg-white', 'text-blue-600', 'shadow-sm');
        signupTab.classList.remove('text-gray-600');
        loginTab.classList.remove('bg-white', 'text-blue-600', 'shadow-sm');
        loginTab.classList.add('text-gray-600');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.bg-white');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'transform 0.3s ease';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    const ratingCard = document.querySelector('.rating-card');
    if (ratingCard) {
        ratingCard.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
            this.style.transition = 'transform 0.3s ease';
        });
        ratingCard.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    }
});

// THEME TOGGLE LOGIC
document.addEventListener("DOMContentLoaded", function () {
    const themeToggleBtn = document.getElementById("theme-toggle");

    function applyTheme(theme) {
        if (theme === "dark") {
            document.documentElement.classList.add("dark-theme");
            document.documentElement.classList.remove("light-theme");
            if (themeToggleBtn) themeToggleBtn.innerText = "☀️ Light";
        } else {
            document.documentElement.classList.remove("dark-theme");
            document.documentElement.classList.add("light-theme");
            if (themeToggleBtn) themeToggleBtn.innerText = "🌙 Dark";
        }
    }

    const savedTheme = localStorage.getItem("theme") || "light";
    applyTheme(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const newTheme = document.documentElement.classList.contains("dark-theme") ? "light" : "dark";
            localStorage.setItem("theme", newTheme);
            applyTheme(newTheme);
        });
    }
});

