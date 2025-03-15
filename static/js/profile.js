document.addEventListener('DOMContentLoaded', function() {
    const personalInfoForm = document.getElementById('personal-info');
    if (personalInfoForm) {
        personalInfoForm.addEventListener('wheel', function(e) {
            // Prevent the default scroll behavior
            e.preventDefault();
            e.stopPropagation();
        }, { passive: false });
    }
    
    // Load user data from API
    loadUserData();
    
    // Setup menu tab switching
    const menuItems = document.querySelectorAll('.profile-menu li');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            menuItems.forEach(menuItem => menuItem.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            // Hide all sections
            const sections = document.querySelectorAll('.profile-section');
            sections.forEach(section => section.classList.remove('active'));
            
            // Show selected section
            const sectionId = this.getAttribute('data-section');
            document.getElementById(sectionId).classList.add('active');
        });
    });
    
    // Setup password toggle visibility
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const passwordInput = this.previousElementSibling;
            
            // Toggle password visibility
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            } else {
                passwordInput.type = 'password';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            }
        });
    });
    
    // Password strength meter
    const newPasswordInput = document.getElementById('new-password');
    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', updatePasswordStrength);
    }
    
    // Form submissions - connect to our new API endpoints
    setupFormSubmission('personal-info-form', '/api/update-profile', 'Profile information updated successfully!');
    setupFormSubmission('security-form', '/api/update-password', 'Password updated successfully!');
    setupFormSubmission('preferences-form', '/api/update-preferences', 'Preferences saved successfully!');
    
    // Profile image upload handling
    const profileAvatar = document.querySelector('.profile-avatar');
    if (profileAvatar) {
        profileAvatar.addEventListener('click', function() {
            // Create hidden file input
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            fileInput.style.display = 'none';
            
            fileInput.addEventListener('change', function(e) {
                if (e.target.files && e.target.files[0]) {
                    const file = e.target.files[0];
                    const reader = new FileReader();
                    
                    reader.onload = function(event) {
                        // Show preview immediately for better UX
                        document.getElementById('profile-image').src = event.target.result;
                        
                        // Upload to server
                        uploadProfileImage(file);
                    };
                    
                    reader.readAsDataURL(file);
                }
            });
            
            document.body.appendChild(fileInput);
            fileInput.click();
            document.body.removeChild(fileInput);
        });
    }
    
    // Setup logout modal
    setupLogoutModal();
    
    // Success modal handling
    setupSuccessModal();
});

// Function to load user data from API
async function loadUserData() {
    try {
        const response = await fetch('/api/user-profile');
        
        if (!response.ok) {
            throw new Error('Failed to load user data');
        }
        
        const userData = await response.json();
        
        // Fill form fields with user data
        if (document.getElementById('full-name')) {
            document.getElementById('full-name').value = userData.full_name;
        }
        if (document.getElementById('email')) {
            document.getElementById('email').value = userData.email;
        }
        if (document.getElementById('phone')) {
            document.getElementById('phone').value = userData.phone_number;
        }
        if (document.getElementById('gender')) {
            const genderSelect = document.getElementById('gender');
            const genderValue = userData.gender.toLowerCase();
            
            const genderOptions = genderSelect.options;
            let valueExists = false;
            
            for (let i = 0; i < genderOptions.length; i++) {
                if (genderOptions[i].value === genderValue) {
                    valueExists = true;
                    break;
                }
            }
            
            if (valueExists) {
                genderSelect.value = genderValue;
            } else {
                console.log('Gender value from API not found in dropdown options:', genderValue);
            }
        }
        
        // Set profile image
        if (userData.profile_image && document.getElementById('profile-image')) {
            document.getElementById('profile-image').src = userData.profile_image;
        }

        if (userData.profile_image) {
            const navProfileImage = document.getElementById('nav-profile-image');
            if (navProfileImage) {
                navProfileImage.src = userData.profile_image;
            }
        }
        
        // Set preferences
        if (userData.preferences) {
            if (document.querySelector('input[name="email_notifications"]')) {
                document.querySelector('input[name="email_notifications"]').checked = userData.preferences.email_notifications;
            }
            if (document.querySelector('input[name="dark_mode"]')) {
                document.querySelector('input[name="dark_mode"]').checked = userData.preferences.dark_mode;
            }
            if (document.getElementById('language')) {
                document.getElementById('language').value = userData.preferences.language;
            }
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        // Optionally show error message to user
    }
}

// Function to handle form submissions
function setupFormSubmission(formId, endpoint, successMessage) {
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Create form data
            const formData = new FormData(form);
            
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData
                });
                
                // Handle response
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Something went wrong');
                }
                
                // Show success message
                showSuccessModal(successMessage);
            } catch (error) {
                console.error('Error submitting form:', error);
                showSuccessModal('Error: ' + error.message, 'error');
            } finally {
                // Reset button state
                submitBtn.innerHTML = originalBtnText;
                submitBtn.disabled = false;
            }
        });
    }
}

// Function to upload profile image
async function uploadProfileImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload-profile-image', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to upload image');
        }
        
        const data = await response.json();
        
        // Update image src with the url returned from server
        if (data.image_url) {
            document.getElementById('profile-image').src = data.image_url;
        }
        
        // Show success message
        showSuccessModal('Profile picture updated successfully!');
    } catch (error) {
        console.error('Error uploading profile image:', error);
        showSuccessModal('Error: ' + error.message, 'error');
        
        // Reset to placeholder if upload failed
        document.getElementById('profile-image').src = '/static/images/avatar-placeholder.jpg';
    }
}

// Function to update password strength meter
function updatePasswordStrength() {
    const password = document.getElementById('new-password').value;
    const strengthBar = document.querySelector('.strength-bar');
    const strengthText = document.querySelector('.strength-text');
    
    // Password strength criteria
    const hasLowerCase = /[a-z]/.test(password);
    const hasUpperCase = /[A-Z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChars = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    const isLongEnough = password.length >= 8;
    
    // Calculate strength
    let strength = 0;
    if (hasLowerCase) strength += 1;
    if (hasUpperCase) strength += 1;
    if (hasNumbers) strength += 1;
    if (hasSpecialChars) strength += 1;
    if (isLongEnough) strength += 1;
    
    // Update UI based on strength
    let percentage = (strength / 5) * 100;
    let color, text;
    
    if (password === '') {
        percentage = 0;
        color = '#e0e0e0';
        text = '';
    } else if (percentage <= 20) {
        color = '#ff4d4d';
        text = 'Very Weak';
    } else if (percentage <= 40) {
        color = '#ff9933';
        text = 'Weak';
    } else if (percentage <= 60) {
        color = '#ffcc00';
        text = 'Fair';
    } else if (percentage <= 80) {
        color = '#99cc33';
        text = 'Good';
    } else {
        color = '#33cc33';
        text = 'Strong';
    }
    
    strengthBar.style.width = `${percentage}%`;
    strengthBar.style.backgroundColor = color;
    strengthText.textContent = text;
}

// Setup success modal
function setupSuccessModal() {
    const modal = document.getElementById('success-modal');
    const closeBtn = modal.querySelector('.close-modal');
    const okBtn = document.getElementById('modal-ok-btn');
    
    // Close modal when X is clicked
    closeBtn.addEventListener('click', function() {
        closeModal(modal);
    });
    
    // Close modal when OK is clicked
    okBtn.addEventListener('click', function() {
        closeModal(modal);
    });
    
    // Close when clicking outside modal
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal(modal);
        }
    });
}

// Function to show success modal
function showSuccessModal(message, type = 'success') {
    const modal = document.getElementById('success-modal');
    const messageElement = document.getElementById('success-message');
    const modalContent = modal.querySelector('.modal-content');
    const modalHeader = modal.querySelector('.modal-header h3');
    
    // Set message
    messageElement.textContent = message;
    
    // Set type-specific styling
    if (type === 'error') {
        modalHeader.textContent = 'Error';
        modalContent.classList.add('error');
    } else {
        modalHeader.textContent = 'Success';
        modalContent.classList.remove('error');
    }
    
    // Show modal
    modal.style.display = 'flex';
    
    // Add class for animation
    setTimeout(() => {
        modalContent.classList.add('show');
    }, 10);
}

// Setup logout modal
function setupLogoutModal() {
    // Create modal elements if they don't exist
    if (!document.getElementById('logout-modal')) {
        const modalHTML = `
            <div id="logout-modal" class="custom-modal">
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
    }
    
    // Get modal elements
    const modal = document.getElementById('logout-modal');
    const closeBtn = modal.querySelector('.close-modal');
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
    closeBtn.addEventListener('click', function() {
        closeModal(modal);
    });
    
    // Close modal when Cancel is clicked
    cancelBtn.addEventListener('click', function() {
        closeModal(modal);
    });
    
    // Logout when Confirm is clicked
    confirmBtn.addEventListener('click', function() {
        // Add loading state
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
        confirmBtn.disabled = true;
        
        // Redirect after a short delay to show loading state
        setTimeout(() => {
            window.location.href = '/logout';
        }, 800);
    });
    
    // Close when clicking outside modal
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal(modal);
        }
    });
}

// Function to close modal with animation
function closeModal(modal) {
    modal.querySelector('.modal-content').classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}