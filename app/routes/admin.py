import os
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Course, CourseModule, CourseMaterial, LibraryBook
from app.utils import admin_required, pemateri_required, sanitize_rich_text, convert_youtube_url


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
        """Admin page to manage users, approve pemateri requests, and create admins."""
        pending_pemateri = User.query.filter_by(pending_role='pemateri').all()
        all_users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin_users.html', pending_pemateri=pending_pemateri, all_users=all_users)

    @app.route('/admin/users/<int:user_id>/approve_pemateri', methods=['POST'])
    @login_required
    @admin_required
    def approve_pemateri(user_id):
        """Approve pemateri role request."""
        user = User.query.get_or_404(user_id)
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

            module = CourseModule(
                course_id=course_id,
                title=title,
                description=description,
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

            material = CourseMaterial(
                module_id=module_id,
                title=title,
                description=description,
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
