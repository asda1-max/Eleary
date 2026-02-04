import os
from flask import send_from_directory, current_app, abort
from flask_login import login_required


def register_upload_routes(app):
    @app.route('/uploads/<path:filename>')
    @login_required
    def uploaded_file(filename):
        """Serve uploaded files from the uploads folder (login required)."""
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            abort(404)
        if not os.path.exists(os.path.join(upload_folder, filename)):
            abort(404)
        return send_from_directory(upload_folder, filename)
