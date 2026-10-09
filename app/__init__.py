"""
Application factory for Smart Food Court and Queue Management System.
"""
import os
from pathlib import Path
from flask import Flask, render_template, g, session
from config import config_by_name, Config
from app.extensions import db, csrf


def create_app(config_name=None):
    """Factory function to build and configure the Flask application instance."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, Config))

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Ensure required static directories exist
    qr_dir = Path(app.config['STATIC_FOLDER']) / 'qr_codes'
    qr_dir.mkdir(parents=True, exist_ok=True)
    img_dir = Path(app.config['STATIC_FOLDER']) / 'images' / 'menu'
    img_dir.mkdir(parents=True, exist_ok=True)

    # User session loading before each request
    @app.before_request
    def load_logged_in_user():
        from app.models import User
        user_id = session.get('user_id')
        if user_id is None:
            g.current_user = None
        else:
            g.current_user = db.session.get(User, user_id)

    # Global context processors for Jinja templates
    @app.context_processor
    def inject_global_vars():
        from app.models import ApplicationSetting, Order, OrderStatus
        court_name = "Campus Smart Food Court"
        active_queue_count = 0
        try:
            val = ApplicationSetting.get_value('food_court_name')
            if val:
                court_name = val
            active_queue_count = Order.query.filter(Order.status.in_(OrderStatus.ACTIVE_QUEUE)).count()
        except Exception:
            # Handle cold-start or migrations when tables are not yet present
            pass

        return {
            'current_user': g.get('current_user', None),
            'food_court_name': court_name,
            'active_queue_count': active_queue_count
        }

    # Error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Register blueprints
    from app.auth import auth_bp
    from app.student import student_bp
    from app.admin import admin_bp
    from app.staff import staff_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)

    return app
