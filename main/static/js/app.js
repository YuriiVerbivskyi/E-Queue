'use strict';

document.addEventListener('DOMContentLoaded', async function() {
    console.log('E-Queue loaded');

    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const url = this.getAttribute('href');
            if (url && url !== '/') {
                console.log('Navigating to:', url);
            }
        });
    });

    const navAuth = document.getElementById("nav-auth");
    const token = localStorage.getItem("access_token");

    if (!token) return;

    try {
        const response = await fetch("/api/profile/", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!response.ok){
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");

            if (window.location.pathname === '/profile/') {
                window.location.href = "/login/"
            }
            return;
        }

        const data = await response.json();

        console.log("SUCCESS: Displaying username:", data.username);

        const username = data.username;

        navAuth.innerHTML = `
            <div class="dropdown">
                <a class="nav-link dropdown-toggle fw-bold" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                    👤 ${username}
                </a>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarDropdown">
                    <li><a class="dropdown-item" href="/profile/">Профіль</a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item" href="#" id="logout-link">Вихід</a></li>
                </ul>
            </div>
        `;

        document.getElementById("logout-link").addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });

        const inputUsername = document.getElementById('profile-username');
        const inputEmail = document.getElementById('profile-email');
        const inputRole = document.getElementById('profile-role');
        const statusDiv = document.getElementById('profile-status');
        const logoutBtn = document.getElementById('logoutBtn');

        if (inputUsername) {
            inputUsername.value = data.username;
            inputEmail.value = data.email;
            inputRole.value = data.role || 'Користувач';
            if (statusDiv) statusDiv.style.display = 'none';

            if (logoutBtn) {
                logoutBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    handleLogout();
                });
            }
        }

    } catch (e) {
        console.error("Auth check failed (Error in JSON parsing or DOM update):", e);
        if (profileInfo) {
             profileInfo.innerHTML = `<p class="text-danger">Помилка завантаження даних.</p>`;
        }
    }
});
function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/";
}


