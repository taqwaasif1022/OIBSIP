"""auth.py - registration, login, password hashing and input validation.

Passwords are NEVER stored. We store a salted PBKDF2-HMAC-SHA256 hash in the
form:   pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
"""
import hashlib
import hmac
import os
import re

from database import DuplicateError

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 200_000
SALT_BYTES = 16

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
_ROOM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _\-]{1,29}$")


class AuthError(Exception):
    """A user-facing validation/authentication problem (message is safe to show)."""


# ---- validation ---------------------------------------------------------
def validate_username(username):
    if not isinstance(username, str) or not _USERNAME_RE.match(username):
        raise AuthError("Username must be 3-20 characters: letters, digits or underscore.")
    return username


def validate_password(password):
    if not isinstance(password, str) or not (8 <= len(password) <= 128):
        raise AuthError("Password must be 8-128 characters long.")
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        raise AuthError("Password must contain at least one letter and one digit.")
    return password


def validate_room_name(name):
    """Return the cleaned room name or raise AuthError."""
    if not isinstance(name, str):
        raise AuthError("Invalid room name.")
    name = " ".join(name.split())  # trim and collapse repeated spaces
    if not _ROOM_RE.match(name):
        raise AuthError("Room name must be 2-30 characters: letters, digits, spaces, '-' or '_'.")
    return name


# ---- hashing ------------------------------------------------------------
def hash_password(password, salt=None, iterations=ITERATIONS):
    salt = salt if salt is not None else os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    """True if `password` matches the stored hash string (constant-time compare)."""
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                     bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest, bytes.fromhex(hash_hex))
    except (ValueError, AttributeError):
        return False


_DUMMY_HASH = hash_password("dummy-password-1")


# ---- registration / login -----------------------------------------------
def register_user(db, username, password):
    validate_username(username)
    validate_password(password)
    try:
        return db.create_user(username, hash_password(password))
    except DuplicateError:
        raise AuthError("That username is already taken.")


def authenticate(db, username, password):
    """Return the user dict on success, else raise AuthError."""
    generic = AuthError("Invalid username or password.")
    if not isinstance(username, str) or not isinstance(password, str):
        raise generic
    user = db.get_user(username)
    if user is None:
        verify_password(password, _DUMMY_HASH)  # same work, so timing doesn't reveal usernames
        raise generic
    if not verify_password(password, user["password_hash"]):
        raise generic
    return user
