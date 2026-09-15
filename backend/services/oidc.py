"""OpenID Connect (Authorization Code Flow + PKCE) for SSO logins.

Written against Authentik, but only uses standard OIDC discovery, so any
compliant provider works. Everything is derived from the issuer's
/.well-known/openid-configuration - no provider specific endpoints here.
"""
import base64
import hashlib
import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple

import requests
from jose import jwt, JWTError

ISSUER = os.getenv("OIDC_ISSUER", "").rstrip("/")
CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "")
SCOPES = os.getenv("OIDC_SCOPES", "openid profile email")
PROVIDER_NAME = os.getenv("OIDC_PROVIDER_NAME", "SSO")
DEFAULT_ROLE = os.getenv("OIDC_DEFAULT_ROLE", "planner")

APP_BASE_URL = os.getenv("APP_BASE_URL", "").rstrip("/")
# Must match the redirect URI configured in the provider exactly.
REDIRECT_URL = os.getenv("OIDC_REDIRECT_URL") or (
    f"{APP_BASE_URL}/api/auth/oidc/callback" if APP_BASE_URL else ""
)

_DISCOVERY_TTL = 3600
_discovery_cache: Dict[str, Any] = {}
_discovery_fetched_at = 0.0
_jwks_cache: Dict[str, Any] = {}
_jwks_fetched_at = 0.0


class OIDCError(Exception):
    """Raised for any failure during the OIDC handshake."""


def is_enabled() -> bool:
    return bool(ISSUER and CLIENT_ID and CLIENT_SECRET and REDIRECT_URL)


def _discovery() -> Dict[str, Any]:
    global _discovery_cache, _discovery_fetched_at
    if _discovery_cache and (time.time() - _discovery_fetched_at) < _DISCOVERY_TTL:
        return _discovery_cache

    url = f"{ISSUER}/.well-known/openid-configuration"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise OIDCError(f"Discovery document could not be loaded from {url}: {e}")

    # The issuer in the document is authoritative for later validation.
    if data.get("issuer", "").rstrip("/") != ISSUER:
        raise OIDCError(
            f"Issuer mismatch: configured '{ISSUER}', document says '{data.get('issuer')}'"
        )

    _discovery_cache = data
    _discovery_fetched_at = time.time()
    return data


def _jwks(force_refresh: bool = False) -> Dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at
    if _jwks_cache and not force_refresh and (time.time() - _jwks_fetched_at) < _DISCOVERY_TTL:
        return _jwks_cache

    url = _discovery().get("jwks_uri")
    if not url:
        raise OIDCError("Discovery document has no jwks_uri")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = time.time()
        return _jwks_cache
    except Exception as e:
        raise OIDCError(f"JWKS could not be loaded from {url}: {e}")


def _signing_key(kid: Optional[str]) -> Dict[str, Any]:
    def find(jwks):
        for key in jwks.get("keys", []):
            if kid is None or key.get("kid") == kid:
                return key
        return None

    key = find(_jwks())
    if key is None:
        # Provider may have rotated its keys - refetch once before giving up.
        key = find(_jwks(force_refresh=True))
    if key is None:
        raise OIDCError(f"No matching signing key for kid '{kid}'")
    return key


def build_authorization_url() -> Tuple[str, str, str, str]:
    """Return (url, state, nonce, code_verifier) for a new login attempt."""
    endpoint = _discovery().get("authorization_endpoint")
    if not endpoint:
        raise OIDCError("Discovery document has no authorization_endpoint")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")

    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URL,
        "scope": SCOPES,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"{endpoint}?{urlencode(params)}", state, nonce, code_verifier


def exchange_code(code: str, code_verifier: str) -> Dict[str, Any]:
    endpoint = _discovery().get("token_endpoint")
    if not endpoint:
        raise OIDCError("Discovery document has no token_endpoint")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URL,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": code_verifier,
    }
    try:
        resp = requests.post(endpoint, data=data, timeout=15)
    except Exception as e:
        raise OIDCError(f"Token endpoint unreachable: {e}")

    if resp.status_code != 200:
        raise OIDCError(f"Token exchange failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


def validate_id_token(id_token: str, expected_nonce: str) -> Dict[str, Any]:
    """Verify signature, issuer, audience, expiry and nonce. Returns the claims."""
    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as e:
        raise OIDCError(f"ID token header unreadable: {e}")

    key = _signing_key(header.get("kid"))
    algorithm = header.get("alg") or key.get("alg") or "RS256"
    if algorithm.lower() == "none":
        raise OIDCError("ID token is unsigned")

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=[algorithm],
            audience=CLIENT_ID,
            issuer=ISSUER,
            options={"verify_at_hash": False},
        )
    except JWTError as e:
        raise OIDCError(f"ID token validation failed: {e}")

    if claims.get("nonce") != expected_nonce:
        raise OIDCError("Nonce mismatch - possible replay, login rejected")
    if not claims.get("sub"):
        raise OIDCError("ID token has no sub claim")

    return claims


def fetch_userinfo(access_token: str) -> Dict[str, Any]:
    """Optional extra claims. A failure here is not fatal - the ID token wins."""
    endpoint = _discovery().get("userinfo_endpoint")
    if not endpoint or not access_token:
        return {}
    try:
        resp = requests.get(
            endpoint, headers={"Authorization": f"Bearer {access_token}"}, timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
        print(f"[OIDC] userinfo returned {resp.status_code}, ignoring")
    except Exception as e:
        print(f"[OIDC] userinfo request failed, ignoring: {e}")
    return {}
