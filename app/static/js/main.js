// main.js - Hospital Management System Core JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize form validations
    initFormValidations();
    
    // Initialize sidebar toggle for mobile
    initSidebarToggle();
    
    // Initialize logout confirmation
    initLogoutConfirmation();
    
    // Initialize patient search functionality
    if (document.getElementById('patient-search')) {
        initPatientSearch();
    }
    
    // Initialize date pickers
    if (document.querySelector('.datepicker')) {
        initDatePickers();
    }
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validations
 */
function initFormValidations() {
    // Example: Validate forms with class 'needs-validation'
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize sidebar toggle for mobile view
 */
function initSidebarToggle() {
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(event) {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }
}

/**
 * Initialize logout confirmation
 */
function initLogoutConfirmation() {
    const logoutLinks = document.querySelectorAll('.logout-link');
    logoutLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to log out?')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initialize patient search with debounce
 */
function initPatientSearch() {
    const searchInput = document.getElementById('patient-search');
    const searchResults = document.getElementById('search-results');
    
    let debounceTimer;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
            const query = searchInput.value.trim();
            
            if (query.length > 2) {
                fetch(`/api/patients/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        displaySearchResults(data);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            } else {
                searchResults.innerHTML = '';
                searchResults.classList.add('d-none');
            }
        }, 300);
    });
    
    function displaySearchResults(patients) {
        searchResults.innerHTML = '';
        
        if (patients.length === 0) {
            searchResults.innerHTML = '<div class="dropdown-item">No patients found</div>';
            searchResults.classList.remove('d-none');
            return;
        }
        
        patients.forEach(patient => {
            const item = document.createElement('a');
            item.className = 'dropdown-item';
            item.href = `/patients/${patient.id}`;
            item.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="flex-grow-1">
                        <h6 class="mb-0">${patient.name}</h6>
                        <small class="text-muted">Patient ID: ${patient.id}</small>
                    </div>
                    <small class="text-muted">${patient.ward || 'No ward assigned'}</small>
                </div>
            `;
            searchResults.appendChild(item);
        });
        
        searchResults.classList.remove('d-none');
    }
}

/**
 * Initialize date pickers
 */
function initDatePickers() {
    flatpickr('.datepicker', {
        dateFormat: 'Y-m-d',
        allowInput: true
    });
    
    flatpickr('.datetimepicker', {
        enableTime: true,
        dateFormat: 'Y-m-d H:i',
        allowInput: true
    });
}

/**
 * AJAX helper function
 */
function makeRequest(method, url, data = null) {
    return new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(xhr.response);
            } else {
                reject({
                    status: xhr.status,
                    statusText: xhr.statusText
                });
            }
        };
        
        xhr.onerror = function() {
            reject({
                status: xhr.status,
                statusText: xhr.statusText
            });
        };
        
        xhr.responseType = 'json';
        xhr.send(data ? JSON.stringify(data) : null);
    });
}

/**
 * Show toast notifications
 */
function showToast(type, message) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    
    // Remove toast after it hides
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// Export functions for use in other modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        makeRequest,
        showToast
    };
}