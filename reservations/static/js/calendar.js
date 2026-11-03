/**
 * Interactive Availability Calendar JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('calendarDateInput');
    const venueSelect = document.getElementById('calendarVenueSelect');
    const form = document.getElementById('calendarFilterForm');

    const prevDayBtn = document.getElementById('prevDayBtn');
    const nextDayBtn = document.getElementById('nextDayBtn');
    const todayBtn = document.getElementById('todayBtn');

    if (dateInput && form) {
        if (prevDayBtn) {
            prevDayBtn.addEventListener('click', () => {
                const currentDate = new Date(dateInput.value || new Date());
                currentDate.setDate(currentDate.getDate() - 1);
                dateInput.value = currentDate.toISOString().split('T')[0];
                form.submit();
            });
        }

        if (nextDayBtn) {
            nextDayBtn.addEventListener('click', () => {
                const currentDate = new Date(dateInput.value || new Date());
                currentDate.setDate(currentDate.getDate() + 1);
                dateInput.value = currentDate.toISOString().split('T')[0];
                form.submit();
            });
        }

        if (todayBtn) {
            todayBtn.addEventListener('click', () => {
                const today = new Date();
                dateInput.value = today.toISOString().split('T')[0];
                form.submit();
            });
        }
    }
});
