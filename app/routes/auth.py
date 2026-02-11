import os
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Course, CourseEnrollment, News, StudentProfile


def register_auth_routes(app):
    @app.route('/setup-admin', methods=['GET', 'POST'])
    def setup_admin():
        """Create the first admin account on initial launch."""
        if User.query.filter_by(role='admin').first():
            return redirect(url_for('login'))

        if request.method == 'POST':
            setup_password = request.form.get('setup_password', '')
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            if setup_password != current_app.config.get('APP_SETUP_PASSWORD'):
                flash('Invalid setup password.', 'danger')
                return redirect(url_for('setup_admin'))

            if not username or not password:
                flash('Username and password are required.', 'danger')
                return redirect(url_for('setup_admin'))

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('setup_admin'))

            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'danger')
                return redirect(url_for('setup_admin'))

            email = f"{username}@eleary.local"
            if User.query.filter_by(email=email).first():
                flash('Email already exists.', 'danger')
                return redirect(url_for('setup_admin'))

            admin = User(username=username, email=email, role='admin', division='Administration')
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            flash('Admin account created. Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('setup_admin.html')

    @app.route('/')
    def index():
        """Home/Dashboard page."""
        if current_user.is_authenticated:
            enrolled_courses = CourseEnrollment.query.filter_by(user_id=current_user.id).count()
            course_total = Course.query.count()
            # Get 3 latest news for carousel
            latest_news = News.query.order_by(News.created_at.desc()).limit(3).all()
            # Get student profile if exists
            student_profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
            return render_template('dashboard.html', 
                                 enrolled_courses=enrolled_courses, 
                                 course_total=course_total, 
                                 latest_news=latest_news,
                                 student_profile=student_profile)
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration."""
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            division = request.form.get('division', 'Medical')
            request_pemateri = request.form.get('request_pemateri') == 'on'  # Checkbox for pemateri role request

            # Validate input
            if not username or not email or not password:
                flash('All fields are required.', 'danger')
                return redirect(url_for('register'))

            # Check if user exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'danger')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already exists.', 'danger')
                return redirect(url_for('register'))

            # Create new user - pemateri requests are pending admin approval
            if request_pemateri:
                user = User(username=username, email=email, division=division, role='user', pending_role='pemateri')
                flash('Registration successful! Your instructor role request is pending admin approval. Please log in.', 'info')
            else:
                user = User(username=username, email=email, division=division, role='user')
                flash('Registration successful! Please log in.', 'success')

            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """User logout."""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    def _allowed_image(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    @app.route('/settings')
    @login_required
    def account_settings():
        """Account settings page."""
        return render_template('account_settings.html')

    @app.route('/settings/profile', methods=['POST'])
    @login_required
    def update_profile():
        """Update username, division, and bio."""
        username = request.form.get('username', '').strip()
        division = request.form.get('division', '').strip()
        bio = request.form.get('bio', '').strip()

        if not username:
            flash('Username is required.', 'danger')
            return redirect(url_for('account_settings'))

        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'danger')
                return redirect(url_for('account_settings'))
            current_user.username = username

        current_user.division = division or current_user.division
        current_user.bio = bio
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('account_settings'))

    @app.route('/settings/password', methods=['POST'])
    @login_required
    def update_password():
        """Update user password."""
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('account_settings'))

        if not new_password or new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('account_settings'))

        current_user.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully.', 'success')
        return redirect(url_for('account_settings'))

    @app.route('/settings/avatar', methods=['POST'])
    @login_required
    def update_avatar():
        """Update profile picture."""
        file = request.files.get('profile_image')
        if not file or file.filename == '':
            flash('Please select an image file.', 'danger')
            return redirect(url_for('account_settings'))

        if not _allowed_image(file.filename):
            flash('Invalid image type. Use PNG, JPG, JPEG, GIF, or WEBP.', 'danger')
            return redirect(url_for('account_settings'))

        filename = secure_filename(file.filename)
        user_folder = 'profile'
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        target_dir = os.path.join(upload_folder, user_folder)
        os.makedirs(target_dir, exist_ok=True)
        save_path = os.path.join(target_dir, f"user_{current_user.id}_{filename}")
        file.save(save_path)

        current_user.profile_image = f"{user_folder}/user_{current_user.id}_{filename}"
        db.session.commit()
        flash('Profile picture updated.', 'success')
        return redirect(url_for('account_settings'))

    @app.route('/settings/request_role', methods=['POST'])
    @login_required
    def request_role():
        """Request instructor or admin role."""
        role = request.form.get('role')
        if role not in {'pemateri', 'admin'}:
            flash('Invalid role request.', 'danger')
            return redirect(url_for('account_settings'))

        if current_user.role == 'admin' and role == 'pemateri':
            flash('Admins cannot request instructor access.', 'danger')
            return redirect(url_for('account_settings'))

        if current_user.role == role:
            flash('You already have this role.', 'info')
            return redirect(url_for('account_settings'))

        if current_user.pending_role:
            flash('You already have a pending role request.', 'info')
            return redirect(url_for('account_settings'))

        current_user.pending_role = role
        db.session.commit()
        flash('Role request submitted for admin approval.', 'info')
        return redirect(url_for('account_settings'))

    @app.route('/settings/revoke_role', methods=['POST'])
    @login_required
    def revoke_role():
        """Allow user to revoke their own admin or instructor role."""
        role = request.form.get('role')
        if role not in {'pemateri', 'admin'}:
            flash('Invalid role revoke request.', 'danger')
            return redirect(url_for('account_settings'))

        if current_user.role != role:
            flash('You do not have this role.', 'info')
            return redirect(url_for('account_settings'))

        current_user.role = 'user'
        current_user.pending_role = None
        db.session.commit()
        flash('Your access has been revoked.', 'success')
        return redirect(url_for('account_settings'))
