import os
import string
import random
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, jsonify, abort, session, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import hashlib
import json

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
    """Main URL model with all features"""
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_url': self.original_url,
            'short_code': self.short_code,
            'custom_code': self.custom_code,
            'clicks': self.clicks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'title': self.title,
            'meta_description': self.meta_description
        }

class ClickLog(db.Model):
    """Analytics tracking model"""
    __tablename__ = 'click_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('urls.id', ondelete='CASCADE'), nullable=False, index=True)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    referer = db.Column(db.String(1000), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    
    url = db.relationship('URL', backref=db.backref('logs', lazy='dynamic'))

class SiteStats(db.Model):
    """Global site statistics"""
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
    # Initialize site stats if not exists
    if SiteStats.query.first() is None:
        stats = SiteStats()
        db.session.add(stats)
        db.session.commit()

# ============================================
# HELPER FUNCTIONS
# ============================================
def generate_short_code(length=6):
    """Generate unique short code"""
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not URL.query.filter_by(short_code=code).first():
            return code

def is_valid_url(url):
    """Validate URL format"""
    url_pattern = re.compile(
        r'^(https?://)'
        r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})'
        r'(:\d+)?'
        r'(/.*)?$'
    )
    return bool(url_pattern.match(url))

def extract_domain(url):
    """Extract domain from URL for smart suggestions"""
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace('www.', '').split('.')[0]
    except:
        return None

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or '127.0.0.1'

def detect_device(user_agent):
    """Detect device type from user agent"""
    ua = user_agent.lower() if user_agent else ''
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua or 'ipod' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'

def detect_browser(user_agent):
    """Detect browser from user agent"""
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
    """Detect OS from user agent"""
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

def update_site_stats(link_added=False):
    """Update global site statistics"""
    stats = SiteStats.query.first()
    if stats:
        if link_added:
            stats.total_links += 1
        stats.total_clicks = URL.query.with_entities(db.func.sum(URL.clicks)).scalar() or 0
        stats.updated_at = datetime.utcnow()
        db.session.commit()

# ============================================
# RATE LIMITING
# ============================================
rate_limit_store = {}

def check_rate_limit(ip, limit=50, window=3600):
    """Check if IP has exceeded rate limit"""
    now = datetime.utcnow().timestamp()
    if ip not in rate_limit_store:
        rate_limit_store[ip] = []
    
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < window]
    
    if len(rate_limit_store[ip]) >= limit:
        return False
    
    rate_limit_store[ip].append(now)
    return True

# ============================================
# CACHE HELPERS
# ============================================
cache_store = {}

def cache_get(key):
    """Get from cache"""
    if key in cache_store:
        data, timestamp = cache_store[key]
        if datetime.utcnow().timestamp() - timestamp < 300:  # 5 minutes
            return data
        del cache_store[key]
    return None

def cache_set(key, value):
    """Set cache"""
    cache_store[key] = (value, datetime.utcnow().timestamp())

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Main dashboard with SEO optimization"""
    # Get site stats for SEO
    stats = SiteStats.query.first()
    total_links = stats.total_links if stats else 0
    
    # Meta data for SEO
    meta_data = {
        'title': 'wafyurl - Premium URL Shortener | Shorten Links with Neon Precision',
        'description': 'Shorten your long URLs with wafyurl. Lightning fast, with real-time analytics, QR codes, and password protection. The ultimate link management tool.',
        'keywords': 'url shortener, link management, QR code generator, link analytics, free url shortener',
        'og_title': 'wafyurl - Premium URL Shortener',
        'og_description': 'Transform long URLs into short, beautiful links. Track clicks, generate QR codes, and manage your links with ease.',
        'og_url': request.url,
        'og_image': url_for('static', filename='icons/favicon.png', _external=True),
        'twitter_card': 'summary_large_image',
        'twitter_site': '@wafyurl',
        'canonical': request.url
    }
    
    return render_template('index.html', 
                         meta=meta_data, 
                         total_links=total_links)

@app.route('/shorten', methods=['POST'])
def shorten():
    """Create short URL with all features"""
    ip = get_client_ip()
    
    # Rate limiting
    if not check_rate_limit(ip):
        return jsonify({'error': 'Too many requests. Please wait a moment.'}), 429
    
    # Get data
    data = request.get_json() if request.is_json else request.form
    long_url = data.get('url', '').strip()
    custom_code = data.get('custom_code', '').strip()
    expires_in = data.get('expires_in', 'never')
    password = data.get('password', '').strip()
    
    # Validation
    if not long_url:
        return jsonify({'error': 'Please enter a URL'}), 400
    
    # Auto-prefix URL
    if not (long_url.startswith('http://') or long_url.startswith('https://')):
        long_url = 'https://' + long_url
    
    # Validate URL
    if not is_valid_url(long_url):
        return jsonify({'error': 'Invalid URL format. Please check and try again.'}), 400
    
    # Check for existing URL
    existing = URL.query.filter_by(original_url=long_url, is_active=True).first()
    if existing:
        short_url = f"{request.host_url}{existing.short_code}"
        return jsonify({
            'success': True,
            'short_url': short_url,
            'short_code': existing.short_code,
            'is_new': False,
            'clicks': existing.clicks,
            'created_at': existing.created_at.isoformat(),
            'title': existing.title
        })
    
    # Handle custom code
    if custom_code:
        if not re.match(r'^[a-zA-Z0-9_-]+$', custom_code):
            return jsonify({'error': 'Custom code can only contain letters, numbers, underscores, and hyphens'}), 400
        
        if len(custom_code) < 3 or len(custom_code) > 20:
            return jsonify({'error': 'Custom code must be between 3 and 20 characters'}), 400
        
        if URL.query.filter_by(short_code=custom_code).first() or URL.query.filter_by(custom_code=custom_code).first():
            return jsonify({'error': 'This custom code is already taken. Please choose another.'}), 400
        
        short_code = custom_code
        is_custom = True
    else:
        short_code = generate_short_code()
        is_custom = False
    
    # Calculate expiry
    expires_at = None
    if expires_in == '1h':
        expires_at = datetime.utcnow() + timedelta(hours=1)
    elif expires_in == '24h':
        expires_at = datetime.utcnow() + timedelta(hours=24)
    elif expires_in == '7d':
        expires_at = datetime.utcnow() + timedelta(days=7)
    elif expires_in == '30d':
        expires_at = datetime.utcnow() + timedelta(days=30)
    
    # Hash password if provided
    password_hash = None
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Get website title
    title = extract_domain(long_url)
    meta_description = f"Shortened link to {title} - powered by wafyurl"
    
    # Create new entry
    new_url = URL(
        original_url=long_url,
        short_code=short_code,
        custom_code=custom_code if is_custom else None,
        expires_at=expires_at,
        password_hash=password_hash,
        created_by_ip=ip,
        title=title,
        meta_description=meta_description
    )
    
    try:
        db.session.add(new_url)
        db.session.commit()
        update_site_stats(link_added=True)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error. Please try again.'}), 500
    
    short_url = f"{request.host_url}{short_code}"
    return jsonify({
        'success': True,
        'short_url': short_url,
        'short_code': short_code,
        'is_new': True,
        'expires_at': expires_at.isoformat() if expires_at else None,
        'has_password': bool(password),
        'title': title
    })

@app.route('/<code_str>')
def redirect_to_url(code_str):
    """Handle redirection with analytics"""
    # Check if it's a stats request (code+)
    if code_str.endswith('+'):
        actual_code = code_str[:-1]
        url_entry = URL.query.filter_by(short_code=actual_code, is_active=True).first()
        if not url_entry:
            url_entry = URL.query.filter_by(custom_code=actual_code, is_active=True).first()
        if not url_entry:
            abort(404)
        
        # Meta for stats page
        meta_data = {
            'title': f'📊 Analytics for {url_entry.short_code} - wafyurl',
            'description': f'View analytics for {url_entry.short_code}. Total clicks: {url_entry.clicks}',
            'canonical': f"{request.host_url}{actual_code}"
        }
        return render_template('index.html', stats=url_entry, meta=meta_data)
    
    # Find the URL
    url_entry = URL.query.filter_by(short_code=code_str, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code_str, is_active=True).first()
        if not url_entry:
            abort(404)
    
    # Check expiry
    if url_entry.expires_at and url_entry.expires_at < datetime.utcnow():
        url_entry.is_active = False
        db.session.commit()
        abort(410)
    
    # Check password
    if url_entry.password_hash:
        return render_template('password.html', code=code_str)
    
    # Log click
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
    except:
        db.session.rollback()
    
    return redirect(url_entry.original_url)

@app.route('/verify-password', methods=['POST'])
def verify_password():
    """Verify password for protected links"""
    code = request.form.get('code', '')
    password = request.form.get('password', '')
    
    url_entry = URL.query.filter_by(short_code=code, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code, is_active=True).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    if not url_entry.password_hash:
        return jsonify({'error': 'This link is not password protected'}), 400
    
    if hashlib.sha256(password.encode()).hexdigest() == url_entry.password_hash:
        # Log the click after password verification
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
        except:
            db.session.rollback()
        
        return jsonify({'success': True, 'url': url_entry.original_url})
    
    return jsonify({'error': 'Incorrect password'}), 401

@app.route('/api/stats/<code>')
def get_stats(code):
    """Get analytics data for a link"""
    url_entry = URL.query.filter_by(short_code=code).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    # Get last 30 days of clicks
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_clicks = ClickLog.query.filter(
        ClickLog.url_id == url_entry.id,
        ClickLog.clicked_at >= thirty_days_ago
    ).all()
    
    # Daily data for last 30 days
    daily_data = {}
    for day in range(30):
        date = (datetime.utcnow() - timedelta(days=day)).date()
        daily_data[date.isoformat()] = 0
    
    for click in recent_clicks:
        date = click.clicked_at.date().isoformat()
        if date in daily_data:
            daily_data[date] += 1
    
    # Device breakdown
    devices = {'mobile': 0, 'desktop': 0, 'tablet': 0}
    browsers = {}
    os_stats = {}
    for click in recent_clicks:
        if click.device_type:
            devices[click.device_type] = devices.get(click.device_type, 0) + 1
        if click.browser:
            browsers[click.browser] = browsers.get(click.browser, 0) + 1
        if click.os:
            os_stats[click.os] = os_stats.get(click.os, 0) + 1
    
    # Top referrers
    referrers = {}
    for click in recent_clicks:
        if click.referer:
            try:
                from urllib.parse import urlparse
                ref = urlparse(click.referer).netloc or click.referer
                referrers[ref] = referrers.get(ref, 0) + 1
            except:
                pass
    
    return jsonify({
        'total_clicks': url_entry.clicks,
        'recent_clicks': len(recent_clicks),
        'daily_data': [{'date': k, 'clicks': v} for k, v in sorted(daily_data.items())],
        'devices': devices,
        'browsers': browsers,
        'os': os_stats,
        'top_referrers': sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10],
        'short_code': code,
        'original_url': url_entry.original_url,
        'created_at': url_entry.created_at.isoformat(),
        'expires_at': url_entry.expires_at.isoformat() if url_entry.expires_at else None,
        'title': url_entry.title
    })

@app.route('/api/link/<code>')
def get_link_info(code):
    """Get basic link information"""
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

@app.route('/sitemap.xml')
def sitemap():
    """Generate sitemap for SEO"""
    urls = URL.query.filter_by(is_active=True).all()
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Add main page
    sitemap_xml += '  <url>\n'
    sitemap_xml += f'    <loc>{request.host_url}</loc>\n'
    sitemap_xml += '    <changefreq>daily</changefreq>\n'
    sitemap_xml += '    <priority>1.0</priority>\n'
    sitemap_xml += '  </url>\n'
    
    # Add all short links
    for url_entry in urls:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{request.host_url}{url_entry.short_code}</loc>\n'
        sitemap_xml += f'    <lastmod>{url_entry.created_at.date().isoformat()}</lastmod>\n'
        sitemap_xml += '    <changefreq>monthly</changefreq>\n'
        sitemap_xml += '    <priority>0.5</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    return sitemap_xml, 200, {'Content-Type': 'application/xml'}

@app.route('/robots.txt')
def robots():
    """Robots.txt for SEO"""
    robots_txt = f"""User-agent: *
Allow: /
Disallow: /api/
Sitemap: {request.host_url}sitemap.xml
"""
    return robots_txt, 200, {'Content-Type': 'text/plain'}

@app.route('/.well-known/security.txt')
def security():
    """Security policy for the site"""
    security_txt = f"""Contact: mailto:afee@example.com
Expires: {datetime.utcnow().replace(year=datetime.utcnow().year + 1).date().isoformat()}
Preferred-Languages: en, bn
"""
    return security_txt, 200, {'Content-Type': 'text/plain'}

# ============================================
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(410)
def gone(e):
    return render_template('index.html', error='This link has expired.'), 410

@app.errorhandler(429)
def rate_limit(e):
    return jsonify({'error': 'Too many requests. Please wait.'}), 429

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error='Something went wrong. Please try again later.'), 500

# ============================================
# CONTEXT PROCESSOR
# ============================================
@app.context_processor
def inject_globals():
    """Inject global variables for templates"""
    stats = SiteStats.query.first()
    return {
        'site_name': 'wafyurl',
        'site_description': 'Premium URL Shortener with neon precision',
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