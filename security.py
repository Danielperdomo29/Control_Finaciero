"""
security.py — Funciones de seguridad: hashing, auditoría, validación.
CONSERVAR PAGA — Dashboard de Control Financiero
"""
import hashlib
import json
import os
from datetime import datetime

AUDIT_LOG = os.path.join(os.path.dirname(__file__), 'audit_log.jsonl')


def hash_file(file_bytes: bytes) -> str:
    """Calcula SHA-256 del archivo para verificar integridad."""
    return hashlib.sha256(file_bytes).hexdigest()


def audit_log(user: str, action: str, details: str = ""):
    """Registra evento en audit_log.jsonl (JSON Lines)."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "details": details,
    }
    try:
        with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass  # No interrumpir la app por fallo de log


def validate_excel_structure(data: dict) -> list:
    """Valida que el Excel tenga las hojas mínimas requeridas."""
    warnings = []
    required = ['pagos']
    optional = ['gastos_cp', 'ingresos', 'incentivos', 'viajes', 'movimientos', 'fiducoldex']

    for sheet in required:
        if sheet not in data:
            warnings.append(f"Hoja requerida no encontrada: {sheet}")

    missing_optional = [s for s in optional if s not in data]
    if missing_optional:
        warnings.append(f"Hojas opcionales no encontradas: {', '.join(missing_optional)}")

    return warnings


def sanitize_string(value: str) -> str:
    """Limpia strings para prevenir injection en HTML."""
    if not isinstance(value, str):
        return str(value)
    replacements = {'<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '&': '&amp;'}
    for char, safe in replacements.items():
        value = value.replace(char, safe)
    return value
