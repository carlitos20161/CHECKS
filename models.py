from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Bank(db.Model):
    """Model for bank information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    routing_number = db.Column(db.String(9), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    last_check_number = db.Column(db.Integer, default=1000)
    
    # Relationship with checks
    checks = db.relationship('Check', backref='bank', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Bank {self.name}>'
    
    def get_next_check_number(self):
        """Generate the next check number and update the last_check_number."""
        self.last_check_number += 1
        return self.last_check_number
    

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CompanyClient(db.Model):
    """Model for company clients."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    
    # Foreign Key
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
    checks = db.relationship('Check', backref='company', lazy=True, cascade="all, delete-orphan")
    clients = db.relationship('CompanyClient', backref='company', lazy=True, cascade="all, delete-orphan")
    default_bank = db.relationship('Bank', backref='companies')
    
    def __repr__(self):
        return f'<Company {self.name}>'

class Employee(db.Model):
    """Model for employee information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    
    # Relationship with checks
    checks = db.relationship('Check', backref='employee', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Employee {self.name}>'

class Check(db.Model):
    """Model for check information."""
    id = db.Column(db.Integer, primary_key=True)
    check_number = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    # Pay calculation fields
    hours_worked = db.Column(db.Numeric(6, 2), nullable=True)
    pay_rate = db.Column(db.Numeric(10, 2), nullable=True)
    overtime_hours = db.Column(db.Numeric(6, 2), nullable=True)
    overtime_rate = db.Column(db.Numeric(10, 2), nullable=True)
    holiday_hours = db.Column(db.Numeric(6, 2), nullable=True)
    holiday_rate = db.Column(db.Numeric(10, 2), nullable=True)
    memo = db.Column(db.String(200), nullable=True)
    
    # Foreign Keys
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('company_client.id'), nullable=True)
    
    # Relationships for the new foreign key
    client = db.relationship('CompanyClient', backref='checks', lazy=True)
    
    def __repr__(self):
        return f'<Check #{self.check_number} for ${self.amount}>'
        
    def calculate_amount(self):
        """Calculate check amount based on hours worked and rates."""
        total = 0
        
        # Regular hours
        if self.hours_worked is not None and self.pay_rate is not None:
            total += float(self.hours_worked) * float(self.pay_rate)
            
        # Overtime hours
        if self.overtime_hours is not None and self.overtime_rate is not None:
            total += float(self.overtime_hours) * float(self.overtime_rate)
            
        # Holiday hours
        if self.holiday_hours is not None and self.holiday_rate is not None:
            total += float(self.holiday_hours) * float(self.holiday_rate)
            
        return total
