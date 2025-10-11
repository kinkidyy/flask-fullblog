from app import create_app, db
from app.models import Post
from datetime import datetime

app = create_app()

with app.app_context():
    posts = Post.query.all()
    fixed_count = 0

    for post in posts:
        if isinstance(post.created_at, str):
            try:
                post.created_at = datetime.fromisoformat(post.created_at)
                fixed_count += 1
            except Exception as e:
                print(f"Skipping post {post.id}: {e}")

    db.session.commit()
    print(f"Updated {fixed_count} posts' created_at!")
