from flask import render_template, request, redirect, url_for, flash, abort, send_file, jsonify
from app import db
from models import Bank, Company, Employee, Check
from forms import BankForm, CompanyForm, EmployeeForm, CheckForm, BatchCheckForm
from utils.pdf_generator import generate_check_pdf
from datetime import datetime
import io
import os

def configure_routes(app):
    
    @app.context_processor
    def inject_now():
        """Inject the current datetime into all templates."""
        return {'now': datetime.now()}
    
    @app.route('/')
    def index():
        """Home page route."""
        return render_template('index.html')
    
    # Bank routes
    @app.route('/banks')
    def banks_index():
        """List all banks."""
        banks = Bank.query.all()
        return render_template('banks/index.html', banks=banks)
    
    @app.route('/banks/create', methods=['GET', 'POST'])
    def banks_create():
        """Create a new bank."""
        form = BankForm()
        if form.validate_on_submit():
            bank = Bank(
                name=form.name.data,
                routing_number=form.routing_number.data,
                account_number=form.account_number.data
            )
            db.session.add(bank)
            db.session.commit()
            flash('Bank created successfully!', 'success')
            return redirect(url_for('banks_index'))
        return render_template('banks/create.html', form=form)
    
    @app.route('/banks/<int:id>/edit', methods=['GET', 'POST'])
    def banks_edit(id):
        """Edit an existing bank."""
        bank = Bank.query.get_or_404(id)
        form = BankForm(obj=bank)
        if form.validate_on_submit():
            form.populate_obj(bank)
            db.session.commit()
            flash('Bank updated successfully!', 'success')
            return redirect(url_for('banks_index'))
        return render_template('banks/edit.html', form=form, bank=bank)
    
    @app.route('/banks/<int:id>/delete', methods=['POST'])
    def banks_delete(id):
        """Delete a bank."""
        bank = Bank.query.get_or_404(id)
        # Check if the bank has any associated checks
        if bank.checks:
            flash('Cannot delete bank with associated checks.', 'danger')
            return redirect(url_for('banks_index'))
        
        db.session.delete(bank)
        db.session.commit()
        flash('Bank deleted successfully!', 'success')
        return redirect(url_for('banks_index'))
    
    # Company routes
    @app.route('/companies')
    def companies_index():
        """List all companies."""
        companies = Company.query.all()
        return render_template('companies/index.html', companies=companies)
    
    @app.route('/companies/create', methods=['GET', 'POST'])
    def companies_create():
        """Create a new company."""
        form = CompanyForm()
        if form.validate_on_submit():
            company = Company(
                name=form.name.data,
                address=form.address.data
            )
            db.session.add(company)
            db.session.commit()
            flash('Company created successfully!', 'success')
            return redirect(url_for('companies_index'))
        return render_template('companies/create.html', form=form)
    
    @app.route('/companies/<int:id>/edit', methods=['GET', 'POST'])
    def companies_edit(id):
        """Edit an existing company."""
        company = Company.query.get_or_404(id)
        form = CompanyForm(obj=company)
        if form.validate_on_submit():
            form.populate_obj(company)
            db.session.commit()
            flash('Company updated successfully!', 'success')
            return redirect(url_for('companies_index'))
        return render_template('companies/edit.html', form=form, company=company)
    
    @app.route('/companies/<int:id>/delete', methods=['POST'])
    def companies_delete(id):
        """Delete a company."""
        company = Company.query.get_or_404(id)
        # Check if the company has any associated employees or checks
        if company.employees or company.checks:
            flash('Cannot delete company with associated employees or checks.', 'danger')
            return redirect(url_for('companies_index'))
        
        db.session.delete(company)
        db.session.commit()
        flash('Company deleted successfully!', 'success')
        return redirect(url_for('companies_index'))
    
    # Employee routes
    @app.route('/employees')
    def employees_index():
        """List all employees."""
        employees = Employee.query.all()
        return render_template('employees/index.html', employees=employees)
    
    @app.route('/employees/create', methods=['GET', 'POST'])
    def employees_create():
        """Create a new employee."""
        form = EmployeeForm()
        # Get all companies for the select field
        form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        
        if form.validate_on_submit():
            employee = Employee(
                name=form.name.data,
                title=form.title.data,
                company_id=form.company_id.data
            )
            db.session.add(employee)
            db.session.commit()
            flash('Employee created successfully!', 'success')
            return redirect(url_for('employees_index'))
        return render_template('employees/create.html', form=form)
    
    @app.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
    def employees_edit(id):
        """Edit an existing employee."""
        employee = Employee.query.get_or_404(id)
        form = EmployeeForm(obj=employee)
        # Get all companies for the select field
        form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        
        if form.validate_on_submit():
            form.populate_obj(employee)
            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees_index'))
        return render_template('employees/edit.html', form=form, employee=employee)
    
    @app.route('/employees/<int:id>/delete', methods=['POST'])
    def employees_delete(id):
        """Delete an employee."""
        employee = Employee.query.get_or_404(id)
        # Check if the employee has any associated checks
        if employee.checks:
            flash('Cannot delete employee with associated checks.', 'danger')
            return redirect(url_for('employees_index'))
        
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
        return redirect(url_for('employees_index'))
    
    # Check routes
    @app.route('/checks')
    def checks_index():
        """List all checks with filtering options."""
        # Get query parameters for filtering
        bank_id = request.args.get('bank_id', type=int)
        company_id = request.args.get('company_id', type=int)
        employee_id = request.args.get('employee_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Start with base query
        query = Check.query
        
        # Apply filters if they exist
        if bank_id:
            query = query.filter(Check.bank_id == bank_id)
        if company_id:
            query = query.filter(Check.company_id == company_id)
        if employee_id:
            query = query.filter(Check.employee_id == employee_id)
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Check.date >= start_date)
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Check.date <= end_date)
        
        # Order by most recent
        checks = query.order_by(Check.date.desc(), Check.check_number.desc()).all()
        
        # Get all banks, companies, and employees for filter dropdowns
        banks = Bank.query.all()
        companies = Company.query.all()
        employees = Employee.query.all()
        
        return render_template(
            'checks/index.html',
            checks=checks,
            banks=banks,
            companies=companies,
            employees=employees,
            bank_id=bank_id,
            company_id=company_id,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date
        )
    
    @app.route('/checks/create', methods=['GET', 'POST'])
    def checks_create():
        """Create a new check."""
        form = CheckForm()
        
        # Get all banks, companies, and employees for the select fields
        form.bank_id.choices = [(b.id, b.name) for b in Bank.query.all()]
        form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        form.employee_id.choices = [(e.id, e.name) for e in Employee.query.all()]
        
        if form.validate_on_submit():
            bank = Bank.query.get(form.bank_id.data)
            if not bank:
                flash('Selected bank not found.', 'danger')
                return redirect(url_for('checks_create'))
            
            # Get the next check number from the bank
            check_number = bank.get_next_check_number()
            
            check = Check(
                bank_id=form.bank_id.data,
                company_id=form.company_id.data,
                employee_id=form.employee_id.data,
                amount=form.amount.data,
                date=form.date.data,
                check_number=check_number
            )
            
            db.session.add(check)
            db.session.commit()
            
            flash(f'Check #{check_number} created successfully!', 'success')
            return redirect(url_for('checks_index'))
        
        return render_template('checks/create.html', form=form)
    
    @app.route('/checks/batch', methods=['GET', 'POST'])
    def checks_batch():
        """Create multiple checks at once."""
        form = BatchCheckForm()
        
        # Get all banks and companies for the select fields
        form.bank_id.choices = [(b.id, b.name) for b in Bank.query.all()]
        form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        
        if request.method == 'POST':
            # Get form data
            bank_id = request.form.get('bank_id', type=int)
            company_id = request.form.get('company_id', type=int)
            date_str = request.form.get('date')
            
            # Validate required fields
            if not bank_id or not company_id or not date_str:
                flash('Please fill out all required fields.', 'danger')
                return redirect(url_for('checks_batch'))
            
            # Convert date string to date object
            try:
                check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(url_for('checks_batch'))
            
            # Get the bank
            bank = Bank.query.get(bank_id)
            if not bank:
                flash('Selected bank not found.', 'danger')
                return redirect(url_for('checks_batch'))
            
            # Process employee data - this comes from dynamic form fields
            employee_ids = request.form.getlist('employee_id', type=int)
            amounts = request.form.getlist('amount')
            
            # Validate we have matching employee_ids and amounts
            if len(employee_ids) != len(amounts) or not employee_ids:
                flash('Invalid employee or amount data.', 'danger')
                return redirect(url_for('checks_batch'))
            
            # Create checks for each employee
            created_checks = []
            for i, employee_id in enumerate(employee_ids):
                try:
                    amount = float(amounts[i])
                    if amount <= 0:
                        raise ValueError("Amount must be positive")
                    
                    # Get the next check number
                    check_number = bank.get_next_check_number()
                    
                    check = Check(
                        bank_id=bank_id,
                        company_id=company_id,
                        employee_id=employee_id,
                        amount=amount,
                        date=check_date,
                        check_number=check_number
                    )
                    db.session.add(check)
                    created_checks.append(check)
                except (ValueError, TypeError):
                    flash(f'Invalid amount for employee #{i+1}.', 'danger')
                    return redirect(url_for('checks_batch'))
            
            db.session.commit()
            
            flash(f'Successfully created {len(created_checks)} checks.', 'success')
            return redirect(url_for('checks_index'))
        
        # Get all employees for JavaScript to use
        employees = Employee.query.all()
        employees_json = [{'id': e.id, 'name': e.name, 'company_id': e.company_id} for e in employees]
        
        return render_template('checks/batch.html', form=form, employees=employees_json)
    
    @app.route('/checks/<int:id>')
    def checks_view(id):
        """View details of a specific check."""
        check = Check.query.get_or_404(id)
        return render_template('checks/view.html', check=check)
    
    @app.route('/checks/<int:id>/pdf')
    def checks_pdf(id):
        """Generate and download a PDF version of a check."""
        check = Check.query.get_or_404(id)
        
        # Generate the PDF
        pdf_data = generate_check_pdf(check)
        
        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()
        buffer.write(pdf_data)
        buffer.seek(0)
        
        # Return the PDF as a downloadable file
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'check_{check.check_number}.pdf',
            mimetype='application/pdf'
        )
    
    @app.route('/api/employees/by-company/<int:company_id>')
    def api_employees_by_company(company_id):
        """API endpoint to get employees by company ID."""
        employees = Employee.query.filter_by(company_id=company_id).all()
        return jsonify([
            {'id': e.id, 'name': e.name, 'title': e.title}
            for e in employees
        ])
