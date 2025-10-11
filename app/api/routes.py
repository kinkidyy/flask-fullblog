from flask import Blueprint, jsonify, request, url_for
from ..models import Post, User
from .. import db
api_bp = Blueprint('api', __name__)

@api_bp.route('/posts', methods=['GET'])
def posts():
    posts = Post.query.order_by(Post.created_at.desc()).limit(20).all()
    out = []
    for p in posts:
        out.append({
            'id': p.id,
            'title': p.title,
            'slug': p.slug,
            'excerpt': p.content[:200],
            'url': url_for('blog.view_post', slug=p.slug, _external=True)
        })
    return jsonify(out)
