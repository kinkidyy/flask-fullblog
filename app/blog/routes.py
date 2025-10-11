from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from ..models import Post, Category, Comment
from .. import db
from flask_login import login_required, current_user
import os

blog_bp = Blueprint('blog', __name__)

ALLOWED = set(['png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'ogg', 'mp3', 'wav', 'm4a'])

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED


# ==========================
# BLOG HOMEPAGE (ALL POSTS)
# ==========================
@blog_bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    cat = request.args.get('cat')
    page = int(request.args.get('page', 1))
    per = 6

    query = Post.query.filter(Post.status == 'published')

    if q:
        query = query.filter(Post.title.ilike(f'%{q}%'))
    if cat:
        query = query.join(Category).filter(Category.name == cat)

    posts = query.order_by(Post.created_at.desc()).limit(per).offset((page-1)*per).all()
    total_posts = query.count()
    total_pages = (total_posts + per - 1) // per
    has_prev = page > 1
    has_next = page < total_pages

    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'blog/index.html',
        posts=posts,
        categories=categories,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        q=q,
        cat=cat
    )


# ==========================
# SINGLE POST VIEW
# ==========================
@blog_bp.route('/post/<slug>', methods=['GET', 'POST'])
def view_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()

    # increment view count
    post.views = (post.views or 0) + 1
    db.session.commit()

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Login required to comment', 'error')
            return redirect(url_for('auth.login'))

        content = request.form.get('content', '').strip()
        parent = request.form.get('parent')

        if not content:
            flash('Comment empty', 'error')
            return redirect(url_for('blog.view_post', slug=slug))

        cm = Comment(content=content, user=current_user, post=post)
        if parent:
            cm.parent_id = int(parent)

        db.session.add(cm)
        db.session.commit()
        flash('Comment posted', 'success')
        return redirect(url_for('blog.view_post', slug=slug))

    return render_template('blog/new_post.html', post=post)


# ==========================
# MEDIA FILES
# ==========================
@blog_bp.route('/media/<filename>')
def media(filename):
    return current_app.send_static_file(os.path.join('uploads', filename))
