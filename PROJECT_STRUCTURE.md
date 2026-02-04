# E-Leary Project Structure

## Directory Tree

```
Eleary/
│
├── app.py                              # Main Flask application with all routes
├── models.py                           # SQLAlchemy database models
├── requirements.txt                    # Python dependencies
├── README.md                           # Project documentation
├── eleary.db                           # SQLite database (auto-created)
│
├── templates/                          # HTML templates
│   ├── base.html                       # Base template with navigation & footer
│   ├── login.html                      # Authentication - Login page
│   ├── register.html                   # Authentication - Registration page
│   ├── dashboard.html                  # User dashboard home page
│   ├── courses.html                    # Course catalog (Kominfo Digitalent style)
│   ├── course_detail.html              # Course detail (Spada-like with sidebar)
│   ├── library.html                    # E-Library view (Scribd-like)
│   ├── admin_approvals.html            # Admin - Document approval panel
│   ├── admin_courses.html              # Admin - Course management
│   ├── admin_create_course.html        # Admin - Create new course
│   ├── admin_manage_modules.html       # Admin - Manage course modules
│   ├── admin_manage_materials.html     # Admin - Manage course materials
│   ├── 404.html                        # Error page - Not found
│   └── 500.html                        # Error page - Server error
│
├── static/                             # Static files (CSS, JS, images)
│   ├── css/                            # (for future custom CSS)
│   ├── js/                             # (for future custom JavaScript)
│   └── images/                         # (for future images/icons)
│
└── uploads/                            # User-uploaded files
    ├── library/                        # Uploaded library documents
    └── courses/                        # Course materials (created via admin)
```

## File Descriptions

### Core Application Files

**app.py** (870 lines)
- Flask application initialization
- Database configuration
- Authentication routes (login, register, logout)
- Course management routes
- Library management routes
- Admin routes
- Error handlers
- Database initialization with sample data

**models.py** (200 lines)
- `User` - User authentication and role management
- `Course` - Course information and metadata
- `CourseModule` - Course sections/modules (Spada structure)
- `CourseMaterial` - Learning materials within modules
- `LibraryBook` - Library document management with approval workflow
- `AttendanceLog` - Attendance tracking for courses
- `CourseEnrollment` - User course enrollment tracking

### Template Files

**base.html** (Navigation & Layout)
- Sticky navigation bar with logo
- User menu with role display
- Flash message system
- Footer with links
- Tailwind CSS styling base

**Authentication Templates**
- `login.html` - Clean login form with demo credentials
- `register.html` - Registration form with division selection

**User Templates**
- `dashboard.html` - Welcome page with quick stats and action buttons
- `courses.html` - Course catalog with search and filter (3-column grid)
- `course_detail.html` - Spada-like layout (sidebar modules + content)
- `library.html` - Library view with upload modal and search

**Admin Templates**
- `admin_approvals.html` - List pending documents with approve/reject buttons
- `admin_courses.html` - Course management grid
- `admin_create_course.html` - Create course form
- `admin_manage_modules.html` - Add/manage course modules
- `admin_manage_materials.html` - Add/manage course materials

**Error Templates**
- `404.html` - Page not found error
- `500.html` - Server error page

### Configuration Files

**requirements.txt**
- Flask 2.3.2
- Flask-SQLAlchemy 3.0.5
- Flask-Login 0.6.2
- Werkzeug 2.3.6

**README.md**
- Comprehensive project documentation
- Setup instructions
- Features overview
- API route documentation
- Usage guide
- Troubleshooting

## Database Schema

```
Users
├── id (PK)
├── username (Unique)
├── email (Unique)
├── password_hash
├── role ('admin' | 'user')
├── division
└── created_at

Courses
├── id (PK)
├── title
├── description
├── thumbnail_url
├── instructor
├── category ('medical' | 'admin' | 'it')
└── created_at

CourseModules
├── id (PK)
├── course_id (FK → Courses)
├── title
├── order_index
└── created_at

CourseMaterials
├── id (PK)
├── module_id (FK → CourseModules)
├── title
├── description
├── file_path
├── type ('pdf' | 'video' | 'assignment')
└── created_at

LibraryBooks
├── id (PK)
├── uploader_id (FK → Users)
├── title
├── description
├── file_path
├── status ('pending' | 'approved' | 'rejected')
├── created_at
└── updated_at

AttendanceLogs
├── id (PK)
├── user_id (FK → Users)
├── course_id (FK → Courses, nullable)
├── timestamp
└── status ('present')

CourseEnrollments
├── id (PK)
├── user_id (FK → Users)
├── course_id (FK → Courses)
└── enrolled_at
```

## Routes Summary

### Authentication Routes
```
GET/POST  /login              → login()
GET/POST  /register           → register()
GET       /logout             → logout()
```

### Course Routes
```
GET       /courses            → courses() - Browse with search/filter
GET       /course/<id>        → course_detail() - Spada-like view
POST      /course/<id>/enroll → enroll_course()
POST      /course/<id>/attendance → submit_attendance()
```

### Library Routes
```
GET       /library            → library() - View approved documents
POST      /library/upload     → upload_document()
```

### Admin Routes
```
GET       /admin/approvals           → admin_approvals()
POST      /admin/approvals/<id>/approve → approve_book()
POST      /admin/approvals/<id>/reject  → reject_book()
GET       /admin/courses             → admin_courses()
GET/POST  /admin/courses/create      → create_course()
GET/POST  /admin/courses/<id>/modules     → manage_modules()
GET/POST  /admin/modules/<id>/materials   → manage_materials()
```

## Key Features Implementation

### 1. Spada-Like Course View
- **File**: `course_detail.html`
- **Layout**: 25% sidebar + 75% content
- **Sidebar**: Sticky, lists course modules with order
- **Content**: Displays module materials (PDF, video, assignment)
- **Attendance**: Block at top showing attendance status

### 2. Digitalent-Like Course Catalog
- **File**: `courses.html`
- **Layout**: Responsive grid (1-2-3 columns)
- **Cards**: Thumbnail, title, instructor, category badge
- **Features**: Search by title/description, filter by category, pagination

### 3. Scribd-Like E-Library
- **File**: `library.html`
- **Features**: 
  - Grid layout for documents
  - Search functionality
  - Upload modal (users can submit documents)
  - Admin approval workflow
  - Document type badges
  - Download functionality

### 4. Role-Based Access
- **Admin**: Full access to all admin routes and approvals
- **User**: Can only enroll, view approved courses, upload documents

### 5. Attendance System
- **Course-specific**: Mark attendance per course per day
- **Display**: Shows present/not present status on course page
- **Storage**: Logged with timestamp

## Styling

### Tailwind CSS
- All templates use Tailwind CSS via CDN
- Responsive design with mobile-first approach
- Color scheme:
  - Primary: Teal (teal-600, teal-700)
  - Secondary: Slate (slate-50 to slate-900)
  - Accents: Blue, Green, Red, Purple
  - Background: Slate-50
  - Cards: White with shadows

### Layout Classes
- `max-w-7xl` - Main content container
- `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3` - Responsive grids
- `flex flex-col gap-4` - Vertical stacking
- `sticky top-20` - Sticky sidebar positioning
- `line-clamp-2` - Text truncation

## Database Initialization

The `init_db()` function in `app.py` automatically:
1. Creates all tables
2. Creates sample data:
   - 1 admin user (admin/admin123)
   - 2 sample users (dr_ahmad, siti_nurse)
   - 3 sample courses (Medical, IT, Admin categories)
   - 3 modules for first course
   - 3 materials across modules
   - 2 approved library books

## Security Features

1. **Password Hashing**: Werkzeug.security for password storage
2. **Session Management**: Flask-Login for authentication
3. **File Upload Validation**:
   - Extension whitelist (PDF, DOC, DOCX, PPT, PPTX, TXT)
   - Filename sanitization with `secure_filename()`
   - Size limit (50MB)
   - Timestamp-prefixed naming
4. **Admin Protection**: `@admin_required` decorator
5. **Login Required**: `@login_required` decorator

## Performance Considerations

1. **Pagination**: 12 items per page for courses/documents
2. **Lazy Loading**: Database relationships use lazy='dynamic'
3. **Indexing**: Indexes on frequently queried fields (user_id, course_id, etc.)
4. **CDN Assets**: Tailwind CSS from CDN
5. **Query Optimization**: Efficient SQLAlchemy filters

## Future Extension Points

1. **Quiz Module**: Add `Quiz` and `QuestionAnswer` models
2. **Notifications**: Add notification system for approvals
3. **Analytics**: Add performance tracking and statistics
4. **API**: Add REST API endpoints
5. **Search**: Add full-text search capabilities
6. **Caching**: Implement Redis caching for frequently accessed data
