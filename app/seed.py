from models import db, User, Course, CourseModule, CourseMaterial, LibraryBook


def init_db(app):
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
