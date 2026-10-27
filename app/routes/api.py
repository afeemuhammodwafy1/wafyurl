import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import urljoin
from flask import Blueprint, current_app, jsonify, request
from app.models import URL, ClickLog
from app.services.helpers import is_valid_url, is_public_http_url, get_client_ip
from app.security.rate_limit import check_rate_limit

bp = Blueprint("api", __name__)

@bp.route('/stats/<code>')
def get_stats(code):
    url_entry = URL.query.filter_by(short_code=code, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code, is_active=True).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    if url_entry.password_hash:
        return jsonify({'error': 'Analytics are unavailable for password-protected links.'}), 403
    if url_entry.expires_at and url_entry.expires_at < datetime.utcnow():
        return jsonify({'error': 'Link has expired.'}), 410

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
    browser_counts = Counter()
    for click in recent_clicks:
        date = click.clicked_at.date().isoformat()
        if date in daily_data:
            daily_data[date] += 1
        if click.referer_domain and click.referer_domain != 'Direct':
            referer_counts[click.referer_domain] += 1
        if click.browser:
            browser_counts[click.browser] += 1
    
    devices = {'mobile': 0, 'desktop': 0, 'tablet': 0}
    for click in recent_clicks:
        if click.device_type:
            devices[click.device_type] = devices.get(click.device_type, 0) + 1
    
    return jsonify({
        'total_clicks': url_entry.clicks,
        'recent_clicks': len(recent_clicks),
        'daily_data': [{'date': k, 'clicks': v} for k, v in sorted(daily_data.items())],
        'devices': devices,
        'browsers': dict(browser_counts.most_common(8)),
        'top_referrers': referer_counts.most_common(10),
        'short_code': code,
        'original_url': url_entry.original_url,
        'created_at': url_entry.created_at.isoformat(),
        'expires_at': url_entry.expires_at.isoformat() if url_entry.expires_at else None
    })


@bp.route('/preview')
def get_preview():
    if not check_rate_limit(f'preview:{get_client_ip()}', limit=20, window=3600):
        return jsonify({'error': 'Preview rate limit reached. Please try again later.'}), 429
    target_url = (request.args.get('url') or '').strip()
    if not target_url or not is_valid_url(target_url):
        return jsonify({'error': 'A valid HTTP or HTTPS URL is required.'}), 400

    current_url = target_url
    response = None
    try:
        for _ in range(4):
            if not is_public_http_url(current_url):
                return jsonify({'error': 'This destination cannot be previewed for security reasons.'}), 400
            response = requests.get(
                current_url,
                timeout=(2, 4),
                allow_redirects=False,
                stream=True,
                headers={'User-Agent': 'WafyURL-Preview/1.0 (+https://url.amwafy.xyz)'}
            )
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get('Location')
                response.close()
                if not location:
                    break
                current_url = urljoin(current_url, location)
                continue
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                response.close()
                return jsonify({'error': 'The destination does not provide an HTML preview.'}), 415
            body = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                body.extend(chunk)
                if len(body) > 1_000_000:
                    break
            response.close()
            soup = BeautifulSoup(bytes(body), 'html.parser')
            title_tag = soup.find('meta', property='og:title') or soup.find('title')
            title = title_tag.get('content', '') if title_tag and title_tag.name == 'meta' else title_tag.get_text(' ', strip=True) if title_tag else ''
            desc_tag = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
            desc = desc_tag.get('content', '') if desc_tag else ''
            image_tag = soup.find('meta', property='og:image')
            image = urljoin(current_url, image_tag.get('content', '')) if image_tag and image_tag.get('content') else ''
            return jsonify({'title': title[:150] or 'No title available', 'description': desc[:300] or 'No description available', 'image': image})
        return jsonify({'error': 'Too many redirects while fetching preview.'}), 400
    except requests.RequestException:
        if response is not None:
            response.close()
        return jsonify({'error': 'Could not fetch preview.'}), 400
    except Exception:
        if response is not None:
            response.close()
        current_app.logger.exception('Preview parsing failed')
        return jsonify({'error': 'Could not parse destination metadata.'}), 400


@bp.route('/link/<code>')
def get_link_info(code):
    url_entry = URL.query.filter_by(short_code=code, is_active=True).first()
    if not url_entry:
        url_entry = URL.query.filter_by(custom_code=code, is_active=True).first()
        if not url_entry:
            return jsonify({'error': 'Link not found'}), 404
    
    if url_entry.password_hash:
        return jsonify({'error': 'Destination preview is unavailable for password-protected links.'}), 403
    if url_entry.expires_at and url_entry.expires_at < datetime.utcnow():
        return jsonify({'error': 'Link has expired.'}), 410

    return jsonify({
        'original_url': url_entry.original_url,
        'clicks': url_entry.clicks,
        'created_at': url_entry.created_at.isoformat(),
        'expires_at': url_entry.expires_at.isoformat() if url_entry.expires_at else None,
        'has_password': bool(url_entry.password_hash)
    })

