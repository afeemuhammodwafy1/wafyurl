import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()

from app.config import Config
from app.extensions import db

def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)
    if not app.config.get("SECRET_KEY"):
        if os.environ.get("VERCEL"):
            raise RuntimeError("SECRET_KEY must be configured in production.")
        app.config["SECRET_KEY"] = "development-only-change-before-deploy"
    db.init_app(app)

    from app import models  # register SQLAlchemy models
    from app.routes.pages import bp as pages_bp
    from app.routes.links import bp as links_bp
    from app.routes.api import bp as api_bp
    app.register_blueprint(pages_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_globals():
        return {"site_name": "WafyURL"}

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("404.html", error_title="Access unavailable", error_message="This resource is unavailable or requires additional access."), 403

    @app.errorhandler(410)
    def gone(e):
        return render_template("404.html", error_title="This link has expired", error_message="The shortened link is no longer active."), 410

    @app.errorhandler(429)
    def rate_limit(e):
        return jsonify({"error": "Too many requests. Please wait."}), 429

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("404.html", error_title="Something went wrong", error_message="The request could not be completed. Please try again."), 500

    with app.app_context():
        db.create_all()
        from app.models import SiteStats
        if SiteStats.query.first() is None:
            db.session.add(SiteStats())
            db.session.commit()
    return app
