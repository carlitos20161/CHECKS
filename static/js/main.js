// Main JavaScript file for application-wide functions

// Handle company change in forms to fetch related employees
function setupCompanyEmployeeRelationship() {
    const companySelect = document.getElementById('company_id');
    const employeeSelect = document.getElementById('employee_id');
    
    if (companySelect && employeeSelect) {
        companySelect.addEventListener('change', function() {
            const companyId = this.value;
            if (companyId) {
                // Clear existing options
                employeeSelect.innerHTML = '<option value="">Loading employees...</option>';
                
                // Fetch employees for the selected company
                fetch(`/api/employees/by-company/${companyId}`)
                    .then(response => response.json())
                    .then(data => {
                        employeeSelect.innerHTML = '';
                        if (data.length === 0) {
                            const option = document.createElement('option');
                            option.value = '';
                            option.textContent = 'No employees found for this company';
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
                // Clear employee select if no company is selected
                employeeSelect.innerHTML = '<option value="">Select a company first</option>';
            }
        });
    }
}

// Initialize tooltips, popovers, and other Bootstrap components
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
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
            // If not empty, format to 2 decimal places
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    setupCompanyEmployeeRelationship();
    initializeBootstrapComponents();
    formatCurrencyFields();
    
    // Add event listener for flash message close button
    const flashCloseButtons = document.querySelectorAll('.alert .btn-close');
    flashCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.alert').remove();
        });
    });
});
