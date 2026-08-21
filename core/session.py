import secrets

from flask import request, session

_active_admin_tokens = {}


def create_admin_session(member_id: int) -> str:
    _remove_tokens_for_member(member_id)
    token = secrets.token_hex(32)
    _active_admin_tokens[token] = member_id
    return token


def destroy_admin_session(token: str) -> None:
    _active_admin_tokens.pop(token, None)


def _remove_tokens_for_member(member_id: int) -> None:
    stale = [t for t, mid in _active_admin_tokens.items() if mid == member_id]
    for t in stale:
        del _active_admin_tokens[t]


def check_admin_token(token: str) -> bool:
    return bool(token) and token in _active_admin_tokens


def require_admin() -> bool:
    return check_admin_token(request.headers.get('X-ADMIN-TOKEN', ''))


def require_self_or_admin(member_id: int) -> bool:
    if session.get('member_id') == member_id:
        return True
    return require_admin()
