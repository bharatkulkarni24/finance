from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import traceback
from logging.handlers import RotatingFileHandler
import os

from core.config import ADMIN_PIN
from core.database import init_db, seed_db


def create_app():
    app = Flask(
        'main',
        static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static'),
        template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'),
    )
    CORS(app)

    os.makedirs('logs', exist_ok=True)
    logfile = os.path.join('logs', 'server.log')
    handler = RotatingFileHandler(logfile, maxBytes=5000000, backupCount=2)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    @app.before_request
    def log_request_info():
        app.logger.info(f"REQUEST {request.method} {request.path} from {request.remote_addr}")

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({'error': 'not_found', 'message': 'The requested URL was not found on the server.'}), 404

    @app.errorhandler(500)
    def handle_exception(e):
        tb = traceback.format_exc()
        app.logger.error(f"Exception on {request.path}: {str(e)}\n{tb}")
        return jsonify({'error': 'internal_server_error', 'message': str(e)}), 500

    from core.routes.auth import auth_bp
    from core.routes.members import members_bp
    from core.routes.admin import admin_bp
    from core.routes.loans import loans_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(loans_bp)

    with app.app_context():
        init_db()
        seed_db()

    return app
