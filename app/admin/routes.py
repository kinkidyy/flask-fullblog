from flask import Blueprint, render_template, request, redirect, url_for, flash, abort,current_app
from flask_login import current_user
from ..models import Post, Category, User
from .. import db, login_manager
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os
from slugify import slugify

# Add this if not already imported for file paths


admin_bp = Blueprint('admin', __name__)

# ===============================
# Decorator: restrict to admins only
# ===============================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not getattr(current_user, "is_admin", False):
            flash("You do not have permission to access this page.", "error")
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ===============================
# Dashboard
# ===============================
@admin_bp.route('/')
@admin_required
def dashboard():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    users = User.query.all()

    posts_serialized = [
        {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category": post.category.name if post.category else "Uncategorized",
            "author": post.author.username if post.author else "Unknown",
            "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": getattr(post, 'status', 'published'),
            "views": getattr(post, 'views', 0),
        }
        for post in posts
    ]

    return render_template('admin/dashboard.html', posts=posts_serialized, users=users, categories=categories)

# ===============================
# New Post
# ===============================
@admin_bp.route("/new-post", methods=["GET", "POST"])
@admin_required
def new_post():
    categories = Category.query.all()  # Query the list
    
    # Optional: One-time creation of default categories if they don't exist
    default_names = ['general', 'politics', 'religion', 'sport', 'entertainment', 'Naija gist']
    for name in default_names:
        if not Category.query.filter_by(name=name).first():
            default_cat = Category(name=name)
            db.session.add(default_cat)
            db.session.commit()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')

        if not title or not content or not category_id:
            flash("All fields are required.", "danger")
            return redirect(url_for('admin.new_post'))

        # Handle both int IDs (from DB) and str names (from hardcoded defaults)
        category = Category.query.filter_by(id=category_id).first() or Category.query.filter_by(name=category_id).first()
        if not category:
            flash("Invalid category selected.", "danger")
            return redirect(url_for('admin.new_post'))
        
        category_id = category.id  # Use the actual ID

        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Post.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Handle media upload
        media_filename = None
        if 'media' in request.files:
            file = request.files['media']
            if file.filename != '':  # File was selected
                # Secure and validate filename
                filename = secure_filename(file.filename)
                if filename:  # Valid file
                    # Add timestamp to avoid duplicates
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    name, ext = os.path.splitext(filename)
                    unique_filename = f"{name}_{timestamp}{ext}"
                    
                    # Define upload folder
                    upload_folder = os.path.join('static', 'uploads', 'media')
                    os.makedirs(os.path.join(current_app.root_path, upload_folder), exist_ok=True)  # Create if missing
                    
                    # Full path
                    file_path = os.path.join(current_app.root_path, upload_folder, unique_filename)
                    file.save(file_path)
                    
                    media_filename = unique_filename  # Store just the filename in DB
                    flash('Media uploaded successfully!', 'success')

        # Create Post with all fields
        post = Post(
            title=title,
            slug=slug,
            content=content,
            category_id=category_id,
            author_id=current_user.id,
            created_at=datetime.utcnow(),  # Fix: Proper datetime
            updated_at=datetime.utcnow(),  # Fix: Proper datetime
            status='published',
            views=0,
            media_filename=media_filename  # From upload or None
        )
        db.session.add(post)
        db.session.commit()

        flash("New post added successfully!", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/new_post.html', categories=categories)  # Pass the actual list

# ===============================
# Edit Category (Dual: Edit with ID, Add without)
# ===============================
@admin_bp.route('/category/edit/', methods=['POST'])  # For create (no ID, POST only)
@admin_bp.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])  # For edit
@admin_required
def edit_category(category_id=None):  # Optional param
    if category_id:  # Editing existing
        category = Category.query.get_or_404(category_id)
        is_edit = True
    else:  # Adding new (no ID)
        category = None
        is_edit = False
    
    if request.method == 'POST':
        new_name = request.form.get('name', '').strip()
        if not new_name:
            flash('Category name required', 'error')
            return redirect(url_for('admin.new_post'))  # Redirect to new_post for modal context
        
        if is_edit:
            # Check duplicate excluding self
            if Category.query.filter(Category.name == new_name, Category.id != category_id).first():
                flash('Category name already exists.', 'error')
                return redirect(url_for('admin.new_post'))
            category.name = new_name
            db.session.commit()
            flash('Category updated successfully!', 'success')
        else:
            # Create new
            if Category.query.filter_by(name=new_name).first():
                flash('Category name already exists.', 'error')
                return redirect(url_for('admin.new_post'))
            new_category = Category(name=new_name)
            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully!', 'success')
        
        return redirect(url_for('admin.new_post'))  # Back to new_post to see updated dropdown
    
    # For GET requests (edit only)
    if category_id and request.method == 'GET':
        return render_template("admin/edit_category.html", category=category)
    
    # If GET to /category/edit/ (no ID), redirect
    return redirect(url_for('admin.new_post'))

# ===============================
# Add Category (Deprecated: Keep if used elsewhere)
# ===============================
@admin_bp.route('/add_category', methods=['POST'])
@admin_required
def add_category():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('admin.dashboard'))
    if Category.query.filter_by(name=name).first():
        flash('Category with this name already exists.', 'error')
        return redirect(url_for('admin.dashboard'))

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    flash('Category added successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

# ===============================
# Delete Post
# ===============================
@admin_bp.route('/post/delete/<int:post_id>', methods=['POST'])
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

# ===============================
# Delete User
# ===============================
@admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('admin.dashboard'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

# ===============================
# Delete Category
# ===============================
@admin_bp.route('/category/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.posts:
        flash('Cannot delete category with posts! Remove or reassign posts first.', 'error')
        return redirect(url_for('admin.dashboard'))
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

# ===============================
# Publish / Unpublish Posts
# ===============================
@admin_bp.route('/publish_post/<int:post_id>', methods=['POST'])
@admin_required
def publish_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = 'published'
    db.session.commit()
    flash('Post published successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/unpublish_post/<int:post_id>', methods=['POST'])
@admin_required
def unpublish_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = 'draft'
    db.session.commit()
    flash('Post unpublished!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/publish_all', methods=['POST'])
@admin_required
def publish_all():
    drafts = Post.query.filter_by(status='draft').all()
    for post in drafts:
        post.status = 'published'
    db.session.commit()
    flash(f'Published {len(drafts)} posts!', 'success')
    return redirect(url_for('admin.dashboard'))