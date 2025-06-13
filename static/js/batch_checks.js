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
    
   
    // Add event listener for client select change
    const clientSelect = document.getElementById('client_id');
    if (clientSelect) {
        clientSelect.addEventListener('change', function () {
            updateEmployeeOptions();
        });

        // Trigger once on page load if client is already selected
        if (clientSelect.value) {
            updateEmployeeOptions();
        }
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
    const clientSelect = document.getElementById('client_id');
    const clientId = clientSelect ? parseInt(clientSelect.value) : null;
    const employeeSelects = document.querySelectorAll('.employee-select');

    employeeSelects.forEach(select => {
        const currentValue = select.value;
        select.innerHTML = '<option value="">Select Employee</option>';
        console.log("Client ID:", clientId);
        console.log("All employees:", employeesData);

        const filteredEmployees = employeesData.filter(emp => {
            return !clientId || clientId == 0 || emp.client_id == clientId;
        });

        console.log("Filtered:", filteredEmployees);




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
        // Auto-update OT rate when pay rate changes

// Auto-update OT rate when pay rate changes
function setupRateInputListener(row) {
    const rateInput = row.querySelector('.rate-input');
    const otRateInput = row.querySelector('.ot-rate-input');

    if (rateInput && otRateInput) {
        rateInput.addEventListener('input', () => {
            const rate = parseFloat(rateInput.value);
            if (!isNaN(rate) && rate > 0) {
                otRateInput.value = (rate * 1.5).toFixed(2);
                calculateRowAmount(row);
            }
        });
    }
}

// Add this inside setupCalculationButtons():
document.querySelectorAll('.employee-row').forEach(setupRateInputListener);





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

    const hours = parseFloat(hoursInput.value) || 0;
    const rate = parseFloat(rateInput.value) || 0;
    const otHours = parseFloat(otHoursInput.value) || 0;
    const holidayHours = parseFloat(holidayHoursInput.value) || 0;
    const holidayRate = parseFloat(holidayRateInput.value) || 0;

    const otRate = rate * 1.5; // ✅ override manual input
    let total = 0;

    if (hours > 0 && rate > 0) total += hours * rate;
    if (otHours > 0 && rate > 0) {
        total += otHours * otRate;
        otRateInput.value = otRate.toFixed(2); // ✅ auto-fill visible input
    }
    if (holidayHours > 0 && holidayRate > 0) total += holidayHours * holidayRate;

    if (total > 0) {
        amountInput.value = total.toFixed(2);
    }
}





function addEmployeeRow() {
    const rows = document.querySelectorAll('.employee-row');
    const newIndex = rows.length;

    const firstRow = document.querySelector('.employee-row');
    const newRow = firstRow.cloneNode(true);

    // Update names and clear values
    newRow.querySelectorAll('input, select, textarea').forEach(el => {
        const name = el.getAttribute('name');
        if (name) {
            const newName = name.replace(/\d+/, newIndex);
            el.setAttribute('name', newName);
        }
        el.value = '';
    });

    employeeChecks.appendChild(newRow);
    updateEmployeeOptions();
    setupRemoveButtons();
    setupCalculationButtons();
    setupRateInputListener(newRow);

}


    // Add submit event listener to validate the form
    const form = document.getElementById('batchCheckForm');
if (form) {
    form.addEventListener('submit', function(event) {
    const employeeSelects = document.querySelectorAll('select[name="employee_id"]');
    const amountInputs = document.querySelectorAll('input[name="amount"]');

    let isValid = true;
    let hasValidRow = false;

    employeeSelects.forEach((select, index) => {
        const amountInput = amountInputs[index];

        if (!select.value) {
            select.classList.add('is-invalid');
            isValid = false;
        } else {
            select.classList.remove('is-invalid');
        }

        if (!amountInput.value || parseFloat(amountInput.value) <= 0) {
            amountInput.classList.add('is-invalid');
            isValid = false;
        } else {
            amountInput.classList.remove('is-invalid');
            hasValidRow = true;
        }
    });

    if (!isValid || !hasValidRow) {
        event.preventDefault();
        alert('Please fill out all required fields correctly and ensure at least one employee is selected.');
    }
});
}

}
