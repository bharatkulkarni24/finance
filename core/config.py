import os
import secrets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'finance.db')


def _load_secret_key() -> str:
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    path = os.path.join(BASE_DIR, '.secret_key')
    if os.path.exists(path):
        with open(path, 'r') as f:
            existing = f.read().strip()
        if existing:
            return existing
    key = secrets.token_hex(32)
    with open(path, 'w') as f:
        f.write(key)
    return key


SECRET_KEY = _load_secret_key()
