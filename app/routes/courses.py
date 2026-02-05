from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Course, CourseModule, CourseMaterial, AttendanceLog, CourseEnrollment, MaterialComment, MaterialSubmission
from app.utils import get_course_attendance_today, save_upload_image, allowed_file
from werkzeug.utils import secure_filename
import os


def register_course_routes(app):
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

    @app.route('/material/<int:material_id>')
    @login_required
    def material_detail(material_id):
        """Display material detail with comments and submissions."""
        material = CourseMaterial.query.get_or_404(material_id)
        module = material.module
        course = module.course

        # Get all comments for this material (ordered by newest first)
        comments = MaterialComment.query.filter_by(material_id=material_id).order_by(MaterialComment.created_at.desc()).all()

        # Get user's submission if exists (for assignment type)
        user_submission = None
        if material.type == 'assignment':
            user_submission = MaterialSubmission.query.filter_by(
                material_id=material_id,
                user_id=current_user.id
            ).first()

        return render_template('material_detail.html',
                               material=material,
                               module=module,
                               course=course,
                               comments=comments,
                               user_submission=user_submission)

    @app.route('/material/<int:material_id>/comment', methods=['POST'])
    @login_required
    def add_comment(material_id):
        """Add a comment to a material."""
        material = CourseMaterial.query.get_or_404(material_id)
        content = request.form.get('content', '').strip()

        if not content:
            flash('Comment cannot be empty.', 'danger')
            return redirect(url_for('material_detail', material_id=material_id))

        comment = MaterialComment(
            material_id=material_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(comment)
        db.session.commit()

        flash('Comment posted successfully!', 'success')
        return redirect(url_for('material_detail', material_id=material_id))

    @app.route('/material/<int:material_id>/submit', methods=['POST'])
    @login_required
    def submit_material(material_id):
        """Submit assignment for a material."""
        material = CourseMaterial.query.get_or_404(material_id)

        # Check if material is assignment type
        if material.type != 'assignment':
            flash('This material does not accept submissions.', 'danger')
            return redirect(url_for('material_detail', material_id=material_id))

        # Check if already submitted
        existing_submission = MaterialSubmission.query.filter_by(
            material_id=material_id,
            user_id=current_user.id
        ).first()

        if existing_submission:
            flash('You have already submitted this assignment.', 'info')
            return redirect(url_for('material_detail', material_id=material_id))

        # Get form data
        text_content = request.form.get('text_content', '').strip()
        file_path = None

        # Handle file upload if provided
        if 'submission_file' in request.files:
            file = request.files['submission_file']
            if file and file.filename:
                # Save the file
                file_path = save_upload_image(file, subfolder='submissions')

        # At least one of text or file must be provided
        if not text_content and not file_path:
            flash('Please provide either a file or text submission.', 'danger')
            return redirect(url_for('material_detail', material_id=material_id))

        # Create submission
        submission = MaterialSubmission(
            material_id=material_id,
            user_id=current_user.id,
            file_path=file_path,
            text_content=text_content if text_content else None
        )
        db.session.add(submission)
        db.session.commit()

        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('material_detail', material_id=material_id))
