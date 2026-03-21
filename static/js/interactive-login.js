/**
 * VRL LOGISTICS - INTERACTIVE LOGIN - VANILLA JAVASCRIPT
 * Converts React animations to pure JavaScript
 * Features:
 * - Eye tracking (mouse following)
 * - Random blinking
 * - Character animations tied to form interaction
 * - Password visibility toggle
 * - Loading states
 */

// ============================================================
// STATE MANAGEMENT
// ============================================================

const state = {
    mouse: { x: 0, y: 0 },
    isPurpleBlinking: false,
    isBlackBlinking: false,
    isTyping: false,
    isLookingAtEachOther: false,
    isPurplePeeking: false,
    showPassword: false,
    isLoading: false,
    passwordLength: 0,
};

// ============================================================
// DOM ELEMENTS
// ============================================================

const elements = {
    loginForm: document.getElementById('loginForm'),
    usernameInput: document.getElementById('username'),
    passwordInput: document.getElementById('password'),
    togglePasswordBtn: document.getElementById('togglePasswordBtn'),
    submitBtn: document.getElementById('submitBtn'),
    submitBtnText: document.getElementById('submitBtnText'),
    submitBtnLoader: document.getElementById('submitBtnLoader'),

    // Character containers
    purpleChar: document.getElementById('purpleChar'),
    blackChar: document.getElementById('blackChar'),
    orangeChar: document.getElementById('orangeChar'),
    yellowChar: document.getElementById('yellowChar'),

    // Eyes containers
    purpleEyes: document.getElementById('purpleEyes'),
    blackEyes: document.getElementById('blackEyes'),
    orangeEyes: document.getElementById('orangeEyes'),
    yellowEyes: document.getElementById('yellowEyes'),
    yellowMouth: document.getElementById('yellowMouth'),

    // Individual eyes
    purpleEye1: document.getElementById('purpleEye1'),
    purpleEye2: document.getElementById('purpleEye2'),
    blackEye1: document.getElementById('blackEye1'),
    blackEye2: document.getElementById('blackEye2'),
    orangeEye1: document.getElementById('orangeEye1'),
    orangeEye2: document.getElementById('orangeEye2'),
    yellowEye1: document.getElementById('yellowEye1'),
    yellowEye2: document.getElementById('yellowEye2'),
};

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeMagicUI();
    setupEventListeners();
    startBlinkLoop();
});

// ============================================================
// EVENT LISTENERS SETUP
// ============================================================

function setupEventListeners() {
    // Mouse tracking
    document.addEventListener('mousemove', handleMouseMove);

    // Form inputs
    elements.usernameInput?.addEventListener('focus', () => {
        state.isTyping = true;
        triggerLookingAtEachOther();
    });

    elements.usernameInput?.addEventListener('blur', () => {
        state.isTyping = false;
    });

    elements.passwordInput?.addEventListener('input', (e) => {
        state.passwordLength = e.target.value.length;
        updateCharacterState();
    });

    elements.passwordInput?.addEventListener('focus', () => {
        state.isTyping = true;
    });

    // Password toggle
    elements.togglePasswordBtn?.addEventListener('click', (e) => {
        e.preventDefault();
        togglePasswordVisibility();
    });

    // Form submission
    elements.loginForm?.addEventListener('submit', (e) => {
        // Form will submit normally to Django backend
        // Just add loading state
        setLoadingState(true);
    });
}

// ============================================================
// MOUSE TRACKING & EYE ANIMATION
// ============================================================

function handleMouseMove(e) {
    state.mouse.x = e.clientX;
    state.mouse.y = e.clientY;
    updateEyePositions();
    updateCharacterPositions();
}

function updateEyePositions() {
    // Only update if password is not being shown (not peeking)
    if (state.passwordLength > 0 && state.showPassword) {
        updatePeekingState();
    } else if (state.isLookingAtEachOther) {
        updateLookingAtEachOtherState();
    } else {
        // Normal eye tracking
        updateNormalEyeTracking();
    }
}

function updateNormalEyeTracking() {
    // Purple eyes - follow cursor normally
    updateEyePupils(
        [elements.purpleEye1, elements.purpleEye2],
        'purpleChar',
        { x: 45, y: 40 },
        { maxDistance: 5, size: 18, pupilSize: 7 }
    );

    // Black eyes
    updateEyePupils(
        [elements.blackEye1, elements.blackEye2],
        'blackChar',
        { x: 26, y: 32 },
        { maxDistance: 4, size: 16, pupilSize: 6 }
    );

    // Orange eyes (pupils only)
    updateEyePupils(
        [elements.orangeEye1, elements.orangeEye2],
        'orangeChar',
        { x: 82, y: 90 },
        { maxDistance: 5, size: 12 }
    );

    // Yellow eyes
    updateEyePupils(
        [elements.yellowEye1, elements.yellowEye2],
        'yellowChar',
        { x: 52, y: 40 },
        { maxDistance: 5, size: 12 }
    );
}

function updateEyePupils(eyeElements, characterId, startPos, config) {
    const char = document.getElementById(characterId);
    if (!char) return;

    const rect = char.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 3;

    const dx = state.mouse.x - centerX;
    const dy = state.mouse.y - centerY;
    const distance = Math.min(Math.hypot(dx, dy), config.maxDistance);
    const angle = Math.atan2(dy, dx);

    const offsetX = Math.cos(angle) * distance;
    const offsetY = Math.sin(angle) * distance;

    eyeElements.forEach((eye) => {
        if (!eye) return;
        const pupil = eye.querySelector('.pupil') || eye;
        if (pupil) {
            pupil.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        }
    });
}

// ============================================================
// CHARACTER POSITION TRACKING
// ============================================================

function updateCharacterPositions() {
    const characters = [
        { id: 'purpleChar', centerOffsetY: 1 / 3 },
        { id: 'blackChar', centerOffsetY: 1 / 3 },
        { id: 'orangeChar', centerOffsetY: 1 / 3 },
        { id: 'yellowChar', centerOffsetY: 1 / 3 },
    ];

    characters.forEach((char) => {
        const element = document.getElementById(char.id);
        if (!element) return;

        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height * char.centerOffsetY;

        const dx = state.mouse.x - centerX;
        const dy = state.mouse.y - centerY;

        let faceX = Math.max(-15, Math.min(15, dx / 20));
        let faceY = Math.max(-10, Math.min(10, dy / 30));
        let bodySkew = Math.max(-6, Math.min(6, -dx / 120));

        // Update character body skew
        if (state.passwordLength > 0 && state.showPassword) {
            element.style.transform = 'skewX(0deg)';
            element.style.transformOrigin = 'bottom center';
        } else if (char.id === 'purpleChar') {
            if (state.isTyping || (state.passwordLength > 0 && !state.showPassword)) {
                element.style.transform = `skewX(${bodySkew - 12}deg) translateX(40px)`;
            } else {
                element.style.transform = `skewX(${bodySkew}deg)`;
            }
        } else if (char.id === 'blackChar') {
            if (state.passwordLength > 0 && state.showPassword) {
                element.style.transform = 'skewX(0deg)';
            } else if (state.isLookingAtEachOther) {
                element.style.transform = `skewX(${bodySkew * 1.5 + 10}deg) translateX(20px)`;
            } else if (state.isTyping || (state.passwordLength > 0 && !state.showPassword)) {
                element.style.transform = `skewX(${bodySkew * 1.5}deg)`;
            } else {
                element.style.transform = `skewX(${bodySkew}deg)`;
            }
        }
    });
}

// ============================================================
// BLINKING ANIMATION
// ============================================================

function startBlinkLoop() {
    // Purple character blinking
    const schedulePurpleBlink = () => {
        const randomMs = Math.random() * 4000 + 3000;
        setTimeout(() => {
            state.isPurpleBlinking = true;
            [elements.purpleEye1, elements.purpleEye2].forEach((eye) => {
                if (eye) eye.classList.add('blinking');
            });

            setTimeout(() => {
                state.isPurpleBlinking = false;
                [elements.purpleEye1, elements.purpleEye2].forEach((eye) => {
                    if (eye) eye.classList.remove('blinking');
                });
                schedulePurpleBlink();
            }, 150);
        }, randomMs);
    };
    schedulePurpleBlink();

    // Black character blinking
    const scheduleBlackBlink = () => {
        const randomMs = Math.random() * 4000 + 3000;
        setTimeout(() => {
            state.isBlackBlinking = true;
            [elements.blackEye1, elements.blackEye2].forEach((eye) => {
                if (eye) eye.classList.add('blinking');
            });

            setTimeout(() => {
                state.isBlackBlinking = false;
                [elements.blackEye1, elements.blackEye2].forEach((eye) => {
                    if (eye) eye.classList.remove('blinking');
                });
                scheduleBlackBlink();
            }, 150);
        }, randomMs);
    };
    scheduleBlackBlink();
}

// ============================================================
// CHARACTER STATE UPDATES
// ============================================================

function triggerLookingAtEachOther() {
    state.isLookingAtEachOther = true;
    setTimeout(() => {
        state.isLookingAtEachOther = false;
        updateEyePositions();
    }, 800);
}

function updatePeekingState() {
    // Purple peeking effect
    if (!elements.purpleEyes) return;

    const shouldPeek = Math.random() < 0.3; // 30% chance to peek
    if (shouldPeek && !state.isPurplePeeking) {
        state.isPurplePeeking = true;
        setTimeout(() => {
            state.isPurplePeeking = false;
            updateNormalEyeTracking();
        }, 800);
    }
}

function updateLookingAtEachOtherState() {
    // Update eyes to look at each other
    if (elements.purpleEyes) {
        elements.purpleEyes.style.left = '55px';
        elements.purpleEyes.style.top = '65px';
    }
    if (elements.blackEyes) {
        elements.blackEyes.style.left = '32px';
        elements.blackEyes.style.top = '12px';
    }
}

function updateCharacterState() {
    if (state.passwordLength > 0 && state.showPassword) {
        // Password is visible - show all characters peeking
        updateCharactersPeeking();
    }
}

function updateCharactersPeeking() {
    // Yellow mouth animation
    if (elements.yellowMouth) {
        elements.yellowMouth.style.left = '10px';
        elements.yellowMouth.style.top = '88px';
    }
}

// ============================================================
// PASSWORD TOGGLE
// ============================================================

function togglePasswordVisibility() {
    state.showPassword = !state.showPassword;

    const isPassword = elements.passwordInput.type === 'password';
    elements.passwordInput.type = state.showPassword ? 'text' : 'password';
    elements.togglePasswordBtn.textContent = state.showPassword ? 'Hide' : 'Show';

    updateCharacterState();
    updateEyePositions();
}

// ============================================================
// LOADING STATE
// ============================================================

function setLoadingState(isLoading) {
    state.isLoading = isLoading;
    elements.submitBtn.disabled = isLoading;

    if (isLoading) {
        elements.submitBtnText.style.display = 'none';
        elements.submitBtnLoader.style.display = 'inline';
    } else {
        elements.submitBtnText.style.display = 'inline';
        elements.submitBtnLoader.style.display = 'none';
    }
}

// ============================================================
// INITIALIZATION
// ============================================================

function initializeMagicUI() {
    // Initial character setup
    if (elements.purpleChar) {
        elements.purpleChar.style.height = '400px';
    }

    // Ensure eyes are visible
    [elements.purpleEye1, elements.purpleEye2, elements.blackEye1, elements.blackEye2].forEach((eye) => {
        if (eye) {
            eye.style.display = 'flex';
        }
    });
}

// ============================================================
// KEYBOARD SHORTCUTS (Optional)
// ============================================================

document.addEventListener('keydown', (e) => {
    // Enter to submit
    if (e.key === 'Enter' && elements.usernameInput?.value && elements.passwordInput?.value) {
        e.preventDefault();
        elements.loginForm?.submit();
    }

    // Alt+P to toggle password visibility
    if (e.altKey && e.key === 'p') {
        e.preventDefault();
        togglePasswordVisibility();
    }
});

// ============================================================
// ACCESSIBILITY: REDUCED MOTION SUPPORT
// ============================================================

if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    // Disable animations if user prefers reduced motion
    document.documentElement.style.setProperty('--animation-duration', '0ms');
}

// ============================================================
// CONSOLE LOG FOR DEBUGGING
// ============================================================

console.log('✓ Interactive login UI loaded');
console.log('Features enabled: Eye tracking, Blinking, Character animations, Password toggle');
