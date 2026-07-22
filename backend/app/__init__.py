import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory

from .extensions import bcrypt, cors, csrf, db, login_manager, migrate


def create_app(test_config=None):
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///eventspace.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=40 * 1024 * 1024,
        UPLOAD_FOLDER=project_root / "uploads",
        STRIPE_PLATFORM_FEE_PERCENT=int(os.getenv("STRIPE_PLATFORM_FEE_PERCENT", "4")),
        STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY", ""),
        STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        FRONTEND_URL=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        ADMIN_EMAIL=os.getenv("ADMIN_EMAIL", ""),
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        MAIL_HOST=os.getenv("MAIL_HOST", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", "465")),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": os.getenv("FRONTEND_URL", "http://localhost:5173")}},
        supports_credentials=True,
    )

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"message": "Authentication required."}), 401

    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        return jsonify({"message": "Your secure session expired. Refresh and try again."}), 400

    from .api.auth import auth_bp
    from .api.events import events_bp
    from .api.payments import payments_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    from .commands import register_commands
    register_commands(app)

    return app
