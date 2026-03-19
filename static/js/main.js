// VRL Logistics - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize popovers
    initializePopovers();
    
    // Handle form validations
    handleFormValidation();
    
    // Initialize date picker default date
    initializeDatePicker();
    
    // Load charts if on dashboard
    if (document.querySelector('[data-chart-type]')) {
        loadDashboardCharts();
    }
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Handle form validation
 */
function handleFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            // Remove previous error highlights
            form.querySelectorAll('.is-invalid').forEach(el => {
                el.classList.remove('is-invalid');
            });
            
            // If form doesn't validate, prevent submission
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Add visual feedback to invalid fields
                form.querySelectorAll(':invalid').forEach(el => {
                    el.classList.add('is-invalid');
                });
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize date picker to minimum date today
 */
function initializeDatePicker() {
    const datePickers = document.querySelectorAll('input[type="date"]');
    const today = new Date();
    const minDate = today.toISOString().split('T')[0];
    
    datePickers.forEach(picker => {
        picker.setAttribute('min', minDate);
    });
}

/**
 * Load dashboard charts
 */
function loadDashboardCharts() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    
    // Get stats from API
    fetch('/api/request-stats/', {
        headers: {
            'X-CSRFToken': csrftoken,
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Draw status pie chart
        const statusChartEl = document.getElementById('statusChart');
        if (statusChartEl) {
            drawStatusChart(data.status_data);
        }
        
        // Draw daily requests chart
        const dailyChartEl = document.getElementById('dailyChart');
        if (dailyChartEl) {
            drawDailyChart(data.daily_data);
        }
        
        // Update stats counters
        updateStatsCounters(data);
    })
    .catch(error => console.error('Error fetching stats:', error));
}

/**
 * Draw status pie chart
 */
function drawStatusChart(statusData) {
    const ctx = document.getElementById('statusChart');
    if (!ctx) return;
    
    const labels = Object.keys(statusData);
    const data = Object.values(statusData);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#ffc107',
                    '#0dcaf0',
                    '#6c757d',
                    '#007bff',
                    '#6f42c1',
                    '#198754',
                    '#dc3545'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

/**
 * Draw daily requests line chart
 */
function drawDailyChart(dailyData) {
    const ctx = document.getElementById('dailyChart');
    if (!ctx) return;
    
    const labels = dailyData.map(d => d.date);
    const data = dailyData.map(d => d.count);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Requests',
                data: data,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#0d6efd',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Update stats counters with animation
 */
function updateStatsCounters(data) {
    const totalRequestsEl = document.getElementById('totalRequests');
    if (totalRequestsEl) {
        animateCounter(totalRequestsEl, data.total_requests);
    }
}

/**
 * Animate counter number
 */
function animateCounter(element, targetNumber) {
    const duration = 1000;
    const startNumber = 0;
    const startTime = Date.now();
    
    function updateCounter() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentNumber = Math.floor(startNumber + (targetNumber - startNumber) * progress);
        
        element.textContent = currentNumber;
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    updateCounter();
}

/**
 * Format currency to Indian Rupees
 */
function formatCurrency(amount) {
    const formatter = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    return formatter.format(amount);
}

/**
 * Format date to readable format
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', options);
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container');
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.role = 'alert';
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alertElement, alertContainer.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertElement.remove();
    }, 5000);
}

/**
 * Confirm action dialog
 */
function confirmAction(message) {
    return confirm(message);
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

/**
 * Format phone number
 */
function formatPhoneNumber(phoneNumber) {
    const cleanPhone = phoneNumber.replace(/\D/g, '');
    return cleanPhone.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
}

/**
 * Get URL parameter
 */
function getUrlParameter(param) {
    const url = new URLSearchParams(window.location.search);
    return url.get(param);
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Handle real-time search
 */
document.querySelectorAll('input[type="search"]').forEach(input => {
    input.addEventListener('input', debounce(function() {
        // Trigger form submission or filter
        const form = this.closest('form');
        if (form) {
            form.submit();
        }
    }, 300));
});

/**
 * Handle print functionality
 */
function printInvoice(invoiceId) {
    window.open(`/invoice/print/${invoiceId}/`, '_blank');
}

/**
 * Export table to CSV
 */
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    let csv = [];
    
    // Get headers
    const headers = [];
    table.querySelectorAll('th').forEach(th => {
        headers.push(th.textContent.trim());
    });
    csv.push(headers.join(','));
    
    // Get rows
    table.querySelectorAll('tbody tr').forEach(tr => {
        const row = [];
        tr.querySelectorAll('td').forEach(td => {
            row.push(`"${td.textContent.trim()}"`);
        });
        csv.push(row.join(','));
    });
    
    // Download
    const csvContent = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv.join('\n'));
    const link = document.createElement('a');
    link.setAttribute('href', csvContent);
    link.setAttribute('download', filename);
    link.click();
}

/**
 * Initialize live tracking
 */
function initializeLiveTracking(trackingNumber) {
    // Poll for updates every 30 seconds
    setInterval(() => {
        fetch(`/api/tracking/${trackingNumber}/`)
            .then(response => response.json())
            .then(data => {
                updateTrackingStatus(data);
            })
            .catch(error => console.error('Error fetching tracking:', error));
    }, 30000);
}

/**
 * Update tracking status
 */
function updateTrackingStatus(data) {
    const statusEl = document.getElementById('trackingStatus');
    if (statusEl) {
        statusEl.innerHTML = `<span class="badge bg-info">${data.status}</span>`;
    }
}

// Export functions for global use
window.VRLLogistics = {
    formatCurrency,
    formatDate,
    showAlert,
    confirmAction,
    copyToClipboard,
    exportTableToCSV,
    initializeLiveTracking
};
