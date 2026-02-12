from models import (db, User, Course, CourseModule, CourseMaterial, LibraryBook,
                    ElearningModule, CompetencyChecklist, ClinicalConfig)
import json


def init_db(app):
    """Initialize database with sample data."""
    with app.app_context():
        db.create_all()

        # Check if data already exists
        if User.query.first():
            print("Database already initialized.")
            return

        # Create default clinical configuration
        default_config = ClinicalConfig(
            documents_json=json.dumps([
                {'type': 'referral', 'label': 'Referral Letter', 'requires_expiration': True},
                {'type': 'health', 'label': 'Health Letter', 'requires_expiration': True},
                {'type': 'insurance', 'label': 'Insurance', 'requires_expiration': True},
                {'type': 'integrity_pact', 'label': 'Integrity Pact', 'requires_expiration': False}
            ]),
            agreements_json=json.dumps([
                {'type': 'confidentiality', 'title': 'Confidentiality', 'text': 'I hereby agree to maintain strict patient confidentiality and comply with all data protection regulations...'},
                {'type': 'ethics', 'title': 'Ethics', 'text': 'I commit to upholding the highest standards of professional ethics in all clinical interactions...'},
                {'type': 'discipline', 'title': 'Discipline', 'text': 'I acknowledge and accept the disciplinary policies and sanctions outlined by the hospital...'},
                {'type': 'emergency', 'title': 'Emergency Procedures', 'text': 'I understand the emergency procedures and agree to follow all safety protocols...'}
            ]),
            required_course_ids_json=json.dumps([]),
            pretest_questions_json=json.dumps([
                {
                    'id': 1,
                    'question': 'Which action is most important before touching a patient?',
                    'options': ['Hand hygiene', 'Adjust bed', 'Write notes', 'Check phone'],
                    'correct_option': 'Hand hygiene'
                },
                {
                    'id': 2,
                    'question': 'What should you do if your ID badge is missing?',
                    'options': ['Report to supervisor', 'Borrow a friend’s badge', 'Ignore it', 'Leave the unit'],
                    'correct_option': 'Report to supervisor'
                },
                {
                    'id': 3,
                    'question': 'Which item is part of basic PPE?',
                    'options': ['Gloves', 'Necklace', 'Perfume', 'Watch'],
                    'correct_option': 'Gloves'
                }
            ]),
            posttest_questions_json=json.dumps([
                {
                    'id': 1,
                    'question': 'When should you perform hand hygiene?',
                    'options': ['Before and after patient contact', 'Only after meals', 'Only at shift end', 'Once per day'],
                    'correct_option': 'Before and after patient contact'
                },
                {
                    'id': 2,
                    'question': 'Which is the correct way to dispose of sharps?',
                    'options': ['Place in a sharps container', 'Throw in regular trash', 'Leave on tray', 'Wrap in tissue'],
                    'correct_option': 'Place in a sharps container'
                },
                {
                    'id': 3,
                    'question': 'If you witness a safety incident, what is the first step?',
                    'options': ['Ensure patient safety', 'Post on chat', 'Finish other tasks', 'Ignore it'],
                    'correct_option': 'Ensure patient safety'
                }
            ])
        )
        db.session.add(default_config)
        db.session.commit()

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
        
        print("✅ Database initialized with clinical platform defaults.")
