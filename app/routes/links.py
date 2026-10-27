import hashlib
import hmac
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import URL, ClickLog, SiteStats
from app.services.helpers import (generate_short_code, is_valid_url, get_client_ip, detect_device, detect_browser, detect_os, extract_referer_domain, update_site_stats)
from app.security.rate_limit import check_rate_limit

bp = Blueprint("links", __name__)

def process_shorten_payload(data, ip):
    raw_url = data.get('url')
    if not isinstance(raw_url, str):
        return {'error': 'Please provide a URL as text.'}, 400
    long_url = raw_url.strip()
    raw_custom_code = data.get('custom_code', '')
    raw_password = data.get('password', '')
    custom_code = raw_custom_code.strip() if isinstance(raw_custom_code, str) else ''
    password = raw_password.strip() if isinstance(raw_password, str) else ''
    expires_in = data.get('expires_in', 'never')
    if not isinstance(expires_in, str):
        return {'error': 'Unsupported expiration option.'}, 400

    if not long_url:
        return {'error': 'Please enter a URL'}, 400
    if not long_url.lower().startswith(('http://', 'https://')):
        long_url = 'https://' + long_url
    if not is_valid_url(long_url):
        return {'error': 'Enter a valid HTTP or HTTPS URL.'}, 400
    if len(password) > 128:
        return {'error': 'Password must be 128 characters or fewer.'}, 400

    if custom_code:
        if not re.fullmatch(r'[a-zA-Z0-9_-]{3,20}', custom_code):
            return {'error': 'Custom alias must be 3–20 letters, numbers, underscores or hyphens.'}, 400
        reserved = {'api', 'robots.txt', 'sitemap.xml', 'favicon.ico', 'icon.webp', 'og-image.webp', 'shorten', 'verify-password', 'bulk-shortener', 'url-shortener', 'bulk-url-shortener', 'custom-url-shortener', 'qr-code-generator', 'link-analytics', 'password-protected-links', 'link-expiration', 'guides', 'privacy', 'terms', 'faq', 'features'}
        if custom_code.lower() in reserved:
            return {'error': 'That alias is reserved. Please choose another.'}, 400
        if URL.query.filter_by(short_code=custom_code).first() or URL.query.filter_by(custom_code=custom_code).first():
            return {'error': 'Custom alias already taken.'}, 409

    # Reuse a destination only for a plain request; customization should create a new link.
    if not custom_code and not password and expires_in == 'never':
        existing = URL.query.filter_by(original_url=long_url, is_active=True).first()
        if existing and not existing.password_hash and not existing.expires_at:
            return {
                'success': True,
                'short_url': f"{current_app.config['PUBLIC_BASE_URL']}/{existing.short_code}",
                'short_code': existing.short_code,
                'is_new': False,
                'clicks': existing.clicks,
                'has_password': False,
                'expires_at': None,
            }, 200

    if expires_in not in {'never', '1h', '24h', '7d', '30d', 'custom'}:
        return {'error': 'Unsupported expiration option.'}, 400
    expires_at = None
    if expires_in == 'custom':
        raw_expiry = data.get('expires_at')
        if not isinstance(raw_expiry, str) or not raw_expiry.strip():
            return {'error': 'Choose a valid expiration date and time.'}, 400
        try:
            parsed_expiry = datetime.fromisoformat(raw_expiry.strip().replace('Z', '+00:00'))
            if parsed_expiry.tzinfo is None:
                return {'error': 'Expiration must include a timezone.'}, 400
            expires_at = parsed_expiry.astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            return {'error': 'Choose a valid expiration date and time.'}, 400
        if expires_at <= datetime.utcnow():
            return {'error': 'Expiration date and time must be in the future.'}, 400
    elif expires_in == '1h':
        expires_at = datetime.utcnow() + timedelta(hours=1)
    elif expires_in == '24h':
        expires_at = datetime.utcnow() + timedelta(hours=24)
    elif expires_in == '7d':
        expires_at = datetime.utcnow() + timedelta(days=7)
    elif expires_in == '30d':
        expires_at = datetime.utcnow() + timedelta(days=30)

    short_code = custom_code or generate_short_code()
    new_url = URL(
        original_url=long_url,
        short_code=short_code,
        custom_code=custom_code or None,
        expires_at=expires_at,
        password_hash=generate_password_hash(password) if password else None,
        created_by_ip=ip,
        title=urlparse(long_url).netloc[:200],
    )
    try:
        db.session.add(new_url)
        db.session.commit()
        update_site_stats()
    except IntegrityError:
        db.session.rollback()
        current_app.logger.info('Short-code uniqueness conflict during creation')
        if custom_code:
            return {'error': 'That short alias is already in use. Please choose another.'}, 409
        return {'error': 'A short-code collision occurred. Please retry.'}, 503
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Could not save a shortened URL')
        return {'error': 'Could not create the link. Please try again.'}, 500

    return {
        'success': True,
        'short_url': f"{current_app.config['PUBLIC_BASE_URL']}/{short_code}",
        'short_code': short_code,
        'is_new': True,
        'expires_at': expires_at.isoformat() if expires_at else None,
        'has_password': bool(password),
    }, 200

@bp.route('/shorten', methods=['POST'])
def shorten():
    ip = get_client_ip()
    if not check_rate_limit(ip, limit=50):
        return jsonify({'error': 'Too many requests. Please wait before creating more links.'}), 429
    data = request.get_json(silent=True) if request.is_json else request.form
    if not data or not hasattr(data, 'get'):
        return jsonify({'error': 'A URL is required.'}), 400
    result, status = process_shorten_payload(data, ip)
    return jsonify(result), status
@bp.route('/bulk-shortener', methods=['POST'])
def bulk_shorten():
    ip = get_client_ip()
    if not check_rate_limit(f'batch:{ip}', limit=5, window=3600):
        return jsonify({'error': 'Bulk rate limit reached. Please try again later.'}), 429
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': 'Request body must be a JSON object.'}), 400
    urls = data.get('urls')
    if not isinstance(urls, list) or not urls:
        return jsonify({'error': 'Provide a non-empty list of URLs.'}), 400
    if len(urls) > 50:
        return jsonify({'error': 'A batch can contain at most 50 URLs.'}), 400
    results = []
    for value in urls:
        result, status = process_shorten_payload({'url': value}, ip)
        results.append({'original': str(value)[:2000], 'success': bool(result.get('success')), 'short_url': result.get('short_url'), 'error': result.get('error')})
    return jsonify({'results': results, 'total': len(results), 'succeeded': sum(item['success'] for item in results), 'failed': sum(not item['success'] for item in results)})
@bp.route('/verify-password', methods=['POST'])
def verify_password():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': 'Request body must be a JSON object.'}), 400
    raw_code = data.get('code')
    raw_password = data.get('password')
    code = raw_code.strip() if isinstance(raw_code, str) else ''
    password = raw_password.strip() if isinstance(raw_password, str) else ''
    
    if not code or not password:
        return jsonify({'error': 'Code and password are required'}), 400
    if not check_rate_limit(f'password:{get_client_ip()}:{code}', limit=10, window=900):
        return jsonify({'error': 'Too many password attempts. Please wait and try again.'}), 429
    
    url_entry = URL.query.filter_by(short_code=code, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code, is_active=True).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    if url_entry.expires_at and url_entry.expires_at < datetime.utcnow():
        return jsonify({'error': 'Link has expired.'}), 410
    if not url_entry.password_hash:
        return jsonify({'error': 'This link is not password protected'}), 400
    
    stored_hash = url_entry.password_hash or ''
    if stored_hash.startswith(('pbkdf2:', 'scrypt:')):
        password_matches = check_password_hash(stored_hash, password)
    else:
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        password_matches = hmac.compare_digest(legacy_hash, stored_hash)
    if password_matches:
        try:
            if not stored_hash.startswith(('pbkdf2:', 'scrypt:')):
                url_entry.password_hash = generate_password_hash(password)
            click = ClickLog(
                url_id=url_entry.id,
                ip_address=None,
                user_agent=request.headers.get('User-Agent', ''),
                referer=None,
                referer_domain=extract_referer_domain(request.headers.get('Referer', '')),
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
@bp.route('/<code_str>')
def redirect_to_url(code_str):
    if code_str.endswith('+'):
        actual_code = code_str[:-1]
        url_entry = URL.query.filter_by(short_code=actual_code, is_active=True).first()
        if not url_entry:
            url_entry = URL.query.filter_by(custom_code=actual_code, is_active=True).first()
        if not url_entry:
            abort(404)
        if url_entry.password_hash:
            abort(403)
        if url_entry.expires_at and url_entry.expires_at < datetime.utcnow():
            abort(410)
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
        referer = request.headers.get('Referer', '')
        referer_domain = extract_referer_domain(referer)
        
        click = ClickLog(
            url_id=url_entry.id,
            ip_address=None,
            user_agent=request.headers.get('User-Agent', ''),
            referer=None,
            referer_domain=referer_domain,
            country='Unknown',
            city='Unknown',
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

