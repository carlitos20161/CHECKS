/**
 * Batch Check Creation JavaScript
 * Handles the dynamic form for batch check creation
 */

// Initialize the batch checks form
function initBatchChecksForm(employeesData) {
    const employeeChecks = document.getElementById('employeeChecks');
    const addEmployeeButton = document.getElementById('addEmployeeRow');
    const companySelect = document.getElementById('company_id');
    
    // Initialize the first row's employee select
    updateEmployeeOptions();
    
    // Add event listener for company select change
    if (companySelect) {
        companySelect.addEventListener('change', function() {
            updateEmployeeOptions();
        });
    }
    
    // Add event listener for add employee button
    if (addEmployeeButton) {
        addEmployeeButton.addEventListener('click', function() {
            addEmployeeRow();
        });
    }
    
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
        // Create a new row
        const newRow = document.createElement('div');
        newRow.className = 'row employee-row mb-2';
        
        // Create employee select
        const employeeCol = document.createElement('div');
        employeeCol.className = 'col-md-6';
        const employeeSelect = document.createElement('select');
        employeeSelect.name = 'employee_id';
        employeeSelect.className = 'form-select employee-select';
        employeeSelect.required = true;
        employeeCol.appendChild(employeeSelect);
        
        // Create amount input
        const amountCol = document.createElement('div');
        amountCol.className = 'col-md-4';
        const amountInput = document.createElement('input');
        amountInput.type = 'number';
        amountInput.name = 'amount';
        amountInput.className = 'form-control';
        amountInput.placeholder = 'Amount';
        amountInput.step = '0.01';
        amountInput.min = '0.01';
        amountInput.required = true;
        amountCol.appendChild(amountInput);
        
        // Create remove button
        const buttonCol = document.createElement('div');
        buttonCol.className = 'col-md-2';
        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'btn btn-danger btn-remove-row';
        removeButton.innerHTML = '<i class="fas fa-trash"></i>';
        buttonCol.appendChild(removeButton);
        
        // Add all elements to the row
        newRow.appendChild(employeeCol);
        newRow.appendChild(amountCol);
        newRow.appendChild(buttonCol);
        
        // Add the row to the container
        employeeChecks.appendChild(newRow);
        
        // Update employee options for the new select
        updateEmployeeOptions();
        
        // Setup remove button for the new row
        setupRemoveButtons();
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
