"""
data_processing.py — Carga y procesamiento de datos financieros.
CONSERVAR PAGA — Dashboard de Control Financiero
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime


# ==================== HELPERS ====================
def find_sheet(xls, name):
    """Find sheet by name ignoring trailing spaces."""
    for s in xls.sheet_names:
        if s.strip().upper() == name.upper():
            return s
    return None


def _find_col(df, candidates):
    """Find first matching column from candidates list."""
    for c in candidates:
        for col in df.columns:
            if c.upper() in col.upper():
                return col
    return None


def classify_concept(concepto):
    if pd.isna(concepto):
        return 'Otros'
    c = str(concepto).upper()
    if 'JURIDICA' in c:
        return 'Contratistas P.J.'
    if 'CONTRATISTA' in c:
        return 'Contratistas P.N.'
    if 'IMPUESTO' in c:
        return 'Impuestos'
    if 'INCENTIVO' in c:
        return 'Incentivos'
    if 'COMISION' in c:
        return 'Comisiones bancarias'
    if 'VIAJE' in c or 'VIATICO' in c:
        return 'Gastos de viaje'
    if 'TRASLADO' in c:
        return 'Traslados'
    return 'Otros'


def fmt_money(val):
    if pd.isna(val) or val == 0:
        return "$0"
    if abs(val) >= 1_000_000_000:
        return f"${val/1_000_000_000:,.1f}B"
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    return f"${val:,.0f}"


# ==================== DATA LOADING ====================
@st.cache_data(ttl=3600)
def load_excel(file_bytes):
    """Load all relevant sheets from the Excel file."""
    try:
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        data = {}

        # INF PAGOS
        sn = find_sheet(xls, 'INF PAGOS')
        if sn:
            df = pd.read_excel(xls, sheet_name=sn)
            df.columns = [str(c).strip() for c in df.columns]
            data['pagos'] = df

        # GASTOS CP (raw, no header)
        sn = find_sheet(xls, 'GASTOS CP')
        if sn:
            data['gastos_cp'] = pd.read_excel(xls, sheet_name=sn, header=None)

        # INGRESOS CP
        sn = find_sheet(xls, 'INGRESOS CP')
        if sn:
            df = pd.read_excel(xls, sheet_name=sn, header=3)
            df.columns = [str(c).strip() for c in df.columns]
            data['ingresos'] = df

        # INCENTIVOS
        sn = find_sheet(xls, 'INCENTIVOS')
        if sn:
            df = pd.read_excel(xls, sheet_name=sn, header=3)
            df.columns = [str(c).strip() for c in df.columns]
            data['incentivos'] = df

        # GASTOS VIAJE
        sn = find_sheet(xls, 'GASTOS VIAJE')
        if sn:
            df = pd.read_excel(xls, sheet_name=sn, header=10)
            df.columns = [str(c).strip() for c in df.columns]
            data['viajes'] = df

        # MOVIMIENTO DB Y CR
        sn = find_sheet(xls, 'MOVIMIENTO DB Y CR')
        if sn:
            df = pd.read_excel(xls, sheet_name=sn, header=2)
            df.columns = [str(c).strip() for c in df.columns]
            data['movimientos'] = df

        # FIDUCOLDEX (raw)
        sn = find_sheet(xls, 'FIDUCOLDEX')
        if sn:
            data['fiducoldex'] = pd.read_excel(xls, sheet_name=sn, header=None)

        # OTROS EGRESOS
        sn = find_sheet(xls, 'OTROS EGRESOS')
        if sn:
            data['otros_egresos'] = pd.read_excel(xls, sheet_name=sn, header=None)

        return data
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None


# ==================== DATA PROCESSING ====================
def process_payments(data):
    """Consolidate all payments into a single DataFrame."""
    frames = []

    # 1. INF PAGOS
    if 'pagos' in data:
        df = data['pagos'].copy()
        col_proveedor = _find_col(df, ['Descripción Proveedor', 'Descripcion Proveedor', 'Proveedor'])
        col_bruto = _find_col(df, ['Valor Bruto'])
        col_neto = _find_col(df, ['Valor Neto'])
        col_fecha = _find_col(df, ['Fecha de Pago', 'Fecha'])
        col_concepto = _find_col(df, ['CONCEPTO'])
        col_anio = _find_col(df, ['Año', 'Ano'])
        col_mes = _find_col(df, ['Mes'])
        col_iva = _find_col(df, ['Iva', 'IVA'])
        col_retefuente = _find_col(df, ['Valor ReteFuente', 'ReteFuente'])
        col_reteiva = _find_col(df, ['Valor ReteIva', 'ReteIva'])
        col_reteica = _find_col(df, ['Valor ReteIca', 'ReteIca'])

        rows = []
        for _, r in df.iterrows():
            prov = r.get(col_proveedor) if col_proveedor else None
            if pd.isna(prov) or prov is None:
                continue
            bruto = pd.to_numeric(r.get(col_bruto, 0), errors='coerce') or 0
            neto = pd.to_numeric(r.get(col_neto, 0), errors='coerce')
            if pd.isna(neto) or neto == 0:
                # Ley Colombiana (Estatuto Tributario Art. 368):
                # Neto = Bruto - (ReteFuente + ReteIva + ReteIca)
                rf = pd.to_numeric(r.get(col_retefuente, 0), errors='coerce') or 0
                ri = pd.to_numeric(r.get(col_reteiva, 0), errors='coerce') or 0
                rc = pd.to_numeric(r.get(col_reteica, 0), errors='coerce') or 0
                neto = bruto - (rf + ri + rc)
            fecha = pd.to_datetime(r.get(col_fecha), errors='coerce')
            concepto = r.get(col_concepto, '')
            rows.append({
                'Proveedor': str(prov).strip(),
                'Valor Bruto': bruto,
                'Valor Neto': neto,
                'Fecha': fecha,
                'Categoría': classify_concept(concepto),
                'Año': r.get(col_anio),
                'Mes Num': r.get(col_mes),
                'Origen': 'INF PAGOS'
            })
        if rows:
            frames.append(pd.DataFrame(rows))

    # 2. INCENTIVOS
    if 'incentivos' in data:
        df = data['incentivos'].copy()
        col_ciclo = _find_col(df, ['PAGO INCENTIVOS', 'CICLO'])
        col_fecha = _find_col(df, ['FECHA DE PAGO', 'FECHA'])
        col_total = _find_col(df, ['VALOR PAGO TOTAL', 'VALOR TOTAL'])
        col_neto = _find_col(df, ['ABONO NETO', 'NETO'])
        if col_total:
            rows = []
            for _, r in df.iterrows():
                ciclo = r.get(col_ciclo)
                if pd.isna(ciclo):
                    continue
                val = pd.to_numeric(r.get(col_total, 0), errors='coerce')
                neto = pd.to_numeric(r.get(col_neto, 0), errors='coerce')
                if pd.isna(val) or val == 0:
                    continue
                fecha = pd.to_datetime(r.get(col_fecha), errors='coerce') if col_fecha else pd.NaT
                rows.append({
                    'Proveedor': f'Incentivo - {str(ciclo).strip()}',
                    'Valor Bruto': val, 'Valor Neto': neto if not pd.isna(neto) else val,
                    'Fecha': fecha, 'Categoría': 'Incentivos', 'Origen': 'INCENTIVOS'
                })
            if rows:
                frames.append(pd.DataFrame(rows))

    # 3. GASTOS VIAJE
    if 'viajes' in data:
        df = data['viajes'].copy()
        col_nombre = _find_col(df, ['NOMBRE COMPLETO', 'NOMBRE'])
        col_pago = _find_col(df, ['PAGO VIATICOS', 'VIATICOS', 'PAGO'])
        col_fecha = _find_col(df, ['FECHA DE PAGO', 'FECHA'])
        if col_pago:
            rows = []
            for _, r in df.iterrows():
                val = pd.to_numeric(r.get(col_pago, 0), errors='coerce')
                if pd.isna(val) or val == 0:
                    continue
                nombre = r.get(col_nombre, 'Viáticos') if col_nombre else 'Viáticos'
                fecha = pd.to_datetime(r.get(col_fecha), errors='coerce') if col_fecha else pd.NaT
                rows.append({
                    'Proveedor': str(nombre).strip() if not pd.isna(nombre) else 'Viáticos',
                    'Valor Bruto': val, 'Valor Neto': val,
                    'Fecha': fecha, 'Categoría': 'Gastos de viaje', 'Origen': 'GASTOS VIAJE'
                })
            if rows:
                frames.append(pd.DataFrame(rows))

    if not frames:
        return pd.DataFrame(columns=['Proveedor', 'Valor Bruto', 'Valor Neto', 'Fecha', 'Categoría', 'Origen'])
    result = pd.concat(frames, ignore_index=True)
    result = result.dropna(subset=['Valor Neto'])
    result = result[result['Valor Neto'] != 0]
    return result


def extract_gastos_cp_totals(data):
    """Extract category totals from GASTOS CP summary sheet.

    Handles the real format where categories appear as:
      DESCRIPCION column: A. PERSONAL, B. PAGO DE INCENTIVOS, etc.
      Or TOTAL rows: TOTAL COSTOS DE PERSONAL, TOTAL INCENTIVOS, etc.
    """
    if 'gastos_cp' not in data:
        return {}
    df = data['gastos_cp']
    totals = {}

    # Mapping: keyword found in cell → dashboard category name
    # Supports both "TOTAL X" summary rows and "A. PERSONAL" description rows
    keywords = {
        # TOTAL rows (original format)
        'TOTAL COSTOS DE PERSONAL': 'Personal',
        'TOTAL INCENTIVOS': 'Incentivos',
        'TOTAL COSTOS SERVICIOS BANCARIOS': 'Comisiones bancarias',
        'TOTAL DINAMIZADORES': 'Dinamizadores',
        'TOTAL VIATICOS': 'Gastos de viaje',
        'TOTAL GASTOS DEL PROYECTO': 'Total Proyecto',
        'VALOR IMPUESTOS': 'Impuestos',
        # DESCRIPCION rows (real format from image)
        'A. PERSONAL': 'Personal',
        'B. PAGO DE INCENTIVOS': 'Incentivos',
        'C. PAGO SERVICIOS BANCARIOS': 'Comisiones bancarias',
        'D. PAGO A DINAMIZADORES': 'Dinamizadores',
        'E. PAGO DE VIATICOS': 'Gastos de viaje',
        'F. PAGO DE IMPUESTOS': 'Impuestos',
    }

    for idx, row in df.iterrows():
        # Check first two columns for keywords (some sheets use col 0, others col 1)
        for col_idx in range(min(2, len(row))):
            cell = str(row.iloc[col_idx]).strip().upper() if pd.notna(row.iloc[col_idx]) else ''
            if not cell:
                continue
            for kw, cat in keywords.items():
                if kw in cell:
                    # Find first numeric value in the row (scan cols 1-10)
                    for c in range(1, min(11, len(row))):
                        v = row.iloc[c]
                        if isinstance(v, (int, float)) and not pd.isna(v) and v != 0:
                            # Keep the largest value if category already found
                            # (TOTAL rows override individual rows)
                            if cat not in totals or ('TOTAL' in kw and cat in totals):
                                totals[cat] = v
                            break
                    break  # Stop checking keywords for this cell

    # Remove "Total Proyecto" from display (it's the grand total, not a category)
    totals.pop('Total Proyecto', None)
    return totals


def get_monthly_balances(data):
    """Extract monthly bank balances from MOVIMIENTO DB Y CR."""
    if 'movimientos' not in data:
        return pd.DataFrame()
    df = data['movimientos'].copy()
    col_mes = _find_col(df, ['MES'])
    col_saldo_ini = _find_col(df, ['SALDO INICIAL'])
    col_ingresos = _find_col(df, ['INGRESOS'])
    col_pagos = _find_col(df, ['PAGOS'])
    col_saldo_fin = _find_col(df, ['SALDO FINAL'])
    col_intereses = _find_col(df, ['INTERESES'])
    if not col_mes:
        return pd.DataFrame()
    rows = []
    for _, r in df.iterrows():
        mes = r.get(col_mes)
        if pd.isna(mes):
            continue
        mes_str = str(mes).strip()
        if mes_str.upper() in ('AÑO 2024', 'AÑO 2025', 'ANO 2024', 'ANO 2025') or 'TOTAL' in mes_str.upper() or 'VALOR' in mes_str.upper():
            continue
        si = pd.to_numeric(r.get(col_saldo_ini, 0), errors='coerce') or 0
        ing = pd.to_numeric(r.get(col_ingresos, 0), errors='coerce') or 0
        pag = pd.to_numeric(r.get(col_pagos, 0), errors='coerce') or 0
        sf = pd.to_numeric(r.get(col_saldo_fin, 0), errors='coerce') or 0
        ints = pd.to_numeric(r.get(col_intereses, 0), errors='coerce') or 0
        if si == 0 and ing == 0 and pag == 0 and sf == 0:
            continue
        rows.append({'Mes': mes_str, 'Saldo Inicial': si, 'Ingresos': ing, 'Pagos': pag, 'Saldo Final': sf, 'Intereses': ints})
    return pd.DataFrame(rows)


def get_fiducoldex_cashflow(data):
    """Extract cash flow from FIDUCOLDEX sheet."""
    if 'fiducoldex' not in data:
        return pd.DataFrame()
    df = data['fiducoldex']
    saldo_idx = None
    for i, row in df.iterrows():
        val = row.iloc[1]
        if pd.notna(val):
            s = str(val).strip().upper()
            if 'SALDO FINAL' in s or 'SALDO  FINAL' in s:
                saldo_idx = i
    if saldo_idx is None:
        return pd.DataFrame()
    months_raw = df.iloc[2, 2:17].values
    saldos = df.iloc[saldo_idx, 2:17].values
    rows = []
    for m, s in zip(months_raw, saldos):
        if pd.isna(m):
            continue
        m_str = str(m).strip()
        if hasattr(m, 'strftime'):
            m_str = m.strftime('%Y-%m')
        s_val = pd.to_numeric(s, errors='coerce')
        if pd.isna(s_val):
            continue
        rows.append({'Periodo': m_str, 'Saldo Proyectado': s_val})
    return pd.DataFrame(rows)


def get_ingresos_summary(data):
    """Extract income summary from INGRESOS CP."""
    if 'ingresos' not in data:
        return pd.DataFrame()
    df = data['ingresos'].copy()
    col_fecha = _find_col(df, ['Fecha'])
    col_concepto = _find_col(df, ['CONCEPTO'])
    col_valor = _find_col(df, ['VALOR'])
    if not col_valor:
        return pd.DataFrame()
    rows = []
    for _, r in df.iterrows():
        val = pd.to_numeric(r.get(col_valor, 0), errors='coerce')
        if pd.isna(val) or val == 0:
            continue
        fecha = pd.to_datetime(r.get(col_fecha), errors='coerce') if col_fecha else pd.NaT
        concepto = r.get(col_concepto, '') if col_concepto else ''
        rows.append({'Fecha': fecha, 'Concepto': str(concepto).strip(), 'Valor': val})
    return pd.DataFrame(rows)

# ==================== ADVANCED ANALYTICS ENGINE ====================

def normalize_category(cat: str) -> str:
    """Limpieza de categorias."""
    return " ".join(str(cat).strip().upper().split())

def normalize_text(val: str) -> str:
    """Limpieza de contratistas/nombres."""
    if pd.isna(val):
        return "DESCONOCIDO"
    return " ".join(str(val).strip().upper().split())

def normalize_date(val):
    """Normaliza fechas a datetime.date. Soporta multiples formatos."""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, str):
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(val[:10], fmt).date()
            except Exception:
                continue
    return pd.NaT

@st.cache_data(show_spinner=False)
def build_analytics_cube(df_pagos: pd.DataFrame, df_ingresos: pd.DataFrame) -> pd.DataFrame:
    """Builds a normalized, aggregated cube for fast filtering."""
    rows = []
    
    # Process EGRESOS
    if not df_pagos.empty:
        for _, r in df_pagos.iterrows():
            d = normalize_date(r['Fecha'])
            if pd.isna(d):
                continue
            rows.append({
                'contractor': normalize_text(r['Proveedor']),
                'category': normalize_category(r['Categoría']),
                'type': 'EGRESO',
                'date': d,
                'amount': float(r['Valor Neto']),
                'year': d.year,
                'month': d.month,
            })
            
    # Process INGRESOS
    if not df_ingresos.empty:
        for _, r in df_ingresos.iterrows():
            d = normalize_date(r['Fecha'])
            if pd.isna(d):
                continue
            rows.append({
                'contractor': normalize_text(r['Concepto']),
                'category': 'INGRESOS PROYECTO',
                'type': 'INGRESO',
                'date': d,
                'amount': float(r['Valor']),
                'year': d.year,
                'month': d.month,
            })
            
    df_cube = pd.DataFrame(rows)
    return df_cube


def get_financial_summary(df_cube: pd.DataFrame, filters: dict) -> dict:
    """Aplica filtros al cubo analitico y retorna aggregaciones.
    
    Args:
        df_cube: DataFrame del cubo analitico (build_analytics_cube)
        filters: dict con start_date, end_date, contractors[], categories[]
    
    Returns:
        dict con keys: detail, totals_by_category, monthly_by_category, kpis
    """
    from collections import defaultdict
    
    if df_cube.empty:
        return {'detail': [], 'totals_by_category': [], 'monthly_by_category': [], 'kpis': {'ingresos': 0, 'egresos': 0, 'balance': 0}}
    
    df = df_cube.copy()
    
    # Apply filters
    if filters.get('start_date'):
        df = df[df['date'] >= filters['start_date']]
    if filters.get('end_date'):
        df = df[df['date'] <= filters['end_date']]
    if filters.get('contractors'):
        pattern = '|'.join([c.upper() for c in filters['contractors']])
        df = df[df['contractor'].str.contains(pattern, na=False)]
    if filters.get('categories'):
        pattern = '|'.join([c.upper() for c in filters['categories']])
        df = df[df['category'].str.contains(pattern, na=False)]
    
    if df.empty:
        return {'detail': [], 'totals_by_category': [], 'monthly_by_category': [], 'kpis': {'ingresos': 0, 'egresos': 0, 'balance': 0}}
    
    # 1. Detalle mensual por contratista (tuplas como llaves)
    detail_map = defaultdict(float)
    for _, r in df.iterrows():
        month_key = f"{int(r['year'])}-{int(r['month']):02d}"
        key = (r['contractor'], month_key, r['category'], r['type'])
        detail_map[key] += r['amount']
    detail = [
        {'contractor': k[0], 'month': k[1], 'category': k[2], 'type': k[3], 'total': v}
        for k, v in detail_map.items()
    ]
    
    # 2. Totales por categoria
    cat_map = defaultdict(float)
    for _, r in df.iterrows():
        cat_map[(r['category'], r['type'])] += r['amount']
    totals_by_category = [
        {'category': k[0], 'type': k[1], 'total': v}
        for k, v in cat_map.items()
    ]
    
    # 3. Serie mensual por tipo (para grafico linea)
    monthly_map = defaultdict(float)
    for _, r in df.iterrows():
        month_key = f"{int(r['year'])}-{int(r['month']):02d}"
        monthly_map[(month_key, r['type'])] += r['amount']
    monthly_by_category = [
        {'month': k[0], 'type': k[1], 'total': v}
        for k, v in monthly_map.items()
    ]
    
    # 4. KPIs
    total_ingresos = float(df[df['type'] == 'INGRESO']['amount'].sum())
    total_egresos = float(df[df['type'] == 'EGRESO']['amount'].sum())
    kpis = {
        'ingresos': total_ingresos,
        'egresos': total_egresos,
        'balance': total_ingresos - total_egresos
    }
    
    return {'detail': detail, 'totals_by_category': totals_by_category, 'monthly_by_category': monthly_by_category, 'kpis': kpis}
