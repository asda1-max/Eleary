from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import (db, User, StudentProfile, LegalDocument, DigitalAgreement, ClinicalConfig,
                    Course, CourseEnrollment, PreClinicalAssessment,
                    LogbookEntry, PatientCase, PatientCaseDailyUpdate,
                    CompetencyChecklist, CompetencyProgress, DailyJournal,
                    WeeklyAssessment, FinalExam, Evaluation360, ClinicalCertificate,
                    IncidentReport, StudentFeedback, AlumniProfile, SupervisorValidationPIN)
from app.utils import save_upload_image, allowed_file
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import os
import json


def get_clinical_config():
    config = ClinicalConfig.query.first()
    if not config:
        config = ClinicalConfig(
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
        db.session.add(config)
        db.session.commit()

    documents = json.loads(config.documents_json or '[]')
    agreements = json.loads(config.agreements_json or '[]')
    required_course_ids = json.loads(config.required_course_ids_json or '[]')
    pretest_questions = json.loads(config.pretest_questions_json or '[]')
    posttest_questions = json.loads(config.posttest_questions_json or '[]')

    return {
        'config': config,
        'documents': documents,
        'agreements': agreements,
        'required_course_ids': required_course_ids,
        'pretest_questions': pretest_questions,
        'posttest_questions': posttest_questions
    }


def register_clinical_routes(app):
    
    # ==================== PRE-CLINICAL ONBOARDING ====================
    
    @app.route('/clinical/onboarding')
    @login_required
    def clinical_onboarding():
        """Pre-clinical onboarding dashboard."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        clinical_config = get_clinical_config()
        required_doc_types = {d['type'] for d in clinical_config['documents']}
        required_agreement_types = {a['type'] for a in clinical_config['agreements']}
        required_course_ids = clinical_config['required_course_ids']

        # Get progress status
        legal_docs = LegalDocument.query.filter_by(student_id=profile.id).all()
        agreements = DigitalAgreement.query.filter_by(student_id=profile.id).all()
        if required_course_ids:
            elearning_courses = Course.query.filter(Course.id.in_(required_course_ids)).all()
        else:
            elearning_courses = Course.query.filter_by(category='clinical').all()

        if elearning_courses:
            enrolled_count = CourseEnrollment.query.filter(
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.course_id.in_([c.id for c in elearning_courses])
            ).count()
        else:
            enrolled_count = 0
        assessments = PreClinicalAssessment.query.filter_by(student_id=profile.id).all()
        
        # Calculate completion status
        docs_uploaded = len([d for d in legal_docs if d.status in ['verified', 'pending'] and d.document_type in required_doc_types])
        docs_required = len(required_doc_types)
        agreements_signed = len([a for a in agreements if a.signed and a.agreement_type in required_agreement_types])
        agreements_required = len(required_agreement_types)
        modules_completed = enrolled_count
        modules_required = len(elearning_courses)
        posttest_passed = any(a.assessment_type == 'posttest' and a.passed for a in assessments)

        elearning_complete = modules_required > 0 and modules_completed >= modules_required
        if profile.elearning_completed != elearning_complete:
            profile.elearning_completed = elearning_complete
            db.session.commit()
        
        return render_template('clinical/onboarding.html',
                             profile=profile,
                             legal_docs=legal_docs,
                             agreements=agreements,
                     agreement_config=clinical_config['agreements'],
                     elearning_courses=elearning_courses,
                             assessments=assessments,
                             docs_uploaded=docs_uploaded,
                             docs_required=docs_required,
                             agreements_signed=agreements_signed,
                             agreements_required=agreements_required,
                             modules_completed=modules_completed,
                             modules_required=modules_required,
                             posttest_passed=posttest_passed)
    
    @app.route('/clinical/student/register', methods=['GET', 'POST'])
    @login_required
    def clinical_student_registration():
        """Student profile registration for clinical practice."""
        existing_profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        
        if request.method == 'POST':
            student_id = request.form.get('student_id')
            institution = request.form.get('institution')
            program = request.form.get('program')
            cohort = request.form.get('cohort')
            placement_hospital = request.form.get('placement_hospital')
            practice_start_date = datetime.strptime(request.form.get('practice_start_date'), '%Y-%m-%d').date()
            practice_end_date = datetime.strptime(request.form.get('practice_end_date'), '%Y-%m-%d').date()
            
            if existing_profile:
                # Update existing profile
                existing_profile.student_id = student_id
                existing_profile.institution = institution
                existing_profile.program = program
                existing_profile.cohort = cohort
                existing_profile.placement_hospital = placement_hospital
                existing_profile.practice_start_date = practice_start_date
                existing_profile.practice_end_date = practice_end_date
                flash('Student profile updated successfully!', 'success')
            else:
                # Create new profile
                profile = StudentProfile(
                    user_id=current_user.id,
                    student_id=student_id,
                    institution=institution,
                    program=program,
                    cohort=cohort,
                    placement_hospital=placement_hospital,
                    practice_start_date=practice_start_date,
                    practice_end_date=practice_end_date
                )
                db.session.add(profile)
                flash('Student profile created successfully!', 'success')
            
            db.session.commit()
            return redirect(url_for('clinical_onboarding'))
        
        return render_template('clinical/student_registration.html', profile=existing_profile)
    
    @app.route('/clinical/documents/upload', methods=['GET', 'POST'])
    @login_required
    def clinical_documents_upload():
        """Upload legal documents."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        clinical_config = get_clinical_config()
        allowed_doc_types = {d['type'] for d in clinical_config['documents']}

        if request.method == 'POST':
            document_type = request.form.get('document_type')
            expiration_date = request.form.get('expiration_date')

            if document_type not in allowed_doc_types:
                flash('Invalid document type.', 'danger')
                return redirect(request.url)
            
            if 'document_file' not in request.files:
                flash('No file uploaded.', 'danger')
                return redirect(request.url)
            
            file = request.files['document_file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{document_type}_{profile.student_id}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'clinical_documents', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                
                # Check if document already exists
                existing_doc = LegalDocument.query.filter_by(
                    student_id=profile.id,
                    document_type=document_type
                ).first()
                
                if existing_doc:
                    existing_doc.file_path = f'clinical_documents/{filename}'
                    existing_doc.status = 'pending'
                    existing_doc.uploaded_at = datetime.utcnow()
                    if expiration_date:
                        existing_doc.expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
                else:
                    document = LegalDocument(
                        student_id=profile.id,
                        document_type=document_type,
                        file_path=f'clinical_documents/{filename}',
                        status='pending',
                        expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None
                    )
                    db.session.add(document)
                
                db.session.commit()
                flash(f'{document_type.replace("_", " ").title()} uploaded successfully!', 'success')
                
                # Check if all required documents are uploaded
                uploaded_types = {d.document_type for d in LegalDocument.query.filter_by(student_id=profile.id).all() if d.status in ['verified', 'pending']}
                if allowed_doc_types.issubset(uploaded_types):
                    profile.documents_verified = True
                    db.session.commit()
                
                return redirect(url_for('clinical_onboarding'))
        
        existing_docs = LegalDocument.query.filter_by(student_id=profile.id).all()
        return render_template('clinical/documents_upload.html',
                     profile=profile,
                     existing_docs=existing_docs,
                     required_documents=clinical_config['documents'])
    
    @app.route('/clinical/agreements/<agreement_type>', methods=['GET', 'POST'])
    @login_required
    def clinical_agreements(agreement_type):
        """Sign digital agreements."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        clinical_config = get_clinical_config()
        agreement_texts = {a['type']: a.get('text', '') for a in clinical_config['agreements']}
        agreement_titles = {a['type']: a.get('title', a['type'].replace('_', ' ').title()) for a in clinical_config['agreements']}

        if agreement_type not in agreement_texts:
            flash('Agreement not found.', 'danger')
            return redirect(url_for('clinical_onboarding'))
        
        existing_agreement = DigitalAgreement.query.filter_by(
            student_id=profile.id,
            agreement_type=agreement_type
        ).first()
        
        if request.method == 'POST':
            if existing_agreement and existing_agreement.signed:
                flash('This agreement has already been signed.', 'info')
                return redirect(url_for('clinical_onboarding'))
            
            signature_data = request.form.get('signature_data', '')
            if not signature_data:
                flash('Signature is required.', 'danger')
                return redirect(request.url)
            
            ip_address = request.remote_addr
            
            if existing_agreement:
                existing_agreement.signed = True
                existing_agreement.signature_data = signature_data
                existing_agreement.signature_timestamp = datetime.utcnow()
                existing_agreement.ip_address = ip_address
            else:
                agreement = DigitalAgreement(
                    student_id=profile.id,
                    agreement_type=agreement_type,
                    content=agreement_texts.get(agreement_type, ''),
                    signed=True,
                    signature_data=signature_data,
                    signature_timestamp=datetime.utcnow(),
                    ip_address=ip_address
                )
                db.session.add(agreement)
            
            db.session.commit()
            flash(f'{agreement_type.replace("_", " ").title()} agreement signed successfully!', 'success')
            
            # Check if all agreements are signed
            signed_count = DigitalAgreement.query.filter_by(student_id=profile.id, signed=True).count()
            if signed_count >= 4:
                profile.agreements_signed = True
                db.session.commit()
            
            return redirect(url_for('clinical_onboarding'))
        
        return render_template('clinical/agreement.html',
                             profile=profile,
                             agreement_type=agreement_type,
                     agreement_title=agreement_titles.get(agreement_type),
                             agreement_text=agreement_texts.get(agreement_type, ''),
                             existing_agreement=existing_agreement)
    
    @app.route('/clinical/elearning')
    @login_required
    def clinical_elearning():
        """E-learning modules list."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))

        clinical_config = get_clinical_config()
        required_course_ids = clinical_config['required_course_ids']

        if required_course_ids:
            courses = Course.query.filter(Course.id.in_(required_course_ids)).order_by(Course.created_at.desc()).all()
        else:
            courses = Course.query.filter_by(category='clinical').order_by(Course.created_at.desc()).all()
        enrolled_course_ids = {
            e.course_id for e in CourseEnrollment.query.filter_by(user_id=current_user.id).all()
        }

        return render_template('clinical/elearning_list.html',
                             profile=profile,
                             courses=courses,
                             enrolled_course_ids=enrolled_course_ids)
    
    @app.route('/clinical/elearning/<int:module_id>', methods=['GET', 'POST'])
    @login_required
    def clinical_elearning_module(module_id):
        """Redirect to course detail for clinical e-learning."""
        course = Course.query.filter_by(id=module_id, category='clinical').first_or_404()
        return redirect(url_for('course_detail', course_id=course.id))
    
    @app.route('/clinical/assessment/<assessment_type>', methods=['GET', 'POST'])
    @login_required
    def clinical_assessment(assessment_type):
        """Pre-test or post-test assessment."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))

        clinical_config = get_clinical_config()
        required_course_ids = clinical_config['required_course_ids']
        if required_course_ids:
            total_clinical = Course.query.filter(Course.id.in_(required_course_ids)).count()
            enrolled_clinical = CourseEnrollment.query.filter(
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.course_id.in_(required_course_ids)
            ).count()
        else:
            total_clinical = Course.query.filter_by(category='clinical').count()
            enrolled_clinical = CourseEnrollment.query.join(Course).filter(
                CourseEnrollment.user_id == current_user.id,
                Course.category == 'clinical'
            ).count()
        profile.elearning_completed = total_clinical > 0 and enrolled_clinical >= total_clinical
        db.session.commit()
        
        # Check prerequisites
        if assessment_type == 'posttest' and not profile.elearning_completed:
            flash('Please complete all e-learning modules before taking the post-test.', 'warning')
            return redirect(url_for('clinical_elearning'))
        
        # Get previous attempts
        previous_attempts = PreClinicalAssessment.query.filter_by(
            student_id=profile.id,
            assessment_type=assessment_type
        ).order_by(PreClinicalAssessment.taken_at.desc()).all()
        
        passed_attempt = next((a for a in previous_attempts if a.passed), None)
        
        if request.method == 'POST':
            # Process assessment submission
            answers_data = request.form.get('answers_json', '{}')
            correct_answers = request.form.get('correct_answers', 0, type=int)
            total_questions = request.form.get('total_questions', 50, type=int)
            score = int((correct_answers / total_questions) * 100)
            passing_score = 80
            passed = score >= passing_score
            
            attempt_number = len(previous_attempts) + 1
            
            assessment = PreClinicalAssessment(
                student_id=profile.id,
                assessment_type=assessment_type,
                score=score,
                total_questions=total_questions,
                correct_answers=correct_answers,
                passing_score=passing_score,
                passed=passed,
                attempt_number=attempt_number,
                answers_json=answers_data
            )
            db.session.add(assessment)
            
            if passed and assessment_type == 'posttest':
                profile.pretest_passed = True
                profile.onboarding_complete = True
            
            db.session.commit()
            
            if passed:
                flash(f'Congratulations! You passed the {assessment_type} with a score of {score}%.', 'success')
            else:
                flash(f'You scored {score}%. You need {passing_score}% to pass. Please try again.', 'warning')
            
            return redirect(url_for('clinical_onboarding'))
        
        clinical_config = get_clinical_config()
        if assessment_type == 'pretest':
            sample_questions = clinical_config['pretest_questions']
        else:
            sample_questions = clinical_config['posttest_questions']

        if not sample_questions:
            sample_questions = [
                {'id': 1, 'question': 'No questions configured yet.', 'options': ['A', 'B', 'C', 'D']}
            ]
        
        return render_template('clinical/assessment.html',
                             profile=profile,
                             assessment_type=assessment_type,
                             questions=sample_questions,
                             previous_attempts=previous_attempts,
                             passed_attempt=passed_attempt)
    
    # ==================== CLINICAL PRACTICE - LOGBOOK ====================
    
    @app.route('/clinical/logbook')
    @login_required
    def clinical_logbook():
        """Digital logbook dashboard."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        # Get logbook entries
        page = request.args.get('page', 1, type=int)
        entries = LogbookEntry.query.filter_by(student_id=profile.id).order_by(
            LogbookEntry.entry_date.desc()
        ).paginate(page=page, per_page=20)
        
        # Get competency progress
        competencies = CompetencyProgress.query.filter_by(student_id=profile.id).all()
        
        # Statistics
        total_entries = LogbookEntry.query.filter_by(student_id=profile.id).count()
        validated_entries = LogbookEntry.query.filter_by(student_id=profile.id, validated=True).count()
        pending_validation = total_entries - validated_entries
        
        return render_template('clinical/logbook.html',
                             profile=profile,
                             entries=entries,
                             competencies=competencies,
                             total_entries=total_entries,
                             validated_entries=validated_entries,
                             pending_validation=pending_validation)
    
    @app.route('/clinical/logbook/add', methods=['GET', 'POST'])
    @login_required
    def clinical_logbook_add():
        """Add new logbook entry."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        if request.method == 'POST':
            entry_date = datetime.strptime(request.form.get('entry_date'), '%Y-%m-%d').date()
            unit = request.form.get('unit')
            procedure_name = request.form.get('procedure_name')
            procedure_type = request.form.get('procedure_type')
            role = request.form.get('role')
            duration_minutes = request.form.get('duration_minutes', type=int)
            patient_case_summary = request.form.get('patient_case_summary')
            learning_points = request.form.get('learning_points')
            
            entry = LogbookEntry(
                student_id=profile.id,
                entry_date=entry_date,
                unit=unit,
                procedure_name=procedure_name,
                procedure_type=procedure_type,
                role=role,
                duration_minutes=duration_minutes,
                patient_case_summary=patient_case_summary,
                learning_points=learning_points
            )
            db.session.add(entry)
            db.session.commit()
            
            # Update competency progress if applicable
            competency = CompetencyChecklist.query.filter_by(
                program=profile.program,
                competency_name=procedure_name
            ).first()
            
            if competency:
                progress = CompetencyProgress.query.filter_by(
                    student_id=profile.id,
                    competency_id=competency.id
                ).first()
                
                if not progress:
                    progress = CompetencyProgress(student_id=profile.id, competency_id=competency.id)
                    db.session.add(progress)
                
                if role == 'observe':
                    progress.observations_count += 1
                elif role == 'assist':
                    progress.assists_count += 1
                elif role == 'independent':
                    progress.independent_count += 1
                
                # Auto-update competency level
                if (progress.observations_count >= competency.minimum_observations and
                    progress.assists_count >= competency.minimum_assists and
                    progress.independent_count >= competency.minimum_independent):
                    if progress.competency_level == 'not_yet':
                        progress.competency_level = 'competent'
                
                db.session.commit()
            
            flash('Logbook entry added successfully! Awaiting supervisor validation.', 'success')
            return redirect(url_for('clinical_logbook'))
        
        return render_template('clinical/logbook_add.html', profile=profile)
    
    @app.route('/clinical/logbook/<int:entry_id>')
    @login_required
    def clinical_logbook_detail(entry_id):
        """View logbook entry detail."""
        entry = LogbookEntry.query.get_or_404(entry_id)
        
        # Check permission
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if entry.student_id != profile.id and entry.supervisor_id != current_user.id and not current_user.is_admin():
            flash('You do not have permission to view this entry.', 'danger')
            return redirect(url_for('clinical_logbook'))
        
        return render_template('clinical/logbook_detail.html', entry=entry, profile=profile)
    
    @app.route('/clinical/logbook/<int:entry_id>/validate', methods=['POST'])
    @login_required
    def clinical_logbook_validate(entry_id):
        """Supervisor validates logbook entry."""
        entry = LogbookEntry.query.get_or_404(entry_id)
        
        # Check if user is a supervisor
        if not current_user.can_manage_courses() and not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Only supervisors can validate entries.'}), 403
        
        validation_method = request.form.get('validation_method', 'pin')
        supervisor_notes = request.form.get('supervisor_notes')
        
        if validation_method == 'pin':
            pin = request.form.get('pin')
            supervisor_pin = SupervisorValidationPIN.query.filter_by(supervisor_id=current_user.id).first()
            
            if not supervisor_pin or not supervisor_pin.check_pin(pin):
                return jsonify({'success': False, 'message': 'Invalid PIN.'}), 400
        
        entry.supervisor_id = current_user.id
        entry.validated = True
        entry.validation_method = validation_method
        entry.validation_timestamp = datetime.utcnow()
        entry.supervisor_notes = supervisor_notes
        entry.locked = True
        
        db.session.commit()
        
        flash('Logbook entry validated successfully!', 'success')
        return jsonify({'success': True, 'message': 'Entry validated successfully.'})

    # ==================== LONG-TERM LEARNING (PATIENT CASE TRACKING) ====================

    @app.route('/clinical/cases')
    @login_required
    def clinical_cases():
        """List patient cases for long-term learning."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))

        cases = PatientCase.query.filter_by(student_id=profile.id).order_by(
            PatientCase.updated_at.desc()
        ).all()

        last_update_map = {}
        case_tree_map = {}
        for case in cases:
            latest_update = PatientCaseDailyUpdate.query.filter_by(case_id=case.id).order_by(
                PatientCaseDailyUpdate.entry_date.desc()
            ).first()
            last_update_map[case.id] = latest_update.entry_date if latest_update else None

            updates = PatientCaseDailyUpdate.query.filter_by(case_id=case.id).order_by(
                PatientCaseDailyUpdate.entry_date.asc()
            ).all()

            nodes = []
            nodes.append({
                'label': 'Day 1',
                'date': case.start_date,
                'status': 'Start',
                'summary': case.initial_diagnosis or case.initial_notes
            })

            for update in updates:
                day_number = (update.entry_date - case.start_date).days + 1
                nodes.append({
                    'label': f'Day {day_number}',
                    'date': update.entry_date,
                    'status': update.status or 'Update',
                    'summary': update.update_summary
                })

            if case.status == 'closed':
                closed_date = case.end_date or (updates[-1].entry_date if updates else case.updated_at.date())
                nodes.append({
                    'label': 'Done',
                    'date': closed_date,
                    'status': 'Closed',
                    'summary': None
                })

            case_tree_map[case.id] = nodes

        active_count = PatientCase.query.filter_by(student_id=profile.id, status='active').count()
        closed_count = PatientCase.query.filter_by(student_id=profile.id, status='closed').count()

        return render_template('clinical/cases_list.html',
                 profile=profile,
                 cases=cases,
                 active_count=active_count,
                 closed_count=closed_count,
                 last_update_map=last_update_map,
                 case_tree_map=case_tree_map)

    @app.route('/clinical/cases/add', methods=['GET', 'POST'])
    @login_required
    def clinical_cases_add():
        """Add a new patient case."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))

        if request.method == 'POST':
            case_title = request.form.get('case_title')
            patient_alias = request.form.get('patient_alias')
            unit = request.form.get('unit')
            initial_diagnosis = request.form.get('initial_diagnosis')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            initial_notes = request.form.get('initial_notes')

            new_case = PatientCase(
                student_id=profile.id,
                case_title=case_title,
                patient_alias=patient_alias,
                unit=unit,
                initial_diagnosis=initial_diagnosis,
                start_date=start_date,
                initial_notes=initial_notes,
                status='active'
            )
            db.session.add(new_case)
            db.session.commit()

            flash('Patient case created successfully.', 'success')
            return redirect(url_for('clinical_cases'))

        return render_template('clinical/cases_add.html', profile=profile)

    @app.route('/clinical/cases/<int:case_id>')
    @login_required
    def clinical_case_detail(case_id):
        """View patient case details and daily updates."""
        patient_case = PatientCase.query.get_or_404(case_id)
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()

        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))

        if patient_case.student_id != profile.id and not current_user.can_manage_courses() and not current_user.is_admin():
            flash('You do not have permission to view this case.', 'danger')
            return redirect(url_for('clinical_cases'))

        updates = PatientCaseDailyUpdate.query.filter_by(case_id=patient_case.id).order_by(
            PatientCaseDailyUpdate.entry_date.desc()
        ).all()

        return render_template('clinical/case_detail.html',
                             profile=profile,
                             patient_case=patient_case,
                             updates=updates)

    @app.route('/clinical/cases/<int:case_id>/update', methods=['POST'])
    @login_required
    def clinical_case_update(case_id):
        """Add a daily update to a patient case."""
        patient_case = PatientCase.query.get_or_404(case_id)
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()

        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))

        if patient_case.student_id != profile.id:
            flash('You do not have permission to update this case.', 'danger')
            return redirect(url_for('clinical_cases'))

        entry_date = datetime.strptime(request.form.get('entry_date'), '%Y-%m-%d').date()
        status = request.form.get('status')
        update_summary = request.form.get('update_summary')
        interventions = request.form.get('interventions')
        patient_response = request.form.get('patient_response')
        follow_up_plan = request.form.get('follow_up_plan')
        next_control_date_raw = request.form.get('next_control_date')
        next_control_date = None
        if next_control_date_raw:
            next_control_date = datetime.strptime(next_control_date_raw, '%Y-%m-%d').date()

        existing_update = PatientCaseDailyUpdate.query.filter_by(
            case_id=patient_case.id,
            entry_date=entry_date
        ).first()

        if existing_update:
            flash('You already submitted an update for this date.', 'warning')
            return redirect(url_for('clinical_case_detail', case_id=patient_case.id))

        update = PatientCaseDailyUpdate(
            case_id=patient_case.id,
            entry_date=entry_date,
            status=status,
            update_summary=update_summary,
            interventions=interventions,
            patient_response=patient_response,
            follow_up_plan=follow_up_plan,
            next_control_date=next_control_date
        )
        db.session.add(update)
        db.session.commit()

        flash('Daily update added successfully.', 'success')
        return redirect(url_for('clinical_case_detail', case_id=patient_case.id))

    @app.route('/clinical/cases/<int:case_id>/close', methods=['POST'])
    @login_required
    def clinical_case_close(case_id):
        """Close a patient case when finished."""
        patient_case = PatientCase.query.get_or_404(case_id)
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()

        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))

        if patient_case.student_id != profile.id:
            flash('You do not have permission to close this case.', 'danger')
            return redirect(url_for('clinical_cases'))

        close_date_raw = request.form.get('end_date')
        close_date = datetime.strptime(close_date_raw, '%Y-%m-%d').date() if close_date_raw else date.today()

        patient_case.status = 'closed'
        patient_case.end_date = close_date
        db.session.commit()

        flash('Case closed successfully.', 'success')
        return redirect(url_for('clinical_case_detail', case_id=patient_case.id))
    
    # ==================== DAILY JOURNAL ====================
    
    @app.route('/clinical/journal')
    @login_required
    def clinical_journal():
        """Daily reflection journal list."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        page = request.args.get('page', 1, type=int)
        journals = DailyJournal.query.filter_by(student_id=profile.id).order_by(
            DailyJournal.entry_date.desc()
        ).paginate(page=page, per_page=15)
        
        return render_template('clinical/journal_list.html', profile=profile, journals=journals)
    
    @app.route('/clinical/journal/add', methods=['GET', 'POST'])
    @login_required
    def clinical_journal_add():
        """Add daily journal entry."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        if request.method == 'POST':
            entry_date = datetime.strptime(request.form.get('entry_date'), '%Y-%m-%d').date()
            shift = request.form.get('shift')
            unit = request.form.get('unit')
            journal_text = request.form.get('journal_text')
            what_went_well = request.form.get('what_went_well')
            challenges_faced = request.form.get('challenges_faced')
            learning_insights = request.form.get('learning_insights')
            confidence_level = request.form.get('confidence_level', type=int)
            emotion_tag = request.form.get('emotion_tag')
            
            # Check if journal for this date already exists
            existing_journal = DailyJournal.query.filter_by(
                student_id=profile.id,
                entry_date=entry_date
            ).first()
            
            if existing_journal:
                flash('You have already submitted a journal for this date.', 'warning')
                return redirect(url_for('clinical_journal'))
            
            journal = DailyJournal(
                student_id=profile.id,
                entry_date=entry_date,
                shift=shift,
                unit=unit,
                journal_text=journal_text,
                what_went_well=what_went_well,
                challenges_faced=challenges_faced,
                learning_insights=learning_insights,
                confidence_level=confidence_level,
                emotion_tag=emotion_tag
            )
            db.session.add(journal)
            db.session.commit()
            
            flash('Daily journal submitted successfully!', 'success')
            return redirect(url_for('clinical_journal'))
        
        return render_template('clinical/journal_add.html', profile=profile)
    
    # ==================== SUPERVISOR DASHBOARD ====================
    
    @app.route('/clinical/supervisor/dashboard')
    @login_required
    def supervisor_dashboard():
        """Supervisor monitoring dashboard."""
        if not current_user.can_manage_courses() and not current_user.is_admin():
            flash('Access denied. Supervisor privileges required.', 'danger')
            return redirect(url_for('index'))
        
        # Get supervised students
        students = StudentProfile.query.filter_by(supervisor_id=current_user.id).all()
        
        # Get pending validations
        pending_logbook = LogbookEntry.query.filter(
            LogbookEntry.student_id.in_([s.id for s in students]),
            LogbookEntry.validated == False
        ).count()
        
        # Get journals needing feedback
        journals_no_feedback = DailyJournal.query.filter(
            DailyJournal.student_id.in_([s.id for s in students]),
            DailyJournal.supervisor_feedback.is_(None)
        ).count()
        
        # Get incident reports
        incidents = IncidentReport.query.filter(
            IncidentReport.student_id.in_([s.id for s in students]),
            IncidentReport.status != 'closed'
        ).all()
        
        return render_template('clinical/supervisor_dashboard.html',
                             students=students,
                             pending_logbook=pending_logbook,
                             journals_no_feedback=journals_no_feedback,
                             incidents=incidents)
    
    @app.route('/clinical/supervisor/student/<int:student_profile_id>')
    @login_required
    def supervisor_student_detail(student_profile_id):
        """View detailed student progress."""
        if not current_user.can_manage_courses() and not current_user.is_admin():
            flash('Access denied. Supervisor privileges required.', 'danger')
            return redirect(url_for('index'))
        
        student_profile = StudentProfile.query.get_or_404(student_profile_id)
        
        # Get all student data
        logbook_entries = LogbookEntry.query.filter_by(student_id=student_profile.id).order_by(
            LogbookEntry.entry_date.desc()
        ).limit(10).all()
        
        journals = DailyJournal.query.filter_by(student_id=student_profile.id).order_by(
            DailyJournal.entry_date.desc()
        ).limit(5).all()
        
        competencies = CompetencyProgress.query.filter_by(student_id=student_profile.id).all()
        
        assessments = WeeklyAssessment.query.filter_by(student_id=student_profile.id).order_by(
            WeeklyAssessment.week_number.desc()
        ).all()
        
        return render_template('clinical/supervisor_student_detail.html',
                             student_profile=student_profile,
                             logbook_entries=logbook_entries,
                             journals=journals,
                             competencies=competencies,
                             assessments=assessments)
    
    # ==================== INCIDENT REPORTING ====================
    
    @app.route('/clinical/incident/report', methods=['GET', 'POST'])
    @login_required
    def incident_report():
        """Report safety incident (panic button feature)."""
        if request.method == 'POST':
            incident_type = request.form.get('incident_type')
            severity = request.form.get('severity')
            incident_date = datetime.strptime(request.form.get('incident_date'), '%Y-%m-%d %H:%M')
            unit = request.form.get('unit')
            description = request.form.get('description')
            immediate_action = request.form.get('immediate_action')
            
            profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
            
            incident = IncidentReport(
                reporter_id=current_user.id,
                student_id=profile.id if profile else None,
                incident_type=incident_type,
                severity=severity,
                incident_date=incident_date,
                unit=unit,
                description=description,
                immediate_action_taken=immediate_action,
                status='reported'
            )
            db.session.add(incident)
            db.session.commit()
            
            flash('Incident report submitted successfully. Hospital management has been notified.', 'success')
            return redirect(url_for('index'))
        
        return render_template('clinical/incident_report.html')
    
    # ==================== ASSESSMENTS & EVALUATIONS ====================
    
    @app.route('/clinical/exam/<exam_type>')
    @login_required
    def clinical_exam(exam_type):
        """Final examinations."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        # Check prerequisites
        if not profile.onboarding_complete:
            flash('Please complete pre-clinical onboarding first.', 'warning')
            return redirect(url_for('clinical_onboarding'))
        
        previous_attempts = FinalExam.query.filter_by(
            student_id=profile.id,
            exam_type=exam_type
        ).order_by(FinalExam.exam_date.desc()).all()
        
        return render_template('clinical/exam.html',
                             profile=profile,
                             exam_type=exam_type,
                             previous_attempts=previous_attempts)
    
    @app.route('/clinical/evaluation360')
    @login_required
    def evaluation_360():
        """360-degree evaluation overview."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        evaluations = Evaluation360.query.filter_by(student_id=profile.id).all()
        
        # Calculate average scores
        if evaluations:
            avg_clinical = sum(e.clinical_competency_score or 0 for e in evaluations) / len(evaluations)
            avg_safety = sum(e.patient_safety_score or 0 for e in evaluations) / len(evaluations)
            avg_professionalism = sum(e.professionalism_score or 0 for e in evaluations) / len(evaluations)
        else:
            avg_clinical = avg_safety = avg_professionalism = 0
        
        return render_template('clinical/evaluation_360.html',
                             profile=profile,
                             evaluations=evaluations,
                             avg_clinical=avg_clinical,
                             avg_safety=avg_safety,
                             avg_professionalism=avg_professionalism)
    
    # ==================== POST-PRACTICE & ALUMNI ====================
    
    @app.route('/clinical/feedback', methods=['GET', 'POST'])
    @login_required
    def clinical_feedback():
        """Submit feedback on hospital and program."""
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your student profile first.', 'warning')
            return redirect(url_for('clinical_student_registration'))
        
        if request.method == 'POST':
            feedback_type = request.form.get('feedback_type')
            teaching_quality = request.form.get('teaching_quality', type=int)
            facilities = request.form.get('facilities', type=int)
            supervisor_support = request.form.get('supervisor_support', type=int)
            safety_climate = request.form.get('safety_climate', type=int)
            overall_experience = request.form.get('overall_experience', type=int)
            comments = request.form.get('comments')
            suggestions = request.form.get('suggestions')
            is_anonymous = request.form.get('is_anonymous') == 'true'
            
            feedback = StudentFeedback(
                student_id=profile.id,
                feedback_type=feedback_type,
                teaching_quality_rating=teaching_quality,
                facilities_rating=facilities,
                supervisor_support_rating=supervisor_support,
                safety_climate_rating=safety_climate,
                overall_experience_rating=overall_experience,
                comments=comments,
                suggestions=suggestions,
                is_anonymous=is_anonymous
            )
            db.session.add(feedback)
            db.session.commit()
            
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('index'))
        
        return render_template('clinical/feedback.html', profile=profile)
    
    @app.route('/clinical/alumni')
    @login_required
    def alumni_directory():
        """Alumni directory and networking."""
        alumni = AlumniProfile.query.filter_by(willing_to_mentor=True).all()
        
        return render_template('clinical/alumni_directory.html', alumni=alumni)
    
    @app.route('/clinical/certificate/<int:student_profile_id>')
    @login_required
    def clinical_certificate(student_profile_id):
        """View digital certificate."""
        student_profile = StudentProfile.query.get_or_404(student_profile_id)
        
        # Check permission
        if student_profile.user_id != current_user.id and not current_user.is_admin():
            flash('You do not have permission to view this certificate.', 'danger')
            return redirect(url_for('index'))
        
        certificate = ClinicalCertificate.query.filter_by(student_id=student_profile_id).first()
        
        if not certificate:
            flash('Certificate not yet issued.', 'warning')
            return redirect(url_for('index'))
        
        return render_template('clinical/certificate.html',
                             student_profile=student_profile,
                             certificate=certificate)
