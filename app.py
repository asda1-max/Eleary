import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import bleach
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Course, CourseModule, CourseMaterial, LibraryBook, AttendanceLog, CourseEnrollment

# Initialize Flask App
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eleary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============================================================================
# User Loader
# ============================================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================================
# Utility Functions
# ============================================================================
def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_rich_text(html):
    """Sanitize rich text HTML from editor input."""
    if not html:
        return ''

    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 's', 'ul', 'ol', 'li', 'a', 'img',
        'h1', 'h2', 'h3', 'h4', 'blockquote', 'code', 'pre', 'hr', 'span', 'div'
    ]
    allowed_attrs = {
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title'],
        'p': ['class'],
        'h1': ['class'],
        'h2': ['class'],
        'h3': ['class'],
        'h4': ['class'],
        'span': ['class'],
        'div': ['class']
    }
    cleaned = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        protocols=['http', 'https', 'mailto']
    )
    return cleaned

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def pemateri_required(f):
    """Decorator to require pemateri or admin role for course management."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage_courses():
            flash('Instructor or Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_course_attendance_today(user_id, course_id):
    """Check if user has marked attendance for this course today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    attendance = AttendanceLog.query.filter(
        AttendanceLog.user_id == user_id,
        AttendanceLog.course_id == course_id,
        AttendanceLog.timestamp >= today_start,
        AttendanceLog.timestamp < today_end
    ).first()
    return attendance

# ============================================================================
# Authentication Routes
# ============================================================================
@app.route('/')
def index():
    """Home/Dashboard page."""
    if current_user.is_authenticated:
        enrolled_courses = CourseEnrollment.query.filter_by(user_id=current_user.id).count()
        course_total = Course.query.count()
        return render_template('dashboard.html', enrolled_courses=enrolled_courses, course_total=course_total)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        division = request.form.get('division', 'Medical')
        request_pemateri = request.form.get('request_pemateri') == 'on'  # Checkbox for pemateri role request
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('register'))
        
        # Create new user - pemateri requests are pending admin approval
        if request_pemateri:
            user = User(username=username, email=email, division=division, role='user', pending_role='pemateri')
            flash('Registration successful! Your instructor role request is pending admin approval. Please log in.', 'info')
        else:
            user = User(username=username, email=email, division=division, role='user')
            flash('Registration successful! Please log in.', 'success')
        
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ============================================================================
# Course Routes
# ============================================================================
@app.route('/courses')
@login_required
def courses():
    """Display all courses in Digitalent-style grid."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Course.query
    
    if search:
        query = query.filter(Course.title.ilike(f'%{search}%') | Course.description.ilike(f'%{search}%'))
    
    if category:
        query = query.filter_by(category=category)
    
    courses_paginated = query.paginate(page=page, per_page=12)
    
    return render_template('courses.html', 
                         courses=courses_paginated.items,
                         total=courses_paginated.total,
                         page=page,
                         search=search,
                         category=category)

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    """Display course detail with Spada-like layout (sidebar + content)."""
    course = Course.query.get_or_404(course_id)
    
    # Get all modules for this course (ordered by order_index)
    modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index).all()
    
    # Get selected module (default to first module if exists)
    default_module_id = modules[0].id if modules else None
    selected_module_id = request.args.get('module_id', default_module_id, type=int)
    selected_module = CourseModule.query.get(selected_module_id) if selected_module_id else None
    
    # Get materials for selected module
    materials = []
    if selected_module:
        materials = CourseMaterial.query.filter_by(module_id=selected_module.id).all()
    
    # Check attendance for today
    attendance_today = get_course_attendance_today(current_user.id, course_id)
    
    # Note: descriptions are already sanitized when stored in DB, no need to re-sanitize
    course_description_html = course.description or ''
    selected_module_description_html = selected_module.description or '' if selected_module else ''

    return render_template('course_detail.html',
                         course=course,
                         modules=modules,
                         selected_module=selected_module,
                         materials=materials,
                         attendance_today=attendance_today,
                         course_description_html=course_description_html,
                         selected_module_description_html=selected_module_description_html)

@app.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course(course_id):
    """Enroll user in a course."""
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing:
        flash('You are already enrolled in this course.', 'info')
    else:
        enrollment = CourseEnrollment(user_id=current_user.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash(f'Successfully enrolled in {course.title}!', 'success')
    
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/course/<int:course_id>/attendance', methods=['POST'])
@login_required
def submit_attendance(course_id):
    """Mark attendance for a course."""
    course = Course.query.get_or_404(course_id)
    
    # Check if already marked today
    attendance_today = get_course_attendance_today(current_user.id, course_id)
    
    if attendance_today:
        flash('You have already marked attendance for this course today.', 'info')
    else:
        attendance = AttendanceLog(
            user_id=current_user.id,
            course_id=course_id,
            status='present'
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
    
    return redirect(url_for('course_detail', course_id=course_id))

# ============================================================================
# Library Routes
# ============================================================================
@app.route('/library')
@login_required
def library():
    """Display approved library documents with search functionality."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = LibraryBook.query.filter_by(status='approved')
    
    if search:
        query = query.filter(LibraryBook.title.ilike(f'%{search}%') | LibraryBook.description.ilike(f'%{search}%'))
    
    books = query.order_by(LibraryBook.created_at.desc()).paginate(page=page, per_page=12)
    
    return render_template('library.html', books=books.items, total=books.total, page=page, search=search)

@app.route('/library/upload', methods=['POST'])
@login_required
def upload_document():
    """Upload document to library (pending approval by admin)."""
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('library'))
    
    file = request.files['file']
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('library'))
    
    if not allowed_file(file.filename):
        flash('File type not allowed. Allowed: PDF, DOC, DOCX, PPT, PPTX, TXT', 'danger')
        return redirect(url_for('library'))
    
    if not title:
        flash('Title is required.', 'danger')
        return redirect(url_for('library'))
    
    try:
        # Save file with secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create library book entry (pending status)
        book = LibraryBook(
            uploader_id=current_user.id,
            title=title,
            description=description,
            file_path=file_path,
            status='pending'
        )
        db.session.add(book)
        db.session.commit()
        
        flash('Document submitted for admin review.', 'success')
    except Exception as e:
        flash(f'Error uploading file: {str(e)}', 'danger')
    
    return redirect(url_for('library'))

@app.route('/library/<int:book_id>/preview')
@login_required
def preview_document(book_id):
    """Preview a library document."""
    book = LibraryBook.query.get_or_404(book_id)
    
    # Check access: admins can preview pending, users can preview approved
    if book.status == 'pending' and not current_user.is_admin():
        flash('You do not have permission to view this document.', 'danger')
        return redirect(url_for('library'))
    elif book.status == 'rejected':
        flash('This document has been rejected.', 'danger')
        return redirect(url_for('library'))
    
    return render_template('preview.html', book=book)

@app.route('/library/<int:book_id>/download')
@login_required
def download_document(book_id):
    """Download a library document."""
    book = LibraryBook.query.get_or_404(book_id)
    
    # Check access: admins can download pending, users can download approved
    if book.status == 'pending' and not current_user.is_admin():
        flash('You do not have permission to download this document.', 'danger')
        return redirect(url_for('library'))
    elif book.status == 'rejected':
        flash('This document has been rejected.', 'danger')
        return redirect(url_for('library'))
    
    # Verify file exists
    if not os.path.exists(book.file_path):
        flash('File not found.', 'danger')
        return redirect(url_for('library'))
    
    try:
        return send_file(
            book.file_path,
            as_attachment=True,
            download_name=f"{book.title}_{book.id}.{book.file_path.rsplit('.', 1)[1]}"
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(url_for('library'))

@app.route('/library/<int:book_id>/view')
@login_required
def view_document(book_id):
    """View a library document inline (for preview)."""
    book = LibraryBook.query.get_or_404(book_id)
    
    # Check access: admins can view pending, users can view approved
    if book.status == 'pending' and not current_user.is_admin():
        flash('You do not have permission to view this document.', 'danger')
        return redirect(url_for('library'))
    elif book.status == 'rejected':
        flash('This document has been rejected.', 'danger')
        return redirect(url_for('library'))
    
    # Verify file exists
    if not os.path.exists(book.file_path):
        flash('File not found.', 'danger')
        return redirect(url_for('library'))
    
    try:
        # Return file with inline disposition for browser preview
        return send_file(
            book.file_path,
            as_attachment=False,  # Display inline, not download
            download_name=f"{book.title}_{book.id}.{book.file_path.rsplit('.', 1)[1]}"
        )
    except Exception as e:
        flash(f'Error viewing file: {str(e)}', 'danger')
        return redirect(url_for('library'))

# ============================================================================
# Admin Routes
# ============================================================================
@app.route('/admin/approvals')
@login_required
@admin_required
def admin_approvals():
    """Admin page to approve/reject pending library documents."""
    page = request.args.get('page', 1, type=int)
    pending_books = LibraryBook.query.filter_by(status='pending').order_by(LibraryBook.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('admin_approvals.html', books=pending_books.items, total=pending_books.total, page=page)

@app.route('/admin/approvals/<int:book_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_book(book_id):
    """Approve a pending library document."""
    book = LibraryBook.query.get_or_404(book_id)
    book.status = 'approved'
    db.session.commit()
    flash(f'Document "{book.title}" approved.', 'success')
    return redirect(url_for('admin_approvals'))

@app.route('/admin/approvals/<int:book_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_book(book_id):
    """Reject a pending library document."""
    book = LibraryBook.query.get_or_404(book_id)
    
    # Delete the file
    if os.path.exists(book.file_path):
        os.remove(book.file_path)
    
    db.session.delete(book)
    db.session.commit()
    flash('Document rejected and deleted.', 'success')
    return redirect(url_for('admin_approvals'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin page to manage users, approve pemateri requests, and create admins."""
    pending_pemateri = User.query.filter_by(pending_role='pemateri').all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', pending_pemateri=pending_pemateri, all_users=all_users)

@app.route('/admin/users/<int:user_id>/approve_pemateri', methods=['POST'])
@login_required
@admin_required
def approve_pemateri(user_id):
    """Approve pemateri role request."""
    user = User.query.get_or_404(user_id)
    user.role = 'pemateri'
    user.pending_role = None
    db.session.commit()
    flash(f'{user.username} is now an Instructor.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/reject_pemateri', methods=['POST'])
@login_required
@admin_required
def reject_pemateri(user_id):
    """Reject pemateri role request."""
    user = User.query.get_or_404(user_id)
    user.pending_role = None
    db.session.commit()
    flash(f'Instructor request for {user.username} rejected.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/make_admin', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    """Promote user to admin."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You are already an admin.', 'info')
    else:
        user.role = 'admin'
        user.pending_role = None
        db.session.commit()
        flash(f'{user.username} is now an Admin.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user account."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
    else:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/courses')
@login_required
@pemateri_required
def admin_courses():
    """Pemateri/Admin page to create and manage courses."""
    # If pemateri (not admin), show only their courses
    if current_user.is_pemateri() and not current_user.is_admin():
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    else:
        # Admin sees all courses
        courses = Course.query.all()
    return render_template('admin_courses.html', courses=courses)

@app.route('/admin/courses/create', methods=['GET', 'POST'])
@login_required
@pemateri_required
def create_course():
    """Create a new course."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = sanitize_rich_text(request.form.get('description'))
        category = request.form.get('category', 'medical')
        thumbnail_url = request.form.get('thumbnail_url')
        
        if not title:
            flash('Title is required.', 'danger')
            return redirect(url_for('create_course'))
        
        # Create course with current user as instructor
        course = Course(
            title=title,
            description=description,
            instructor_id=current_user.id,  # Set to current user (pemateri/admin)
            category=category,
            thumbnail_url=thumbnail_url
        )
        db.session.add(course)
        db.session.commit()
        
        flash(f'Course "{title}" created successfully!', 'success')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin_create_course.html')

@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@pemateri_required
def delete_course(course_id):
    """Delete a course - admin can delete any, pemateri can delete only their own."""
    course = Course.query.get_or_404(course_id)
    
    # Check permission
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('You do not have permission to delete this course.', 'danger')
        return redirect(url_for('admin_courses'))
    
    title = course.title
    db.session.delete(course)
    db.session.commit()
    flash(f'Course "{title}" deleted successfully.', 'success')
    return redirect(url_for('admin_courses'))

@app.route('/admin/courses/<int:course_id>/modules', methods=['GET', 'POST'])
@login_required
@pemateri_required
def manage_modules(course_id):
    """Manage modules for a course."""
    course = Course.query.get_or_404(course_id)
    
    # Check permission: only course creator or admin can manage
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = sanitize_rich_text(request.form.get('description'))
        order_index = request.form.get('order_index', 0, type=int)
        
        if not title:
            flash('Module title is required.', 'danger')
            return redirect(url_for('manage_modules', course_id=course_id))
        
        module = CourseModule(
            course_id=course_id,
            title=title,
            description=description,
            order_index=order_index
        )
        db.session.add(module)
        db.session.commit()
        
        flash(f'Module "{title}" added successfully!', 'success')
    
    modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index).all()
    return render_template('admin_manage_modules.html', course=course, modules=modules)

@app.route('/admin/modules/<int:module_id>/edit', methods=['GET', 'POST'])
@login_required
@pemateri_required
def edit_module(module_id):
    """Edit a module."""
    module = CourseModule.query.get_or_404(module_id)
    course = module.course
    
    # Check permission: only course creator or admin can manage
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = sanitize_rich_text(request.form.get('description'))
        order_index = request.form.get('order_index', 0, type=int)
        
        if not title:
            flash('Module title is required.', 'danger')
            return redirect(url_for('edit_module', module_id=module_id))
        
        module.title = title
        module.description = description
        module.order_index = order_index
        db.session.commit()
        
        flash(f'Module "{title}" updated successfully!', 'success')
        return redirect(url_for('manage_modules', course_id=course.id))
    
    return render_template('admin_edit_module.html', module=module, course=course)

@app.route('/admin/modules/<int:module_id>/delete', methods=['POST'])
@login_required
@pemateri_required
def delete_module(module_id):
    """Delete a module."""
    module = CourseModule.query.get_or_404(module_id)
    course = module.course
    
    # Check permission: only course creator or admin can manage
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('admin_courses'))
    
    title = module.title
    db.session.delete(module)
    db.session.commit()
    
    flash(f'Module "{title}" deleted successfully.', 'success')
    return redirect(url_for('manage_modules', course_id=course.id))

@app.route('/admin/modules/<int:module_id>/materials', methods=['GET', 'POST'])
@login_required
@pemateri_required
def manage_materials(module_id):
    """Manage materials for a module."""
    module = CourseModule.query.get_or_404(module_id)
    course = module.course
    
    # Check permission: only course creator or admin can manage
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = sanitize_rich_text(request.form.get('description'))
        file_path = request.form.get('file_path')
        material_type = request.form.get('type', 'pdf')
        
        if not title:
            flash('Material title is required.', 'danger')
            return redirect(url_for('manage_materials', module_id=module_id))
        
        material = CourseMaterial(
            module_id=module_id,
            title=title,
            description=description,
            file_path=file_path,
            type=material_type
        )
        db.session.add(material)
        db.session.commit()
        
        flash(f'Material "{title}" added successfully!', 'success')
    
    materials = CourseMaterial.query.filter_by(module_id=module_id).all()
    return render_template('admin_manage_materials.html', module=module, materials=materials)

@app.route('/admin/materials/<int:material_id>/edit', methods=['GET', 'POST'])
@login_required
@pemateri_required
def edit_material(material_id):
    """Edit a course material."""
    material = CourseMaterial.query.get_or_404(material_id)
    module = material.module
    course = module.course
    
    # Check permission: only course creator or admin can manage
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = sanitize_rich_text(request.form.get('description'))
        file_path = request.form.get('file_path')
        material_type = request.form.get('type', 'pdf')
        
        if not title:
            flash('Material title is required.', 'danger')
            return redirect(url_for('edit_material', material_id=material_id))
        
        material.title = title
        material.description = description
        material.file_path = file_path
        material.type = material_type
        db.session.commit()
        
        flash(f'Material "{title}" updated successfully!', 'success')
        return redirect(url_for('manage_materials', module_id=module.id))
    
    return render_template('admin_edit_material.html', material=material, module=module, course=course)

@app.route('/admin/materials/<int:material_id>/delete', methods=['POST'])
@login_required
@pemateri_required
def delete_material(material_id):
    """Delete a course material."""
    material = CourseMaterial.query.get_or_404(material_id)
    module = material.module
    course = module.course
    
    # Check permission: only course creator or admin can manage
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('admin_courses'))
    
    title = material.title
    db.session.delete(material)
    db.session.commit()
    
    flash(f'Material "{title}" deleted successfully.', 'success')
    return redirect(url_for('manage_materials', module_id=module.id))
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return render_template('500.html'), 500

# ============================================================================
# Database Initialization
# ============================================================================
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Course': Course, 'CourseModule': CourseModule, 
            'CourseMaterial': CourseMaterial, 'LibraryBook': LibraryBook, 'AttendanceLog': AttendanceLog}

def init_db():
    """Initialize database with sample data."""
    with app.app_context():
        db.create_all()
        
        # Check if data already exists
        if User.query.first():
            print("Database already initialized.")
            return
        
        # Create admin user
        admin = User(username='admin', email='admin@eleary.com', role='admin', division='Administration')
        admin.set_password('admin123')
        
        # Create pemateri (instructor) user
        pemateri1 = User(username='dr_ahmad', email='ahmad@hospital.com', role='pemateri', division='Medical')
        pemateri1.set_password('password123')
        
        # Create regular user
        user1 = User(username='siti_nurse', email='siti@hospital.com', role='user', division='Medical')
        user1.set_password('password123')
        
        db.session.add_all([admin, pemateri1, user1])
        db.session.commit()
        
        # Create sample courses with instructor_id
        course1 = Course(
            title='Pengenalan Sistem Informasi Kesehatan',
            description='Kursus dasar tentang sistem informasi kesehatan dan penggunaannya di rumah sakit.',
            instructor_id=pemateri1.id,  # Assign to pemateri
            category='medical',
            thumbnail_url='https://via.placeholder.com/300x200?text=SIK'
        )
        
        course2 = Course(
            title='Basic IT Security for Medical Staff',
            description='Dasar-dasar keamanan IT untuk staf medis.',
            instructor_id=admin.id,  # Assign to admin
            category='it',
            thumbnail_url='https://via.placeholder.com/300x200?text=Security'
        )
        
        course3 = Course(
            title='Hospital Management Best Practices',
            description='Praktik terbaik dalam manajemen rumah sakit.',
            instructor_id=pemateri1.id,  # Assign to pemateri
            category='admin',
            thumbnail_url='https://via.placeholder.com/300x200?text=Management'
        )
        
        db.session.add_all([course1, course2, course3])
        db.session.commit()
        
        # Create modules for course1
        module1 = CourseModule(course_id=course1.id, title='Pengenalan', order_index=1)
        module2 = CourseModule(course_id=course1.id, title='Modul Dasar', order_index=2)
        module3 = CourseModule(course_id=course1.id, title='Praktik', order_index=3)
        
        db.session.add_all([module1, module2, module3])
        db.session.commit()
        
        # Create materials for modules
        material1 = CourseMaterial(
            module_id=module1.id,
            title='Apa itu SIK?',
            description='Video pengenalan tentang sistem informasi kesehatan',
            file_path='https://www.youtube.com/embed/example',
            type='video'
        )
        
        material2 = CourseMaterial(
            module_id=module1.id,
            title='Slide Pengenalan',
            description='Slide presentasi pengenalan SIK',
            file_path='/uploads/sik_intro.pdf',
            type='pdf'
        )
        
        material3 = CourseMaterial(
            module_id=module2.id,
            title='Dokumentasi',
            description='Dokumentasi lengkap sistem',
            file_path='/uploads/sik_documentation.pdf',
            type='pdf'
        )
        
        db.session.add_all([material1, material2, material3])
        db.session.commit()
        
        # Create sample library books
        book1 = LibraryBook(
            uploader_id=user1.id,
            title='Medical Best Practices',
            description='Panduan praktik terbaik dalam pelayanan medis',
            file_path='/uploads/medical_bp.pdf',
            status='approved'
        )
        
        book2 = LibraryBook(
            uploader_id=user1.id,
            title='Nursing Guidelines',
            description='Pedoman nursing terkini',
            file_path='/uploads/nursing_guidelines.pdf',
            status='approved'
        )
        
        db.session.add_all([book1, book2])
        db.session.commit()
        
        print("Database initialized with sample data!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
