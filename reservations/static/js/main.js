// LPU Campus Venue Reservation Portal — main.js

document.addEventListener('DOMContentLoaded', function () {

    // ── Dark/Light Theme Toggle ───────────────────────────────────────────
    const themeBtn  = document.getElementById('themeToggleBtn');
    const htmlEl    = document.documentElement;
    const savedTheme = localStorage.getItem('lpu-theme') || 'light';
    htmlEl.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', function () {
            const current = htmlEl.getAttribute('data-theme');
            const next    = current === 'dark' ? 'light' : 'dark';
            htmlEl.setAttribute('data-theme', next);
            localStorage.setItem('lpu-theme', next);
            updateThemeIcon(next);
        });
    }
    function updateThemeIcon(theme) {
        if (!themeBtn) return;
        themeBtn.innerHTML = theme === 'dark'
            ? '<i class="fa-solid fa-sun"></i>'
            : '<i class="fa-solid fa-moon"></i>';
    }

    // ── Mobile Nav Toggle ─────────────────────────────────────────────────
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const navMenu   = document.getElementById('navMenu');
    if (mobileBtn && navMenu) {
        mobileBtn.addEventListener('click', function () {
            navMenu.classList.toggle('open');
        });
        document.addEventListener('click', function (e) {
            if (!navMenu.contains(e.target) && !mobileBtn.contains(e.target)) {
                navMenu.classList.remove('open');
            }
        });
    }

    // ── Auto-dismiss Toasts ───────────────────────────────────────────────
    document.querySelectorAll('.toast').forEach(function (toast) {
        setTimeout(function () {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(30px)';
            toast.style.transition = 'all .4s ease';
            setTimeout(function () { toast.remove(); }, 400);
        }, 5000);
    });

    // ── Booking Form: show capacity hint on venue change ──────────────────
    const venueSelect   = document.getElementById('id_venue');
    const attendInput   = document.getElementById('id_attendance');
    const capacityHint  = document.getElementById('capacityHint');

    if (venueSelect && attendInput && capacityHint) {
        venueSelect.addEventListener('change', updateCapacityHint);
        attendInput.addEventListener('input',  updateCapacityHint);
        updateCapacityHint();
    }
    function updateCapacityHint() {
        const option = venueSelect ? venueSelect.options[venueSelect.selectedIndex] : null;
        if (!option) return;
        const cap = parseInt(option.getAttribute('data-capacity') || '0', 10);
        const att = parseInt(attendInput ? attendInput.value : '0', 10);
        if (cap && capacityHint) {
            if (att > cap) {
                capacityHint.textContent = '⚠ Attendance exceeds venue capacity (~' + cap + ')';
                capacityHint.style.color = 'var(--danger)';
            } else if (att > 0) {
                const pct = Math.round((att / cap) * 100);
                capacityHint.textContent = '✔ ' + pct + '% of ~' + cap + ' capacity used';
                capacityHint.style.color = pct > 85 ? 'var(--warning)' : 'var(--success)';
            } else {
                capacityHint.textContent = 'Venue capacity: ~' + cap + ' persons';
                capacityHint.style.color = 'var(--text-muted)';
            }
        }
    }
});
