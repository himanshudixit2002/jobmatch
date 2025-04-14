from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class JobForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired(), Length(min=5, max=120)])
    description = TextAreaField('Job Description', validators=[DataRequired(), Length(min=20)])
    location = StringField('Location', validators=[DataRequired(), Length(max=120)])
    salary = StringField('Salary Range', validators=[Optional(), Length(max=80)])
    experience_required = IntegerField('Experience Required (years)', validators=[Optional(), NumberRange(min=0, max=30)])
    skills = SelectMultipleField('Required Skills', coerce=int)
    submit = SubmitField('Post Job')

class ApplicationForm(FlaskForm):
    cover_letter = TextAreaField('Cover Letter', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Apply') 