import os
import string
import random
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, jsonify, abort, session, url_for, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import hashlib
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter

# ============================================
# APP INITIALIZATION
# ============================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ============================================
# DATABASE CONFIGURATION
# ============================================
database_url = os.environ.get('DATABASE_URL', 'sqlite:///wafyurl.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

db = SQLAlchemy(app)

# ============================================
# DATABASE MODELS
# ============================================
class URL(db.Model):
    __tablename__ = 'urls'
    
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2000), nullable=False)
    short_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    custom_code = db.Column(db.String(20), unique=True, nullable=True)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_by_ip = db.Column(db.String(45), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.String(300), nullable=True)

class ClickLog(db.Model):
    __tablename__ = 'click_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('urls.id', ondelete='CASCADE'), nullable=False, index=True)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    referer = db.Column(db.String(1000), nullable=True)
    referer_domain = db.Column(db.String(200), nullable=True, index=True)
    country = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    
    url = db.relationship('URL', backref=db.backref('logs', lazy='dynamic'))

class SiteStats(db.Model):
    __tablename__ = 'site_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    total_links = db.Column(db.Integer, default=0)
    total_clicks = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================
# CREATE TABLES
# ============================================
with app.app_context():
    db.create_all()
    if SiteStats.query.first() is None:
        stats = SiteStats()
        db.session.add(stats)
        db.session.commit()

# ============================================
# HELPER FUNCTIONS
# ============================================
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not URL.query.filter_by(short_code=code).first():
            return code

def is_valid_url(url):
    url_pattern = re.compile(
        r'^(https?://)'
        r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})'
        r'(:\d+)?'
        r'(/.*)?$'
    )
    return bool(url_pattern.match(url))

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or '127.0.0.1'

def detect_device(user_agent):
    ua = user_agent.lower() if user_agent else ''
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua or 'ipod' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'

def detect_browser(user_agent):
    ua = user_agent.lower() if user_agent else ''
    if 'chrome' in ua and 'edg' not in ua:
        return 'Chrome'
    elif 'firefox' in ua:
        return 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        return 'Safari'
    elif 'edg' in ua:
        return 'Edge'
    elif 'opera' in ua:
        return 'Opera'
    return 'Other'

def detect_os(user_agent):
    ua = user_agent.lower() if user_agent else ''
    if 'windows' in ua:
        return 'Windows'
    elif 'mac' in ua:
        return 'macOS'
    elif 'linux' in ua:
        return 'Linux'
    elif 'android' in ua:
        return 'Android'
    elif 'ios' in ua or 'iphone' in ua or 'ipad' in ua:
        return 'iOS'
    return 'Other'

def extract_referer_domain(referer):
    if not referer:
        return 'Direct'
    try:
        parsed = urlparse(referer)
        domain = parsed.netloc or parsed.path
        domain = domain.replace('www.', '')
        if not domain:
            return 'Direct'
        return domain
    except Exception:
        return 'Direct'

def update_site_stats(link_added=False):
    stats = SiteStats.query.first()
    if stats:
        if link_added:
            stats.total_links += 1
        stats.total_clicks = URL.query.with_entities(db.func.sum(URL.clicks)).scalar() or 0
        stats.updated_at = datetime.utcnow()
        db.session.commit()

def get_geo_location(ip):
    if ip in ['127.0.0.1', 'localhost']:
        return {'country': 'Local', 'city': 'Local'}
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=3)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country', 'Unknown'),
                'city': data.get('city', 'Unknown')
            }
    except Exception:
        pass
    return {'country': 'Unknown', 'city': 'Unknown'}

# ============================================
# RATE LIMITING
# ============================================
rate_limit_store = {}

def check_rate_limit(ip, limit=50, window=3600):
    now = datetime.utcnow().timestamp()
    if ip not in rate_limit_store:
        rate_limit_store[ip] = []
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < window]
    if len(rate_limit_store[ip]) >= limit:
        return False
    rate_limit_store[ip].append(now)
    return True

# ============================================
# STATIC ICON, FAVICON & OG-IMAGE ROUTES
# ============================================
@app.route('/icon.webp')
@app.route('/favicon.ico')
def serve_icon():
    return send_from_directory(app.root_path, 'icon.webp', mimetype='image/webp')

@app.route('/og-image.webp')
def serve_og_image():
    return send_from_directory(app.root_path, 'og-image.webp', mimetype='image/webp')

# ============================================
# SEO: ROBOTS.TXT & SITEMAP.XML
# ============================================
@app.route('/robots.txt')
def robots():
    robots_content = "User-agent: *\nAllow: /\n\nSitemap: https://url.amwafy.xyz/sitemap.xml\n"
    return Response(robots_content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    urls = URL.query.filter_by(is_active=True).all()
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += '  <url>\n'
    sitemap_xml += '    <loc>https://url.amwafy.xyz/</loc>\n'
    sitemap_xml += '    <changefreq>daily</changefreq>\n'
    sitemap_xml += '    <priority>1.0</priority>\n'
    sitemap_xml += '  </url>\n'
    for url_entry in urls:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>https://url.amwafy.xyz/{url_entry.short_code}</loc>\n'
        sitemap_xml += f'    <lastmod>{url_entry.created_at.date().isoformat()}</lastmod>\n'
        sitemap_xml += '    <changefreq>monthly</changefreq>\n'
        sitemap_xml += '    <priority>0.5</priority>\n'
        sitemap_xml += '  </url>\n'
    sitemap_xml += '</urlset>'
    return Response(sitemap_xml, mimetype='application/xml')

# ============================================
# CORE APP ROUTES
# ============================================
@app.route('/')
def index():
    stats = SiteStats.query.first()
    total_links = stats.total_links if stats else 0
    return render_template('index.html', total_links=total_links)

@app.route('/shorten', methods=['POST'])
def shorten():
    ip = get_client_ip()
    
    if not check_rate_limit(ip):
        return jsonify({'error': 'Too many requests. Please wait.'}), 429
    
    data = request.get_json() if request.is_json else request.form
    long_url = data.get('url', '').strip()
    custom_code = data.get('custom_code', '').strip()
    expires_in = data.get('expires_in', 'never')
    password = data.get('password', '').strip()
    
    if not long_url:
        return jsonify({'error': 'Please enter a URL'}), 400
    
    if not (long_url.startswith('http://') or long_url.startswith('https://')):
        long_url = 'https://' + long_url
    
    if not is_valid_url(long_url):
        return jsonify({'error': 'Invalid URL format'}), 400
    
    existing = URL.query.filter_by(original_url=long_url, is_active=True).first()
    if existing:
        short_url = f"{request.host_url}{existing.short_code}"
        return jsonify({
            'success': True,
            'short_url': short_url,
            'short_code': existing.short_code,
            'is_new': False,
            'clicks': existing.clicks
        })
    
    if custom_code:
        if not re.match(r'^[a-zA-Z0-9_-]+$', custom_code):
            return jsonify({'error': 'Custom code: letters, numbers, underscores, hyphens only'}), 400
        if len(custom_code) < 3 or len(custom_code) > 20:
            return jsonify({'error': 'Custom code must be 3-20 characters'}), 400
        if URL.query.filter_by(short_code=custom_code).first() or URL.query.filter_by(custom_code=custom_code).first():
            return jsonify({'error': 'Custom code already taken'}), 400
        short_code = custom_code
    else:
        short_code = generate_short_code()
    
    expires_at = None
    if expires_in == '1h':
        expires_at = datetime.utcnow() + timedelta(hours=1)
    elif expires_in == '24h':
        expires_at = datetime.utcnow() + timedelta(hours=24)
    elif expires_in == '7d':
        expires_at = datetime.utcnow() + timedelta(days=7)
    elif expires_in == '30d':
        expires_at = datetime.utcnow() + timedelta(days=30)
    
    password_hash = None
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    new_url = URL(
        original_url=long_url,
        short_code=short_code,
        custom_code=custom_code if custom_code else None,
        expires_at=expires_at,
        password_hash=password_hash,
        created_by_ip=ip,
        title=urlparse(long_url).netloc
    )
    
    try:
        db.session.add(new_url)
        db.session.commit()
        update_site_stats(link_added=True)
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Server error. Please try again.'}), 500
    
    short_url = f"{request.host_url}{short_code}"
    return jsonify({
        'success': True,
        'short_url': short_url,
        'short_code': short_code,
        'is_new': True,
        'expires_at': expires_at.isoformat() if expires_at else None,
        'has_password': bool(password)
    })

@app.route('/verify-password', methods=['POST'])
def verify_password():
    data = request.get_json()
    code = data.get('code', '').strip()
    password = data.get('password', '').strip()
    
    if not code or not password:
        return jsonify({'error': 'Code and password are required'}), 400
    
    url_entry = URL.query.filter_by(short_code=code, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code, is_active=True).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    if not url_entry.password_hash:
        return jsonify({'error': 'This link is not password protected'}), 400
    
    if hashlib.sha256(password.encode()).hexdigest() == url_entry.password_hash:
        try:
            click = ClickLog(
                url_id=url_entry.id,
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                referer=request.headers.get('Referer', ''),
                device_type=detect_device(request.headers.get('User-Agent', '')),
                browser=detect_browser(request.headers.get('User-Agent', '')),
                os=detect_os(request.headers.get('User-Agent', ''))
            )
            db.session.add(click)
            url_entry.clicks += 1
            db.session.commit()
            update_site_stats()
        except Exception:
            db.session.rollback()
        
        return jsonify({
            'success': True,
            'url': url_entry.original_url
        })
    
    return jsonify({'error': 'Incorrect password'}), 401

@app.route('/<code_str>')
def redirect_to_url(code_str):
    if code_str.endswith('+'):
        actual_code = code_str[:-1]
        url_entry = URL.query.filter_by(short_code=actual_code, is_active=True).first()
        if not url_entry:
            url_entry = URL.query.filter_by(custom_code=actual_code, is_active=True).first()
        if not url_entry:
            abort(404)
        return render_template('index.html', stats=url_entry)
    
    url_entry = URL.query.filter_by(short_code=code_str, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code_str, is_active=True).first()
        if not url_entry:
            abort(404)
    
    if url_entry.expires_at and url_entry.expires_at < datetime.utcnow():
        url_entry.is_active = False
        db.session.commit()
        abort(410)
    
    if url_entry.password_hash:
        return render_template('password.html', code=code_str)
    
    try:
        ip = get_client_ip()
        geo = get_geo_location(ip)
        referer = request.headers.get('Referer', '')
        referer_domain = extract_referer_domain(referer)
        
        click = ClickLog(
            url_id=url_entry.id,
            ip_address=ip,
            user_agent=request.headers.get('User-Agent', ''),
            referer=referer[:1000] if referer else None,
            referer_domain=referer_domain,
            country=geo.get('country'),
            city=geo.get('city'),
            device_type=detect_device(request.headers.get('User-Agent', '')),
            browser=detect_browser(request.headers.get('User-Agent', '')),
            os=detect_os(request.headers.get('User-Agent', ''))
        )
        db.session.add(click)
        url_entry.clicks += 1
        db.session.commit()
        update_site_stats()
    except Exception:
        db.session.rollback()
    
    return redirect(url_entry.original_url)

@app.route('/api/stats/<code>')
def get_stats(code):
    url_entry = URL.query.filter_by(short_code=code).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_clicks = ClickLog.query.filter(
        ClickLog.url_id == url_entry.id,
        ClickLog.clicked_at >= thirty_days_ago
    ).all()
    
    daily_data = {}
    for day in range(30):
        date = (datetime.utcnow() - timedelta(days=day)).date()
        daily_data[date.isoformat()] = 0
    
    referer_counts = Counter()
    for click in recent_clicks:
        date = click.clicked_at.date().isoformat()
        if date in daily_data:
            daily_data[date] += 1
        if click.referer_domain:
            referer_counts[click.referer_domain] += 1
    
    devices = {'mobile': 0, 'desktop': 0, 'tablet': 0}
    for click in recent_clicks:
        if click.device_type:
            devices[click.device_type] = devices.get(click.device_type, 0) + 1
    
    return jsonify({
        'total_clicks': url_entry.clicks,
        'recent_clicks': len(recent_clicks),
        'daily_data': [{'date': k, 'clicks': v} for k, v in sorted(daily_data.items())],
        'devices': devices,
        'top_referrers': referer_counts.most_common(10),
        'short_code': code,
        'original_url': url_entry.original_url,
        'created_at': url_entry.created_at.isoformat(),
        'expires_at': url_entry.expires_at.isoformat() if url_entry.expires_at else None
    })

@app.route('/api/preview')
def get_preview():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('meta', property='og:title') or soup.find('title')
        title = title_tag.get('content', '') if title_tag and title_tag.name == 'meta' else title_tag.text if title_tag else ''
        
        desc_tag = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag.get('content', '') if desc_tag else ''
        
        image_tag = soup.find('meta', property='og:image')
        image = image_tag.get('content', '') if image_tag else ''
        
        return jsonify({
            'title': title[:150] if title else 'No title available',
            'description': desc[:300] if desc else 'No description available',
            'image': image if image else ''
        })
    except requests.RequestException:
        return jsonify({'error': 'Could not fetch preview'}), 400
    except Exception:
        return jsonify({'error': 'Error parsing page'}), 400

@app.route('/api/link/<code>')
def get_link_info(code):
    url_entry = URL.query.filter_by(short_code=code, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code, is_active=True).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    return jsonify({
        'original_url': url_entry.original_url,
        'clicks': url_entry.clicks,
        'created_at': url_entry.created_at.isoformat(),
        'expires_at': url_entry.expires_at.isoformat() if url_entry.expires_at else None,
        'has_password': bool(url_entry.password_hash)
    })

# ============================================
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(e):
    return render_template('index.html', error='Link not found.'), 404

@app.errorhandler(410)
def gone(e):
    return render_template('index.html', error='This link has expired.'), 410

@app.errorhandler(429)
def rate_limit(e):
    return jsonify({'error': 'Too many requests. Please wait.'}), 429

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error='Server error. Please try again.'), 500

# ============================================
# CONTEXT PROCESSOR
# ============================================
@app.context_processor
def inject_globals():
    stats = SiteStats.query.first()
    return {
        'site_name': 'WafyURL',
        'total_links': stats.total_links if stats else 0,
        'total_clicks': stats.total_clicks if stats else 0
    }

# ============================================
# START SERVER
# ============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)