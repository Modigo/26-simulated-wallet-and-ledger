import hashlib, secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
ph = PasswordHasher()
def hash_password(p: str) -> str: return ph.hash(p)
def verify_password(p: str, h: str | None) -> bool:
    if not h: return False
    try: ph.verify(h, p); return True
    except VerifyMismatchError: return False
    except Exception: return False
def new_token() -> str: return secrets.token_urlsafe(48)
def token_hash(t: str) -> str: return hashlib.sha256(t.encode()).hexdigest()
