# E-Leary Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies (2 min)
```bash
cd /home/azeroth/Productivity/Projects/Eleary
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Initialize Database (1 min)
```bash
python app.py
```
This creates `eleary.db` and clinical platform defaults (no demo users).

### Step 3: Run Application (1 min)
```bash
python app.py
```
Open: http://localhost:5000

### Step 4: Create First Admin (1 min)
- Open: http://localhost:5000/setup-admin
- Set the initial admin username and password

---

## Common Tasks

### 👨‍💼 As an Admin

#### Create a Course
1. Login with admin account
2. Dashboard → "Admin Panel" → "Manage Courses"
3. Click "Create Course"
4. Fill in: Title, Description, Instructor, Category, Thumbnail URL
5. Click "Create Course"

#### Add Modules to Course
1. Go to "Manage Courses"
2. Click "Modules" on desired course
3. Enter module title and order
4. Click "Add Module"

#### Add Materials to Module
1. Click "Manage Materials" on a module
2. Enter: Title, Description, File Path/URL, Type (PDF/Video/Assignment)
3. Click "Add Material"

**Material Path Examples:**
- PDF: `/uploads/course_material.pdf`
- Video: `https://www.youtube.com/embed/dQw4w9WgXcQ`
- Assignment: `Submit assignment 1 by Friday`

#### Approve Documents
1. Go to "Admin Panel" → "Approve Documents"
2. Review pending uploads
3. Click "Approve" or "Reject"

### 👨‍🎓 As a User

#### Enroll in Course
1. Go to "Courses"
2. (Optional) Search or filter by category
3. Find course and click "Start Learning"
4. You're enrolled!

#### Access Course Materials
1. Click on enrolled course
2. Choose module from left sidebar
3. View/download materials
4. Click "Submit Attendance" to mark present

#### Upload Document to Library
1. Go to "E-Library"
2. Click "Upload Document"
3. Fill form: Title, Description, Select File
4. Click "Submit for Review"
5. Wait for admin approval (appears in library when approved)

---

## System Features

### 🎯 Core Features

| Feature | Where | Details |
|---------|-------|---------|
| **Course Browsing** | `/courses` | Grid layout, search, filter by category |
| **Course Materials** | `/course/<id>` | Spada-like sidebar + content |
| **E-Library** | `/library` | Browse approved documents, upload new |
| **Attendance** | Course page | Mark attendance once per course per day |
| **Admin Panel** | Dashboard | Approve documents, create courses |

### 🎨 Design Features

- **Responsive**: Works on mobile, tablet, desktop
- **Colors**: Teal (primary), Slate (secondary), White (background)
- **Icons**: SVG icons throughout
- **Animations**: Hover effects, transitions, shadows
- **Accessibility**: Semantic HTML, proper labels

### 🔐 Security

- Password hashing (Werkzeug)
- Session management (Flask-Login)
- File upload validation
- Admin-only routes protected
- Secure filename handling

---

## Troubleshooting

### Issue: Port 5000 already in use
```bash
# Find and kill process
lsof -i :5000
kill -9 <PID>

# Or run on different port
# Modify app.py: app.run(debug=True, port=5001)
```

### Issue: Database errors
```bash
# Reset database
rm eleary.db
python app.py
```

### Issue: Import errors
```bash
# Reinstall packages
pip install -r requirements.txt --force-reinstall
```

### Issue: Static files not loading
- Ensure Tailwind CSS CDN is accessible
- Check browser console for errors

---

## Project Files Reference

| File | Purpose | Key Routes |
|------|---------|-----------|
| `app.py` | Main Flask app | All routes |
| `models.py` | Database models | 7 models defined |
| `base.html` | Navigation template | Extends all pages |
| `courses.html` | Course catalog | GET /courses |
| `course_detail.html` | Spada-like view | GET /course/<id> |
| `library.html` | E-Library | GET/POST /library |
| `admin_*.html` | Admin pages | /admin/* |

---

## Key Shortcuts

**Admin Dashboard Quick Links:**
- Manage Courses: http://localhost:5000/admin/courses
- Approve Documents: http://localhost:5000/admin/approvals

**User Quick Links:**
- My Courses: http://localhost:5000/courses
- E-Library: http://localhost:5000/library
- Dashboard: http://localhost:5000/

---

## Sample Data Included

### Users
- **admin** (role: admin) - Can manage everything
- **dr_ahmad** (role: user) - Can enroll and upload
- **siti_nurse** (role: user) - Can enroll and upload

### Courses (3 courses pre-created)
1. Pengenalan Sistem Informasi Kesehatan (Medical)
2. Basic IT Security for Medical Staff (IT)
3. Hospital Management Best Practices (Admin)

### Course Structure
- First course has 3 modules: "Pengenalan", "Modul Dasar", "Praktik"
- Each module has sample materials

### Library
- 2 approved sample documents from test users

---

## Configuration

Edit `app.py` to customize:

```python
# Line ~30
app.config['SECRET_KEY'] = 'your-secret-key'  # Change for production
app.config['UPLOAD_FOLDER'] = 'uploads'        # Upload folder
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Line ~475
app.run(debug=True)  # Set debug=False for production
```

---

## Database Models Summary

```
User (7 fields)
  ├── username, email, password_hash, role, division
  └── Relationships: uploaded_books, attendance_logs, enrollments

Course (6 fields)
  ├── title, description, instructor, category, thumbnail_url
  └── Relationships: modules, enrollments, attendance_logs

CourseModule (4 fields)
  ├── course_id, title, order_index
  └── Relationships: materials

CourseMaterial (5 fields)
  ├── module_id, title, description, file_path, type
  └── Relationships: module

LibraryBook (6 fields)
  ├── uploader_id, title, description, file_path, status
  └── Relationships: uploader

AttendanceLog (4 fields)
  ├── user_id, course_id, timestamp, status
  └── Relationships: user, course

CourseEnrollment (3 fields)
  ├── user_id, course_id, enrolled_at
  └── Relationships: user, course
```

---

## Recommended Next Steps

1. **Change Admin Password**
   - Login as admin
   - Modify password in database or code

2. **Add Real Courses**
   - Create courses through admin panel
   - Add modules and materials
   - Set thumbnail URLs

3. **Customize Branding**
   - Edit `base.html` logo/name
   - Update color scheme in templates
   - Add hospital logo to static folder

4. **Set Up File Storage**
   - Ensure `/uploads` folder has write permissions
   - Consider cloud storage (S3) for production

5. **Deploy to Production**
   - Change `SECRET_KEY`
   - Set `debug=False`
   - Use production database
   - Set up HTTPS
   - Use production server (Gunicorn, uWSGI)

---

## Support Resources

- **Flask Docs**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **Tailwind CSS**: https://tailwindcss.com/
- **Werkzeug**: https://werkzeug.palletsprojects.com/

---

**Version**: 1.0.0  
**Last Updated**: February 4, 2026  
**For**: RST Slamet Riyadi Solo Hospital
