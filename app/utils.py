from datetime import datetime, timedelta
from functools import wraps
import bleach
import os
import uuid
from flask import flash, redirect, url_for, current_app
from flask_login import current_user
from models import AttendanceLog
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_image_file(filename):
    """Check if image file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_upload_image(file_obj, subfolder='materials'):
    """Save uploaded image file and return relative path.
    
    Args:
        file_obj: File object from request.files
        subfolder: Subfolder within uploads (default: 'materials')
    
    Returns:
        Relative path to saved image or None if invalid
    """
    if not file_obj or file_obj.filename == '':
        return None
    
    if not allowed_image_file(file_obj.filename):
        return None
    
    # Generate unique filename
    ext = file_obj.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{ext}"
    
    # Create subfolder if it doesn't exist
    upload_folder = current_app.config['UPLOAD_FOLDER']
    subfolder_path = os.path.join(upload_folder, subfolder)
    os.makedirs(subfolder_path, exist_ok=True)
    
    # Save file
    file_path = os.path.join(subfolder_path, unique_filename)
    file_obj.save(file_path)
    
    # Return relative path for URL usage
    return f'/uploads/{subfolder}/{unique_filename}'


def convert_youtube_url(url):
    """Convert YouTube watch URL to embed URL format to bypass X-Frame-Options restrictions.

    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID (already correct)
    """
    if not url:
        return url

    url = url.strip()

    # Already in embed format
    if 'youtube.com/embed/' in url:
        return url

    # Extract video ID from watch URL
    if 'youtube.com/watch' in url:
        video_id = url.split('v=')[-1].split('&')[0]
        return f'https://www.youtube.com/embed/{video_id}'

    # Extract video ID from youtu.be short URL
    if 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[-1].split('?')[0]
        return f'https://www.youtube.com/embed/{video_id}'

    # Return original URL if not YouTube
    return url


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
