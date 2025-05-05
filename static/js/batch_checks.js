/**
 * Batch Check Creation JavaScript
 * Handles the dynamic form for batch check creation
 */

// Initialize the batch checks form
function initBatchChecksForm(employeesData) {
    const employeeChecks = document.getElementById('employeeChecks');
    const addEmployeeButton = document.getElementById('addEmployeeRow');
    const companySelect = document.getElementById('company_id');
    const showPayDetailsCheckbox = document.getElementById('showPayDetails');
    
    // Initialize the first row's employee select
    updateEmployeeOptions();
    
    // Add event listener for company select change
    if (companySelect) {
        companySelect.addEventListener('change', function() {
            updateEmployeeOptions();
            
            // Also load clients for the selected company if the API exists
            const clientSelect = document.getElementById('client_id');
            if (clientSelect) {
                const companyId = this.value;
                if (companyId) {
                    fetch(`/api/clients/by-company/${companyId}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json();
                        })
                        .then(data => {
                            clientSelect.innerHTML = '<option value="">-- Select Client (Optional) --</option>';
                            data.forEach(client => {
                                const option = document.createElement('option');
                                option.value = client.id;
                                option.textContent = client.name;
                                clientSelect.appendChild(option);
                            });
                        })
                        .catch(error => {
                            // If endpoint doesn't exist yet, just empty the dropdown
                            clientSelect.innerHTML = '<option value="">-- Select Client (Optional) --</option>';
                            console.log('Could not load clients:', error);
                        });
                }
            }
        });
    }
    
    // Add event listener for add employee button
    if (addEmployeeButton) {
        addEmployeeButton.addEventListener('click', function() {
            addEmployeeRow();
        });
    }
    
    // Toggle pay details sections
    if (showPayDetailsCheckbox) {
        showPayDetailsCheckbox.addEventListener('change', function() {
            const payDetailsSections = document.querySelectorAll('.pay-details');
            payDetailsSections.forEach(section => {
                section.style.display = this.checked ? 'block' : 'none';
            });
        });
    }
    
    // Setup initial calculation buttons
    setupCalculationButtons();
    
    // Add event listener for existing remove button
    setupRemoveButtons();
    
    // Function to update employee options based on selected company
    function updateEmployeeOptions() {
        const companyId = companySelect ? parseInt(companySelect.value) : null;
        const employeeSelects = document.querySelectorAll('.employee-select');
        
        employeeSelects.forEach(select => {
            const currentValue = select.value;
            select.innerHTML = '<option value="">Select Employee</option>';
            
            // Filter employees by company if a company is selected
            const filteredEmployees = companyId 
                ? employeesData.filter(emp => emp.company_id === companyId)
                : employeesData;
            
            filteredEmployees.forEach(employee => {
                const option = document.createElement('option');
                option.value = employee.id;
                option.textContent = employee.name;
                if (currentValue && parseInt(currentValue) === employee.id) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        });
    }
    
    // Function to add a new employee row
    function addEmployeeRow() {
        // Clone the first row as a template
        const firstRow = document.querySelector('.employee-row');
        const newRow = firstRow.cloneNode(true);
        
        // Clear all input values in the new row
        const inputs = newRow.querySelectorAll('input');
        inputs.forEach(input => {
            input.value = '';
        });
        
        // Reset select to default option
        const select = newRow.querySelector('select');
        select.selectedIndex = 0;
        
        // Add the row to the container
        employeeChecks.appendChild(newRow);
        
        // Update employee options for the new select
        updateEmployeeOptions();
        
        // Setup remove button for the new row
        setupRemoveButtons();
        
        // Setup calculation buttons
        setupCalculationButtons();
    }
    
    // Setup remove buttons for all rows
    function setupRemoveButtons() {
        const removeButtons = document.querySelectorAll('.btn-remove-row');
        
        removeButtons.forEach(button => {
            // Remove existing event listeners by cloning the button
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add new event listener
            newButton.addEventListener('click', function() {
                const row = this.closest('.employee-row');
                
                // Don't remove if it's the last row
                const rows = document.querySelectorAll('.employee-row');
                if (rows.length > 1) {
                    row.remove();
                } else {
                    // Clear the fields instead of removing
                    const select = row.querySelector('select');
                    const input = row.querySelector('input');
                    if (select) select.value = '';
                    if (input) input.value = '';
                }
            });
        });
    }
    
    // Setup calculation buttons
    function setupCalculationButtons() {
        // Individual row calculation buttons
        const calculateRowButtons = document.querySelectorAll('.btn-calculate-row');
        calculateRowButtons.forEach(button => {
            // Remove existing event listeners by cloning the button
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add new event listener
            newButton.addEventListener('click', function() {
                const row = this.closest('.employee-row');
                calculateRowAmount(row);
            });
        });
        
        // Quick calculation buttons (calculator icon)
        const quickCalcButtons = document.querySelectorAll('.btn-calculate');
        quickCalcButtons.forEach(button => {
            // Remove existing event listeners by cloning the button
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add new event listener
            newButton.addEventListener('click', function() {
                const row = this.closest('.employee-row');
                // Toggle pay details visibility
                const payDetails = row.querySelector('.pay-details');
                if (payDetails) {
                    const isVisible = payDetails.style.display !== 'none';
                    payDetails.style.display = isVisible ? 'none' : 'block';
                    
                    // If showing, set the checkbox to checked
                    if (!isVisible) {
                        const showPayDetailsCheckbox = document.getElementById('showPayDetails');
                        if (showPayDetailsCheckbox) {
                            showPayDetailsCheckbox.checked = true;
                        }
                    }
                }
            });
        });
    }
    
    // Calculate total amount for a row based on hours and rates
    function calculateRowAmount(row) {
        const hoursInput = row.querySelector('.hours-input');
        const rateInput = row.querySelector('.rate-input');
        const otHoursInput = row.querySelector('.ot-hours-input');
        const otRateInput = row.querySelector('.ot-rate-input');
        const holidayHoursInput = row.querySelector('.holiday-hours-input');
        const holidayRateInput = row.querySelector('.holiday-rate-input');
        const amountInput = row.querySelector('.amount-input');
        
        if (amountInput) {
            const hours = parseFloat(hoursInput.value) || 0;
            const rate = parseFloat(rateInput.value) || 0;
            const otHours = parseFloat(otHoursInput.value) || 0;
            const otRate = parseFloat(otRateInput.value) || 0;
            const holidayHours = parseFloat(holidayHoursInput.value) || 0;
            const holidayRate = parseFloat(holidayRateInput.value) || 0;
            
            let total = 0;
            
            // Regular pay
            if (hours > 0 && rate > 0) {
                total += hours * rate;
            }
            
            // Overtime pay
            if (otHours > 0 && otRate > 0) {
                total += otHours * otRate;
            }
            
            // Holiday pay
            if (holidayHours > 0 && holidayRate > 0) {
                total += holidayHours * holidayRate;
            }
            
            // Format to 2 decimal places and update amount field
            if (total > 0) {
                amountInput.value = total.toFixed(2);
            }
        }
    }

    // Add submit event listener to validate the form
    const form = document.getElementById('batchCheckForm');
    if (form) {
        form.addEventListener('submit', function(event) {
            const rows = document.querySelectorAll('.employee-row');
            let isValid = true;
            
            // Check if we have at least one valid employee row
            let hasValidRow = false;
            
            rows.forEach(row => {
                const select = row.querySelector('.employee-select');
                const input = row.querySelector('input[name="amount"]');
                
                if (select && input) {
                    // Mark fields as invalid if they're empty
                    if (!select.value) {
                        select.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        select.classList.remove('is-invalid');
                    }
                    
                    if (!input.value || parseFloat(input.value) <= 0) {
                        input.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        input.classList.remove('is-invalid');
                        hasValidRow = true;
                    }
                }
            });
            
            if (!isValid || !hasValidRow) {
                event.preventDefault();
                alert('Please fill out all required fields correctly and ensure at least one employee is selected.');
            }
        });
    }
}
