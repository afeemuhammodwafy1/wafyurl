import os
import string
import random
from flask import Flask, render_template, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the Flask App
app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# This creates a file named 'wafyurl.db' in your project directory
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wafyurl.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODEL ---
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(1000), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create the database tables inside the app context
with app.app_context():
    db.create_all()

# --- HELPER FUNCTIONS ---
def generate_short_code(length=6):
    """Generates a random unique string of letters and digits."""
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        # Ensure the code doesn't already exist in the database
        if not URL.query.filter_by(short_code=code).first():
            return code

# --- ROUTES ---

@app.route('/')
def index():
    """Renders the main dashboard."""
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten():
    """Handles the form submission to create a short link."""
    # Get user input from the form
    long_url = request.form.get('url', '').strip()

    if not long_url:
        return render_template('index.html', error="Error: Please enter a URL.")

    # FIX: AUTO-PREFIX URL
    # If the user typed 'google.com', this changes it to 'https://google.com'
    if not (long_url.startswith('http://') or long_url.startswith('https://')):
        long_url = 'https://' + long_url

    # CHECK IF EXISTS: If the URL is already in our DB, don't create a new one
    existing = URL.query.filter_by(original_url=long_url).first()
    if existing:
        short_url = f"{request.host_url}{existing.short_code}"
        return render_template('index.html', short_url=short_url)

    # CREATE NEW ENTRY
    code = generate_short_code()
    new_entry = URL(original_url=long_url, short_code=code)
    
    try:
        db.session.add(new_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return render_template('index.html', error="Server Error. Please try again.")

    # Return the result to the UI
    short_url = f"{request.host_url}{code}"
    return render_template('index.html', short_url=short_url)

@app.route('/<code_str>')
def redirect_to_url(code_str):
    """Handles redirection and the analytics (+) feature."""
    
    # ANALYTICS CHECK: If URL is domain.com/abc+
    if code_str.endswith('+'):
        actual_code = code_str[:-1] # Remove the '+' from the end
        url_entry = URL.query.filter_by(short_code=actual_code).first_or_404()
        # Render the stats view instead of redirecting
        return render_template('index.html', stats=url_entry)

    # STANDARD REDIRECTION: If URL is domain.com/abc
    url_entry = URL.query.filter_by(short_code=code_str).first_or_404()
    
    # Increment Click Counter
    url_entry.clicks += 1
    db.session.commit()
    
    # Redirect to the original long URL
    return redirect(url_entry.original_url)

# --- START THE SERVER ---
if __name__ == '__main__':
    # host='0.0.0.0' is required for Render deployment
    app.run(host='0.0.0.0', port=5000, debug=True)