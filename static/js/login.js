/**
 * VRL LOGISTICS - LOGIN PAGE INTERACTIVITY
 * Handles: password toggle, animations, form validation, loading states
 */

// ============================================================
// Initialize on DOM Ready
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    initializePasswordToggle();
    initializeFormEvents();
    initializeAlertDismissal();
    initializeKeyboardShortcuts();
    focusUsernameField();
});

// ============================================================
// PASSWORD SHOW/HIDE TOGGLE WITH EYE ANIMATION
// ============================================================

function initializePasswordToggle() {
    const toggleBtn = document.getElementById('togglePassword');
    const passwordField = document.getElementById('password');

    if (!toggleBtn || !passwordField) return;

    toggleBtn.addEventListener('click', function (e) {
        e.preventDefault();

        // Toggle input type
        const isPassword = passwordField.type === 'password';
        passwordField.type = isPassword ? 'text' : 'password';

        // Toggle icon with animation
        const icon = toggleBtn.querySelector('i');
        if (icon) {
            icon.style.transition = 'all 0.3s ease';
            icon.style.transform = 'scale(0.8)';

            // Update icon
            if (isPassword) {
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }

            // Reset scale
            setTimeout(() => {
                icon.style.transform = 'scale(1)';
            }, 50);
        }

        // Add focus to password field
        passwordField.focus();
    });

    // Also toggle on Enter key within password field
    passwordField.addEventListener('keydown', function (e) {
        if (e.key === 'Alt') {
            // Alt + P to toggle password visibility (accessibility)
            if (e.code === 'KeyP') {
                toggleBtn.click();
            }
        }
    });
}

// ============================================================
// FORM EVENTS & SUBMISSION HANDLING
// ============================================================

function initializeFormEvents() {
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const usernameField = document.getElementById('username');
    const passwordField = document.getElementById('password');

    if (!loginForm) return;

    // Real-time input validation styling
    usernameField.addEventListener('input', validateUsernameField);
    passwordField.addEventListener('input', validatePasswordField);

    // Handle form submission
    loginForm.addEventListener('submit', function (e) {
        // Don't prevent default - we want normal POST form submission
        // BUT we'll add loading animation

        // Validate fields are not empty
        if (!usernameField.value.trim()) {
            e.preventDefault();
            usernameField.focus();
            showFieldError(usernameField, 'Please enter username or email');
            return;
        }

        if (!passwordField.value.trim()) {
            e.preventDefault();
            passwordField.focus();
            showFieldError(passwordField, 'Please enter password');
            return;
        }

        // Add loading state to button
        addButtonLoadingState(loginBtn);
    });

    // Clear error on focus
    usernameField.addEventListener('focus', function () {
        clearFieldError(this);
    });

    passwordField.addEventListener('focus', function () {
        clearFieldError(this);
    });

    // Enter key to submit form (standard behavior)
    passwordField.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && usernameField.value && passwordField.value) {
            loginForm.submit();
        }
    });
}

// ============================================================
// FIELD VALIDATION & ERROR HANDLING
// ============================================================

function validateUsernameField() {
    const field = document.getElementById('username');
    const value = field.value.trim();

    if (value.length > 0) {
        clearFieldError(field);
        // Optional: add success state
        field.style.borderColor = '#198754';
    } else {
        field.style.borderColor = '';
    }
}

function validatePasswordField() {
    const field = document.getElementById('password');
    const value = field.value.trim();

    if (value.length > 0) {
        clearFieldError(field);
        if (value.length >= 3) {
            field.style.borderColor = '#198754';
        }
    } else {
        field.style.borderColor = '';
    }
}

function showFieldError(field, message) {
    field.style.borderColor = '#dc3545';
    field.style.boxShadow = '0 0 0 4px rgba(220, 53, 69, 0.1)';

    // Remove any existing error message
    const existingError = field.nextElementSibling?.classList.contains('field-error');
    if (existingError) {
        field.nextElementSibling.remove();
    }

    // Add error message (optional)
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.cssText = `
        font-size: 12px;
        color: #dc3545;
        margin-top: 4px;
        animation: slideInLeft 0.3s ease;
    `;
    errorDiv.textContent = message;
    // Uncomment if you want to show error messages
    // field.after(errorDiv);
}

function clearFieldError(field) {
    field.style.borderColor = '';
    field.style.boxShadow = '';

    // Remove error message
    const errorMsg = field.nextElementSibling;
    if (errorMsg?.classList.contains('field-error')) {
        errorMsg.remove();
    }
}

// ============================================================
// BUTTON LOADING ANIMATION
// ============================================================

function addButtonLoadingState(btn) {
    btn.disabled = true;
    btn.classList.add('loading');

    // Alternative: Set the button back to normal after a timeout (for demo)
    // setTimeout(() => {
    //     btn.classList.remove('loading');
    //     btn.disabled = false;
    // }, 2000);
}

function removeButtonLoadingState(btn) {
    btn.disabled = false;
    btn.classList.remove('loading');
}

// ============================================================
// ALERT MESSAGE HANDLING
// ============================================================

function initializeAlertDismissal() {
    const alerts = document.querySelectorAll('.alert-message');

    alerts.forEach((alert, index) => {
        // Auto-dismiss after 6 seconds (staggered)
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.animation = 'slideInLeft 0.4s ease reverse';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 400);
            }
        }, 6000 + index * 500);

        // Manual dismiss on close button
        const closeBtn = alert.querySelector('.close-alert');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                alert.style.animation = 'slideInLeft 0.3s ease reverse';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 300);
            });
        }
    });
}

// ============================================================
// KEYBOARD SHORTCUTS & ACCESSIBILITY
// ============================================================

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const form = document.getElementById('loginForm');
            if (form) {
                form.submit();
            }
        }

        // Alt + U to focus username
        if (e.altKey && e.key === 'u') {
            e.preventDefault();
            const usernameField = document.getElementById('username');
            if (usernameField) {
                usernameField.focus();
                usernameField.select();
            }
        }

        // Alt + P to focus password
        if (e.altKey && e.key === 'p') {
            e.preventDefault();
            const passwordField = document.getElementById('password');
            if (passwordField) {
                passwordField.focus();
                passwordField.select();
            }
        }
    });
}

// ============================================================
// AUTO-FOCUS USERNAME FIELD ON LOAD
// ============================================================

function focusUsernameField() {
    const usernameField = document.getElementById('username');
    if (usernameField && !usernameField.value) {
        usernameField.focus();
    }
}

// ============================================================
// REMEMBER ME FUNCTIONALITY (Optional)
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    const rememberMeCheckbox = document.querySelector('input[name="remember_me"]');

    if (rememberMeCheckbox) {
        // Load saved username from localStorage
        const savedUsername = localStorage.getItem('vrl_saved_username');
        if (savedUsername) {
            document.getElementById('username').value = savedUsername;
            rememberMeCheckbox.checked = true;
        }

        // Save username when form is submitted and checkbox is checked
        document.getElementById('loginForm').addEventListener('submit', function () {
            if (rememberMeCheckbox.checked) {
                const username = document.getElementById('username').value;
                localStorage.setItem('vrl_saved_username', username);
            } else {
                localStorage.removeItem('vrl_saved_username');
            }
        });
    }
});

// ============================================================
// UTILITY: Performance Observer
// ============================================================

if (window.PerformanceObserver) {
    const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.duration > 1000) {
                console.warn(`[Performance] ${entry.name} took ${entry.duration}ms`);
            }
        }
    });

    observer.observe({ entryTypes: ['measure', 'navigation'] });
}

// ============================================================
// DEBUG MODE (Uncomment to enable)
// ============================================================

const DEBUG = false;

function debugLog(...args) {
    if (DEBUG) {
        console.log('[VRL-Login Debug]', ...args);
    }
}

// Log initialization
debugLog('Login page initialized');
debugLog('Username field:', document.getElementById('username'));
debugLog('Password field:', document.getElementById('password'));
debugLog('Login button:', document.getElementById('loginBtn'));
