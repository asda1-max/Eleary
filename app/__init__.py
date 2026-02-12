import os
from flask import Flask, request, redirect, url_for
from models import (db, User, Course, CourseModule, CourseMaterial, LibraryBook, AttendanceLog, CourseEnrollment, News,
                    StudentProfile, LegalDocument, DigitalAgreement, ElearningModule, ElearningProgress, ClinicalConfig,
                    PreClinicalAssessment, LogbookEntry, PatientCase, PatientCaseDailyUpdate,
                    CompetencyChecklist, CompetencyProgress, DailyJournal, WeeklyAssessment, FinalExam, Evaluation360,
                    ClinicalCertificate, IncidentReport, StudentFeedback, AlumniProfile, SupervisorValidationPIN)
from app.extensions import login_manager
from app.routes.auth import register_auth_routes
from app.routes.courses import register_course_routes
from app.routes.library import register_library_routes
from app.routes.news import register_news_routes
from app.routes.admin import register_admin_routes
from app.routes.errors import register_error_handlers
from app.routes.uploads import register_upload_routes
from app.routes.clinical import register_clinical_routes


def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static')
    )

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eleary.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['APP_SETUP_PASSWORD'] = os.getenv('APP_SETUP_PASSWORD', 'diponegoro')

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register routes
    register_auth_routes(app)
    register_course_routes(app)
    register_library_routes(app)
    register_news_routes(app)
    register_admin_routes(app)
    register_error_handlers(app)
    register_upload_routes(app)
    register_clinical_routes(app)

    @app.before_request
    def ensure_first_admin():
        if request.endpoint in {None, 'static', 'setup_admin'}:
            return
        if User.query.filter_by(role='admin').first() is None:
            return redirect(url_for('setup_admin'))

    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Course': Course,
            'CourseModule': CourseModule,
            'CourseMaterial': CourseMaterial,
            'LibraryBook': LibraryBook,
            'AttendanceLog': AttendanceLog,
            'CourseEnrollment': CourseEnrollment,
            'News': News,
            'StudentProfile': StudentProfile,
            'LogbookEntry': LogbookEntry,
            'CompetencyProgress': CompetencyProgress,
            'DailyJournal': DailyJournal,
        }

    return app
