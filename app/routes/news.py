import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, News
from app.utils import allowed_file


def register_news_routes(app):
    @app.route('/news')
    @login_required
    def news():
        """Display all news articles."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')

        query = News.query

        if search:
            query = query.filter(News.title.ilike(f'%{search}%') | News.content.ilike(f'%{search}%'))

        news_articles = query.order_by(News.created_at.desc()).paginate(page=page, per_page=12)

        return render_template('news.html', news_articles=news_articles.items, total=news_articles.total, page=page, search=search)

    @app.route('/news/<int:id>')
    @login_required
    def news_detail(id):
        """Display single news article."""
        article = News.query.get_or_404(id)
        return render_template('news_detail.html', article=article)

    @app.route('/admin/news')
    @login_required
    def admin_news():
        """Admin page to manage news."""
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))

        news_articles = News.query.order_by(News.created_at.desc()).all()
        return render_template('admin_news.html', news_articles=news_articles)

    @app.route('/admin/news/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_news():
        """Create new news article."""
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            
            if not title or not content:
                flash('Title and content are required.', 'danger')
                return redirect(url_for('admin_create_news'))

            # Handle image upload
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    # Check if file is an image
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        filename = secure_filename(file.filename)
                        # Create unique filename with timestamp
                        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'news')
                        os.makedirs(upload_folder, exist_ok=True)
                        file.save(os.path.join(upload_folder, unique_filename))
                        image_path = f'news/{unique_filename}'
                    else:
                        flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP', 'danger')
                        return redirect(url_for('admin_create_news'))

            # Create news article
            news = News(
                title=title,
                content=content,
                image_path=image_path,
                author_id=current_user.id
            )
            db.session.add(news)
            db.session.commit()

            flash('News article created successfully!', 'success')
            return redirect(url_for('admin_news'))

        return render_template('admin_create_news.html')

    @app.route('/admin/news/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_edit_news(id):
        """Edit existing news article."""
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))

        article = News.query.get_or_404(id)

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            
            if not title or not content:
                flash('Title and content are required.', 'danger')
                return redirect(url_for('admin_edit_news', id=id))

            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        # Delete old image if exists
                        if article.image_path:
                            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], article.image_path)
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        
                        filename = secure_filename(file.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'news')
                        os.makedirs(upload_folder, exist_ok=True)
                        file.save(os.path.join(upload_folder, unique_filename))
                        article.image_path = f'news/{unique_filename}'

            article.title = title
            article.content = content
            article.updated_at = datetime.utcnow()
            db.session.commit()

            flash('News article updated successfully!', 'success')
            return redirect(url_for('admin_news'))

        return render_template('admin_edit_news.html', article=article)

    @app.route('/admin/news/<int:id>/delete', methods=['POST'])
    @login_required
    def admin_delete_news(id):
        """Delete news article."""
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))

        article = News.query.get_or_404(id)
        
        # Delete image file if exists
        if article.image_path:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], article.image_path)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(article)
        db.session.commit()

        flash('News article deleted successfully!', 'success')
        return redirect(url_for('admin_news'))
