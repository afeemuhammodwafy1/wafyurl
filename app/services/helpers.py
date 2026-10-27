import ipaddress
import socket
import string
from datetime import datetime
from urllib.parse import urlparse
from flask import request
from secrets import choice
from app.extensions import db
from app.models import URL, SiteStats

def generate_short_code(length=7):
    chars = string.ascii_letters + string.digits
    for _ in range(10):
        code = ''.join(choice(chars) for _ in range(length))
        if not URL.query.filter_by(short_code=code).first() and not URL.query.filter_by(custom_code=code).first():
            return code
    raise RuntimeError('Unable to allocate a unique short code.')


def is_valid_url(value):
    try:
        parsed = urlparse(value)
        return (
            parsed.scheme in {'http', 'https'}
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and len(value) <= 2000
            and not any(char.isspace() for char in value)
            and not any(ord(char) < 32 for char in value)
            and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except (TypeError, ValueError):
        return False


def is_public_http_url(value):
    """Reject non-public destinations before the server fetches preview metadata."""
    try:
        parsed = urlparse(value)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
            return False
        hostname = parsed.hostname.rstrip('.').lower()
        if hostname in {'localhost', 'localhost.localdomain'} or hostname.endswith(('.local', '.internal', '.test')):
            return False
        try:
            addresses = [ipaddress.ip_address(hostname)]
        except ValueError:
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)]
        return bool(addresses) and all(address.is_global for address in addresses)
    except (ValueError, OSError, socket.gaierror):
        return False


def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or '127.0.0.1'


def detect_device(user_agent):
    ua = user_agent.lower() if user_agent else ''
    if 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua or 'ipod' in ua:
        return 'mobile'
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
    if 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        return 'iOS'
    elif 'android' in ua:
        return 'Android'
    elif 'windows' in ua:
        return 'Windows'
    elif 'mac os' in ua or 'macintosh' in ua:
        return 'macOS'
    elif 'linux' in ua:
        return 'Linux'
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

