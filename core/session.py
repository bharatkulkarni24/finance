import secrets

from flask import request, session

_active_admin_tokens = {}


def create_admin_session(member_id: int) -> str:
    token = secrets.token_hex(32)
    _active_admin_tokens[token] = member_id
    return token


def check_admin_token(token: str) -> bool:
    return bool(token) and token in _active_admin_tokens


def require_admin() -> bool:
    return check_admin_token(request.headers.get('X-ADMIN-TOKEN', ''))


def require_self_or_admin(member_id: int) -> bool:
    if session.get('member_id') == member_id:
        return True
    return require_admin()
