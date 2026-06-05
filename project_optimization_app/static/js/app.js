document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggle  = document.getElementById('sidebarToggle');

    if (!sidebar || !toggle) return;

    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    const open  = () => { sidebar.classList.add('sidebar-open');    overlay.classList.add('show'); };
    const close = () => { sidebar.classList.remove('sidebar-open'); overlay.classList.remove('show'); };

    toggle.addEventListener('click', () =>
        sidebar.classList.contains('sidebar-open') ? close() : open()
    );
    overlay.addEventListener('click', close);
});
