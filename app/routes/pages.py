import os
from flask import Blueprint, abort, current_app, redirect, render_template, Response, send_from_directory
from app.routes.seo_content import SEO_PAGES, SEO_CONTENT

bp = Blueprint("pages", __name__)

@bp.route('/icon.webp')
@bp.route('/favicon.ico')
def serve_icon():
    return send_from_directory(os.path.dirname(current_app.root_path), 'icon.webp', mimetype='image/webp')


@bp.route('/og-image.webp')
def serve_og_image():
    image_path = os.path.join(os.path.dirname(current_app.root_path), 'og-image.webp')
    if not os.path.isfile(image_path):
        image_path = os.path.join(os.path.dirname(current_app.root_path), 'docs', 'images', 'wafyurl-banner.webp')
    return send_from_directory(os.path.dirname(image_path), os.path.basename(image_path), mimetype='image/webp')


@bp.route('/robots.txt')
def robots():
    content = "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /bulk-shortener\nDisallow: /verify-password\n\nSitemap: https://url.amwafy.xyz/sitemap.xml\n"
    return Response(content, mimetype='text/plain')


@bp.route('/sitemap.xml')
def sitemap():
    from xml.sax.saxutils import escape
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in SEO_PAGES:
        sitemap_xml.append('  <url><loc>https://url.amwafy.xyz' + escape(path) + '</loc></url>')
    sitemap_xml.append('</urlset>')
    return Response('\n'.join(sitemap_xml), mimetype='application/xml')


@bp.route('/features')
def features_page():
    return redirect('/#features', code=301)


@bp.route('/<path:page_path>')
def seo_page(page_path):
    path = '/' + page_path.strip('/')
    if path not in SEO_CONTENT:
        abort(404)
    metadata = SEO_PAGES[path]
    content = SEO_CONTENT[path]
    if path == '/faq':
        return render_template('faq.html', path=path, metadata=metadata, content=content)
    return render_template('seo_page.html', path=path, metadata=metadata, content=content)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/shorten')
def shortener_page():
    return redirect('/#shortener', code=301)



def _render_seo_path(path):
    template = "faq.html" if path == "/faq" else "seo_page.html"
    return render_template(template, path=path, metadata=SEO_PAGES[path], content=SEO_CONTENT[path])

for _seo_path in SEO_CONTENT:
    if _seo_path.count("/") == 1:
        _seo_endpoint = "seo_" + _seo_path.strip("/").replace("-", "_")
        bp.add_url_rule(_seo_path, endpoint=_seo_endpoint, view_func=lambda path=_seo_path: _render_seo_path(path))
