from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Course, CourseEnrollment


def register_auth_routes(app):
    @app.route('/')
    def index():
        """Home/Dashboard page."""
        if current_user.is_authenticated:
            enrolled_courses = CourseEnrollment.query.filter_by(user_id=current_user.id).count()
            course_total = Course.query.count()
            return render_template('dashboard.html', enrolled_courses=enrolled_courses, course_total=course_total)
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
