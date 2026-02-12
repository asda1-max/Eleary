from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    User model for authentication and role management.
    Roles: 'admin', 'pemateri' (instructor), or 'user'
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin', 'pemateri', or 'user'
    pending_role = db.Column(db.String(20), nullable=True)  # Requested role pending admin approval
    division = db.Column(db.String(100), nullable=True)  # e.g., Medical, IT, Admin, Mahasiswa/Koas
    profile_image = db.Column(db.String(255), nullable=True)  # Relative path under /uploads
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploaded_books = db.relationship('LibraryBook', backref='uploader', lazy='dynamic', foreign_keys='LibraryBook.uploader_id')
    attendance_logs = db.relationship('AttendanceLog', backref='user', lazy='dynamic')
    enrollments = db.relationship('CourseEnrollment', backref='user', lazy='dynamic')
    instructed_courses = db.relationship('Course', backref='instructor_user', lazy='dynamic', foreign_keys='Course.instructor_id')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'
    
    def is_pemateri(self):
        """Check if user has pemateri (instructor) role."""
        return self.role == 'pemateri'
    
    def can_manage_courses(self):
        """Check if user can create courses."""
        return self.role in ['admin', 'pemateri']
    
    def __repr__(self):
        return f'<User {self.username}>'


class Course(db.Model):
    """
    Course model for training programs.
    Categories: 'medical', 'admin', 'it'
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # Foreign Key to User
    category = db.Column(db.String(50), default='medical', nullable=False)  # 'medical', 'admin', 'it'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    modules = db.relationship('CourseModule', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    attendance_logs = db.relationship('AttendanceLog', backref='course', lazy='dynamic')
    
    def __repr__(self):
        return f'<Course {self.title}>'


class CourseModule(db.Model):
    """
    Module within a course (e.g., "Pertemuan 1", "Topic 2").
    Used to create the Spada-like sidebar structure.
    """
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)  # Path to module image
    order_index = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('CourseMaterial', backref='module', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CourseModule {self.title}>'


class CourseMaterial(db.Model):
    """
    Learning materials within a module.
    Types: 'pdf', 'video', 'assignment'
    """
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('course_module.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)  # Path to material thumbnail/image
    file_path = db.Column(db.String(255), nullable=True)  # Path to uploaded file or external URL
    type = db.Column(db.String(50), default='pdf', nullable=False)  # 'pdf', 'video', 'assignment'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseMaterial {self.title}>'


class LibraryBook(db.Model):
    """
    Library document model.
    Status: 'pending' (default for user uploads), 'approved', 'rejected'
    """
    id = db.Column(db.Integer, primary_key=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LibraryBook {self.title}>'


class News(db.Model):
    """
    News model for announcements and updates.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)  # HTML content from Quill editor
    image_path = db.Column(db.String(255), nullable=True)  # Path to news image
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='news_articles', lazy=True)
    
    def __repr__(self):
        return f'<News {self.title}>'


class AttendanceLog(db.Model):
    """
    Attendance tracking for users.
    Can be used for general daily attendance or specific course attendance.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True, index=True)  # Optional, can be null for general attendance
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(20), default='present', nullable=False)  # 'present', others if extended
    
    def __repr__(self):
        return f'<AttendanceLog User:{self.user_id} Course:{self.course_id}>'


class CourseEnrollment(db.Model):
    """
    User enrollment in courses.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='uq_user_course'),)
    
    def __repr__(self):
        return f'<CourseEnrollment User:{self.user_id} Course:{self.course_id}>'


class MaterialComment(db.Model):
    """
    Comments on course materials for discussion.
    """
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('course_material.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    material = db.relationship('CourseMaterial', backref='comments', lazy=True)
    author = db.relationship('User', backref='material_comments', lazy=True)
    
    def __repr__(self):
        return f'<MaterialComment Material:{self.material_id} User:{self.user_id}>'


class MaterialSubmission(db.Model):
    """
    Student submissions for exercise/assignment materials.
    """
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('course_material.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    file_path = db.Column(db.String(255), nullable=True)  # Path to submitted file
    text_content = db.Column(db.Text, nullable=True)  # Text submission if applicable
    score = db.Column(db.Integer, nullable=True)  # Score given by instructor (0-100)
    feedback = db.Column(db.Text, nullable=True)  # Instructor feedback
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    material = db.relationship('CourseMaterial', backref='submissions', lazy=True)
    student = db.relationship('User', backref='material_submissions', lazy=True)
    
    # Unique constraint to allow only one submission per user per material
    __table_args__ = (db.UniqueConstraint('user_id', 'material_id', name='uq_user_material_submission'),)
    
    def __repr__(self):
        return f'<MaterialSubmission Material:{self.material_id} User:{self.user_id}>'


# ==================== CLINICAL PLATFORM MODELS ====================

class StudentProfile(db.Model):
    """
    Extended profile for clinical students with institution and program data.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # University student ID
    institution = db.Column(db.String(255), nullable=False)  # University/Institution name
    program = db.Column(db.String(100), nullable=False)  # e.g., Medicine, Nursing, Pharmacy
    cohort = db.Column(db.String(50), nullable=True)  # Batch/year
    practice_start_date = db.Column(db.Date, nullable=True)
    practice_end_date = db.Column(db.Date, nullable=True)
    placement_hospital = db.Column(db.String(255), nullable=True)
    current_unit = db.Column(db.String(100), nullable=True)  # Current rotation unit
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    
    # Pre-clinical completion status
    documents_verified = db.Column(db.Boolean, default=False)
    agreements_signed = db.Column(db.Boolean, default=False)
    elearning_completed = db.Column(db.Boolean, default=False)
    pretest_passed = db.Column(db.Boolean, default=False)
    onboarding_complete = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='student_profile', lazy=True)
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref='supervised_students', lazy=True)
    
    def __repr__(self):
        return f'<StudentProfile {self.student_id}>'


class LegalDocument(db.Model):
    """
    Legal documents uploaded by students (referral letter, health letter, insurance, etc.)
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    document_type = db.Column(db.String(50), nullable=False)  # 'referral', 'health', 'insurance', 'integrity_pact'
    file_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'verified', 'rejected'
    verified_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='legal_documents', lazy=True)
    verified_by = db.relationship('User', backref='verified_documents', lazy=True)
    
    def __repr__(self):
        return f'<LegalDocument {self.document_type} Student:{self.student_id}>'


class DigitalAgreement(db.Model):
    """
    Digital agreements and consent forms signed by students.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    agreement_type = db.Column(db.String(50), nullable=False)  # 'confidentiality', 'ethics', 'discipline', 'emergency'
    content = db.Column(db.Text, nullable=False)  # Agreement text
    signed = db.Column(db.Boolean, default=False)
    signature_data = db.Column(db.Text, nullable=True)  # Base64 encoded signature image
    signature_timestamp = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='agreements', lazy=True)
    
    def __repr__(self):
        return f'<DigitalAgreement {self.agreement_type} Student:{self.student_id}>'


class ElearningModule(db.Model):
    """
    Pre-clinical e-learning modules (hospital orientation, safety, K3RS, etc.)
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    module_type = db.Column(db.String(50), nullable=False)  # 'orientation', 'safety', 'infection_control', 'k3rs', 'communication', 'emergency', 'his'
    content_type = db.Column(db.String(20), nullable=False)  # 'video', 'pdf', 'infographic', 'interactive'
    file_path = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    duration_minutes = db.Column(db.Integer, default=10)
    order_index = db.Column(db.Integer, default=0)
    is_mandatory = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ElearningModule {self.title}>'


class ElearningProgress(db.Model):
    """
    Track student progress through e-learning modules.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    module_id = db.Column(db.Integer, db.ForeignKey('elearning_module.id'), nullable=False, index=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completion_percentage = db.Column(db.Integer, default=0)
    time_spent_minutes = db.Column(db.Integer, default=0)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='elearning_progress', lazy=True)
    module = db.relationship('ElearningModule', backref='student_progress', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'module_id', name='uq_student_elearning'),)
    
    def __repr__(self):
        return f'<ElearningProgress Student:{self.student_id} Module:{self.module_id}>'


class ClinicalConfig(db.Model):
    """
    Clinical module configuration editable by admin.
    Stores documents, agreements, required courses, and assessment questions.
    """
    id = db.Column(db.Integer, primary_key=True)
    documents_json = db.Column(db.Text, nullable=True)
    agreements_json = db.Column(db.Text, nullable=True)
    required_course_ids_json = db.Column(db.Text, nullable=True)
    pretest_questions_json = db.Column(db.Text, nullable=True)
    posttest_questions_json = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ClinicalConfig {self.id}>'


class PreClinicalAssessment(db.Model):
    """
    Pre-test and post-test for e-learning modules.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    assessment_type = db.Column(db.String(20), nullable=False)  # 'pretest', 'posttest'
    score = db.Column(db.Integer, nullable=False)  # 0-100
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    passing_score = db.Column(db.Integer, default=80)
    passed = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)
    answers_json = db.Column(db.Text, nullable=True)  # Store answers as JSON
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='preclinical_assessments', lazy=True)
    
    def __repr__(self):
        return f'<PreClinicalAssessment {self.assessment_type} Student:{self.student_id}>'


class LogbookEntry(db.Model):
    """
    Digital logbook entries for clinical practice.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False, index=True)
    unit = db.Column(db.String(100), nullable=False)  # ER, ICU, OR, Inpatient, Outpatient
    procedure_name = db.Column(db.String(255), nullable=False)
    procedure_type = db.Column(db.String(100), nullable=True)  # Category/type of procedure
    role = db.Column(db.String(20), nullable=False)  # 'observe', 'assist', 'independent', 'teach'
    duration_minutes = db.Column(db.Integer, nullable=True)
    patient_case_summary = db.Column(db.Text, nullable=True)
    learning_points = db.Column(db.Text, nullable=True)
    
    # Supervisor validation
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    validated = db.Column(db.Boolean, default=False)
    validation_method = db.Column(db.String(20), nullable=True)  # 'pin', 'qr', 'manual'
    validation_timestamp = db.Column(db.DateTime, nullable=True)
    supervisor_notes = db.Column(db.Text, nullable=True)
    
    # Audit trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    locked = db.Column(db.Boolean, default=False)  # Lock after 24 hours
    
    # Relationships
    student = db.relationship('StudentProfile', backref='logbook_entries', lazy=True)
    supervisor = db.relationship('User', backref='validated_logbook_entries', lazy=True)
    
    def __repr__(self):
        return f'<LogbookEntry {self.procedure_name} Student:{self.student_id}>'


class PatientCase(db.Model):
    """
    Long-term patient case tracking for clinical students.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    case_title = db.Column(db.String(255), nullable=False)
    patient_alias = db.Column(db.String(100), nullable=True)  # Anonymized patient identifier
    unit = db.Column(db.String(100), nullable=True)
    initial_diagnosis = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active', index=True)  # 'active', 'closed'
    initial_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('StudentProfile', backref='patient_cases', lazy=True)

    def __repr__(self):
        return f'<PatientCase {self.case_title} Student:{self.student_id}>'


class PatientCaseDailyUpdate(db.Model):
    """
    Daily follow-up updates for a patient case.
    """
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('patient_case.id'), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=True)  # 'improving', 'stable', 'worsening', 'resolved'
    update_summary = db.Column(db.Text, nullable=False)
    interventions = db.Column(db.Text, nullable=True)
    patient_response = db.Column(db.Text, nullable=True)
    follow_up_plan = db.Column(db.Text, nullable=True)
    next_control_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient_case = db.relationship('PatientCase', backref='daily_updates', lazy=True)

    __table_args__ = (db.UniqueConstraint('case_id', 'entry_date', name='uq_case_daily_update'),)

    def __repr__(self):
        return f'<PatientCaseDailyUpdate Case:{self.case_id} Date:{self.entry_date}>'


class CompetencyChecklist(db.Model):
    """
    Competency requirements per program.
    """
    id = db.Column(db.Integer, primary_key=True)
    program = db.Column(db.String(100), nullable=False, index=True)  # Medicine, Nursing, etc.
    competency_name = db.Column(db.String(255), nullable=False)
    competency_category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    minimum_observations = db.Column(db.Integer, default=0)
    minimum_assists = db.Column(db.Integer, default=0)
    minimum_independent = db.Column(db.Integer, default=0)
    learning_objectives = db.Column(db.Text, nullable=True)
    assessment_rubric = db.Column(db.Text, nullable=True)
    is_mandatory = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CompetencyChecklist {self.competency_name}>'


class CompetencyProgress(db.Model):
    """
    Track student progress on competency checklist.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    competency_id = db.Column(db.Integer, db.ForeignKey('competency_checklist.id'), nullable=False, index=True)
    observations_count = db.Column(db.Integer, default=0)
    assists_count = db.Column(db.Integer, default=0)
    independent_count = db.Column(db.Integer, default=0)
    competency_level = db.Column(db.String(20), default='not_yet')  # 'not_yet', 'developing', 'competent', 'advanced'
    supervisor_signoff = db.Column(db.Boolean, default=False)
    signoff_date = db.Column(db.DateTime, nullable=True)
    signoff_supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='competency_progress', lazy=True)
    competency = db.relationship('CompetencyChecklist', backref='student_progress', lazy=True)
    signoff_supervisor = db.relationship('User', backref='competency_signoffs', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'competency_id', name='uq_student_competency'),)
    
    def __repr__(self):
        return f'<CompetencyProgress Student:{self.student_id} Competency:{self.competency_id}>'


class DailyJournal(db.Model):
    """
    Daily reflection journal entries.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False, index=True)
    shift = db.Column(db.String(20), nullable=True)  # 'morning', 'afternoon', 'night'
    unit = db.Column(db.String(100), nullable=True)
    journal_text = db.Column(db.Text, nullable=False)
    what_went_well = db.Column(db.Text, nullable=True)
    challenges_faced = db.Column(db.Text, nullable=True)
    learning_insights = db.Column(db.Text, nullable=True)
    confidence_level = db.Column(db.Integer, nullable=True)  # 1-5 scale
    emotion_tag = db.Column(db.String(50), nullable=True)  # 'confident', 'anxious', 'overwhelmed', etc.
    
    # Supervisor feedback
    supervisor_feedback = db.Column(db.Text, nullable=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    feedback_timestamp = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='daily_journals', lazy=True)
    supervisor = db.relationship('User', backref='journal_feedbacks', lazy=True)
    
    def __repr__(self):
        return f'<DailyJournal Student:{self.student_id} Date:{self.entry_date}>'


class WeeklyAssessment(db.Model):
    """
    Weekly CBT questions and mini-case studies.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    week_number = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(100), nullable=False)
    assessment_type = db.Column(db.String(20), nullable=False)  # 'cbt', 'case_study'
    score = db.Column(db.Integer, nullable=True)
    total_questions = db.Column(db.Integer, nullable=True)
    correct_answers = db.Column(db.Integer, nullable=True)
    answers_json = db.Column(db.Text, nullable=True)
    case_analysis = db.Column(db.Text, nullable=True)  # For case studies
    participation_score = db.Column(db.Integer, nullable=True)  # For discussions
    supervisor_comments = db.Column(db.Text, nullable=True)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='weekly_assessments', lazy=True)
    
    def __repr__(self):
        return f'<WeeklyAssessment Week:{self.week_number} Student:{self.student_id}>'


class FinalExam(db.Model):
    """
    Final competency examinations (CBT, mini-OSCE, case study).
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    exam_type = db.Column(db.String(20), nullable=False)  # 'cbt', 'mini_osce', 'case_study'
    score = db.Column(db.Integer, nullable=True)
    total_points = db.Column(db.Integer, nullable=False)
    passing_score = db.Column(db.Integer, default=75)
    passed = db.Column(db.Boolean, default=False)
    attempt_number = db.Column(db.Integer, default=1)
    
    # OSCE specific
    stations_json = db.Column(db.Text, nullable=True)  # Station scores and rubric
    video_paths = db.Column(db.Text, nullable=True)  # Recorded video paths
    
    # Case study specific
    case_submission = db.Column(db.Text, nullable=True)
    
    # Examiner feedback
    examiner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    examiner_comments = db.Column(db.Text, nullable=True)
    
    exam_date = db.Column(db.DateTime, default=datetime.utcnow)
    graded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='final_exams', lazy=True)
    examiner = db.relationship('User', backref='graded_exams', lazy=True)
    
    def __repr__(self):
        return f'<FinalExam {self.exam_type} Student:{self.student_id}>'


class Evaluation360(db.Model):
    """
    360-degree evaluation from multiple evaluators.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    evaluator_role = db.Column(db.String(50), nullable=False)  # 'clinical_supervisor', 'nurse', 'lecturer', 'self'
    
    # Evaluation domains (1-5 scale)
    clinical_competency_score = db.Column(db.Integer, nullable=True)
    patient_safety_score = db.Column(db.Integer, nullable=True)
    professionalism_score = db.Column(db.Integer, nullable=True)
    communication_score = db.Column(db.Integer, nullable=True)
    learning_attitude_score = db.Column(db.Integer, nullable=True)
    emergency_response_score = db.Column(db.Integer, nullable=True)
    
    # Weighted percentage (based on role)
    weight_percentage = db.Column(db.Integer, default=0)  # Supervisor 40%, Nurse 30%, Lecturer 20%, Self 10%
    
    comments = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    areas_for_improvement = db.Column(db.Text, nullable=True)
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='evaluations_360', lazy=True)
    evaluator = db.relationship('User', backref='evaluations_given', lazy=True)
    
    def __repr__(self):
        return f'<Evaluation360 Student:{self.student_id} Evaluator:{self.evaluator_role}>'


class ClinicalCertificate(db.Model):
    """
    Digital certificates issued upon program completion.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, unique=True, index=True)
    certificate_number = db.Column(db.String(100), unique=True, nullable=False)
    qr_code_path = db.Column(db.String(255), nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    
    # Score summary
    final_score = db.Column(db.Float, nullable=True)
    pretest_score = db.Column(db.Integer, nullable=True)
    posttest_score = db.Column(db.Integer, nullable=True)
    cbt_score = db.Column(db.Integer, nullable=True)
    osce_score = db.Column(db.Integer, nullable=True)
    case_study_score = db.Column(db.Integer, nullable=True)
    evaluation_360_average = db.Column(db.Float, nullable=True)
    competency_achievement_percentage = db.Column(db.Float, nullable=True)
    
    issued_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_url = db.Column(db.String(500), nullable=True)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='certificate', lazy=True, uselist=False)
    issued_by = db.relationship('User', backref='issued_certificates', lazy=True)
    
    def __repr__(self):
        return f'<ClinicalCertificate {self.certificate_number}>'


class IncidentReport(db.Model):
    """
    Safety incident and near-miss reporting (panic button feature).
    """
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=True, index=True)
    incident_type = db.Column(db.String(50), nullable=False)  # 'safety', 'ethics', 'near_miss', 'adverse_event'
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    incident_date = db.Column(db.DateTime, nullable=False)
    unit = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    immediate_action_taken = db.Column(db.Text, nullable=True)
    
    # Investigation
    investigated = db.Column(db.Boolean, default=False)
    investigator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    investigation_notes = db.Column(db.Text, nullable=True)
    root_cause_analysis = db.Column(db.Text, nullable=True)
    corrective_action = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), default='reported')  # 'reported', 'under_review', 'resolved', 'closed'
    
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='incident_reports', lazy=True)
    student = db.relationship('StudentProfile', backref='incident_reports', lazy=True)
    investigator = db.relationship('User', foreign_keys=[investigator_id], backref='investigated_incidents', lazy=True)
    
    def __repr__(self):
        return f'<IncidentReport {self.incident_type} Severity:{self.severity}>'


class StudentFeedback(db.Model):
    """
    Student feedback on hospital, supervisors, and program.
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False, index=True)
    feedback_type = db.Column(db.String(50), nullable=False)  # 'hospital', 'supervisor', 'program', 'curriculum'
    
    # Ratings (1-5)
    teaching_quality_rating = db.Column(db.Integer, nullable=True)
    facilities_rating = db.Column(db.Integer, nullable=True)
    supervisor_support_rating = db.Column(db.Integer, nullable=True)
    safety_climate_rating = db.Column(db.Integer, nullable=True)
    overall_experience_rating = db.Column(db.Integer, nullable=True)
    
    comments = db.Column(db.Text, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('StudentProfile', backref='feedbacks', lazy=True)
    
    def __repr__(self):
        return f'<StudentFeedback {self.feedback_type} Student:{self.student_id}>'


class AlumniProfile(db.Model):
    """
    Alumni career tracking and networking.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    current_position = db.Column(db.String(255), nullable=True)
    current_hospital = db.Column(db.String(255), nullable=True)
    specialization = db.Column(db.String(100), nullable=True)
    further_certifications = db.Column(db.Text, nullable=True)
    willing_to_mentor = db.Column(db.Boolean, default=False)
    job_performance_1yr = db.Column(db.Text, nullable=True)  # 1-year follow-up
    job_performance_3yr = db.Column(db.Text, nullable=True)  # 3-year follow-up
    job_performance_5yr = db.Column(db.Text, nullable=True)  # 5-year follow-up
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='alumni_profile', lazy=True, uselist=False)
    student_profile = db.relationship('StudentProfile', backref='alumni_profile', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<AlumniProfile User:{self.user_id}>'


class SupervisorValidationPIN(db.Model):
    """
    Supervisor PIN codes for logbook validation.
    """
    id = db.Column(db.Integer, primary_key=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    pin_hash = db.Column(db.String(255), nullable=False)
    last_changed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    supervisor = db.relationship('User', backref='validation_pin', lazy=True, uselist=False)
    
    def set_pin(self, pin):
        """Hash and set PIN."""
        self.pin_hash = generate_password_hash(str(pin))
        self.last_changed = datetime.utcnow
    
    def check_pin(self, pin):
        """Check if provided PIN matches hash."""
        return check_password_hash(self.pin_hash, str(pin))
    
    def __repr__(self):
        return f'<SupervisorValidationPIN Supervisor:{self.supervisor_id}>'
