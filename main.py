from app import create_app
from flask import redirect, url_for
from app.models import db

# Create the app
app = create_app()

# Homepage route
@app.route('/')
def home():
    # For now, don't fetch from MongoDB — just verify the template works
    return redirect(url_for('blog.index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
