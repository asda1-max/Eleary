# E-Leary: Hospital E-Learning & Management System

A comprehensive Flask-based e-learning platform for RST Slamet Riyadi Solo hospital with features inspired by Moodle/Spada, Kominfo Digitalent, and Scribd.

## Features

### 🎓 Course Management (Spada-Like)
- Browse courses in a responsive grid layout
- Enroll in courses
- Access course materials organized by modules
- Sidebar navigation for easy module access
- Support for PDF, Video, and Assignment materials
- Instructors (Pemateri) can create and manage courses after admin approval

### 📚 E-Library (Scribd-Like)
- Browse approved library documents
- Search functionality
- User document uploads (pending admin approval)
- Document preview functionality
- Document management for admins

### 🔐 Instructor Approval System
- Users can request instructor (Pemateri) role during registration
- Admin reviews and approves/rejects instructor requests
- Approved instructors can create courses

### 👥 Admin User Management
- View all users with role badges
- Promote users to admin role
- Delete user accounts
- Manage pending instructor requests
- Full control over all content

### 🎨 Dark Mode
- Toggle dark mode with smooth transitions
- Persistent preference via localStorage
- Enhanced contrast and visibility
- Glass-morphism effects

### 📋 Attendance Tracking
- Daily course attendance marking
- Attendance history
- Course-specific attendance

### 👤 User Roles
- **Admin**: Full system access, approve/reject instructors and documents, manage courses and users
- **Pemateri**: Can create and manage courses (after approval)
- **User**: Can enroll in courses, upload documents, mark attendance

## Project Structure

```
Eleary/
├── app.py                           # Main Flask application
├── models.py                        # SQLAlchemy models
├── requirements.txt                 # Python dependencies
├── eleary.db                        # SQLite database (auto-generated)
├── templates/
│   ├── base.html                   # Base template with navigation and dark mode
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page (with Mahasiswa/Koas division)
│   ├── dashboard.html              # User dashboard
│   ├── courses.html                # Course catalog (Digitalent-style)
│   ├── course_detail.html          # Course view with sidebar (Spada-style)
│   ├── library.html                # E-Library view (Scribd-style)
│   ├── preview.html                # Library document preview
│   ├── admin_approvals.html        # Admin document approval
│   ├── admin_courses.html          # Admin course management with delete
│   ├── admin_create_course.html    # Admin course creation
│   ├── admin_manage_modules.html   # Admin module management
│   ├── admin_manage_materials.html # Admin material management
│   ├── admin_users.html            # Admin user & instructor approval management
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
- `role` ('admin', 'pemateri', or 'user')
- `pending_role` (Pending role for approval workflow - nullable)
- `division` (e.g., Medical, Nursing, Mahasiswa/Koas, Administration, IT, Other)
- `created_at`

### Course
- `id` (Primary Key)
- `title`
- `description`
- `thumbnail_url`
- `instructor_id` (Foreign Key to User)
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
- **Frontend**: HTML5 + Tailwind CSS (CDN) + Vanilla JS
- **Templating**: Jinja2
- **Authentication**: Flask-Login
- **Security**: Werkzeug for password hashing
- **Sanitization**: bleach for rich text cleanup

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

4. **Initialize database**
```bash
python app.py
```

This will:
- Create `eleary.db` SQLite database
- Create all tables
- Populate clinical platform defaults (no demo users)

5. **Run the application**
```bash
python app.py
```

The app will run at `http://localhost:5000`

## First Admin Setup

On first launch, the app will prompt you to create the initial admin account at `/setup-admin`.

## API Routes

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration (with Mahasiswa/Koas division option)
- `GET /logout` - User logout

### Courses
- `GET /courses` - Browse all courses with search/filter
- `GET /course/<id>` - View course with Spada-like layout
- `POST /course/<id>/enroll` - Enroll in course
- `POST /course/<id>/attendance` - Mark attendance
- `POST /course/<id>/delete` - Delete course (admin or creator only)

### Library
- `GET /library` - Browse approved documents
- `POST /library/upload` - Upload document (pending approval)
- `GET /library/<id>/preview` - Preview document
- `GET /library/<id>/download` - Download document
- `DELETE /library/<id>/delete` - Delete document (admin only)

### Admin - Documents
- `GET /admin/approvals` - View pending documents
- `POST /admin/approvals/<id>/approve` - Approve document
- `POST /admin/approvals/<id>/reject` - Reject document

### Admin - Courses
- `GET /admin/courses` - Manage courses
- `GET/POST /admin/courses/create` - Create course
- `POST /admin/courses/<id>/delete` - Delete course
- `GET/POST /admin/courses/<id>/modules` - Manage modules
- `GET/POST /admin/modules/<id>/materials` - Manage materials

### Admin - Users
- `GET /admin/users` - View all users and pending instructor requests
- `POST /admin/users/<id>/approve_pemateri` - Approve instructor request
- `POST /admin/users/<id>/reject_pemateri` - Reject instructor request
- `POST /admin/users/<id>/make_admin` - Promote user to admin
- `POST /admin/users/<id>/delete` - Delete user account

## Design Features

### Color Palette (Medical/Hospital)
- **Primary**: Teal-600 (#0d9488)
- **Light mode Secondary**: Slate-100 to Slate-900
- **Dark mode Background**: Slate-800/900 with opacity
- **Dark mode Text**: Slate-200/400
- **Accent**: White (#ffffff)

### Dark Mode
- Toggle button in navigation bar
- Persistent preference stored in localStorage
- Glass-morphism effects for depth and contrast
- Smooth transitions between light and dark mode
- Enhanced readability in both modes

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
- Glass-morphism cards and effects

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

4. **Manage Users & Instructors**
   - Go to "Users" in admin section
   - Review pending instructor requests
   - Approve or reject instructor applications
   - Promote users to admin role
   - Delete user accounts

5. **Manage Modules & Materials**
   - Access course modules
   - Add/edit modules
   - Add learning materials (PDF, video, assignment)

6. **Delete Content**
   - Delete any course or library document
   - Confirmation dialog prevents accidental deletion

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
- Admin accounts cannot be deleted by themselves (self-protection)
- Pending instructor requests require admin approval before access
- All file uploads require content-type validation

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

3. **Instructor Approval Notifications**
   - Email notifications for instructor requests
   - Admin notification dashboard
   - Request status updates

4. **Certificates**
   - Generate certificates upon completion
   - PDF export functionality

5. **Analytics**
   - Student progress tracking
   - Course completion rates
   - Admin dashboard with statistics

6. **Live Sessions**
   - Video conferencing integration
   - Recorded sessions
   - Session scheduling

7. **Mobile App**
   - Mobile-first responsive enhancements to the existing web UI
   - Offline-friendly patterns for static resources
   - Notification UX within the web app

8. **Two-Factor Authentication**
   - Optional 2FA for security
   - SMS or email verification

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

MIT License

Copyright (c) 2026 Asda1-max

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

**Version**: 1.0.0  
**Last Updated**: February 4, 2026  
**Author**: E-Leary Development Team
