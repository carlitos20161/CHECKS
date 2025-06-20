from flask_wtf import FlaskForm
from wtforms import FieldList, FormField
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DecimalField, DateField, SelectField, FieldList, FormField, IntegerField, TextAreaField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange, Optional, Email
from wtforms.validators import Optional
import datetime
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
from wtforms import IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms import SubmitField


class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkbox selection."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class BankForm(FlaskForm):
    """Form for adding or editing banks."""
    name = StringField('Bank Name', validators=[DataRequired(), Length(min=2, max=100)])
    routing_number = StringField('Routing Number', validators=[DataRequired(), Length(min=9, max=9)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=5, max=20)])
    starting_check_number = IntegerField('Starting Check Number', validators=[DataRequired(), NumberRange(min=1)], default=1000)
    submit = SubmitField('Submit')
    
    def validate_routing_number(self, field):
        # Basic validation for routing numbers (9 digits)
        if not field.data.isdigit() or len(field.data) != 9:
            raise ValidationError('Routing number must be exactly 9 digits')
    
    def validate_account_number(self, field):
        # Basic validation for account numbers (between 5-20 digits)
        if not field.data.isdigit() or len(field.data) < 5:
            raise ValidationError('Account number must be at least 5 digits')

class CompanyClientForm(FlaskForm):
    """Form for adding or editing company clients."""
    name = StringField('Client Name', validators=[DataRequired(), Length(min=2, max=100)])
    address = StringField('Address', validators=[DataRequired(), Length(min=5, max=200)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(max=100)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])

class CompanyForm(FlaskForm):
    """Form for adding or editing companies."""
    name = StringField('Company Name', validators=[DataRequired(), Length(min=2, max=100)])
    address = StringField('Address', validators=[DataRequired(), Length(min=5, max=200)])
    default_bank_id = SelectField('Default Bank', coerce=int, validators=[Optional()], default='')
    logo = FileField('Company Logo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    clients = MultiCheckboxField('Clients', coerce=int, validators=[Optional()])

class EmployeeForm(FlaskForm):
    """Form for adding or editing employees."""
    name = StringField('Employee Name', validators=[DataRequired(), Length(min=2, max=100)])
    title = StringField('Job Title', validators=[DataRequired(), Length(min=2, max=100)])
    client_id = SelectField("Client", coerce=int, validators=[DataRequired()])


class CheckForm(FlaskForm):
    """Form for creating a single check."""
    bank_id = SelectField('Bank', coerce=int, validators=[Optional()])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Client (Optional)', coerce=int, validators=[Optional()], default='')
    
    # Pay calculation fields (all optional)
    hours_worked = DecimalField('Hours Worked', validators=[Optional(), NumberRange(min=0)])
    pay_rate = DecimalField('Pay Rate ($/hour)', validators=[Optional(), NumberRange(min=0)])
    overtime_hours = DecimalField('Overtime Hours', validators=[Optional(), NumberRange(min=0)])
    overtime_rate = DecimalField('Overtime Rate ($/hour)', validators=[Optional(), NumberRange(min=0)])
    holiday_hours = DecimalField('Holiday Hours', validators=[Optional(), NumberRange(min=0)])
    holiday_rate = DecimalField('Holiday Rate ($/hour)', validators=[Optional(), NumberRange(min=0)])
    
    # Allow manual entry of amount (used if pay calculation fields are empty)
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    memo = TextAreaField('Memo', validators=[Optional(), Length(max=200)])
    date = DateField('Date', validators=[DataRequired()], default=datetime.date.today)
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

    # your custom validation logic here (optional)
        return True

            
        # If pay calculation fields are provided, verify we have at least hours and rate
        if (self.hours_worked.data is not None and self.hours_worked.data > 0 and 
            self.pay_rate.data is None):
            self.pay_rate.errors = ["Pay rate is required if hours are specified"]
            return False
            
        if (self.pay_rate.data is not None and self.pay_rate.data > 0 and 
            self.hours_worked.data is None):
            self.hours_worked.errors = ["Hours worked is required if pay rate is specified"]
            return False
            
        # Validate overtime
        if (self.overtime_hours.data is not None and self.overtime_hours.data > 0 and 
            self.overtime_rate.data is None):
            self.overtime_rate.errors = ["Overtime rate is required if overtime hours are specified"]
            return False
            
        # Validate holiday
        if (self.holiday_hours.data is not None and self.holiday_hours.data > 0 and 
            self.holiday_rate.data is None):
            self.holiday_rate.errors = ["Holiday rate is required if holiday hours are specified"]
            return False
            
        return True

class BatchCheckEmployeeItem(FlaskForm):
    """Subform for batch check creation."""
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    
    # Pay calculation fields (all optional)
    hours_worked = DecimalField('Hours', validators=[Optional(), NumberRange(min=0)])
    pay_rate = DecimalField('Rate', validators=[Optional(), NumberRange(min=0)])
    overtime_hours = DecimalField('OT Hours', validators=[Optional(), NumberRange(min=0)])
    overtime_rate = DecimalField('OT Rate', validators=[Optional(), NumberRange(min=0)])
    holiday_hours = DecimalField('Holiday Hours', validators=[Optional(), NumberRange(min=0)])
    holiday_rate = DecimalField('Holiday Rate', validators=[Optional(), NumberRange(min=0)])
    
    # Manual amount entry
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    memo = TextAreaField('Memo', validators=[Optional(), Length(max=200)])

class BatchCheckForm(FlaskForm):
    """Form for creating multiple checks at once."""
    bank_id = SelectField('Bank', coerce=int, validators=[DataRequired()])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Client (Optional)', coerce=int, validators=[Optional()], default='')
    date = DateField('Date', validators=[DataRequired()], default=datetime.date.today)
    # Employee fields will be dynamically populated with JavaScript
    employees = FieldList(FormField(BatchCheckEmployeeItem), min_entries=1)


class CSRFOnlyForm(FlaskForm):
    """Empty form for CSRF protection in templates that don't use a full form."""
    pass


class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3)])