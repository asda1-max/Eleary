import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, LibraryBook
from app.utils import allowed_file


def register_library_routes(app):
    @app.route('/library')
    @login_required
    def library():
        """Display approved library documents with search functionality."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')

        query = LibraryBook.query.filter_by(status='approved')

        if search:
            query = query.filter(LibraryBook.title.ilike(f'%{search}%') | LibraryBook.description.ilike(f'%{search}%'))

        books = query.order_by(LibraryBook.created_at.desc()).paginate(page=page, per_page=12)

        return render_template('library.html', books=books.items, total=books.total, page=page, search=search)

    @app.route('/library/upload', methods=['POST'])
    @login_required
    def upload_document():
        """Upload document to library (pending approval by admin)."""
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(url_for('library'))

        file = request.files['file']
        title = request.form.get('title', '')
        description = request.form.get('description', '')

        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('library'))

        if not allowed_file(file.filename):
            flash('File type not allowed. Allowed: PDF, DOC, DOCX, PPT, PPTX, TXT', 'danger')
            return redirect(url_for('library'))

        if not title:
            flash('Title is required.', 'danger')
            return redirect(url_for('library'))

        try:
            # Save file with secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S_')
            filename = timestamp + filename
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Create library book entry (pending status)
            book = LibraryBook(
                uploader_id=current_user.id,
                title=title,
                description=description,
                file_path=file_path,
                status='pending'
            )
            db.session.add(book)
            db.session.commit()

            flash('Document submitted for admin review.', 'success')
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'danger')

        return redirect(url_for('library'))

    @app.route('/library/<int:book_id>/preview')
    @login_required
    def preview_document(book_id):
        """Preview a library document."""
        book = LibraryBook.query.get_or_404(book_id)

        # Check access: admins can preview pending, users can preview approved
        if book.status == 'pending' and not current_user.is_admin():
            flash('You do not have permission to view this document.', 'danger')
            return redirect(url_for('library'))
        elif book.status == 'rejected':
            flash('This document has been rejected.', 'danger')
            return redirect(url_for('library'))

        return render_template('preview.html', book=book)

    @app.route('/library/<int:book_id>/download')
    @login_required
    def download_document(book_id):
        """Download a library document."""
        book = LibraryBook.query.get_or_404(book_id)

        # Check access: admins can download pending, users can download approved
        if book.status == 'pending' and not current_user.is_admin():
            flash('You do not have permission to download this document.', 'danger')
            return redirect(url_for('library'))
        elif book.status == 'rejected':
            flash('This document has been rejected.', 'danger')
            return redirect(url_for('library'))

        # Verify file exists
        if not os.path.exists(book.file_path):
            flash('File not found.', 'danger')
            return redirect(url_for('library'))

        try:
            return send_file(
                book.file_path,
                as_attachment=True,
                download_name=f"{book.title}_{book.id}.{book.file_path.rsplit('.', 1)[1]}"
            )
        except Exception as e:
            flash(f'Error downloading file: {str(e)}', 'danger')
            return redirect(url_for('library'))

    @app.route('/library/<int:book_id>/view')
    @login_required
    def view_document(book_id):
        """View a library document inline (for preview)."""
        book = LibraryBook.query.get_or_404(book_id)

        # Check access: admins can view pending, users can view approved
        if book.status == 'pending' and not current_user.is_admin():
            flash('You do not have permission to view this document.', 'danger')
            return redirect(url_for('library'))
        elif book.status == 'rejected':
            flash('This document has been rejected.', 'danger')
            return redirect(url_for('library'))

        # Verify file exists
        if not os.path.exists(book.file_path):
            flash('File not found.', 'danger')
            return redirect(url_for('library'))

        try:
            # Return file with inline disposition for browser preview
            return send_file(
                book.file_path,
                as_attachment=False,  # Display inline, not download
                download_name=f"{book.title}_{book.id}.{book.file_path.rsplit('.', 1)[1]}"
            )
        except Exception as e:
            flash(f'Error viewing file: {str(e)}', 'danger')
            return redirect(url_for('library'))
