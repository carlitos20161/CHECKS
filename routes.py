from flask import render_template, request, redirect, url_for, flash, abort, send_file, session, jsonify
from extensions import db
from collections import defaultdict  # ✅ this is fine
from models import Bank, Company, Employee, Check, User, CompanyClient, UserCompanyAssignment, UserClientAssignment
from forms import BankForm, CompanyForm, EmployeeForm, CheckForm, BatchCheckForm, CompanyClientForm
from utils.pdf_generator import generate_clean_check
from utils import login_required, role_required
from werkzeug.datastructures import FileStorage
from flask import send_file
import pandas as pd
from io import BytesIO
from models import Check  # adjust if needed
from sqlalchemy.orm import joinedload
from forms import CSRFOnlyForm
from forms import AddUserForm
from werkzeug.security import generate_password_hash
from models import User
from flask import session, redirect, url_for
from utils.check_utils import get_next_check_number_by_bank
from flask import Response
import csv
from io import StringIO









from datetime import datetime
import io
import os

def configure_routes(app):

    @app.before_request
    def enforce_authentication_and_valid_user():
        allowed_endpoints = ['login', 'static', 'logout']
        endpoint = request.endpoint or ""

        # Allow login/logout/static only
        if any(endpoint.startswith(route) for route in allowed_endpoints):
            return

        user_id = session.get('user_id')

        # Block if no session
        if not user_id:
            session.clear()
            flash("Session expired or unauthorized.", "warning")
            return redirect(url_for('login'))

        # Block if user has been deleted
        user = User.query.get(user_id)
        if not user:
            session.clear()
            flash("Your account was removed.", "danger")
            return redirect(url_for('login'))


    

    



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
                account_number=form.account_number.data,
                starting_check_number=form.starting_check_number.data
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
        form.default_bank_id.choices = [(0, '-- Select Bank -- ')] + [(b.id, b.name) for b in Bank.query.all()]
        
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
            if isinstance(form.logo.data, FileStorage) and form.logo.data.filename:
                try:
                    logo_data = form.logo.data.read()
                    import base64
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
            if isinstance(form.logo.data, FileStorage) and form.logo.data.filename:
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
        form = EmployeeForm()
        # Populate client choices
        clients = CompanyClient.query.all()
        form.client_id.choices = [(c.id, c.name) for c in clients]

        if form.validate_on_submit():
            selected_client = CompanyClient.query.get(form.client_id.data)
            employee = Employee(
                name=form.name.data,
                title=form.title.data,
                client_id=selected_client.id,
                company_id=selected_client.company_id  # Auto-fill company based on client
            )
            db.session.add(employee)
            db.session.commit()
            flash('Employee created successfully!', 'success')
            return redirect(url_for('employees_index'))

        return render_template('employees/create.html', form=form)

    
    @app.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
    def employees_edit(id):
        employee = Employee.query.get_or_404(id)
        form = EmployeeForm(obj=employee)

        # Populate client dropdown
        clients = CompanyClient.query.all()
        form.client_id.choices = [(c.id, c.name) for c in clients]

        if form.validate_on_submit():
            employee.name = form.name.data
            employee.title = form.title.data
            employee.client_id = form.client_id.data
            employee.company_id = CompanyClient.query.get(form.client_id.data).company_id
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
        client_id = request.args.get('client_id', type=int)
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
        if client_id:
            query = query.filter(Check.client_id == client_id)
        if employee_id:
            query = query.filter(Check.employee_id == employee_id)
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Check.date >= start_date)
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Check.date <= end_date)
        
        grouped_checks = defaultdict(lambda: defaultdict(list))
        checks = query.order_by(Check.date.desc(), Check.check_number.desc()).all()

        for check in checks:
            client_name = check.client.name if check.client else "No Client"
            week_key = check.date.strftime("%Y-W%U")
            grouped_checks[client_name][week_key].append(check)
                
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

        if session.get('role') == 'admin':
            clients = CompanyClient.query.all()
        else:
            user_id = session.get('user_id')
            assigned_client_ids = [a.client_id for a in UserClientAssignment.query.filter_by(user_id=user_id).all()]
            clients = CompanyClient.query.filter(CompanyClient.id.in_(assigned_client_ids)).all()


        return render_template(
            'checks/index.html',
            grouped_checks=grouped_checks,
            banks=banks,
            clients=clients, 
            companies=companies,
            employees=employees,
            bank_id=bank_id,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            client_id=client_id
        )
        
    

    @app.route('/checks/create', methods=['GET', 'POST'])
    @login_required
    def checks_create():
        form = CheckForm()
        user_id = session.get('user_id')
        is_admin = session.get('role') == 'admin'

        # STEP 1: Determine selected client (early)
        selected_client_id = request.form.get('client_id', type=int) or form.client_id.data

        if not is_admin and request.method == 'POST' and selected_client_id:
            client = CompanyClient.query.get(selected_client_id)
            if client and client.company_id:
                form.company_id.data = client.company_id
                company = Company.query.get(client.company_id)

                if company:
                    choice = (company.id, company.name)

                    if not hasattr(form, "company_id") or form.company_id is None:
                        from wtforms import SelectField
                        form.company_id = SelectField("Company", coerce=int, choices=[choice])
                    elif not getattr(form.company_id, "choices", None):
                        form.company_id.choices = [choice]
                    elif choice not in form.company_id.choices:
                        form.company_id.choices.append(choice)
                else:
                    print("⚠️ Client has company_id but company not found in DB")
            else:
                    print("⚠️ No company_id found for selected client or client is None")


        # STEP 2: Populate dropdowns
        if is_admin:
            form.bank_id.choices = [(b.id, b.name) for b in Bank.query.all()]
            form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
            form.employee_id.choices = [(e.id, e.name) for e in Employee.query.all()]
        else:
            companies = db.session.query(Company).join(UserCompanyAssignment).filter(
                UserCompanyAssignment.user_id == user_id
            ).all()
            form.company_id.choices = [(c.id, c.name) for c in companies]
            form.bank_id.choices = []  # will be fetched from default_bank_id later

        if is_admin:
            form.client_id.choices = [(0, '-- Select Client --')] + [
                (c.id, c.name) for c in CompanyClient.query.all()
            ]
        else:
            assigned_ids = [a.client_id for a in UserClientAssignment.query.filter_by(user_id=user_id).all()]
            form.client_id.choices = [(0, '-- Select Client --')] + [
                (c.id, c.name) for c in CompanyClient.query.filter(CompanyClient.id.in_(assigned_ids)).all()
            ]

        if selected_client_id:
            form.employee_id.choices = [
                (e.id, e.name) for e in Employee.query.filter_by(client_id=selected_client_id).all()
            ]
        else:
            form.employee_id.choices = []

        # STEP 3: Form submission
        if form.validate_on_submit():
            try:
                if is_admin:
                    bank = Bank.query.get(form.bank_id.data)
                else:
                    company = Company.query.get(form.company_id.data)
                    bank = Bank.query.get(company.default_bank_id) if company else None

                if not bank:
                    flash('No valid bank found for the selected company.', 'danger')
                    return redirect(url_for('checks_create'))

                
                check_number = get_next_check_number_by_bank(bank.id)

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
                db.session.add(check)
                db.session.commit()
                flash(f'✅ Check #{check_number} created successfully!', 'success')
                return redirect(url_for('checks_index'))

            except Exception as e:
                print("❌ Error during check creation:", str(e))
                flash(f'Something went wrong: {e}', 'danger')

        elif request.method == 'POST':
            print("❌ FORM INVALID")
            print(form.errors)
            flash('Please fix the errors in the form.', 'danger')

        return render_template('checks/create.html', form=form)


    
    @app.route('/api/assigned-clients/<int:user_id>')
    @role_required('admin')
    def get_assigned_clients(user_id):
        assignments = UserClientAssignment.query.filter_by(user_id=user_id).all()
        data = []
        for a in assignments:
            data.append({
                "client_id": a.client.id,
                "client_name": a.client.name,
                "company_name": a.client.company.name if a.client.company else "NO COMPANY"
            })
        return jsonify(data)



    @app.route('/assign-clients', methods=['GET', 'POST'])
    @role_required('admin')
    def assign_clients():
        form = CSRFOnlyForm()
        users = User.query.filter(User.role != 'admin').all()
        clients = CompanyClient.query.all()

        if request.method == 'POST':
            user_id = int(request.form.get('user_id'))
            selected_client_ids = request.form.getlist('client_ids')

            print(f"🔄 Reassigning clients for user_id={user_id}")
            print(f"📝 Selected client IDs: {selected_client_ids}")

            # Clear previous assignments
            UserClientAssignment.query.filter_by(user_id=user_id).delete()
            print("🧹 Cleared previous client assignments.")

            for client_id in selected_client_ids:
                client = CompanyClient.query.get(int(client_id))
                if client:
                    db.session.add(UserClientAssignment(user_id=user_id, client_id=client.id))
                    print(f"✅ Assigned client '{client.name}' (ID={client.id})")

                    if client.company_id:
                        existing = UserCompanyAssignment.query.filter_by(
                            user_id=user_id,
                            company_id=client.company_id
                        ).first()

                        print(f"🔍 Client's company_id: {client.company_id}")
                        if not existing:
                            db.session.add(UserCompanyAssignment(user_id=user_id, company_id=client.company_id))
                            print(f"🏢 Assigned company_id={client.company_id} for client '{client.name}'")
                        else:
                            print(f"⏩ Company already assigned: {client.company_id}")

            db.session.commit()
            print("✅ DB commit completed.")
            flash('Client (and related company) assignments updated successfully.', 'success')
            return redirect(url_for('assign_clients'))

        return render_template('admin/assign_clients.html', users=users, clients=clients, form=form)





    @app.route('/checks/batch', methods=['GET', 'POST'])
    @login_required
    def checks_batch():
        """Create multiple checks at once (dynamically added like single check)."""
        form = BatchCheckForm()
        user_id = session.get('user_id')
        is_admin = session.get('role') == 'admin'

        # Populate choices
        form.bank_id.choices = [(b.id, b.name) for b in Bank.query.all()]
        if is_admin:
            form.company_id.choices = [(c.id, c.name) for c in Company.query.all()]
        else:
            companies = db.session.query(Company).join(UserCompanyAssignment).filter(
                UserCompanyAssignment.user_id == user_id
            ).all()
            form.company_id.choices = [(c.id, c.name) for c in companies]

        selected_company_id = request.form.get('company_id', type=int) or form.company_id.data

        # Populate client dropdown
        if is_admin:
            clients = CompanyClient.query.all()
        else:
            assigned_ids = [a.client_id for a in UserClientAssignment.query.filter_by(user_id=user_id).all()]
            clients = CompanyClient.query.filter(CompanyClient.id.in_(assigned_ids)).all()
        form.client_id.choices = [(0, '-- Select Client --')] + [(c.id, c.name) for c in clients]

        if request.method == 'POST':
            client_id = request.form.get('client_id', type=int)
            client = CompanyClient.query.get(client_id) if client_id else None
            company_id = client.company_id if client else None

            company = Company.query.get(company_id) if company_id else None

            if not company and not is_admin:
                flash('Please select a company.', 'danger')
                return redirect(url_for('checks_batch'))

            if is_admin:
                company_id = request.form.get('company_id', type=int)
                company = Company.query.get(company_id)
                bank_id = company.default_bank_id if company else None
                bank = Bank.query.get(bank_id) if bank_id else None
            else:
                bank_id = company.default_bank_id
                bank = Bank.query.get(bank_id) if bank_id else None


            if not bank:
                flash('No valid bank found for the selected company.', 'danger')
                return redirect(url_for('checks_batch'))

            date_str = request.form.get('date')
            try:
                check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                flash('Invalid or missing date.', 'danger')
                return redirect(url_for('checks_batch'))

            client_id = request.form.get('client_id', type=int)
            client_id = client_id if client_id and client_id > 0 else None

            # Collect all employee rows from DOM (dynamic)
            employee_ids = request.form.getlist('employee_id')
            amounts = request.form.getlist('amount')
            memos = request.form.getlist('memo')
            hours_worked_list = request.form.getlist('hours_worked')
            pay_rates = request.form.getlist('pay_rate')
            overtime_hours_list = request.form.getlist('overtime_hours')
            overtime_rates = request.form.getlist('overtime_rate')
            holiday_hours_list = request.form.getlist('holiday_hours')
            holiday_rates = request.form.getlist('holiday_rate')

            if len(employee_ids) != len(amounts) or not employee_ids:
                flash('Invalid employee or amount data.', 'danger')
                return redirect(url_for('checks_batch'))

            created_checks = []
            for i in range(len(employee_ids)):
                try:
                    emp_id = int(employee_ids[i]) if employee_ids[i] else None
                    amount = float(amounts[i]) if amounts[i] else None
                    if not emp_id or not amount or amount <= 0:
                        raise ValueError("Invalid employee or amount")

                   
                    check_number = get_next_check_number_by_bank(bank.id)

                    check = Check(
                        bank_id=bank_id,
                        company_id=company_id,
                        employee_id=emp_id,
                        client_id=client_id,
                        amount=amount,
                        date=check_date,
                        check_number=check_number,
                        memo=memos[i] if i < len(memos) else None,
                        hours_worked=float(hours_worked_list[i]) if i < len(hours_worked_list) and hours_worked_list[i] else None,
                        pay_rate=float(pay_rates[i]) if i < len(pay_rates) and pay_rates[i] else None,
                        overtime_hours=float(overtime_hours_list[i]) if i < len(overtime_hours_list) and overtime_hours_list[i] else None,
                        overtime_rate=float(overtime_rates[i]) if i < len(overtime_rates) and overtime_rates[i] else None,
                        holiday_hours=float(holiday_hours_list[i]) if i < len(holiday_hours_list) and holiday_hours_list[i] else None,
                        holiday_rate=float(holiday_rates[i]) if i < len(holiday_rates) and holiday_rates[i] else None,
                        created_by_id=user_id
                    )
                    db.session.add(check)
                    created_checks.append(check)

                except (ValueError, TypeError) as e:
                    flash(f'Error in row {i+1}: {str(e)}', 'danger')
                    return redirect(url_for('checks_batch'))

            db.session.commit()
            flash(f"Successfully created {len(created_checks)} checks.", 'success')
            return redirect(url_for('checks_index'))

        # Preload employees for JS
        if is_admin:
            employees = Employee.query.all()
        else:
            assigned_client_ids = [a.client_id for a in UserClientAssignment.query.filter_by(user_id=user_id).all()]
            employees = Employee.query.filter(
                (Employee.client_id.in_(assigned_client_ids)) | (Employee.client_id == None)
            ).all()

        employees_json = [
            {
                'id': e.id,
                'name': e.name,
                'company_id': e.company_id,
                'client_id': e.client_id if e.client_id is not None else 0
            }
            for e in employees
        ]

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
    @app.route('/api/employees/by-client/<int:client_id>')
    def employees_by_client(client_id):
        employees = Employee.query.filter_by(client_id=client_id).all()
        return jsonify([{'id': e.id, 'name': e.name} for e in employees])

        
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
    
    @app.route('/delete-user/<int:user_id>', methods=['POST'])
    @role_required('admin')  # optional, but good to enforce
    def delete_user(user_id):
        user = User.query.get(user_id)
        if user:
            try:
                # Delete assignments first
                UserClientAssignment.query.filter_by(user_id=user_id).delete()
                UserCompanyAssignment.query.filter_by(user_id=user_id).delete()

                db.session.delete(user)
                db.session.commit()
                return jsonify({'success': True}), 200
            except Exception as e:
                print(f"❌ Error deleting user: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        return jsonify({'error': 'User not found'}), 404

    
    @app.route('/checks/download-selected', methods=['POST'])
    @login_required
    @role_required('admin')
    def bulk_download_checks_pdf():
        check_ids = request.form.getlist('check_ids')
        if not check_ids:
            flash("No checks selected for export.", "warning")
            return redirect(url_for('checks_index'))

        # Fetch checks
        checks = Check.query.filter(Check.id.in_(check_ids)).order_by(Check.check_number).all()

        # Create ZIP with one PDF per check
        from io import BytesIO
        import zipfile
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for check in checks:
                pdf_bytes = generate_clean_check(check)
  # <- your PDF function returning BytesIO or bytes
                filename = f"Check_{check.check_number}.pdf"
                zf.writestr(filename, pdf_bytes.getvalue() if hasattr(pdf_bytes, 'getvalue') else pdf_bytes)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            download_name='selected_checks.zip',
            as_attachment=True
        )


    @app.route("/checks/export/<int:client_id>/xlsx")
    @login_required
    def export_checks_by_client_excel(client_id):
        checks = Check.query.filter_by(client_id=client_id).join(Company).join(Employee).order_by(Check.date, Check.check_number).all()

        # Group by ISO week
        grouped = defaultdict(list)
        for check in checks:
            week = check.date.strftime("%Y-W%U")  # Week number (Sunday start)
            grouped[week].append(check)

        writer = pd.ExcelWriter("checks_export.xlsx", engine='xlsxwriter')
        for week, week_checks in grouped.items():
            data = []
            for check in sorted(week_checks, key=lambda c: c.check_number):
                data.append({
                    "Check #": check.check_number,
                    "Date": check.date.strftime("%-m/%-d/%y"),
                    "Amount": check.amount,
                    "Employee": check.employee.name if check.employee else "",
                    "Client": check.client.name if check.client else "",
                    "Company": check.company.name if check.company else "",
                })

            df = pd.DataFrame(data)
            df.to_excel(writer, index=False, sheet_name=week[:31])  # Excel sheet names max length = 31 chars

        output = BytesIO()
        writer.close()
        with open("checks_export.xlsx", "rb") as f:
            output.write(f.read())
        output.seek(0)

        return send_file(output,
                        download_name=f"client_{client_id}_checks.xlsx",
                        as_attachment=True,
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



    @app.route('/add-user', methods=['GET', 'POST'])
    @role_required('admin')
    def add_user():
        form = AddUserForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            # Hash password and create user
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_password, role='user')

            db.session.add(new_user)
            db.session.commit()
            flash("User added successfully", "success")
            return redirect(url_for('assign_clients'))

        return render_template('admin/add_user.html', form=form)


                    

