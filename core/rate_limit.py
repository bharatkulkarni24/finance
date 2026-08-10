"""In-memory sliding-window rate limiter.

Counts failed attempts per key (e.g. client IP or login name) and blocks a
key once it exceeds the limit inside the window. Successful attempts reset
the counter for that key.

State lives only in this process; it is lost on restart, which is acceptable
for a single-process deployment. (For multi-process production you would back
this with Redis.)
"""

import time
from collections import defaultdict, deque
from threading import Lock

WINDOW_SECONDS = 300
MAX_ATTEMPTS = 5

_attempts = defaultdict(deque)
_lock = Lock()


def _now():
    return time.monotonic()


def too_many(key: str) -> bool:
    with _lock:
        q = _attempts[key]
        while q and _now() - q[0] > WINDOW_SECONDS:
            q.popleft()
        return len(q) >= MAX_ATTEMPTS


def record_failure(key: str) -> None:
    with _lock:
        _attempts[key].append(_now())


def record_success(key: str) -> None:
    with _lock:
        _attempts.pop(key, None)


def reset() -> None:
    """Clear all recorded attempts (used by tests and on reload)."""
    with _lock:
        _attempts.clear()
