document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var modal = document.getElementById("eventModal");
    var btn = document.getElementById("openModalBtn");
    var span = document.getElementsByClassName("close-btn")[0];
    var form = document.getElementById("addEventForm");

    if (!calendarEl) return;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'uk',
        firstDay: 1,
        fixedWeekCount: false,
        showNonCurrentDates: false,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
        },
        events: '/api/calendar/events/',
        eventTimeFormat: {
            hour: '2-digit', minute: '2-digit', meridiem: false
        },
        eventClick: function(info) {
            info.jsEvent.preventDefault();
            if (info.event.url) {
                window.open(info.event.url);
            }
        }
    });

    calendar.render();

    if (btn) {
        btn.onclick = function() { modal.style.display = "block"; }
        span.onclick = function() { modal.style.display = "none"; }
        window.onclick = function(event) {
            if (event.target == modal) modal.style.display = "none";
        }

        form.onsubmit = function(e) {
            e.preventDefault();

            var title = document.getElementById("eventTitle").value;
            var start = document.getElementById("eventStart").value;

            var year = new Date(start).getFullYear();
            if (year > 9999) {
                alert("Рік не може бути більше 9999!");
                return;
            }

            var submitBtn = form.querySelector('button[type="submit"]');
            var originalText = submitBtn.innerText;
            submitBtn.innerText = "Збереження...";
            submitBtn.disabled = true;

            fetch('/api/calendar/add/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title, start: start })
            })
            .then(response => response.json())
            .then(data => {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;

                if (data.ok) {
                    calendar.refetchEvents();
                    modal.style.display = "none";
                    form.reset();
                } else if (data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    alert('Помилка: ' + data.message);
                }
            })
            .catch(error => {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
                console.error(error);
                alert('Помилка з\'єднання з сервером');
            });
        }
    }
});