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
