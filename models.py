from datetime import datetime
from app import db

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

class Company(db.Model):
    """Model for company information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    
    # Relationships
    employees = db.relationship('Employee', backref='company', lazy=True, cascade="all, delete-orphan")
    checks = db.relationship('Check', backref='company', lazy=True, cascade="all, delete-orphan")
    
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
    
    # Foreign Keys
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    def __repr__(self):
        return f'<Check #{self.check_number} for ${self.amount}>'
