import secrets

_active_admin_tokens = {}


def create_admin_session(member_id: int) -> str:
    token = secrets.token_hex(32)
    _active_admin_tokens[token] = member_id
    return token


def check_admin_token(token: str) -> bool:
    return bool(token) and token in _active_admin_tokens


def revoke_admin_session(token: str) -> None:
    _active_admin_tokens.pop(token, None)
