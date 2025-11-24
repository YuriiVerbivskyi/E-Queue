'use strict';

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');

    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        errorMessage.classList.add('d-none');
        successMessage.classList.add('d-none');

        const formData = {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        };

        try {
            const response = await fetch('/api/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);

                successMessage.textContent = 'Успішний вхід! Перенаправлення на головну...';
                successMessage.classList.remove('d-none');

                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                let errors = '';
                for (let key in data) {
                    errors += `${key}: ${data[key]}\n`;
                }
                errorMessage.textContent = errors;
                errorMessage.classList.remove('d-none');
            }
        } catch (err) {
            errorMessage.textContent = 'Помилка підключення до сервера';
            errorMessage.classList.remove('d-none');
        }
    });
});
