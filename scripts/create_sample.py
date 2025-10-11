from app import create_app, db
from app.models import User, Category, Post
app = create_app()
with app.app_context():
    if not Category.query.first():
        cats = ['Politics','Religion','Tech','Entertainment','Music','Security','Health','Naija Gist']
        for c in cats:
            Category(name=c, slug=c.lower().replace(' ','-')).save = None
    if not User.query.filter_by(username='sampleuser').first():
        u = User(username='sampleuser', email='user@example.com')
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()
    print('Sample setup done (you may need to run migrations).')
