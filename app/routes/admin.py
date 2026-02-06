import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Course, CourseModule, CourseMaterial, LibraryBook, ClinicalConfig, LegalDocument, StudentProfile
from app.utils import admin_required, pemateri_required, sanitize_rich_text, convert_youtube_url, save_upload_image, allowed_image_file


def register_admin_routes(app):
    @app.route('/admin/approvals')
    @login_required
    @admin_required
    def admin_approvals():
        """Admin page to approve/reject pending library documents."""
        page = request.args.get('page', 1, type=int)
        pending_books = LibraryBook.query.filter_by(status='pending').order_by(LibraryBook.created_at.desc()).paginate(page=page, per_page=10)

        return render_template('admin_approvals.html', books=pending_books.items, total=pending_books.total, page=page)

    @app.route('/admin/approvals/<int:book_id>/approve', methods=['POST'])
    @login_required
    @admin_required
    def approve_book(book_id):
        """Approve a pending library document."""
        book = LibraryBook.query.get_or_404(book_id)
        book.status = 'approved'
        db.session.commit()
        flash(f'Document "{book.title}" approved.', 'success')
        return redirect(url_for('admin_approvals'))

    @app.route('/admin/approvals/<int:book_id>/reject', methods=['POST'])
    @login_required
    @admin_required
    def reject_book(book_id):
        """Reject a pending library document."""
        book = LibraryBook.query.get_or_404(book_id)

        # Delete the file
        if os.path.exists(book.file_path):
            os.remove(book.file_path)

        db.session.delete(book)
        db.session.commit()
        flash('Document rejected and deleted.', 'success')
        return redirect(url_for('admin_approvals'))

    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        """Admin page to manage users, approve role requests, and manage access."""
        pending_pemateri = User.query.filter_by(pending_role='pemateri').all()
        pending_admin = User.query.filter_by(pending_role='admin').all()
        all_users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin_users.html', pending_pemateri=pending_pemateri, pending_admin=pending_admin, all_users=all_users)

    @app.route('/admin/users/<int:user_id>/approve_pemateri', methods=['POST'])
    @login_required
    @admin_required
    def approve_pemateri(user_id):
        """Approve pemateri role request."""
        user = User.query.get_or_404(user_id)
        if user.role == 'admin':
            user.pending_role = None
            db.session.commit()
            flash('Admins cannot be instructors.', 'info')
            return redirect(url_for('admin_users'))
        user.role = 'pemateri'
        user.pending_role = None
        db.session.commit()
        flash(f'{user.username} is now an Instructor.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/reject_pemateri', methods=['POST'])
    @login_required
    @admin_required
    def reject_pemateri(user_id):
        """Reject pemateri role request."""
        user = User.query.get_or_404(user_id)
        user.pending_role = None
        db.session.commit()
        flash(f'Instructor request for {user.username} rejected.', 'info')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/approve_admin', methods=['POST'])
    @login_required
    @admin_required
    def approve_admin(user_id):
        """Approve admin role request."""
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You are already an admin.', 'info')
        else:
            user.role = 'admin'
            user.pending_role = None
            db.session.commit()
            flash(f'{user.username} is now an Admin.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/reject_admin', methods=['POST'])
    @login_required
    @admin_required
    def reject_admin(user_id):
        """Reject admin role request."""
        user = User.query.get_or_404(user_id)
        user.pending_role = None
        db.session.commit()
        flash(f'Admin request for {user.username} rejected.', 'info')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/make_admin', methods=['POST'])
    @login_required
    @admin_required
    def make_admin(user_id):
        """Promote user to admin."""
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You are already an admin.', 'info')
        else:
            user.role = 'admin'
            user.pending_role = None
            db.session.commit()
            flash(f'{user.username} is now an Admin.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/revoke_admin', methods=['POST'])
    @login_required
    @admin_required
    def revoke_admin(user_id):
        """Remove admin access from a user."""
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You cannot remove your own admin access.', 'danger')
        else:
            if user.role == 'admin':
                user.role = 'user'
                user.pending_role = None
                db.session.commit()
                flash(f'Admin access removed from {user.username}.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/revoke_pemateri', methods=['POST'])
    @login_required
    @admin_required
    def revoke_pemateri(user_id):
        """Remove instructor access from a user."""
        user = User.query.get_or_404(user_id)
        if user.role == 'pemateri':
            user.role = 'user'
            user.pending_role = None
            db.session.commit()
            flash(f'Instructor access removed from {user.username}.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_user(user_id):
        """Delete a user account."""
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
        else:
            username = user.username
            db.session.delete(user)
            db.session.commit()
            flash(f'User {username} deleted.', 'success')
        return redirect(url_for('admin_users'))

    def get_clinical_config():
        config = ClinicalConfig.query.first()
        if not config:
            config = ClinicalConfig()
            db.session.add(config)
            db.session.commit()
        return config

    @app.route('/admin/clinical/modules', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_clinical_modules():
        """Admin editor for clinical module settings."""
        import json

        config = get_clinical_config()

        if request.method == 'POST':
            doc_types = request.form.getlist('doc_type[]')
            doc_labels = request.form.getlist('doc_label[]')
            doc_requires = request.form.getlist('doc_requires_expiration[]')

            documents = []
            for idx, doc_type in enumerate(doc_types):
                label = doc_labels[idx] if idx < len(doc_labels) else ''
                if doc_type and label:
                    documents.append({
                        'type': doc_type.strip(),
                        'label': label.strip(),
                        'requires_expiration': doc_type in doc_requires
                    })

            agreement_types = request.form.getlist('agreement_type[]')
            agreement_titles = request.form.getlist('agreement_title[]')
            agreement_texts = request.form.getlist('agreement_text[]')

            agreements = []
            for idx, agreement_type in enumerate(agreement_types):
                title = agreement_titles[idx] if idx < len(agreement_titles) else ''
                text = agreement_texts[idx] if idx < len(agreement_texts) else ''
                if agreement_type and title:
                    agreements.append({
                        'type': agreement_type.strip(),
                        'title': title.strip(),
                        'text': text.strip()
                    })

            required_course_ids = [int(cid) for cid in request.form.getlist('required_course_ids') if cid.isdigit()]

            pretest_questions_raw = request.form.get('pretest_questions_json', '[]')
            posttest_questions_raw = request.form.get('posttest_questions_json', '[]')

            try:
                pretest_questions = json.loads(pretest_questions_raw) if pretest_questions_raw else []
                posttest_questions = json.loads(posttest_questions_raw) if posttest_questions_raw else []
            except json.JSONDecodeError:
                flash('Assessment questions JSON is invalid.', 'danger')
                return redirect(request.url)

            config.documents_json = json.dumps(documents)
            config.agreements_json = json.dumps(agreements)
            config.required_course_ids_json = json.dumps(required_course_ids)
            config.pretest_questions_json = json.dumps(pretest_questions)
            config.posttest_questions_json = json.dumps(posttest_questions)
            db.session.commit()

            flash('Clinical module settings updated successfully.', 'success')
            return redirect(url_for('admin_clinical_modules'))

        import json
        documents = json.loads(config.documents_json or '[]')
        agreements = json.loads(config.agreements_json or '[]')
        required_course_ids = json.loads(config.required_course_ids_json or '[]')
        pretest_questions = json.loads(config.pretest_questions_json or '[]')
        posttest_questions = json.loads(config.posttest_questions_json or '[]')

        clinical_courses = Course.query.filter_by(category='clinical').all()

        return render_template('admin_clinical_modules.html',
                             documents=documents,
                             agreements=agreements,
                             required_course_ids=required_course_ids,
                             pretest_questions_json=json.dumps(pretest_questions, indent=2),
                             posttest_questions_json=json.dumps(posttest_questions, indent=2),
                             clinical_courses=clinical_courses)

    @app.route('/admin/clinical/documents')
    @login_required
    @admin_required
    def admin_clinical_documents():
        """Admin page to approve/reject clinical documents."""
        pending_docs = LegalDocument.query.filter_by(status='pending').order_by(LegalDocument.uploaded_at.desc()).all()
        return render_template('admin_clinical_documents.html', pending_docs=pending_docs)

    @app.route('/admin/clinical/documents/<int:doc_id>/approve', methods=['POST'])
    @login_required
    @admin_required
    def approve_clinical_document(doc_id):
        doc = LegalDocument.query.get_or_404(doc_id)
        doc.status = 'verified'
        doc.verified_by_id = current_user.id
        doc.verified_at = datetime.utcnow()
        db.session.commit()

        # Update student profile documents_verified if all required docs are verified
        config = get_clinical_config()
        import json
        required_types = {d['type'] for d in json.loads(config.documents_json or '[]')}
        student_docs = LegalDocument.query.filter_by(student_id=doc.student_id).all()
        verified_types = {d.document_type for d in student_docs if d.status == 'verified'}
        profile = StudentProfile.query.get(doc.student_id)
        if profile and required_types and required_types.issubset(verified_types):
            profile.documents_verified = True
            db.session.commit()

        flash('Document approved.', 'success')
        return redirect(url_for('admin_clinical_documents'))

    @app.route('/admin/clinical/documents/<int:doc_id>/reject', methods=['POST'])
    @login_required
    @admin_required
    def reject_clinical_document(doc_id):
        doc = LegalDocument.query.get_or_404(doc_id)
        doc.status = 'rejected'
        doc.verified_by_id = current_user.id
        doc.verified_at = datetime.utcnow()
        db.session.commit()
        profile = StudentProfile.query.get(doc.student_id)
        if profile:
            profile.documents_verified = False
            db.session.commit()
        flash('Document rejected.', 'info')
        return redirect(url_for('admin_clinical_documents'))

    @app.route('/admin/courses')
    @login_required
    @pemateri_required
    def admin_courses():
        """Pemateri/Admin page to create and manage courses."""
        # If pemateri (not admin), show only their courses
        if current_user.is_pemateri() and not current_user.is_admin():
            courses = Course.query.filter_by(instructor_id=current_user.id).all()
        else:
            # Admin sees all courses
            courses = Course.query.all()
        return render_template('admin_courses.html', courses=courses)

    @app.route('/admin/courses/create', methods=['GET', 'POST'])
    @login_required
    @pemateri_required
    def create_course():
        """Create a new course."""
        if request.method == 'POST':
            title = request.form.get('title')
            description = sanitize_rich_text(request.form.get('description'))
            category = request.form.get('category', 'medical')
            thumbnail_url = request.form.get('thumbnail_url')

            if not title:
                flash('Title is required.', 'danger')
                return redirect(url_for('create_course'))

            # Handle image upload if provided
            if 'thumbnail_image' in request.files:
                image_file = request.files['thumbnail_image']
                if image_file and image_file.filename:
                    image_path = save_upload_image(image_file, subfolder='courses')
                    if image_path:
                        thumbnail_url = image_path

            # Create course with current user as instructor
            course = Course(
                title=title,
                description=description,
                instructor_id=current_user.id,  # Set to current user (pemateri/admin)
                category=category,
                thumbnail_url=thumbnail_url
            )
            db.session.add(course)
            db.session.commit()

            flash(f'Course "{title}" created successfully!', 'success')
            return redirect(url_for('admin_courses'))

        return render_template('admin_create_course.html')

    @app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
    @login_required
    @pemateri_required
    def edit_course(course_id):
        """Edit an existing course."""
        course = Course.query.get_or_404(course_id)

        # Check permission - admin can edit any, pemateri can edit only their own
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to edit this course.', 'danger')
            return redirect(url_for('admin_courses'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = sanitize_rich_text(request.form.get('description'))
            category = request.form.get('category', 'medical')

            if not title:
                flash('Title is required.', 'danger')
                return redirect(url_for('edit_course', course_id=course_id))

            # Update course details
            course.title = title
            course.description = description
            course.category = category

            # Handle image upload if provided
            if 'thumbnail_image' in request.files:
                image_file = request.files['thumbnail_image']
                if image_file and image_file.filename:
                    image_path = save_upload_image(image_file, subfolder='courses')
                    if image_path:
                        course.thumbnail_url = image_path

            db.session.commit()
            flash(f'Course "{title}" updated successfully!', 'success')
            return redirect(url_for('admin_courses'))

        return render_template('admin_edit_course.html', course=course)

    @app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
    @login_required
    @pemateri_required
    def delete_course(course_id):
        """Delete a course - admin can delete any, pemateri can delete only their own."""
        course = Course.query.get_or_404(course_id)

        # Check permission
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to delete this course.', 'danger')
            return redirect(url_for('admin_courses'))

        title = course.title
        db.session.delete(course)
        db.session.commit()
        flash(f'Course "{title}" deleted successfully.', 'success')
        return redirect(url_for('admin_courses'))

    @app.route('/admin/courses/<int:course_id>/modules', methods=['GET', 'POST'])
    @login_required
    @pemateri_required
    def manage_modules(course_id):
        """Manage modules for a course."""
        course = Course.query.get_or_404(course_id)

        # Check permission: only course creator or admin can manage
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to manage this course.', 'danger')
            return redirect(url_for('admin_courses'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = sanitize_rich_text(request.form.get('description'))
            order_index = request.form.get('order_index', 0, type=int)

            if not title:
                flash('Module title is required.', 'danger')
                return redirect(url_for('manage_modules', course_id=course_id))

            # Handle image upload if provided
            image_path = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    image_path = save_upload_image(image_file, subfolder='modules')

            module = CourseModule(
                course_id=course_id,
                title=title,
                description=description,
                image_path=image_path,
                order_index=order_index
            )
            db.session.add(module)
            db.session.commit()

            flash(f'Module "{title}" added successfully!', 'success')

        modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index).all()
        return render_template('admin_manage_modules.html', course=course, modules=modules)

    @app.route('/admin/modules/<int:module_id>/edit', methods=['GET', 'POST'])
    @login_required
    @pemateri_required
    def edit_module(module_id):
        """Edit a module."""
        module = CourseModule.query.get_or_404(module_id)
        course = module.course

        # Check permission: only course creator or admin can manage
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to manage this course.', 'danger')
            return redirect(url_for('admin_courses'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = sanitize_rich_text(request.form.get('description'))
            order_index = request.form.get('order_index', 0, type=int)

            if not title:
                flash('Module title is required.', 'danger')
                return redirect(url_for('edit_module', module_id=module_id))

            # Handle image upload if provided
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    image_path = save_upload_image(image_file, subfolder='modules')
                    module.image_path = image_path

            module.title = title
            module.description = description
            module.order_index = order_index
            db.session.commit()

            flash(f'Module "{title}" updated successfully!', 'success')
            return redirect(url_for('manage_modules', course_id=course.id))

        return render_template('admin_edit_module.html', module=module, course=course)

    @app.route('/admin/modules/<int:module_id>/delete', methods=['POST'])
    @login_required
    @pemateri_required
    def delete_module(module_id):
        """Delete a module."""
        module = CourseModule.query.get_or_404(module_id)
        course = module.course

        # Check permission: only course creator or admin can manage
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to manage this course.', 'danger')
            return redirect(url_for('admin_courses'))

        title = module.title
        db.session.delete(module)
        db.session.commit()

        flash(f'Module "{title}" deleted successfully.', 'success')
        return redirect(url_for('manage_modules', course_id=course.id))

    @app.route('/admin/modules/<int:module_id>/materials', methods=['GET', 'POST'])
    @login_required
    @pemateri_required
    def manage_materials(module_id):
        """Manage materials for a module."""
        module = CourseModule.query.get_or_404(module_id)
        course = module.course

        # Check permission: only course creator or admin can manage
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to manage this course.', 'danger')
            return redirect(url_for('admin_courses'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = sanitize_rich_text(request.form.get('description'))
            file_path = request.form.get('file_path')
            material_type = request.form.get('type', 'pdf')

            # Convert YouTube URLs to embed format if video type
            if material_type == 'video':
                file_path = convert_youtube_url(file_path)

            if not title:
                flash('Material title is required.', 'danger')
                return redirect(url_for('manage_materials', module_id=module_id))

            # Handle image upload if provided
            image_path = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    image_path = save_upload_image(image_file, subfolder='materials')

            material = CourseMaterial(
                module_id=module_id,
                title=title,
                description=description,
                image_path=image_path,
                file_path=file_path,
                type=material_type
            )
            db.session.add(material)
            db.session.commit()

            flash(f'Material "{title}" added successfully!', 'success')

        materials = CourseMaterial.query.filter_by(module_id=module_id).all()
        return render_template('admin_manage_materials.html', module=module, materials=materials)

    @app.route('/admin/materials/<int:material_id>/edit', methods=['GET', 'POST'])
    @login_required
    @pemateri_required
    def edit_material(material_id):
        """Edit a course material."""
        material = CourseMaterial.query.get_or_404(material_id)
        module = material.module
        course = module.course

        # Check permission: only course creator or admin can manage
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to manage this course.', 'danger')
            return redirect(url_for('admin_courses'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = sanitize_rich_text(request.form.get('description'))
            file_path = request.form.get('file_path')
            material_type = request.form.get('type', 'pdf')

            # Convert YouTube URLs to embed format if video type
            if material_type == 'video':
                file_path = convert_youtube_url(file_path)

            if not title:
                flash('Material title is required.', 'danger')
                return redirect(url_for('edit_material', material_id=material_id))

            # Handle image upload if provided
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    image_path = save_upload_image(image_file, subfolder='materials')
                    material.image_path = image_path

            material.title = title
            material.description = description
            material.file_path = file_path
            material.type = material_type
            db.session.commit()

            flash(f'Material "{title}" updated successfully!', 'success')
            return redirect(url_for('manage_materials', module_id=module.id))

        return render_template('admin_edit_material.html', material=material, module=module, course=course)

    @app.route('/admin/materials/<int:material_id>/delete', methods=['POST'])
    @login_required
    @pemateri_required
    def delete_material(material_id):
        """Delete a course material."""
        material = CourseMaterial.query.get_or_404(material_id)
        module = material.module
        course = module.course

        # Check permission: only course creator or admin can manage
        if not current_user.is_admin() and course.instructor_id != current_user.id:
            flash('You do not have permission to manage this course.', 'danger')
            return redirect(url_for('admin_courses'))

        title = material.title
        db.session.delete(material)
        db.session.commit()

        flash(f'Material "{title}" deleted successfully.', 'success')
        return redirect(url_for('manage_materials', module_id=module.id))

    @app.route('/admin/materials/upload-image', methods=['POST'])
    @login_required
    @pemateri_required
    def upload_material_image():
        """Handle image uploads for Quill editor in material management.
        
        Returns JSON with:
        - success: True/False
        - message: Status message
        - url: Image URL if successful
        """
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image file provided'
            }), 400
        
        file_obj = request.files['image']
        
        if not file_obj or file_obj.filename == '':
            return jsonify({
                'success': False,
                'message': 'No image selected'
            }), 400
        
        if not allowed_image_file(file_obj.filename):
            return jsonify({
                'success': False,
                'message': 'Invalid image format. Allowed: JPG, PNG, GIF, WebP, SVG'
            }), 400
        
        try:
            image_path = save_upload_image(file_obj, subfolder='materials')
            if not image_path:
                return jsonify({
                    'success': False,
                    'message': 'Failed to save image'
                }), 400
            
            return jsonify({
                'success': True,
                'message': 'Image uploaded successfully',
                'url': image_path
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Upload error: {str(e)}'
            }), 500

