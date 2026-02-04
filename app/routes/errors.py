from flask import render_template
from models import db


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return render_template('500.html'), 500
