from models import (db, User, Course, CourseModule, CourseMaterial, LibraryBook,
                    ElearningModule, CompetencyChecklist)


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
        
        # ==================== CLINICAL PLATFORM DATA ====================
        
        # Create E-Learning Modules for Pre-Clinical Onboarding
        elearning_modules = [
            ElearningModule(
                title='Hospital Orientation & Culture',
                description='Introduction to hospital environment, culture, and expectations',
                module_type='orientation',
                content_type='video',
                duration_minutes=15,
                order_index=1,
                is_mandatory=True
            ),
            ElearningModule(
                title='Patient Safety Goals',
                description='Learn about the 6 core patient safety objectives',
                module_type='safety',
                content_type='infographic',
                duration_minutes=10,
                order_index=2,
                is_mandatory=True
            ),
            ElearningModule(
                title='Infection Prevention & Control',
                description='Protocols for infection prevention and hand hygiene',
                module_type='infection_control',
                content_type='video',
                duration_minutes=12,
                order_index=3,
                is_mandatory=True
            ),
            ElearningModule(
                title='K3RS Compliance',
                description='Workplace safety and health regulations in hospitals',
                module_type='k3rs',
                content_type='pdf',
                duration_minutes=8,
                order_index=4,
                is_mandatory=True
            ),
            ElearningModule(
                title='Professional Communication & Ethics',
                description='Patient interaction and professional communication skills',
                module_type='communication',
                content_type='video',
                duration_minutes=10,
                order_index=5,
                is_mandatory=True
            ),
            ElearningModule(
                title='Emergency Procedures',
                description='Emergency response flow and disaster protocols',
                module_type='emergency',
                content_type='interactive',
                duration_minutes=12,
                order_index=6,
                is_mandatory=True
            ),
            ElearningModule(
                title='Hospital Information System Basics',
                description='Basic navigation and usage of hospital IT systems',
                module_type='his',
                content_type='video',
                duration_minutes=15,
                order_index=7,
                is_mandatory=True
            ),
        ]
        
        db.session.add_all(elearning_modules)
        
        # Create Competency Checklists for Medicine Program
        medicine_competencies = [
            CompetencyChecklist(
                program='Medicine',
                competency_name='Blood Pressure Measurement',
                competency_category='Vital Signs',
                description='Accurately measure and record patient blood pressure',
                minimum_observations=3,
                minimum_assists=5,
                minimum_independent=10,
                is_mandatory=True
            ),
            CompetencyChecklist(
                program='Medicine',
                competency_name='IV Cannulation',
                competency_category='Procedures',
                description='Insert intravenous cannula safely',
                minimum_observations=5,
                minimum_assists=10,
                minimum_independent=15,
                is_mandatory=True
            ),
            CompetencyChecklist(
                program='Medicine',
                competency_name='Wound Suturing',
                competency_category='Minor Surgery',
                description='Perform basic wound suturing',
                minimum_observations=10,
                minimum_assists=15,
                minimum_independent=20,
                is_mandatory=True
            ),
            CompetencyChecklist(
                program='Medicine',
                competency_name='Patient History Taking',
                competency_category='Clinical Skills',
                description='Conduct comprehensive patient history interview',
                minimum_observations=5,
                minimum_assists=10,
                minimum_independent=30,
                is_mandatory=True
            ),
            CompetencyChecklist(
                program='Medicine',
                competency_name='Physical Examination',
                competency_category='Clinical Skills',
                description='Perform systematic physical examination',
                minimum_observations=5,
                minimum_assists=10,
                minimum_independent=25,
                is_mandatory=True
            ),
        ]
        
        # Create Competency Checklists for Nursing Program
        nursing_competencies = [
            CompetencyChecklist(
                program='Nursing',
                competency_name='Medication Administration',
                competency_category='Patient Care',
                description='Safely administer medications via various routes',
                minimum_observations=3,
                minimum_assists=5,
                minimum_independent=15,
                is_mandatory=True
            ),
            CompetencyChecklist(
                program='Nursing',
                competency_name='Wound Care & Dressing',
                competency_category='Patient Care',
                description='Perform wound cleaning and dressing changes',
                minimum_observations=5,
                minimum_assists=10,
                minimum_independent=20,
                is_mandatory=True
            ),
            CompetencyChecklist(
                program='Nursing',
                competency_name='Patient Mobilization',
                competency_category='Patient Care',
                description='Safely mobilize and transfer patients',
                minimum_observations=3,
                minimum_assists=8,
                minimum_independent=15,
                is_mandatory=True
            ),
            CompetencyChecklist(
                program='Nursing',
                competency_name='Catheter Insertion & Care',
                competency_category='Procedures',
                description='Insert and maintain urinary catheter',
                minimum_observations=5,
                minimum_assists=8,
                minimum_independent=12,
                is_mandatory=True
            ),
        ]
        
        db.session.add_all(medicine_competencies + nursing_competencies)
        db.session.commit()
        
        print("✅ Database initialized with sample data including clinical platform features!")

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
