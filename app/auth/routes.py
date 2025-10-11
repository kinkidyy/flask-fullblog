from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from ..models import User
from .. import db

auth_bp = Blueprint('auth', __name__)

# ===============================
# Login
# ===============================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # already logged in -> redirect based on role
        return redirect(url_for('admin.dashboard') if current_user.is_admin else url_for('blog.index'))

    if request.method == 'POST':
        ident = request.form.get('ident', '').strip()
        password = request.form.get('password', '').strip()

        # Check by username or email
        user = User.query.filter((User.username == ident) | (User.email == ident)).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            # next page support
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.dashboard') if user.is_admin else url_for('blog.index'))
        else:
            flash('Invalid username/email or password', 'danger')

    return render_template('auth/login.html')

# ===============================
# Register
# ===============================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard') if current_user.is_admin else url_for('blog.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash('All fields required.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('User already exists.', 'error')
            return redirect(url_for('auth.register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

# ===============================
# Create Admin (for initial setup)
# ===============================
@auth_bp.route("/create-admin", methods=["GET", "POST"])
def create_admin():
    if request.method == "POST":
        username = request.form.get("username", '').strip()
        email = request.form.get("email", '').strip()
        password = request.form.get("password", '').strip()

        if User.query.filter_by(email=email).first():
            flash("A user with this email already exists!", "danger")
            return redirect(url_for("auth.create_admin"))

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        flash("Admin account created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return """
    <form method="POST">
        <label>Username:</label><input type="text" name="username" required><br>
        <label>Email:</label><input type="email" name="email" required><br>
        <label>Password:</label><input type="password" name="password" required><br>
        <button type="submit">Create Admin</button>
    </form>
    """

# ===============================
# Logout
# ===============================
@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Logged out successfully.', 'success')
    return redirect(url_for('blog.index'))
