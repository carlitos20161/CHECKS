from flask import render_template, request, redirect, url_for, flash, abort, send_file, session, jsonify
from app import db
from models import Bank, Company, Employee, Check, User, CompanyClient
from forms import BankForm, CompanyForm, EmployeeForm, CheckForm, BatchCheckForm, CompanyClientForm
from utils.pdf_generator import generate_clean_check
from collections import defaultdict
from utils import login_required, role_required
from models import UserCompanyAssignment



from datetime import datetime
import io
import os

def configure_routes(app):

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'danger')
                return redirect(url_for('register'))

            user = User(username=username, role='user')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')



    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    @app.route('/checks/<int:id>', endpoint='checks_view')
    @login_required
    def checks_view(id):
        check = Check.query.get_or_404(id)
        return render_template('checks/view.html', check=check)
    
    @app.route('/checks/<int:id>/flag', methods=['POST'])
    @login_required
    def flag_check(id):
        check = Check.query.get_or_404(id)
        if session.get('role') != 'admin' and check.created_by_id != session.get('user_id'):
            abort(403)

        reason = request.form.get('reason', '').strip()
        check.flagged_by_user = True
        check.flag_reason = reason
        db.session.commit()
        flash('Check has been flagged for admin review.', 'info')
        return redirect(url_for('checks_view', id=check.id))

        
    @app.route('/checks/<int:id>/unflag', methods=['POST'])
    @role_required('admin')
    def unflag_check(id):
        check = Check.query.get_or_404(id)
        check.flagged_by_user = False
        check.flag_reason = None
        db.session.commit()
        flash('Check marked as reviewed.', 'success')
        return redirect(url_for('checks_index'))


    @app.route('/')
    @login_required
    def index():
        flagged_checks = []
        if session.get('role') == 'admin':
            flagged_checks = Check.query.filter_by(flagged_by_user=True).order_by(Check.date.desc()).all()
        return render_template('index.html', flagged_checks=flagged_checks)

    @app.route('/banks')
    @login_required
    @role_required('admin')
    def banks_index():
        banks = Bank.query.all()
        return render_template('banks/index.html', banks=banks)

    @app.route('/banks/create', methods=['GET', 'POST'])
    def banks_create():
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
        bank = Bank.query.get_or_404(id)
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
        form.default_bank_id.choices = [(0, '-- Select Bank (Optional) --')] + [(b.id, b.name) for b in Bank.query.all()]
        
        # Get all clients for the multi-checkbox field
        all_clients = CompanyClient.query.all()
        form.clients.choices = [(c.id, c.name) for c in all_clients]
        
        if form.validate_on_submit():
            company = Company(
                name=form.name.data,
                address=form.address.data,
                default_bank_id=form.default_bank_id.data if form.default_bank_id.data != 0 else None
            )
            
            # Handle logo upload if present
            if form.logo.data:
                try:
                    logo_data = form.logo.data.read()
                    import base64
                    # Convert logo to base64 to store in database
                    company.logo = base64.b64encode(logo_data).decode('utf-8')
                except Exception as e:
                    flash(f'Error processing logo upload: {str(e)}', 'danger')
            
            db.session.add(company)
            db.session.commit()
            
            # Handle client associations
            selected_client_ids = request.form.getlist('clients')
            if selected_client_ids:
                for client_id in selected_client_ids:
                    client = CompanyClient.query.get(client_id)
                    if client:
                        client.company_id = company.id
                
                db.session.commit()
            
            flash('Company created successfully!', 'success')
            return redirect(url_for('companies_index'))
        return render_template('companies/create.html', form=form)
    
    @app.route('/companies/<int:id>/edit', methods=['GET', 'POST'])
    def companies_edit(id):
        """Edit an existing company."""
        company = Company.query.get_or_404(id)
        form = CompanyForm(obj=company)

        # Populate bank choices
        form.default_bank_id.choices = [(0, '-- Select Bank (Optional) --')] + [(b.id, b.name) for b in Bank.query.all()]

        # Get all available clients
        all_clients = CompanyClient.query.all()
        form.clients.choices = [(c.id, c.name) for c in all_clients]

        # Get currently associated client IDs for checkbox pre-selection
        company_client_ids = [client.id for client in company.clients]

        if form.validate_on_submit():
            # Manually assign standard fields
            company.name = form.name.data
            company.address = form.address.data
            company.default_bank_id = form.default_bank_id.data if form.default_bank_id.data != 0 else None

            # Handle logo upload
            if form.logo.data:
                try:
                    logo_data = form.logo.data.read()
                    import base64
                    company.logo = base64.b64encode(logo_data).decode('utf-8')
                except Exception as e:
                    flash(f'Error processing logo upload: {str(e)}', 'danger')

            # Update associated clients
            company.clients = []
            selected_client_ids = request.form.getlist('clients')
            for client_id in selected_client_ids:
                client = CompanyClient.query.get(int(client_id))
                if client:
                    company.clients.append(client)

            db.session.commit()
            flash('Company updated successfully!', 'success')
            return redirect(url_for('companies_index'))

        # Pre-select the current client IDs for rendering
        return render_template('companies/edit.html', form=form, company=company, selected_client_ids=company_client_ids)




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
        if session.get('role') != 'admin':
            query = query.filter(Check.created_by_id == session.get('user_id'))


        
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
        
        checks = query.order_by(Check.date.desc(), Check.check_number.desc()).all()
        # Order by most recent
        grouped_checks = defaultdict(list)
        for check in checks:
            grouped_checks[check.company.name].append(check)

        
        # Get all banks, companies, and employees for filter dropdowns
        if session.get('role') == 'admin':
            banks = Bank.query.all()
            companies = Company.query.all()
            employees = Employee.query.all()
        else:
            user_id = session.get('user_id')

            # Only companies where this user created checks
            companies = db.session.query(Company).join(UserCompanyAssignment).filter(UserCompanyAssignment.user_id == user_id).all()


            # Only banks related to those companies
            banks = db.session.query(Bank).join(Check).filter(Check.created_by_id == user_id).distinct().all()

            # Only employees from those companies
            employees = db.session.query(Employee).join(Company).join(Check).filter(Check.created_by_id == user_id).distinct().all()

        
        return render_template(
            'checks/index.html',
            grouped_checks=grouped_checks,
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
        form = CheckForm()
        user_id = session.get('user_id')
        is_admin = session.get('role') == 'admin'

        # === Populate form choices ===
        if is_admin:
            form.bank_id.choices = [(b.id, b.name) for b in Bank.query.all()]
            form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
            form.employee_id.choices = [(e.id, e.name) for e in Employee.query.all()]
        else:
            # Get assigned companies
            companies = db.session.query(Company).join(UserCompanyAssignment).filter(
                UserCompanyAssignment.user_id == user_id
            ).all()
            form.company_id.choices = [(c.id, c.name) for c in companies]

            # Default company
            selected_company_id = request.form.get('company_id', type=int) or form.company_id.data
            if not selected_company_id and len(companies) == 1:
                selected_company_id = companies[0].id
                form.company_id.data = selected_company_id

            # Employees from that company
            if selected_company_id:
                form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(company_id=selected_company_id).all()]
            else:
                form.employee_id.choices = []

            # Skip bank_id for non-admin
            form.bank_id.choices = []

        # Client choices
        selected_company_id = request.form.get('company_id', type=int) or form.company_id.data
        if selected_company_id:
            form.client_id.choices = [(0, '-- Select Client (Optional) --')] + [
                (c.id, c.name) for c in CompanyClient.query.filter_by(company_id=selected_company_id).all()
            ]
        else:
            form.client_id.choices = [(0, '-- Select Client (Optional) --')]

        # === Form Submit ===
        if request.method == 'POST':
            print("📨 Form submitted!")
            print(f"Form data: {request.form}")


        if form.validate_on_submit():
            print("📥 POST RECEIVED")
            print(f"🔍 Admin selected bank: {form.bank_id.data}")
            print("✅ FORM VALIDATED")

            try:
                if is_admin:
                    bank = Bank.query.get(form.bank_id.data)
                    print(f"🔍 Admin selected bank: {bank}")
                else:
                    company = Company.query.get(form.company_id.data)
                    bank = Bank.query.get(company.default_bank_id) if company else None
                    print(f"🏦 Bank for non-admin: {bank}")

                if not bank:
                    flash('No valid bank found for the selected company.', 'danger')
                    print("❌ Bank not found")
                    return redirect(url_for('checks_create'))

                check_number = bank.get_next_check_number()
                print(f"🔢 Check number: {check_number}")

                check = Check(
                    bank_id=bank.id,
                    company_id=form.company_id.data,
                    employee_id=form.employee_id.data,
                    client_id=form.client_id.data if form.client_id.data != 0 else None,
                    amount=form.amount.data,
                    date=form.date.data,
                    check_number=check_number,
                    hours_worked=form.hours_worked.data,
                    pay_rate=form.pay_rate.data,
                    overtime_hours=form.overtime_hours.data,
                    overtime_rate=form.overtime_rate.data,
                    holiday_hours=form.holiday_hours.data,
                    holiday_rate=form.holiday_rate.data,
                    memo=form.memo.data,
                    created_by_id=user_id
                )

                print("💾 Committing check to database...")
                db.session.add(check)
                db.session.commit()
                print("✅ Check committed successfully")

                flash(f'Check #{check_number} created successfully!', 'success')
                return redirect(url_for('checks_index'))

            except Exception as e:
                print("❌ ERROR DURING SUBMISSION:", str(e))
                flash(f"Something went wrong: {e}", 'danger')
        
        else:
            if request.method == 'POST':
                print("❌ FORM INVALID")
                print(form.errors)
                flash('Please fix the errors in the form.', 'danger')



        return render_template('checks/create.html', form=form)









    @app.route('/assign-companies', methods=['GET', 'POST'])
    @role_required('admin')
    def assign_companies():
        users = User.query.filter(User.role != 'admin').all()
        companies = Company.query.all()

        if request.method == 'POST':
            user_id = int(request.form.get('user_id'))
            selected_company_ids = request.form.getlist('company_ids')

            # Clear previous assignments
            UserCompanyAssignment.query.filter_by(user_id=user_id).delete()

            # Assign selected companies
            for company_id in selected_company_ids:
                assignment = UserCompanyAssignment(user_id=user_id, company_id=int(company_id))
                db.session.add(assignment)

            db.session.commit()
            flash('Company assignments updated successfully.', 'success')
            return redirect(url_for('assign_companies'))

        return render_template('admin/assign_companies.html', users=users, companies=companies)

       
    
    @app.route('/checks/batch', methods=['GET', 'POST'])
    def checks_batch():
        """Create multiple checks at once."""
        form = BatchCheckForm()
        user_id = session.get('user_id')
        is_admin = session.get('role') == 'admin'
        
        # Get all banks and companies for the select fields
        form.bank_id.choices = [(b.id, b.name) for b in Bank.query.all()]
        if is_admin:
            form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        else:
            user_companies = db.session.query(Company).join(UserCompanyAssignment).filter(UserCompanyAssignment.user_id == user_id).all()
            form.company_id.choices = [(c.id, c.name) for c in user_companies]


        selected_company_id = request.form.get('company_id', type=int) or form.company_id.data

        if selected_company_id:
            clients = CompanyClient.query.filter_by(company_id=selected_company_id).all()
            form.client_id.choices = [(0, '-- Select Client (Optional) --')] + [(c.id, c.name) for c in clients]
        else:
            form.client_id.choices = [(0, '-- Select Client (Optional) --')]

        created_by_id=session.get('user_id')
        
        if request.method == 'POST':
            # Get form data
           # Get bank based on user role
            if session.get('role') == 'admin':
                bank_id = request.form.get('bank_id', type=int)
            else:
                company_id = request.form.get('company_id', type=int)
                company = Company.query.get(company_id)
                bank_id = company.default_bank_id if company else None

            # Validate bank
            bank = Bank.query.get(bank_id) if bank_id else None
            if not bank:
                flash('Bank not found or not associated with the company.', 'danger')
                return redirect(url_for('checks_batch'))

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
            
            # Get client ID if provided
            client_id = request.form.get('client_id', type=int)
            client_id = client_id if client_id and client_id > 0 else None
            
            # Process employee data - this comes from dynamic form fields
            employee_ids = request.form.getlist('employee_id', type=int)
            amounts = request.form.getlist('amount')
            memos = request.form.getlist('memo')
            
            # Get pay calculation fields
            hours_worked_list = request.form.getlist('hours_worked')
            pay_rates = request.form.getlist('pay_rate')
            overtime_hours_list = request.form.getlist('overtime_hours')
            overtime_rates = request.form.getlist('overtime_rate')
            holiday_hours_list = request.form.getlist('holiday_hours')
            holiday_rates = request.form.getlist('holiday_rate')
            
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
                    
                    # Parse optional pay calculation fields
                    memo = memos[i] if i < len(memos) else None
                    hours_worked = float(hours_worked_list[i]) if i < len(hours_worked_list) and hours_worked_list[i] else None
                    pay_rate = float(pay_rates[i]) if i < len(pay_rates) and pay_rates[i] else None
                    overtime_hours = float(overtime_hours_list[i]) if i < len(overtime_hours_list) and overtime_hours_list[i] else None
                    overtime_rate = float(overtime_rates[i]) if i < len(overtime_rates) and overtime_rates[i] else None
                    holiday_hours = float(holiday_hours_list[i]) if i < len(holiday_hours_list) and holiday_hours_list[i] else None
                    holiday_rate = float(holiday_rates[i]) if i < len(holiday_rates) and holiday_rates[i] else None
                    
                    check = Check(
                        bank_id=bank_id,
                        company_id=company_id,
                        employee_id=employee_id,
                        client_id=client_id,
                        amount=amount,
                        date=check_date,
                        check_number=check_number,
                        memo=memo,
                        hours_worked=hours_worked,
                        pay_rate=pay_rate,
                        overtime_hours=overtime_hours,
                        overtime_rate=overtime_rate,
                        holiday_hours=holiday_hours,
                        holiday_rate=holiday_rate,
                        created_by_id=session.get('user_id')
                    )
                    db.session.add(check)
                    created_checks.append(check)
                except (ValueError, TypeError) as e:
                    flash(f'Invalid data for employee #{i+1}: {str(e)}', 'danger')
                    return redirect(url_for('checks_batch'))
            
            db.session.commit()
            
            flash(f'Successfully created {len(created_checks)} checks.', 'success')
            return redirect(url_for('checks_index'))
        
        # Get all employees for JavaScript to use

        employees = Employee.query.all()
        employees_json = [{'id': e.id, 'name': e.name, 'company_id': e.company_id} for e in employees]
        
        return render_template('checks/batch.html', form=form, employees=employees_json)

    @app.route('/checks/<int:id>/pdf', endpoint='checks_pdf')
    @role_required('admin')
    def checks_pdf(id):
        check = Check.query.get_or_404(id)
        from num2words import num2words
        check.amount_words = num2words(
            check.amount, to='currency', lang='en'
        ).replace("euro", "dollars").capitalize()
        pdf_data = generate_clean_check(check)
        buffer = io.BytesIO()
        buffer.write(pdf_data)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'check_{check.check_number}.pdf',
            mimetype='application/pdf'
        )

    
    # Client routes
    @app.route('/clients')
    def clients_index():
        """List all clients."""
        clients = CompanyClient.query.all()
        return render_template('clients/index.html', clients=clients)
    
    @app.route('/clients/create', methods=['GET', 'POST'])
    def clients_create():
        """Create a new client."""
        form = CompanyClientForm()
        # Get all companies for the select field
        form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        
        if form.validate_on_submit():
            client = CompanyClient(
                name=form.name.data,
                address=form.address.data,
                contact_person=form.contact_person.data,
                contact_email=form.contact_email.data,
                contact_phone=form.contact_phone.data,
                company_id=form.company_id.data
            )
            db.session.add(client)
            db.session.commit()
            flash('Client created successfully!', 'success')
            return redirect(url_for('clients_index'))
        return render_template('clients/create.html', form=form)
    
    @app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
    def clients_edit(id):
        """Edit an existing client."""
        client = CompanyClient.query.get_or_404(id)
        form = CompanyClientForm(obj=client)
        # Get all companies for the select field
        form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        
        if form.validate_on_submit():
            form.populate_obj(client)
            db.session.commit()
            flash('Client updated successfully!', 'success')
            return redirect(url_for('clients_index'))
        return render_template('clients/edit.html', form=form, client=client)
        
    
    @app.route('/checks/<int:id>/update-amount', methods=['POST'])
    @role_required('admin')
    def update_check_amount(id):
        check = Check.query.get_or_404(id)
        try:
            check.amount = float(request.form['amount'])
            db.session.commit()
            flash('Check amount updated.', 'success')
        except ValueError:
            flash('Invalid amount.', 'danger')
        return redirect(url_for('checks_view', id=id))

    
    @app.route('/clients/<int:id>/delete', methods=['POST'])
    def clients_delete(id):
        """Delete a client."""
        client = CompanyClient.query.get_or_404(id)
        # Check if the client has any associated checks
        if client.checks:
            flash('Cannot delete client with associated checks.', 'danger')
            return redirect(url_for('clients_index'))
        
        db.session.delete(client)
        db.session.commit()
        flash('Client deleted successfully!', 'success')
        return redirect(url_for('clients_index'))
    
    # API routes
    @app.route('/api/employees/by-company/<int:company_id>')
    def api_employees_by_company(company_id):
        """API endpoint to get employees by company ID."""
        employees = Employee.query.filter_by(company_id=company_id).all()
        return jsonify([
            {'id': e.id, 'name': e.name, 'title': e.title}
            for e in employees
        ])
        
    @app.route('/api/clients/by-company/<int:company_id>')
    def api_clients_by_company(company_id):
        """API endpoint to get clients by company ID."""
        clients = CompanyClient.query.filter_by(company_id=company_id).all()
        return jsonify([
            {'id': c.id, 'name': c.name, 'address': c.address}
            for c in clients
        ])
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['role'] = user.role
                flash('Logged in successfully.', 'success')
                return redirect(url_for('index'))
            flash('Invalid username or password.', 'danger')

        return render_template('login.html')


    @app.route('/logout')
    def logout():
        session.clear()
        flash('Logged out.', 'info')
        return redirect(url_for('login'))
            
    @app.route('/api/company/<int:company_id>')
    def api_company(company_id):
        """API endpoint to get company details by ID."""
        company = Company.query.get_or_404(company_id)
        return jsonify({
            'id': company.id,
            'name': company.name,
            'address': company.address,
            'default_bank_id': company.default_bank_id
        })

