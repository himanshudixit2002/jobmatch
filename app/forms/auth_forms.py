from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    user_type = SelectField('Account Type', choices=[('applicant', 'Job Seeker'), ('recruiter', 'Recruiter')])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    # Recruiter specific fields
    company = StringField('Company Name', validators=[Optional(), Length(max=120)])
    position = StringField('Position at Company', validators=[Optional(), Length(max=80)])
    
    # Applicant specific fields
    experience = IntegerField('Years of Experience', validators=[Optional()])
    education = StringField('Highest Education', validators=[Optional(), Length(max=120)])
    
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email address.')
            
    def validate_company(self, company):
        if self.user_type.data == 'recruiter' and not company.data:
            raise ValidationError('Company name is required for recruiters.')
            
    def validate_position(self, position):
        if self.user_type.data == 'recruiter' and not position.data:
            raise ValidationError('Position is required for recruiters.') 