# E-Leary: Hospital E-Learning & Management System

A comprehensive Flask-based e-learning platform for RST Slamet Riyadi Solo hospital with features inspired by Moodle/Spada, Kominfo Digitalent, and Scribd.

## Features

### 🎓 Course Management (Spada-Like)
- Browse courses in a responsive grid layout
- Enroll in courses
- Access course materials organized by modules
- Sidebar navigation for easy module access
- Support for PDF, Video, and Assignment materials

### 📚 E-Library (Scribd-Like)
- Browse approved library documents
- Search functionality
- User document uploads (pending admin approval)
- Document management for admins

### 📋 Attendance Tracking
- Daily course attendance marking
- Attendance history
- Course-specific attendance

### 👤 User Roles
- **Admin**: Full system access, approve/reject documents, manage courses
- **User**: Can enroll in courses, upload documents, mark attendance

## Project Structure

```
Eleary/
├── app.py                           # Main Flask application
├── models.py                        # SQLAlchemy models
├── requirements.txt                 # Python dependencies
├── eleary.db                        # SQLite database (auto-generated)
├── templates/
│   ├── base.html                   # Base template with navigation
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── dashboard.html              # User dashboard
│   ├── courses.html                # Course catalog (Digitalent-style)
│   ├── course_detail.html          # Course view with sidebar (Spada-style)
│   ├── library.html                # E-Library view (Scribd-style)
│   ├── admin_approvals.html        # Admin document approval
│   ├── admin_courses.html          # Admin course management
│   ├── admin_create_course.html    # Admin course creation
│   ├── admin_manage_modules.html   # Admin module management
│   ├── admin_manage_materials.html # Admin material management
│   ├── 404.html                    # 404 error page
│   └── 500.html                    # 500 error page
├── static/                         # Static files (CSS, JS, images)
└── uploads/                        # User-uploaded documents
```

## Database Models

### User
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `role` ('admin' or 'user')
- `division` (e.g., Medical, IT, Administration)
- `created_at`

### Course
- `id` (Primary Key)
- `title`
- `description`
- `thumbnail_url`
- `instructor`
- `category` ('medical', 'admin', 'it')
- `created_at`

### CourseModule
- `id` (Primary Key)
- `course_id` (Foreign Key)
- `title` (e.g., "Pertemuan 1")
- `order_index`
- `created_at`

### CourseMaterial
- `id` (Primary Key)
- `module_id` (Foreign Key)
- `title`
- `description`
- `file_path`
- `type` ('pdf', 'video', 'assignment')
- `created_at`

### LibraryBook
- `id` (Primary Key)
- `uploader_id` (Foreign Key)
- `title`
- `description`
- `file_path`
- `status` ('pending', 'approved', 'rejected')
- `created_at`
- `updated_at`

### AttendanceLog
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `course_id` (Foreign Key, nullable)
- `timestamp`
- `status` ('present')

### CourseEnrollment
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `course_id` (Foreign Key)
- `enrolled_at`

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite3 with SQLAlchemy ORM
- **Frontend**: HTML5 + Tailwind CSS (CDN)
- **Authentication**: Flask-Login
- **Security**: Werkzeug for password hashing

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Steps

1. **Clone/Navigate to project**
```bash
cd /home/azeroth/Productivity/Projects/Eleary
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize database with sample data**
```bash
python app.py
```

This will:
- Create `eleary.db` SQLite database
- Create all tables
- Populate with sample data (admin user, courses, materials)

5. **Run the application**
```bash
python app.py
```

The app will run at `http://localhost:5000`

## Default Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`

### Sample User
- **Username**: `dr_ahmad`
- **Password**: `password123`

## API Routes

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### Courses
- `GET /courses` - Browse all courses with search/filter
- `GET /course/<id>` - View course with Spada-like layout
- `POST /course/<id>/enroll` - Enroll in course
- `POST /course/<id>/attendance` - Mark attendance

### Library
- `GET /library` - Browse approved documents
- `POST /library/upload` - Upload document (pending approval)

### Admin
- `GET /admin/approvals` - View pending documents
- `POST /admin/approvals/<id>/approve` - Approve document
- `POST /admin/approvals/<id>/reject` - Reject document
- `GET /admin/courses` - Manage courses
- `GET/POST /admin/courses/create` - Create course
- `GET/POST /admin/courses/<id>/modules` - Manage modules
- `GET/POST /admin/modules/<id>/materials` - Manage materials

## Design Features

### Color Palette (Medical/Hospital)
- **Primary**: Teal-600 (#0d9488)
- **Secondary**: Slate-100 to Slate-900
- **Accent**: White (#ffffff)

### Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px)
- Grid layouts: 1-2-3 columns based on screen size

### UI Components
- Sticky sidebar navigation for courses
- Card-based layouts for courses and documents
- Modal dialogs for document upload
- Flash messages for user feedback
- Loading states and transitions
- Professional gradients and shadows

## Usage Guide

### For Students/Users

1. **Register/Login**
   - Create account or login with credentials
   - Specify your division

2. **Browse & Enroll Courses**
   - Go to "Courses"
   - Search by title or filter by category
   - Click "Start Learning" to enroll

3. **Access Course Materials**
   - Click on course
   - Select module from sidebar
   - View/download materials
   - Mark attendance

4. **Use E-Library**
   - Browse approved documents
   - Search for specific materials
   - Upload documents (requires admin approval)

### For Admins

1. **Dashboard**
   - Access admin panel from dashboard
   - Manage all system activities

2. **Create Courses**
   - Go to "Manage Courses"
   - Click "Create Course"
   - Add modules and materials

3. **Approve Documents**
   - Go to "Approve Documents"
   - Review pending uploads
   - Approve or reject with feedback

4. **Manage Modules & Materials**
   - Access course modules
   - Add/edit modules
   - Add learning materials (PDF, video, assignment)

## Configuration

Edit `app.py` to modify:

```python
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eleary.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
```

## Security Notes

- Change `SECRET_KEY` in production
- Use strong passwords
- Implement HTTPS in production
- Add rate limiting for file uploads
- Validate all user inputs
- Use environment variables for sensitive data

## File Upload

- **Allowed types**: PDF, DOC, DOCX, PPT, PPTX, TXT
- **Max size**: 50MB
- **Storage**: `/uploads` folder
- **Default status**: 'pending' (requires admin approval)

## Performance Optimization

- Database indexing on frequently queried fields
- Pagination for large datasets (12 courses/documents per page)
- Lazy loading for relationships
- CSS CDN for faster loading
- Secure filename handling

## Future Enhancements

1. **Quiz & Assessment Module**
   - Create quizzes within modules
   - Auto-grading system
   - Student performance tracking

2. **Discussion Forums**
   - Course-specific forums
   - Real-time notifications
   - Thread moderation

3. **Certificates**
   - Generate certificates upon completion
   - PDF export functionality

4. **Analytics**
   - Student progress tracking
   - Course completion rates
   - Admin dashboard with statistics

5. **Live Sessions**
   - Video conferencing integration
   - Recorded sessions
   - Session scheduling

6. **Mobile App**
   - React Native/Flutter app
   - Offline learning support
   - Push notifications

## Troubleshooting

### Database Errors
```bash
# Reset database
rm eleary.db
python app.py
```

### Port Already in Use
```bash
# Run on different port
python app.py --port 5001
```

### Import Errors
```bash
# Verify installation
pip install -r requirements.txt --upgrade
```

## Support

For issues or questions, contact:
- Email: support@eleary.hospital
- System: E-Leary Platform
- Client: RST Slamet Riyadi Solo

## License

© 2026 RST Slamet Riyadi Solo. All rights reserved.

---

**Version**: 1.0.0  
**Last Updated**: February 4, 2026  
**Author**: E-Leary Development Team
