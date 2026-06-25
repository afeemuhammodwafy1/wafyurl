import os
import string
import random
from flask import Flask, render_template, request, redirect, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database Configuration
# Using SQLite for simplicity; Render supports this but data clears on redeploy 
# unless using a persistent disk or external DB like PostgreSQL.
db = SQLAlchemy(app)

# Database Model
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create database tables
with app.app_context():
    db.create_all()

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not URL.query.filter_by(short_code=code).first():
            return code

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    long_url = data.get('url')

    if not long_url or not long_url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid URL. Must start with http:// or https://'}), 400

    # Check if URL already exists to save space
    existing = URL.query.filter_by(original_url=long_url).first()
    if existing:
        return jsonify({'short_url': f"{request.host_url}{existing.short_code}", 'short_code': existing.short_code})

    short_code = generate_short_code()
    new_url = URL(original_url=long_url, short_code=short_code)
    db.session.add(new_url)
    db.session.commit()

    return jsonify({'short_url': f"{request.host_url}{short_code}", 'short_code': short_code})

@app.route('/<code_str>')
def redirect_to_url(code_str):
    # Analytics check: if URL ends with '+', show stats
    if code_str.endswith('+'):
        actual_code = code_str[:-1]
        url_entry = URL.query.filter_by(short_code=actual_code).first_or_404()
        return render_template('index.html', stats=url_entry, base_url=request.host_url)

    # Standard redirection
    url_entry = URL.query.filter_by(short_code=code_str).first_or_404()
    url_entry.clicks += 1
    db.session.commit()
    return redirect(url_entry.original_url)

if __name__ == '__main__':
    app.run(debug=True)
