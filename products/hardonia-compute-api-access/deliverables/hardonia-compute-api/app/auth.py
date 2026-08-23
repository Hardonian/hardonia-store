from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
import hmac
import time
from collections import defaultdict, deque

from app import db
from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# simple in-memory sliding-window rate limiter (per key); Redis optional later
_hits = defaultdict(deque)
# brute-force lockout: per source key (IP or api-key) -> fail timestamps
_fails = defaultdict(deque)

# Max failed auth attempts before a short cooldown (helps against key guessing).
MAX_FAILS = 25
FAIL_WINDOW_S = 60
COOLDOWN_S = 300


def _rate_ok(key):
    if not settings.rate_limit_per_min:
        return True
    now = time.monotonic()
    window = _hits[key]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_min:
        return False
    window.append(now)
    return True


def _constant_time_eq(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return hmac.compare_digest(a, b)


def _lockout_ok(source: str) -> bool:
    now = time.monotonic()
    f = _fails[source]
    while f and now - f[0] > FAIL_WINDOW_S:
        f.popleft()
    if len(f) >= MAX_FAILS:
        # Above threshold: require a cooldown before trying again.
        if now - f[0] < COOLDOWN_S:
            return False
        f.clear()
    return True


def _register_fail(source: str) -> None:
    _fails[source].append(time.monotonic())


def require_key(x_api_key: str | None = Depends(API_KEY_HEADER)):
    if not x_api_key:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key")

    # Brute-force protection (keyed on the presented key itself).
    if not _lockout_ok(x_api_key):
        raise HTTPException(status_code=429, detail="Too many invalid attempts; slow down")

    demo_active = settings.demo_key and not settings.disable_demo_key
    valid = (
        (demo_active and _constant_time_eq(x_api_key, settings.demo_key))
        or (settings.admin_key and _constant_time_eq(x_api_key, settings.admin_key))
        or db.key_exists(x_api_key)
    )
    if not valid:
        _register_fail(x_api_key)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API key")
    if not _rate_ok(x_api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return x_api_key
