"""
auth.py — Sistema de autenticación con bcrypt + JWT.
CONSERVAR PAGA — Dashboard de Control Financiero

Seguridad OWASP:
- A01 Broken Access Control: Auth gate obligatorio antes de acceder a datos
- A02 Cryptographic Failures: bcrypt para passwords, JWT HS256 para tokens
- A07 Auth Failures: Rate limiting (5 intentos, 5 min lockout), session timeout
"""
import streamlit as st
import bcrypt
import jwt
from datetime import datetime, timedelta
from security import audit_log

# ==================== CONFIG ====================
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 5
INACTIVITY_TIMEOUT_MINUTES = 30


def _get_secret(key, default=None):
    """Lee secrets de Streamlit (secrets.toml o Streamlit Cloud)."""
    try:
        keys = key.split('.')
        val = st.secrets
        for k in keys:
            val = val[k]
        return val
    except Exception:
        return default

JWT_SECRET = _get_secret('auth.jwt_secret', 'conservar-paga-secret-key-2026-change-me')
TOKEN_EXPIRY = int(_get_secret('auth.token_expiry_hours', 8))


# ==================== RATE LIMITING ====================
def _get_login_attempts():
    """Obtiene el contador de intentos fallidos."""
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
        st.session_state.lockout_until = None
    return st.session_state.login_attempts


def _is_locked_out():
    """Verifica si la cuenta esta bloqueada por intentos fallidos."""
    lockout = st.session_state.get('lockout_until')
    if lockout and datetime.now() < lockout:
        remaining = (lockout - datetime.now()).seconds // 60 + 1
        return True, remaining
    if lockout and datetime.now() >= lockout:
        st.session_state.login_attempts = 0
        st.session_state.lockout_until = None
    return False, 0


def _record_failed_attempt(username):
    """Registra intento fallido y activa lockout si excede el limite."""
    st.session_state.login_attempts = st.session_state.get('login_attempts', 0) + 1
    attempts = st.session_state.login_attempts
    if attempts >= MAX_LOGIN_ATTEMPTS:
        st.session_state.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        audit_log(username, 'ACCOUNT_LOCKED', f'{attempts} intentos fallidos, bloqueado {LOCKOUT_MINUTES} min')


def _reset_attempts():
    """Resetea contador tras login exitoso."""
    st.session_state.login_attempts = 0
    st.session_state.lockout_until = None


# ==================== SESSION TIMEOUT ====================
def _check_inactivity():
    """Verifica si la sesion expiro por inactividad."""
    last_activity = st.session_state.get('last_activity')
    if last_activity:
        elapsed = (datetime.now() - last_activity).total_seconds() / 60
        if elapsed > INACTIVITY_TIMEOUT_MINUTES:
            user = st.session_state.get('username', 'unknown')
            audit_log(user, 'SESSION_TIMEOUT', f'Inactivo {elapsed:.0f} min')
            st.session_state.pop('auth_token', None)
            st.session_state.pop('username', None)
            st.session_state.pop('last_activity', None)
            return True
    st.session_state.last_activity = datetime.now()
    return False


# ==================== AUTH FUNCTIONS ====================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contrasena contra hash bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_token(username: str) -> str:
    """Genera JWT con expiracion."""
    payload = {
        'sub': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def validate_token(token: str) -> dict | None:
    """Valida JWT y retorna payload o None si expiro."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_users() -> dict:
    """Lee usuarios desde secrets.toml."""
    try:
        return dict(st.secrets['users'])
    except Exception:
        return {}


def is_authenticated() -> bool:
    """Verifica si hay sesion activa con token valido + timeout por inactividad."""
    token = st.session_state.get('auth_token')
    if not token:
        return False
    payload = validate_token(token)
    if payload is None:
        st.session_state.pop('auth_token', None)
        st.session_state.pop('username', None)
        return False
    # Check inactivity timeout
    if _check_inactivity():
        return False
    return True


def login(username: str, password: str) -> bool:
    """Intenta login con rate limiting."""
    # Check lockout
    locked, remaining = _is_locked_out()
    if locked:
        audit_log(username, 'LOGIN_BLOCKED', f'Cuenta bloqueada, {remaining} min restantes')
        return False

    users = get_users()
    if username not in users:
        _record_failed_attempt(username)
        audit_log(username, 'LOGIN_FAILED', 'Usuario no encontrado')
        return False

    if verify_password(password, users[username]):
        _reset_attempts()
        token = create_token(username)
        st.session_state['auth_token'] = token
        st.session_state['username'] = username
        st.session_state['last_activity'] = datetime.now()
        audit_log(username, 'LOGIN_SUCCESS', '')
        return True
    else:
        _record_failed_attempt(username)
        audit_log(username, 'LOGIN_FAILED', 'Contrasena incorrecta')
        return False


def logout():
    """Cierra sesion y limpia todo el estado."""
    user = st.session_state.get('username', 'unknown')
    audit_log(user, 'LOGOUT', '')
    for key in ['auth_token', 'username', 'last_activity', 'login_attempts', 'lockout_until']:
        st.session_state.pop(key, None)


def show_login_form():
    """Muestra formulario de login estilizado con feedback de lockout."""
    from styles import FA_CDN, MAIN_CSS, LOGIN_HEADER

    st.markdown(FA_CDN, unsafe_allow_html=True)
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
    st.markdown(LOGIN_HEADER, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        # Show lockout warning if active
        locked, remaining = _is_locked_out()
        if locked:
            st.error(f"Cuenta bloqueada por {remaining} minuto{'s' if remaining > 1 else ''}. Intente mas tarde.")

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contrasena", type="password", placeholder="Ingrese su contrasena")
            submitted = st.form_submit_button("Iniciar Sesion", use_container_width=True, disabled=locked)

            if submitted and not locked:
                if not username or not password:
                    st.error("Complete todos los campos")
                elif login(username, password):
                    st.rerun()
                else:
                    attempts = st.session_state.get('login_attempts', 0)
                    remaining_attempts = MAX_LOGIN_ATTEMPTS - attempts
                    if remaining_attempts > 0:
                        st.error(f"Credenciales incorrectas. {remaining_attempts} intento{'s' if remaining_attempts > 1 else ''} restante{'s' if remaining_attempts > 1 else ''}.")
                    else:
                        st.error(f"Cuenta bloqueada por {LOCKOUT_MINUTES} minutos.")

        st.markdown("""
        <div style="text-align:center; opacity:0.4; font-size:0.75rem; margin-top:1rem;">
            <i class="fas fa-shield-halved"></i> Conexion segura · JWT + bcrypt · OWASP Top 10
        </div>
        """, unsafe_allow_html=True)
