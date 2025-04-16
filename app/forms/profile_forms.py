from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed

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

class ResumeParserForm(FlaskForm):
    resume_file = FileField('Upload Resume', 
                          validators=[
                              Optional(),
                              FileAllowed(['txt', 'pdf', 'docx'], 'Only plain text, PDF, and Word files are allowed.')
                          ])
    resume_text = TextAreaField('Or paste resume text',
                              validators=[Optional()])
    apply_to_profile = BooleanField('Apply extracted data to my profile', default=True)
    submit = SubmitField('Parse Resume')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if not self.resume_file.data and not self.resume_text.data:
            self.resume_file.errors.append('Please either upload a file or paste resume text.')
            return False
        return True