from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from ..models import Post, Category, Comment, Reply, db
import os
from datetime import datetime

blog_bp = Blueprint("blog", __name__)

# ==========================
# HELPER TABLES FOR LIKES
# ==========================
from sqlalchemy import Table, Column, Integer, ForeignKey

# Association tables for likes (many-to-many)
from .. import db

post_likes = db.Table(
    "post_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id")),
)

comment_likes = db.Table(
    "comment_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("comment_id", db.Integer, db.ForeignKey("comment.id")),
)

ALLOWED = {"png", "jpg", "jpeg", "gif", "mp4", "webm", "ogg", "mp3", "wav", "m4a"}


def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED


# ==========================
# BLOG HOMEPAGE (ALL POSTS)
# ==========================
@blog_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat")
    page = int(request.args.get("page", 1))
    per = 6

    query = Post.query.filter(Post.status == "published")

    if q:
        query = query.filter(Post.title.ilike(f"%{q}%"))
    if cat:
        query = query.join(Category).filter(Category.name == cat)

    posts = query.order_by(Post.created_at.desc()).limit(per).offset((page - 1) * per).all()
    total_posts = query.count()
    total_pages = (total_posts + per - 1) // per
    has_prev = page > 1
    has_next = page < total_pages

    categories = Category.query.order_by(Category.name).all()

    return render_template(
        "blog/index.html",
        posts=posts,
        categories=categories,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        q=q,
        cat=cat,
    )


# ==========================
# SINGLE POST VIEW + COMMENTS
# ==========================
@blog_bp.route("/post/<slug>", methods=["GET", "POST"])
def view_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()

    # Increment view count
    post.views = (post.views or 0) + 1
    db.session.commit()

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("You must be logged in to comment.", "warning")
            return redirect(url_for("auth.login"))

        content = request.form.get("content", "").strip()
        if content:
            comment = Comment(content=content, user_id=current_user.id, post_id=post.id, created_at=datetime.utcnow())
            db.session.add(comment)
            db.session.commit()
            flash("Comment added successfully!", "success")

        return redirect(url_for("blog.view_post", slug=slug))

    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.desc()).all()
    return render_template("blog/new_post.html", post=post, comments=comments)


# ==========================
# ADD REPLY TO COMMENT
# ==========================
@blog_bp.route("/reply/<int:comment_id>", methods=["POST"])
@login_required
def add_reply(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    content = request.form.get("reply_content", "").strip()

    if content:
        reply = Reply(content=content, user_id=current_user.id, comment_id=comment.id, created_at=datetime.utcnow())
        db.session.add(reply)
        db.session.commit()
        flash("Reply added!", "success")

    return redirect(url_for("blog.view_post", slug=comment.post.slug))


# ==========================
# LIKE A POST (once per user)
# ==========================
@blog_bp.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if user has already liked this post
    result = db.session.execute(
        post_likes.select().where(
            (post_likes.c.user_id == current_user.id) &
            (post_likes.c.post_id == post_id)
        )
    ).fetchone()

    if result:
        flash("You already liked this post!", "info")
    else:
        db.session.execute(post_likes.insert().values(user_id=current_user.id, post_id=post_id))
        post.likes = (post.likes or 0) + 1
        db.session.commit()
        flash("You liked this post!", "success")

    return redirect(url_for("blog.view_post", slug=post.slug))


# ==========================
# LIKE A COMMENT (once per user)
# ==========================
@blog_bp.route("/like_comment/<int:comment_id>", methods=["POST"])
@login_required
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # Check if user has already liked this comment
    result = db.session.execute(
        comment_likes.select().where(
            (comment_likes.c.user_id == current_user.id) &
            (comment_likes.c.comment_id == comment_id)
        )
    ).fetchone()

    if result:
        flash("You already liked this comment!", "info")
    else:
        db.session.execute(comment_likes.insert().values(user_id=current_user.id, comment_id=comment_id))
        comment.likes = (comment.likes or 0) + 1
        db.session.commit()
        flash("You liked this comment!", "success")

    return redirect(url_for("blog.view_post", slug=comment.post.slug))


# ==========================
# EDIT COMMENT
# ==========================
@blog_bp.route("/edit_comment/<int:comment_id>", methods=["POST"])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id:
        flash("You are not authorized to edit this comment.", "danger")
        return redirect(url_for("blog.view_post", slug=comment.post.slug))

    content = request.form.get("content", "").strip()
    if content:
        comment.content = content
        db.session.commit()
        flash("Comment updated successfully!", "success")
    else:
        flash("Comment cannot be empty.", "warning")

    return redirect(url_for("blog.view_post", slug=comment.post.slug))


# ==========================
# MEDIA FILES
# ==========================
@blog_bp.route("/media/<filename>")
def media(filename):
    return current_app.send_static_file(os.path.join("uploads", filename))
