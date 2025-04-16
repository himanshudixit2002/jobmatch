from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.models import db, User, Skill, Application, Job, RecruiterNote
from app.forms.profile_forms import ProfileForm, SkillForm, ResumeParserForm
from app.utils.resume_parser import parse_resume, extract_skills_from_resume
from datetime import datetime
import os
import io

profiles = Blueprint('profiles', __name__)

@profiles.route('/profile')
@login_required
def view_profile():
    """View current user profile"""
    return render_template('profiles/view.html', title='My Profile', user=current_user)

@profiles.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit current user profile"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        try:
            # Start a database transaction
            db_session = db.session
            
            # Update user profile
            current_user.name = form.name.data
            
            # Update user type specific fields
            if current_user.is_recruiter():
                current_user.company = form.company.data
                current_user.position = form.position.data
            else:
                current_user.experience = form.experience.data
                current_user.education = form.education.data
                
                # Check if resume was updated
                if form.resume.data != current_user.resume:
                    current_user.resume = form.resume.data
                    
                    # Parse resume with Gemini API if there's content
                    if current_user.resume and current_user.resume.strip():
                        try:
                            # Parse the resume
                            parsed_data = parse_resume(current_user.resume)
                            
                            if parsed_data["success"]:
                                # Update user information from parsed data
                                if parsed_data["education"] and not current_user.education:
                                    current_user.education = parsed_data["education"]
                                    
                                if parsed_data["experience"] and not current_user.experience:
                                    current_user.experience = parsed_data["experience"]
                                
                                # Add extracted skills
                                if parsed_data["skills"]:
                                    skills_added = 0
                                    for skill_name in parsed_data["skills"]:
                                        skill_name = skill_name.strip().lower()
                                        if not skill_name:
                                            continue
                                        
                                        # Check if skill already exists in database
                                        existing_skill = Skill.query.filter(Skill.name.ilike(skill_name)).first()
                                        
                                        if existing_skill:
                                            # Add existing skill to user if not already added
                                            if existing_skill not in current_user.skills:
                                                current_user.skills.append(existing_skill)
                                                skills_added += 1
                                        else:
                                            # Create new skill
                                            new_skill = Skill(name=skill_name)
                                            db_session.add(new_skill)
                                            current_user.skills.append(new_skill)
                                            skills_added += 1
                                    
                                    if skills_added > 0:
                                        flash(f'Added {skills_added} skills extracted from your resume!', 'success')
                        except Exception as e:
                            current_app.logger.error(f"Error in resume parsing: {str(e)}")
                else:
                    current_user.resume = form.resume.data
            
            # Commit all changes to the database
            db_session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profiles.view_profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating your profile. Please try again.', 'danger')
    
    return render_template('profiles/edit.html', title='Edit Profile', form=form)

@profiles.route('/profile/skills', methods=['GET', 'POST'])
@login_required
def manage_skills():
    """Manage user skills (for applicants)"""
    if not current_user.is_applicant():
        flash('Only applicants can manage skills.', 'danger')
        return redirect(url_for('profiles.view_profile'))
    
    # Get all available skills
    all_skills = Skill.query.all()
    
    # Handle adding a new skill
    form = SkillForm()
    if form.validate_on_submit():
        try:
            skill_name = form.name.data.strip().lower()
            
            if not skill_name:
                flash('Skill name cannot be empty.', 'danger')
                return redirect(url_for('profiles.manage_skills'))
                
            # Check if skill already exists
            existing_skill = Skill.query.filter(Skill.name.ilike(skill_name)).first()
            
            if existing_skill:
                # Add existing skill to user if not already added
                if existing_skill not in current_user.skills:
                    current_user.skills.append(existing_skill)
                    db.session.commit()
                    flash(f'Skill "{existing_skill.name}" added!', 'success')
                else:
                    flash(f'You already have this skill.', 'warning')
            else:
                # Create new skill
                new_skill = Skill(name=skill_name)
                db.session.add(new_skill)
                current_user.skills.append(new_skill)
                db.session.commit()
                flash(f'New skill "{new_skill.name}" created and added!', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error managing skills: {str(e)}")
            flash('An error occurred. Please try again.', 'danger')
            
        return redirect(url_for('profiles.manage_skills'))
    
    return render_template(
        'profiles/skills.html', 
        title='Manage Skills', 
        user_skills=current_user.skills,
        all_skills=all_skills,
        form=form
    )

@profiles.route('/profile/skills/remove/<int:skill_id>', methods=['POST'])
@login_required
def remove_skill(skill_id):
    """Remove a skill from user profile"""
    if not current_user.is_applicant():
        flash('Only applicants can manage skills.', 'danger')
        return redirect(url_for('profiles.view_profile'))
    
    try:
        skill = Skill.query.get_or_404(skill_id)
        
        if skill in current_user.skills:
            current_user.skills.remove(skill)
            db.session.commit()
            flash(f'Skill "{skill.name}" removed!', 'success')
        else:
            flash('This skill is not in your profile.', 'warning')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing skill: {str(e)}")
        flash('An error occurred while removing the skill. Please try again.', 'danger')
    
    return redirect(url_for('profiles.manage_skills'))

@profiles.route('/profile/applications')
@login_required
def view_applications():
    """View applicant's job applications"""
    if not current_user.is_applicant():
        flash('Only applicants can view their applications.', 'danger')
        return redirect(url_for('profiles.view_profile'))
    
    try:
        # Get all applications with related job and recruiter data
        applications = Application.query.filter_by(
            applicant_id=current_user.id
        ).order_by(
            Application.created_at.desc()
        ).all()
        
        # Ensure match_score isn't None
        for app in applications:
            if app.match_score is None:
                # Calculate and update the match score
                job = Job.query.get(app.job_id)
                if job:
                    app.match_score = job.match_score(current_user)
        
        # Commit any updates to match_score
        if any(app.match_score is None for app in applications):
            db.session.commit()
        
        return render_template(
            'profiles/applications.html', 
            title='My Applications', 
            applications=applications
        )
    except Exception as e:
        current_app.logger.error(f"Error loading applications: {str(e)}")
        flash('An error occurred while loading your applications.', 'danger')
        return redirect(url_for('profiles.view_profile'))

@profiles.route('/profile/applications/<int:application_id>/accept-offer', methods=['POST'])
@login_required
def accept_job_offer(application_id):
    """Accept a job offer"""
    if not current_user.is_applicant():
        flash('Only applicants can accept job offers.', 'danger')
        return redirect(url_for('profiles.view_profile'))
    
    try:
        # Get the application
        application = Application.query.get_or_404(application_id)
        
        # Verify application belongs to current user
        if application.applicant_id != current_user.id:
            flash('You can only accept offers for your own applications.', 'danger')
            return redirect(url_for('profiles.view_applications'))
        
        # Verify application status is 'offered'
        if application.status != 'offered':
            flash('This application is not in offered status.', 'warning')
            return redirect(url_for('profiles.view_applications'))
        
        # Update application with accepted status (could be a new status)
        application.status = 'accepted'
        application.updated_at = datetime.utcnow()
        
        # You might want to update other applications for this user
        # For example, mark other active applications as withdrawn
        other_applications = Application.query.filter(
            Application.applicant_id == current_user.id,
            Application.id != application_id,
            Application.status.in_(['pending', 'reviewed', 'interviewed'])
        ).all()
        
        for other_app in other_applications:
            other_app.status = 'withdrawn'
            other_app.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Get job details for the message
        job = Job.query.get(application.job_id)
        company = job.recruiter.company if job and job.recruiter else "the company"
        
        flash(f'Congratulations! You have accepted the job offer from {company}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error accepting job offer: {str(e)}")
        flash('An error occurred while processing your request.', 'danger')
    
    return redirect(url_for('profiles.view_applications'))

@profiles.route('/applicant/<int:applicant_id>')
@login_required
def view_applicant_profile(applicant_id):
    """View applicant profile (for recruiters)"""
    if not current_user.is_recruiter():
        flash('Access denied. Recruiters only.', 'danger')
        return redirect(url_for('main.index'))
    
    applicant = User.query.get_or_404(applicant_id)
    
    # Only allow viewing of applicants who have applied to recruiter's jobs
    if not applicant.is_applicant():
        flash('User is not an applicant.', 'danger')
        return redirect(url_for('jobs.recruiter_dashboard'))
    
    # Check if the applicant has applied to any of recruiter's jobs
    application = Application.query.join(Job).filter(
        Application.applicant_id == applicant_id,
        Job.recruiter_id == current_user.id
    ).first()
    
    if not application:
        flash('You can only view applicants who have applied to your jobs.', 'danger')
        return redirect(url_for('jobs.recruiter_dashboard'))
    
    # Get all applications from this applicant to this recruiter's jobs
    applications = Application.query.join(Job).filter(
        Application.applicant_id == applicant_id,
        Job.recruiter_id == current_user.id
    ).all()
    
    return render_template(
        'profiles/applicant_view.html',
        title=f'Applicant Profile: {applicant.name}',
        applicant=applicant,
        applications=applications
    )

@profiles.route('/api/applicant/<int:applicant_id>/notes', methods=['POST'])
@login_required
def save_applicant_note(applicant_id):
    """Save recruiter notes about an applicant"""
    if not current_user.is_recruiter():
        return jsonify({'error': 'Unauthorized'}), 403
    
    applicant = User.query.get_or_404(applicant_id)
    
    # Verify the applicant has applied to recruiter's jobs
    application = Application.query.join(Job).filter(
        Application.applicant_id == applicant_id,
        Job.recruiter_id == current_user.id
    ).first()
    
    if not application:
        return jsonify({'error': 'You can only add notes for applicants who have applied to your jobs'}), 403
    
    data = request.get_json()
    
    if not data or 'notes' not in data:
        return jsonify({'error': 'Notes content is required'}), 400
    
    # Check if note already exists
    existing_note = RecruiterNote.query.filter_by(
        recruiter_id=current_user.id,
        applicant_id=applicant_id
    ).first()
    
    if existing_note:
        # Update existing note
        existing_note.content = data['notes']
        existing_note.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Notes updated successfully',
            'note_id': existing_note.id
        })
    else:
        # Create new note
        new_note = RecruiterNote(
            recruiter_id=current_user.id,
            applicant_id=applicant_id,
            content=data['notes']
        )
        db.session.add(new_note)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Notes saved successfully',
            'note_id': new_note.id
        })

@profiles.route('/api/applicant/<int:applicant_id>/notes', methods=['GET'])
@login_required
def get_applicant_note(applicant_id):
    """Get recruiter notes about an applicant"""
    if not current_user.is_recruiter():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if note exists
    note = RecruiterNote.query.filter_by(
        recruiter_id=current_user.id,
        applicant_id=applicant_id
    ).first()
    
    if note:
        return jsonify({
            'success': True,
            'content': note.content,
            'updated_at': note.updated_at.isoformat()
        })
    else:
        return jsonify({
            'success': True,
            'content': '',
            'message': 'No notes found'
        })

@profiles.route('/profile/parse-resume', methods=['GET', 'POST'])
@login_required
def parse_resume_view():
    """Parse a resume and extract information"""
    if not current_user.is_applicant():
        flash('Only applicants can use the resume parser.', 'danger')
        return redirect(url_for('profiles.view_profile'))
    
    form = ResumeParserForm()
    parsed_data = None
    
    if form.validate_on_submit():
        resume_text = ""
        
        # Handle file upload
        if form.resume_file.data:
            try:
                # Read the uploaded file
                resume_file = form.resume_file.data
                if resume_file.filename.endswith('.txt'):
                    resume_text = resume_file.read().decode('utf-8')
                elif resume_file.filename.endswith('.pdf'):
                    # Import PyPDF2 for PDF parsing
                    import PyPDF2
                    from io import BytesIO
                    
                    # Read the PDF file
                    pdf_reader = PyPDF2.PdfReader(BytesIO(resume_file.read()))
                    
                    # Extract text from all pages
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        resume_text += page.extract_text() + "\n"
                    
                elif resume_file.filename.endswith('.docx'):
                    # Import docx for DOCX parsing
                    import docx
                    from io import BytesIO
                    
                    # Read the DOCX file
                    doc = docx.Document(BytesIO(resume_file.read()))
                    
                    # Extract text from paragraphs
                    for para in doc.paragraphs:
                        resume_text += para.text + "\n"
                else:
                    flash('Only .txt, .pdf, and .docx files are supported.', 'warning')
                    return redirect(url_for('profiles.parse_resume_view'))
            except Exception as e:
                current_app.logger.error(f"Error reading resume file: {str(e)}")
                flash(f'Error reading the uploaded file: {str(e)}. Please try again.', 'danger')
                return redirect(url_for('profiles.parse_resume_view'))
        # Use pasted text if no file
        elif form.resume_text.data:
            resume_text = form.resume_text.data
        else:
            flash('Please upload a file or paste resume text.', 'warning')
            return redirect(url_for('profiles.parse_resume_view'))
        
        # Parse the resume
        try:
            parsed_data = parse_resume(resume_text)
            
            if not parsed_data["success"]:
                flash(f'Error parsing resume: {parsed_data.get("error", "Unknown error")}', 'danger')
                return redirect(url_for('profiles.parse_resume_view'))
                
            # For debugging
            current_app.logger.info(f"Parsed data: {parsed_data}")
            
        except Exception as e:
            current_app.logger.error(f"Error in resume parsing: {str(e)}")
            flash(f'Error parsing resume: {str(e)}', 'danger')
            return redirect(url_for('profiles.parse_resume_view'))
        
        # Apply parsed data if requested
        if form.apply_to_profile.data:
            try:
                # Update user information from parsed data
                if parsed_data["education"]:
                    # Convert education to string if it's a dictionary
                    if isinstance(parsed_data["education"], dict):
                        education_parts = []
                        if "degree" in parsed_data["education"]:
                            education_parts.append(parsed_data["education"]["degree"])
                        if "field" in parsed_data["education"]:
                            education_parts.append(parsed_data["education"]["field"])
                        current_user.education = " in ".join(education_parts)
                    else:
                        current_user.education = parsed_data["education"]
                    
                if parsed_data["experience"]:
                    current_user.experience = parsed_data["experience"]
                
                # Save resume text
                current_user.resume = resume_text
                
                # Add extracted skills
                if parsed_data["skills"]:
                    skills_added = 0
                    for skill_name in parsed_data["skills"]:
                        skill_name = skill_name.strip().lower()
                        if not skill_name:
                            continue
                        
                        # Check if skill already exists in database
                        existing_skill = Skill.query.filter(Skill.name.ilike(skill_name)).first()
                        
                        if existing_skill:
                            # Add existing skill to user if not already added
                            if existing_skill not in current_user.skills:
                                current_user.skills.append(existing_skill)
                                skills_added += 1
                        else:
                            # Create new skill
                            new_skill = Skill(name=skill_name)
                            db.session.add(new_skill)
                            current_user.skills.append(new_skill)
                            skills_added += 1
                
                db.session.commit()
                flash('Resume parsed and profile updated successfully!', 'success')
                return redirect(url_for('profiles.view_profile'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error updating profile with parsed data: {str(e)}")
                flash(f'Error updating profile: {str(e)}', 'danger')
    
    return render_template('profiles/parse_resume.html', 
                          title='Parse Resume', 
                          form=form,
                          parsed_data=parsed_data) 