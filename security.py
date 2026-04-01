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
    """Valida que el Excel tenga las hojas minimas requeridas."""
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


def validate_upload(filename: str, file_bytes: bytes) -> tuple:
    """Valida archivo subido: extension, tamano y magic bytes.

    OWASP A04/A08: Prevenir archivos maliciosos disfrazados de Excel.
    Returns (is_valid, error_message)
    """
    # Check extension
    allowed_ext = {'.xlsx', '.xls'}
    ext = ('.' + filename.rsplit('.', 1)[-1].lower()) if '.' in filename else ''
    if ext not in allowed_ext:
        return False, f"Tipo de archivo no permitido: {ext}. Solo se aceptan .xlsx y .xls"

    # Check file size (max 50MB)
    max_size = 50 * 1024 * 1024
    if len(file_bytes) > max_size:
        return False, f"Archivo demasiado grande ({len(file_bytes) / 1024 / 1024:.1f} MB). Maximo 50 MB."

    # Check magic bytes (file signature)
    # XLSX = ZIP format (PK header: 50 4B 03 04)
    # XLS = OLE2 format (D0 CF 11 E0)
    xlsx_magic = b'\x50\x4b\x03\x04'
    xls_magic = b'\xd0\xcf\x11\xe0'
    if not (file_bytes[:4] == xlsx_magic or file_bytes[:4] == xls_magic):
        return False, "El archivo no es un Excel valido (firma de archivo incorrecta)"

    return True, ""


def sanitize_string(value: str) -> str:
    """Limpia strings para prevenir injection en HTML."""
    if not isinstance(value, str):
        return str(value)
    replacements = {'<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '&': '&amp;'}
    for char, safe in replacements.items():
        value = value.replace(char, safe)
    return value
