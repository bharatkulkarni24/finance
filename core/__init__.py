from flask import Flask, jsonify, request, redirect
from flask import session as flask_session
import logging
import time
import traceback
from logging.handlers import RotatingFileHandler
import os
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix

from core.database import init_db, seed_db
from core.session import destroy_admin_session
import core.config

# Session security limits
SESSION_INACTIVITY_SECONDS = 30 * 60   # auto-logout after 30 min of inactivity
SESSION_ABSOLUTE_SECONDS = 12 * 3600   # re-login at least once every 12 hours


def create_app():
    app = Flask(
        'main',
        static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static'),
        template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'),
    )
    # Trust X-Forwarded-Proto/Host when running behind a reverse proxy (nginx/caddy).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.secret_key = core.config.SECRET_KEY
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=SESSION_ABSOLUTE_SECONDS)
    app.config['FORCE_HTTPS'] = os.environ.get('FORCE_HTTPS', '') == '1'
    if app.config['FORCE_HTTPS']:
        app.config['SESSION_COOKIE_SECURE'] = True

    os.makedirs('logs', exist_ok=True)
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        logfile = os.path.join('logs', 'server.log')
        handler = RotatingFileHandler(logfile, maxBytes=5000000, backupCount=2)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    if app.config['FORCE_HTTPS']:
        @app.before_request
        def enforce_https():
            if not request.is_secure:
                return redirect(request.url.replace('http://', 'https://', 1), 308)

    @app.before_request
    def log_request_info():
        app.logger.info(f"REQUEST {request.method} {request.path} from {request.remote_addr}")

    @app.before_request
    def enforce_session_inactivity():
        # Sliding inactivity timeout: any authenticated request extends the
        # session; after SESSION_INACTIVITY_SECONDS of silence it is dropped.
        path = request.path
        if (path.startswith('/static')
                or path == '/'
                or path == '/api/login'
                or path == '/api/client_error'):
            return
        if not flask_session.get('member_id'):
            return
        now = time.time()
        try:
            last = float(flask_session.get('last_seen', now))
        except (TypeError, ValueError):
            last = now
        if now - last > SESSION_INACTIVITY_SECONDS:
            token = request.headers.get('X-ADMIN-TOKEN', '')
            if token:
                destroy_admin_session(token)
            flask_session.clear()
            return jsonify({'error': 'session_expired'}), 401
        # Absolute cap: even continuously active sessions must re-login.
        try:
            started = float(flask_session.get('started_at', now))
        except (TypeError, ValueError):
            started = now
        if now - started > SESSION_ABSOLUTE_SECONDS:
            token = request.headers.get('X-ADMIN-TOKEN', '')
            if token:
                destroy_admin_session(token)
            flask_session.clear()
            return jsonify({'error': 'session_expired'}), 401
        flask_session['last_seen'] = now

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
