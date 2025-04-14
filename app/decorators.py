from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def recruiter_required(f):
    """
    Decorator for views that require the user to be a recruiter.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_recruiter():
            flash('This action requires recruiter privileges.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def interviewer_required(f):
    """
    Decorator for views that require the user to be an interviewer or recruiter.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # In a more complex system, there would be a separate interviewer role.
        # Here, we assume all recruiters can be interviewers.
        if not current_user.is_recruiter():
            flash('This action requires interviewer privileges.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """
    Decorator for views that require the user to have admin privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Check if user has admin role or privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            abort(403)  # Forbidden
        
        return f(*args, **kwargs)
    
    return decorated_function

def applicant_required(f):
    """
    Decorator for views that require the user to be an applicant.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_applicant():
            flash('This action requires applicant privileges.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    
    return decorated_function 