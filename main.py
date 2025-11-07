from flask import Flask, render_template
from app import create_app
from app.models import db

# Create the app
app = create_app()

# Homepage route
@app.route('/')
def home():
    # For now, don't fetch from MongoDB — just verify the template works
    return render_template('blog/index.html')

if __name__ == '__main__':
    app.run(debug=True)
