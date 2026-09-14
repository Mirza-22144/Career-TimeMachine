import hashlib
import re
import secrets

# Anonymous access tokens. The raw token is only held for the length of a
# request (or returned once when a session is created); storage and lookups
# use its SHA-256 hash, matching anon_session.token_hash in the DB schema.

TOKEN_BYTES = 32  # secrets.token_urlsafe(32) -> 43 URL-safe characters
MAX_TOKEN_LENGTH = 128
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]+")


def generate_token() -> str:
    """Return a new random, unguessable access token."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Return the 64-character hex SHA-256 hash stored in place of a token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_well_formed_token(token: str) -> bool:
    """Cheap shape check so obviously bad input never reaches storage."""
    return 0 < len(token) <= MAX_TOKEN_LENGTH and _TOKEN_PATTERN.fullmatch(token) is not None
