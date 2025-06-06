from datetime import datetime
from app import db
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    routing_number = db.Column(db.String(9), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    last_check_number = db.Column(db.Integer, default=1000)

    checks = db.relationship('Check', backref='bank', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Bank {self.name}>'

    def get_next_check_number(self):
        self.last_check_number += 1
        return self.last_check_number

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserCompanyAssignment(db.Model):
    __tablename__ = 'user_company_assignment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    user = db.relationship('User', backref='company_assignments')
    company = db.relationship('Company', backref='user_assignments')

class CompanyClient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    def __repr__(self):
        return f'<CompanyClient {self.name}>'

class Company(db.Model):
    """Model for company information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    logo = db.Column(db.Text, nullable=True)  # Store as base64 encoded string
    default_bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=True)
    
    # Relationships
    employees = db.relationship('Employee', backref='company', lazy=True, cascade="all, delete-orphan")
    clients = db.relationship('CompanyClient', backref='company', lazy=True, cascade="all, delete-orphan")
    default_bank = db.relationship('Bank', backref='companies')
    
    def __repr__(self):
        return f'<Company {self.name}>'


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('company_client.id'), nullable=True)

    client = db.relationship('CompanyClient', backref='employees', foreign_keys=[client_id])

    checks = db.relationship('Check', backref='employee', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Employee {self.name}>'


class UserClientAssignment(db.Model):
    __tablename__ = 'user_client_assignment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('company_client.id'), nullable=False)

    user = db.relationship('User', backref='client_assignments')
    client = db.relationship('CompanyClient', backref='user_assignments')

class Check(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_number = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    flagged_by_user = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(255), nullable=True)

    hours_worked = db.Column(db.Numeric(6, 2), nullable=True)
    pay_rate = db.Column(db.Numeric(10, 2), nullable=True)
    overtime_hours = db.Column(db.Numeric(6, 2), nullable=True)
    overtime_rate = db.Column(db.Numeric(10, 2), nullable=True)
    holiday_hours = db.Column(db.Numeric(6, 2), nullable=True)
    holiday_rate = db.Column(db.Numeric(10, 2), nullable=True)
    memo = db.Column(db.String(200), nullable=True)

    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('company_client.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    company = db.relationship('Company', backref='check_records', foreign_keys=[company_id])
    client = db.relationship('CompanyClient', backref='check_records', foreign_keys=[client_id])
    created_by = db.relationship('User', backref='created_checks')

    def __repr__(self):
        return f'<Check #{self.check_number} for ${self.amount}>'

    def calculate_amount(self):
        total = 0
        if self.hours_worked and self.pay_rate:
            total += float(self.hours_worked) * float(self.pay_rate)
        if self.overtime_hours and self.overtime_rate:
            total += float(self.overtime_hours) * float(self.overtime_rate)
        if self.holiday_hours and self.holiday_rate:
            total += float(self.holiday_hours) * float(self.holiday_rate)
        return total
