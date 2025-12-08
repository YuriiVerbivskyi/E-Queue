let currentRoomId = null;
let queueRefreshInterval = null;

document.getElementById('createRoomForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const nameInput = document.getElementById('roomName');
    const name = nameInput.value.trim();

    if (!name) {
        alert('Введіть назву черги');
        return;
    }

    try {
        const res = await fetch('/create-room/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ name })
        });

        const data = await res.json();
        if (data.ok) {
            nameInput.value = '';
            location.reload();
        } else {
            alert('Помилка: ' + (data.message || 'Невідома помилка'));
        }
    } catch (err) {
        alert('Помилка мережі: ' + err);
    }
});

function openRoom(roomId, roomName) {
    currentRoomId = roomId;
    const modal = document.getElementById('roomModal');
    const titleEl = document.getElementById('modalRoomName');
    if (!modal || !titleEl) return;

    titleEl.textContent = roomName;
    modal.style.display = 'flex';
    loadQueueList(roomId);

    if (queueRefreshInterval) {
        clearInterval(queueRefreshInterval);
    }
    queueRefreshInterval = setInterval(() => {
        if (modal.style.display !== 'none') {
            loadQueueList(roomId);
        }
    }, 2000);
}

function closeRoom() {
    const modal = document.getElementById('roomModal');
    if (modal) {
        modal.style.display = 'none';
    }
    if (queueRefreshInterval) {
        clearInterval(queueRefreshInterval);
        queueRefreshInterval = null;
    }
}

async function loadQueueList(roomId) {
    const container = document.getElementById('queueList');
    if (!container) return;

    try {
        const res = await fetch(`/get-room-entries/?room_id=${encodeURIComponent(roomId)}`);
        if (!res.ok) throw new Error('Network error');

        const entries = await res.json();

        if (!Array.isArray(entries) || entries.length === 0) {
            container.innerHTML = '<p class="no-entries-message">Студентів немає</p>';
            return;
        }

        const html = entries.map((e, idx) => {
            const fullName = `${e.first_name || e.username} ${e.last_name || ''}`.trim();
            const username = e.username || '';
            const statusText = e.status === 'ready' ? '🔴 Ready' : '⏳ Waiting';
            const statusClass = e.status === 'ready' ? 'status-ready' : 'status-waiting';

            return `
                <div class="queue-entry-item">
                    <div class="entry-position">${idx + 1}</div>
                    <div class="entry-info">
                        <div class="entry-name">${fullName}</div>
                        <div class="entry-username">@${username}</div>
                    </div>
                    <span class="entry-status ${statusClass}">${statusText}</span>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
    } catch (err) {
        console.error('Error loading queue:', err);
        container.innerHTML = '<p class="error-message">Помилка завантаження</p>';
    }
}

async function nextStudent() {
    if (!currentRoomId) return;

    try {
        const res = await fetch('/next-student-in-room/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ room_id: currentRoomId })
        });

        const data = await res.json();
        if (data.ok) {
            alert(`✅ ${data.current_student} - наступний!`);
            loadQueueList(currentRoomId);
        } else {
            alert('❌ ' + (data.message || 'Невідома помилка'));
        }
    } catch (err) {
        alert('Помилка: ' + err);
    }
}

async function joinRoom(roomId, roomName) {
    try {
        const res = await fetch('/join-room/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ room_id: roomId })
        });

        const data = await res.json();
        if (data.ok) {
            showStudentQueue(roomName, data.position);
        } else {
            alert('❌ ' + (data.message || 'Невідома помилка'));
        }
    } catch (err) {
        alert('Помилка: ' + err);
    }
}

function showStudentQueue(roomName, position) {
    const existing = document.getElementById('studentQueueModal');
    if (existing) existing.remove();

    const modal = document.createElement('div');
    modal.id = 'studentQueueModal';
    modal.className = 'student-queue-modal-overlay';
    modal.innerHTML = `
        <div class="register-card student-queue-modal-card">
            <h2 class="modal-success-title">✅ Успішно!</h2>
            <p class="modal-room-name">${roomName}</p>
            <h1 class="modal-position-number">${position}</h1>
            <p class="modal-position-label">Ваш номер у черзі</p>
            <button class="btn btn-primary w-100 modal-close-button" onclick="document.getElementById('studentQueueModal')?.remove()">Закрити</button>
        </div>
    `;
    document.body.appendChild(modal);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
