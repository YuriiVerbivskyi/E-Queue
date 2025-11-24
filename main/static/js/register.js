'use strict';

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registerForm');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');

    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            errorMessage.classList.add('d-none');
            successMessage.classList.add('d-none');

            const formData = {
                username: document.getElementById('username').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                password2: document.getElementById('password2').value
            };

            try {
                const response = await fetch('/api/register/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (response.ok) {
                    successMessage.textContent = 'Реєстрація успішна! Перенаправлення на логін...';
                    successMessage.classList.remove('d-none');

                    setTimeout(() => {
                        window.location.href = '/login/';
                    }, 1500);
                } else {
                    let errors = '';
                    for (let key in data) {
                        errors += `${key}: ${data[key]}\n`;
                    }
                    errorMessage.textContent = errors;
                    errorMessage.classList.remove('d-none');
                }
            } catch (error) {
                errorMessage.textContent = 'Помилка підключення до сервера';
                errorMessage.classList.remove('d-none');
            }
        });
    }
});
