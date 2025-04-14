from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=80)])
    
    # Recruiter specific fields
    company = StringField('Company Name', validators=[Optional(), Length(max=120)])
    position = StringField('Position at Company', validators=[Optional(), Length(max=80)])
    
    # Applicant specific fields
    experience = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0, max=50)])
    education = StringField('Highest Education', validators=[Optional(), Length(max=120)])
    resume = TextAreaField('Resume/CV', validators=[Optional(), Length(max=5000)])
    
    submit = SubmitField('Update Profile')

class SkillForm(FlaskForm):
    name = StringField('Skill Name', validators=[DataRequired(), Length(min=2, max=80)])
    submit = SubmitField('Add Skill')