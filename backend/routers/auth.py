import hmac
import os
import re
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User, AuditLog
from schemas import Token, TokenData
from services import oidc

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Username/password login stays available unless explicitly switched off
LOCAL_LOGIN_ENABLED = os.getenv("LOCAL_LOGIN_ENABLED", "true").lower() in ("1", "true", "yes")
COOKIE_SECURE = os.getenv("OIDC_COOKIE_SECURE", "true").lower() in ("1", "true", "yes")

FLOW_COOKIE = "oidc_flow"       # carries state/nonce/verifier across the redirect
HANDOFF_COOKIE = "sso_handoff"  # carries the issued app token back to the frontend
FLOW_TTL_SECONDS = 600
HANDOFF_TTL_SECONDS = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

router = APIRouter(prefix="/auth", tags=["auth"])

def secrets_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a or "", b or "")

def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False  # SSO-only account, no local password set
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if not LOCAL_LOGIN_ENABLED:
        raise HTTPException(status_code=403, detail="Local login is disabled, please use SSO")

    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    user.last_login = datetime.utcnow()
    db.commit()

    return _issue_token(user)

from schemas import PasswordChange
@router.post("/change-password")
async def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="This account signs in via SSO and has no local password",
        )
    if not verify_password(data.old_password, current_user.password_hash):
         raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"status": "password updated"}


# ---------------------------------------------------------------------------
# Single Sign-On (OpenID Connect)
# ---------------------------------------------------------------------------

def _issue_token(user: User) -> dict:
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


def _sso_redirect(target: str) -> RedirectResponse:
    # 303 so the browser switches to GET on the frontend route
    return RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)


def _unique_username(db: Session, candidate: str) -> str:
    """Derive a username that is not taken yet."""
    base = re.sub(r"[^a-zA-Z0-9._-]", "", (candidate or "").strip()) or "sso-user"
    base = base[:40]
    name = base
    suffix = 1
    while db.query(User).filter(User.username == name).first():
        suffix += 1
        name = f"{base}{suffix}"
    return name


def _resolve_user(db: Session, claims: dict) -> User:
    """Find, link or create the local account for a set of OIDC claims.

    Match order: the provider's subject first (stable across renames), then the
    email address so an account that already exists locally gets linked instead
    of duplicated.
    """
    sub = claims.get("sub")
    email = (claims.get("email") or "").strip().lower()

    user = db.query(User).filter(User.oidc_sub == sub).first()
    if user:
        return user

    if email:
        user = db.query(User).filter(User.email.ilike(email)).first()
        if user:
            if user.oidc_sub and user.oidc_sub != sub:
                raise oidc.OIDCError(
                    f"Account '{user.username}' is already linked to a different SSO identity"
                )
            user.oidc_sub = sub
            db.add(AuditLog(
                user_id=user.id,
                username=user.username,
                action="SSO_LINK",
                target_table="users",
                target_id=user.id,
                new_value={"oidc_sub": sub},
            ))
            db.commit()
            print(f"[OIDC] Linked existing account '{user.username}' to SSO subject {sub}")
            return user

    # Nothing matched - provision a new account.
    if not email:
        raise oidc.OIDCError(
            "The provider returned no email address, a new account cannot be created. "
            "Check that the 'email' scope is granted."
        )

    given = claims.get("given_name") or ""
    family = claims.get("family_name") or ""
    if not given and not family:
        parts = (claims.get("name") or email.split("@")[0]).split()
        given = parts[0] if parts else email.split("@")[0]
        family = " ".join(parts[1:]) if len(parts) > 1 else ""

    username = _unique_username(db, claims.get("preferred_username") or email.split("@")[0])

    user = User(
        username=username,
        email=email,
        password_hash=None,  # SSO only, no local password
        first_name=given or username,
        last_name=family or "",
        role=oidc.DEFAULT_ROLE,
        is_active=True,
        can_take_duty=False,  # an admin decides who is eligible for duty
        oidc_sub=sub,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(AuditLog(
        user_id=user.id,
        username=user.username,
        action="SSO_CREATE",
        target_table="users",
        target_id=user.id,
        new_value={"username": user.username, "email": user.email, "role": user.role},
    ))
    db.commit()
    print(f"[OIDC] Created account '{user.username}' ({email}) from SSO login")
    return user


@router.get("/config")
async def auth_config():
    """What the login page needs to know. Public on purpose - no secrets here."""
    return {
        "local_login_enabled": LOCAL_LOGIN_ENABLED,
        "oidc_enabled": oidc.is_enabled(),
        "oidc_provider_name": oidc.PROVIDER_NAME,
    }


@router.get("/oidc/login")
async def oidc_login():
    """Start the login: remember the flow in a cookie, then hand off to the provider."""
    if not oidc.is_enabled():
        raise HTTPException(status_code=404, detail="SSO is not configured")

    try:
        url, state, nonce, verifier = oidc.build_authorization_url()
    except oidc.OIDCError as e:
        print(f"[OIDC] Login could not be started: {e}")
        return _sso_redirect("/login?sso_error=provider_unreachable")

    flow_token = jwt.encode(
        {
            "state": state,
            "nonce": nonce,
            "verifier": verifier,
            "exp": datetime.utcnow() + timedelta(seconds=FLOW_TTL_SECONDS),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = _sso_redirect(url)
    response.set_cookie(
        FLOW_COOKIE,
        flow_token,
        max_age=FLOW_TTL_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",  # sent on the top-level redirect back from the provider
        path="/",
    )
    return response


@router.get("/oidc/callback")
async def oidc_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Where the provider sends the user back to."""
    if not oidc.is_enabled():
        raise HTTPException(status_code=404, detail="SSO is not configured")

    def fail(reason: str, log_message: str) -> RedirectResponse:
        print(f"[OIDC] Login failed ({reason}): {log_message}")
        resp = _sso_redirect(f"/login?sso_error={reason}")
        resp.delete_cookie(FLOW_COOKIE, path="/")
        return resp

    if error:
        return fail("provider_rejected", f"{error}: {error_description}")
    if not code or not state:
        return fail("invalid_response", "callback without code or state")

    flow_cookie = request.cookies.get(FLOW_COOKIE)
    if not flow_cookie:
        return fail("state_expired", "flow cookie missing or expired")

    try:
        flow = jwt.decode(flow_cookie, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        return fail("state_invalid", f"flow cookie not readable: {e}")

    if not secrets_equal(flow.get("state", ""), state):
        return fail("state_mismatch", "state does not match the stored value")

    try:
        tokens = oidc.exchange_code(code, flow["verifier"])
        id_token = tokens.get("id_token")
        if not id_token:
            return fail("no_id_token", "token response contained no id_token")

        claims = oidc.validate_id_token(id_token, flow["nonce"])
        # userinfo may carry claims the ID token omits (email, name)
        merged = {**oidc.fetch_userinfo(tokens.get("access_token", "")), **claims}

        user = _resolve_user(db, merged)
    except oidc.OIDCError as e:
        return fail("oidc_error", str(e))
    except Exception as e:
        db.rollback()
        return fail("internal_error", f"unexpected error: {e}")

    if not user.is_active:
        return fail("account_disabled", f"account '{user.username}' is deactivated")

    user.last_login = datetime.utcnow()
    db.commit()

    token = _issue_token(user)

    # Hand the token over in a short-lived cookie instead of the URL, so it does
    # not end up in the browser history, proxy logs or the Referer header.
    response = _sso_redirect("/login?sso=ok")
    response.delete_cookie(FLOW_COOKIE, path="/")
    response.set_cookie(
        HANDOFF_COOKIE,
        token["access_token"],
        max_age=HANDOFF_TTL_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/oidc/complete", response_model=Token)
async def oidc_complete(
    response: Response,
    db: Session = Depends(get_db),
    sso_handoff: Optional[str] = Cookie(default=None),
):
    """Frontend picks up the token issued by the callback and clears the cookie."""
    if not sso_handoff:
        raise HTTPException(status_code=401, detail="No pending SSO login")

    response.delete_cookie(HANDOFF_COOKIE, path="/")

    try:
        payload = jwt.decode(sso_handoff, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="SSO login expired, please try again")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not available")

    return {"access_token": sso_handoff, "token_type": "bearer", "role": user.role}
