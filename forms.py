from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, FieldList, FormField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange
import datetime

class BankForm(FlaskForm):
    """Form for adding or editing banks."""
    name = StringField('Bank Name', validators=[DataRequired(), Length(min=2, max=100)])
    routing_number = StringField('Routing Number', validators=[DataRequired(), Length(min=9, max=9)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=5, max=20)])
    
    def validate_routing_number(self, field):
        # Basic validation for routing numbers (9 digits)
        if not field.data.isdigit() or len(field.data) != 9:
            raise ValidationError('Routing number must be exactly 9 digits')
    
    def validate_account_number(self, field):
        # Basic validation for account numbers (between 5-20 digits)
        if not field.data.isdigit() or len(field.data) < 5:
            raise ValidationError('Account number must be at least 5 digits')

class CompanyForm(FlaskForm):
    """Form for adding or editing companies."""
    name = StringField('Company Name', validators=[DataRequired(), Length(min=2, max=100)])
    address = StringField('Address', validators=[DataRequired(), Length(min=5, max=200)])

class EmployeeForm(FlaskForm):
    """Form for adding or editing employees."""
    name = StringField('Employee Name', validators=[DataRequired(), Length(min=2, max=100)])
    title = StringField('Job Title', validators=[DataRequired(), Length(min=2, max=100)])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])

class CheckForm(FlaskForm):
    """Form for creating a single check."""
    bank_id = SelectField('Bank', coerce=int, validators=[DataRequired()])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    date = DateField('Date', validators=[DataRequired()], default=datetime.date.today)

class BatchCheckEmployeeItem(FlaskForm):
    """Subform for batch check creation."""
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])

class BatchCheckForm(FlaskForm):
    """Form for creating multiple checks at once."""
    bank_id = SelectField('Bank', coerce=int, validators=[DataRequired()])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.date.today)
    # This field will be dynamically populated with JavaScript
