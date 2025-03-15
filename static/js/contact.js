// Add this JavaScript to your script
document.addEventListener('DOMContentLoaded', function() {
    // Create modal elements
    const modalHTML = `
        <div id="custom-modal" class="custom-modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Log Out?</h3>
            <span class="close-modal">&times;</span>
        </div>
        <div class="modal-body">
            <p>Are you sure you want to log out?</p>
        </div>
        <div class="modal-footer">
            <button id="cancel-logout" class="btn cancel-btn">Cancel</button>
            <button id="confirm-logout" class="btn confirm-btn">
                <i class="fas fa-sign-out-alt"></i> Yes, Log Out
            </button>
        </div>
    </div>
</div>
    `;
    
    // Append modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Get modal elements
    const modal = document.getElementById('custom-modal');
    const closeBtn = document.querySelector('.close-modal');
    const cancelBtn = document.getElementById('cancel-logout');
    const confirmBtn = document.getElementById('confirm-logout');
    
    // Get logout link
    const logoutLink = document.getElementById('logout-link');
    
    // Show modal when logout is clicked
    if (logoutLink) {
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default link behavior
            modal.style.display = 'flex';
            // Add class for animation
            setTimeout(() => {
                modal.querySelector('.modal-content').classList.add('show');
            }, 10);
        });
    }
    
    // Close modal when X is clicked
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            closeModal();
        });
    }
    
    // Close modal when Cancel is clicked
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            closeModal();
        });
    }
    
    // Logout when Confirm is clicked
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            // Add loading state
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
            confirmBtn.disabled = true;
            
            // Redirect after a short delay to show loading state
            setTimeout(() => {
                window.location.href = '/logout';
            }, 800);
        });
    }
    
    // Close when clicking outside modal
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });
    
    // Function to close modal with animation
    function closeModal() {
        modal.querySelector('.modal-content').classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
    // User profile display logic
    const logoElement = document.querySelector('.logo');
    const userProfileNav = document.getElementById('user-profile-nav');
    const profileImg = document.getElementById('nav-profile-image');
    
    // Check if user is logged in by looking for the element with the username
    const usernameElement = document.getElementById('nav-username');
    const username = usernameElement ? usernameElement.textContent.trim() : '';

    const isLoggedIn = username && username !== 'None' && username !== '{{ username }}';
    
    if (isLoggedIn) {
        // If logged in, hide the logo and show the user profile
        logoElement.style.display = 'none';
        userProfileNav.style.display = 'flex';
        
        // Fix the profile image path
        // First try to load from the API if possible
        fetch('/api/user-profile')
            .then(response => {
                if (response.ok) return response.json();
                throw new Error('Failed to fetch profile data');
            })
            .then(data => {
                if (data.profile_image) {
                    profileImg.src = data.profile_image;
                }
            })
            .catch(error => {
                console.error('Error loading profile:', error);
                // Fallback to a known working placeholder
                profileImg.src = "/static/uploads/profile_images/avatar-placeholder.jpg";
            });
    } else {
        // If not logged in, show the logo and hide the user profile
        logoElement.style.display = 'block';
        userProfileNav.style.display = 'none';
    }
});