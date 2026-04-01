"""
auth.py — Sistema de autenticación con bcrypt + JWT.
CONSERVAR PAGA — Dashboard de Control Financiero
"""
import streamlit as st
import bcrypt
import jwt
from datetime import datetime, timedelta
from security import audit_log

# ==================== CONFIG ====================
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


# ==================== AUTH FUNCTIONS ====================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra hash bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_token(username: str) -> str:
    """Genera JWT con expiración."""
    payload = {
        'sub': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def validate_token(token: str) -> dict | None:
    """Valida JWT y retorna payload o None si expiró."""
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
    """Verifica si hay sesión activa con token válido."""
    token = st.session_state.get('auth_token')
    if not token:
        return False
    payload = validate_token(token)
    if payload is None:
        st.session_state.pop('auth_token', None)
        st.session_state.pop('username', None)
        return False
    return True


def login(username: str, password: str) -> bool:
    """Intenta login. Retorna True si exitoso."""
    users = get_users()
    if username not in users:
        audit_log(username, 'LOGIN_FAILED', 'Usuario no encontrado')
        return False

    if verify_password(password, users[username]):
        token = create_token(username)
        st.session_state['auth_token'] = token
        st.session_state['username'] = username
        audit_log(username, 'LOGIN_SUCCESS', '')
        return True
    else:
        audit_log(username, 'LOGIN_FAILED', 'Contraseña incorrecta')
        return False


def logout():
    """Cierra sesión."""
    user = st.session_state.get('username', 'unknown')
    audit_log(user, 'LOGOUT', '')
    st.session_state.pop('auth_token', None)
    st.session_state.pop('username', None)


def show_login_form():
    """Muestra formulario de login estilizado."""
    from styles import FA_CDN, MAIN_CSS, LOGIN_HEADER

    st.markdown(FA_CDN, unsafe_allow_html=True)
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
    st.markdown(LOGIN_HEADER, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Complete todos los campos")
                elif login(username, password):
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

        st.markdown("""
        <div style="text-align:center; opacity:0.4; font-size:0.75rem; margin-top:1rem;">
            <i class="fas fa-shield-halved"></i> Conexión segura · Sesión con token JWT
        </div>
        """, unsafe_allow_html=True)
