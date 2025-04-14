import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from app.models.models import db, User
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_recruitment.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # Temporarily disable CSRF protection
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 25))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'yes', '1']
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'yes', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', None)
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', None)
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'JobMatch <noreply@jobmatch.com>')
    app.config['MAIL_MAX_EMAILS'] = int(os.environ.get('MAIL_MAX_EMAILS', 50))
    app.config['MAIL_DEBUG'] = app.debug
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Exempt API routes from CSRF protection
    csrf.exempt("/api/*")
    
    # Register blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.jobs import jobs
    from app.routes.profiles import profiles
    from app.routes.insights import insights
    from app.routes.interviews import interviews
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(jobs)
    app.register_blueprint(profiles)
    app.register_blueprint(insights)
    app.register_blueprint(interviews)
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 