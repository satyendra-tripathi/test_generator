document.addEventListener("DOMContentLoaded", () => {
    const themeToggleBtn = document.getElementById("theme-toggle");
    const body = document.body;

    // Load saved theme from localStorage
    const currentTheme = localStorage.getItem("theme");
    if (currentTheme) {
        body.setAttribute("data-theme", currentTheme);
    }

    // Toggle theme
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            if (body.getAttribute("data-theme") === "dark") {
                body.removeAttribute("data-theme");
                localStorage.setItem("theme", "light");
            } else {
                body.setAttribute("data-theme", "dark");
                localStorage.setItem("theme", "dark");
            }
        });
    }
});
