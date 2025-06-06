// Main JavaScript file for application-wide functions

// Handle client change in forms to fetch related employees
function setupClientEmployeeRelationship() {
    const clientSelect = document.getElementById('client_id');
    const employeeSelect = document.getElementById('employee_id');
    
    if (clientSelect && employeeSelect) {
        clientSelect.addEventListener('change', function() {
            const clientId = this.value;
            if (clientId) {
                // Show loading text
                employeeSelect.innerHTML = '<option value="">Loading employees...</option>';
                
                // Fetch employees for the selected client
                fetch(`/api/employees/by-client/${clientId}`)
                    .then(response => response.json())
                    .then(data => {
                        employeeSelect.innerHTML = '';
                        if (data.length === 0) {
                            const option = document.createElement('option');
                            option.value = '';
                            option.textContent = 'No employees found for this client';
                            employeeSelect.appendChild(option);
                        } else {
                            data.forEach(employee => {
                                const option = document.createElement('option');
                                option.value = employee.id;
                                option.textContent = employee.name;
                                employeeSelect.appendChild(option);
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching employees:', error);
                        employeeSelect.innerHTML = '<option value="">Error loading employees</option>';
                    });
            } else {
                // No client selected
                employeeSelect.innerHTML = '<option value="">Select a client first</option>';
            }
        });
    }
}

// Initialize tooltips, popovers, and other Bootstrap components
function initializeBootstrapComponents() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Format currency input fields
function formatCurrencyFields() {
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    setupClientEmployeeRelationship();
    initializeBootstrapComponents();
    formatCurrencyFields();

    // Flash message dismiss
    const flashCloseButtons = document.querySelectorAll('.alert .btn-close');
    flashCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.alert').remove();
        });
    });
});
