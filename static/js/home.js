document.addEventListener('DOMContentLoaded', function() {
    const authBtn = document.getElementById('authBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    // ฟังก์ชันตรวจสอบสถานะการเข้าสู่ระบบ
    function checkLoggedInStatus() {
        // แทนที่ด้วยการตรวจสอบสถานะการเข้าสู่ระบบจริงของคุณ
        // เช่น ตรวจสอบคุกกี้ หรือ localStorage
        return localStorage.getItem('user') !== null;
    }

    const isLoggedIn = checkLoggedInStatus();

    if (authBtn) { // ตรวจสอบว่า authBtn มีอยู่จริง
        if (isLoggedIn) {
            authBtn.textContent = 'Log Out';
            authBtn.classList.add('logout');
            authBtn.classList.remove('login');
            authBtn.addEventListener('click', function() {
                window.location.href = '/logout';
            });
        } else {
            authBtn.textContent = 'Log In';
            authBtn.classList.add('login');
            authBtn.classList.remove('logout');
            authBtn.addEventListener('click', function() {
                window.location.href = '/login-page';
            });
        }
    }

    if (logoutBtn) { // ตรวจสอบว่า logoutBtn มีอยู่จริง
        logoutBtn.addEventListener('click', function() {
            window.location.href = '/logout';
        });
    }
});