"""
app.py — Dashboard de Control Financiero (CONSERVAR PAGA)
Punto de entrada principal con autenticación y dos pestañas.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Module imports
from styles import FA_CDN, MAIN_CSS, COLORS, PLOTLY_LAYOUT, PRIVACY_BANNER
from auth import is_authenticated, show_login_form, logout
from security import hash_file, audit_log, validate_excel_structure, validate_upload
from data_processing import (
    load_excel, process_payments, extract_gastos_cp_totals,
    get_monthly_balances, get_fiducoldex_cashflow, get_ingresos_summary, fmt_money,
    build_analytics_cube, get_financial_summary
)

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Control Financiero | Francia Ester Patino ",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== AUTH GATE ====================
if not is_authenticated():
    show_login_form()
    st.stop()

# ==================== INIT SESSION STATE ====================
if 'alertas_manuales' not in st.session_state:
    st.session_state.alertas_manuales = []

# ==================== LOAD STYLES ====================
st.markdown(FA_CDN, unsafe_allow_html=True)
st.markdown(MAIN_CSS, unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("""<div style="text-align:center; margin-bottom:1rem;">
        <i class="fas fa-tree" style="font-size:2rem; color:#66bb6a;"></i>
        <h4 style="color:#81c784; margin:0.3rem 0 0;">Francia Ester Patino</h4>
        <p style="color:#a5d6a7; font-size:0.75rem; margin:0;">Control Financiero</p>
    </div>""", unsafe_allow_html=True)

    user = st.session_state.get('username', 'usuario')
    st.markdown(f"<div style='font-size:0.75rem; color:#a5d6a7;'><i class='fas fa-user-circle'></i> {user}</div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión", use_container_width=True):
        logout()
        st.rerun()

    st.markdown("---")
    st.markdown("**Cargar archivo Excel**")
    uploaded = st.file_uploader("", type=['xlsx', 'xls'], label_visibility="collapsed")

# ==================== LOAD DATA ====================
data = None
default_path = os.path.join(os.path.dirname(__file__), 'ingresos y gastos Proyecto ambiental.xlsx')

if uploaded:
    file_bytes = uploaded.read()
    # OWASP A04/A08: Validate file before processing
    is_valid, err_msg = validate_upload(uploaded.name, file_bytes)
    if not is_valid:
        st.error(err_msg)
        audit_log(user, 'FILE_REJECTED', f"name={uploaded.name} reason={err_msg}")
        st.stop()
    file_hash = hash_file(file_bytes)
    audit_log(user, 'FILE_UPLOAD', f"name={uploaded.name} hash={file_hash[:16]}...")
    data = load_excel(file_bytes)
elif os.path.exists(default_path):
    with open(default_path, 'rb') as f:
        file_bytes = f.read()
    data = load_excel(file_bytes)

if data is None:
    st.info("Sube un archivo Excel con las hojas: INF PAGOS, GASTOS CP, INGRESOS CP, etc.")
    st.stop()

# Validate structure
warnings = validate_excel_structure(data)
if warnings:
    for w in warnings:
        st.sidebar.warning(w)
else:
    st.sidebar.success("Estructura del archivo validada correctamente")

# ==================== PROCESS DATA ====================
df_pagos = process_payments(data)
totals_cp = extract_gastos_cp_totals(data)
df_balances = get_monthly_balances(data)
df_cashflow = get_fiducoldex_cashflow(data)
df_ingresos = get_ingresos_summary(data)

# Analytics Engine (Cube)
df_cube = build_analytics_cube(df_pagos, df_ingresos)

# ==================== HEADER ====================
st.markdown("""
<div class="header-bar">
    <h1><i class="fas fa-leaf"></i> Dashboard de Control Financiero</h1>
    <p>CONSERVAR PAGA — Proyecto Ambiental | Actualizado: """ + datetime.now().strftime('%d/%m/%Y %H:%M') + """</p>
</div>
""", unsafe_allow_html=True)

# ==================== PRIVACY BANNER ====================
st.markdown(PRIVACY_BANNER, unsafe_allow_html=True)

# ==================== SIDEBAR FILTERS ====================
with st.sidebar:
    st.markdown("### <i class='fas fa-filter' style='margin-right:6px;'></i> Filtros", unsafe_allow_html=True)
    if not df_pagos.empty and 'Fecha' in df_pagos.columns:
        valid_dates = df_pagos['Fecha'].dropna()
        if not valid_dates.empty:
            min_d = valid_dates.min().date()
            max_d = valid_dates.max().date()
            date_range = st.date_input("Rango de fechas", [min_d, max_d], min_value=min_d, max_value=max_d)
        else:
            date_range = None
    else:
        date_range = None

    all_cats = sorted(df_pagos['Categoría'].unique().tolist()) if not df_pagos.empty else []
    selected_cats = st.multiselect("Categorías", all_cats, default=all_cats)

    st.markdown("---")
    st.markdown("<i class='fas fa-file-contract' style='margin-right:6px; color:#81c784;'></i> **Contrato / Proveedor**", unsafe_allow_html=True)
    if not df_pagos.empty and 'Proveedor' in df_pagos.columns:
        all_proveedores = sorted(df_pagos['Proveedor'].dropna().unique().tolist())
    else:
        all_proveedores = []
    selected_proveedores = st.multiselect(
        "Seleccionar proveedores", all_proveedores, default=all_proveedores,
        help="Filtrar por contratista o proveedor específico"
    )

# ==================== APPLY FILTERS ====================
df_f = df_pagos.copy()
df_cube_f = df_cube.copy()

if not df_f.empty:
    if date_range and len(date_range) == 2:
        mask = df_f['Fecha'].notna()
        df_f = df_f[mask & (df_f['Fecha'].dt.date >= date_range[0]) & (df_f['Fecha'].dt.date <= date_range[1])]
    if selected_cats:
        df_f = df_f[df_f['Categoría'].isin(selected_cats)]
    if selected_proveedores and len(selected_proveedores) < len(all_proveedores):
        df_f = df_f[df_f['Proveedor'].isin(selected_proveedores)]

if not df_cube_f.empty:
    if date_range and len(date_range) == 2:
        mask_c = df_cube_f['date'].notna()
        df_cube_f = df_cube_f[mask_c & (df_cube_f['date'] >= date_range[0]) & (df_cube_f['date'] <= date_range[1])]
    # Note: df_cube_f['category'] uses the normalized categories, but for simplicity we match the sidebar selection.
    # The user wanted a flexible Category/Contractor filter.
    if selected_cats:
        # Match using str.contains so we get a flexible match
        pattern_cat = '|'.join(selected_cats).upper()
        df_cube_f = df_cube_f[df_cube_f['category'].str.contains(pattern_cat, na=False)]
    if selected_proveedores and len(selected_proveedores) < len(all_proveedores):
        pattern_prov = '|'.join([p.upper() for p in selected_proveedores])
        df_cube_f = df_cube_f[df_cube_f['contractor'].str.contains(pattern_prov, na=False)]

# ==================== COMPUTE METRICS ====================
total_pagado = df_f['Valor Neto'].sum() if not df_f.empty else 0
kpis = {}
for cat in ['Contratistas P.N.', 'Contratistas P.J.', 'Incentivos', 'Impuestos', 'Comisiones bancarias', 'Gastos de viaje']:
    kpis[cat] = df_f[df_f['Categoría'] == cat]['Valor Neto'].sum() if not df_f.empty else 0

ultimo_saldo = 0
if not df_balances.empty and 'Saldo Final' in df_balances.columns:
    vals = df_balances['Saldo Final']
    non_zero = vals[vals != 0]
    if not non_zero.empty:
        ultimo_saldo = non_zero.iloc[-1]

total_ingresos = df_ingresos['Valor'].sum() if not df_ingresos.empty else 0
disponible = total_ingresos - total_pagado
pct_ejec = (total_pagado / total_ingresos * 100) if total_ingresos > 0 else 0
presupuesto_total = sum(totals_cp.values()) if totals_cp else 0

try:
    n_months = df_f['Fecha'].dt.to_period('M').nunique() if not df_f.empty else 1
    avg_monthly = total_pagado / max(1, n_months)
    ratio_efectivo = round(ultimo_saldo / avg_monthly, 1) if avg_monthly > 0 else 0.0
    if not isinstance(ratio_efectivo, (int, float)) or str(ratio_efectivo) == 'nan':
        ratio_efectivo = 0.0
except Exception:
    ratio_efectivo = 0.0

# ==================== EXECUTIVE CHARTS (Helpers) ====================
def plot_donut(totals_by_category):
    df = pd.DataFrame(totals_by_category)
    if df.empty: return None
    import plotly.express as px
    fig = px.pie(df, values='amount', names='category', hole=0.6,
                 color_discrete_sequence=px.colors.sequential.Greens_r)
    fig.update_traces(textposition='inside', textinfo='percent+label',
                      hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}')
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(showlegend=False, height=300, margin=dict(l=20, r=20, t=20, b=20))
    return fig

def plot_gauge(ejecucion):
    import plotly.graph_objects as go
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = ejecucion,
        title = {'text': "Ejecución Presupuestal"},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgreen"},
            'bar': {'color': "#2e7d32"},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': 90}}))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def plot_monthly_evolution(monthly_evolution):
    if monthly_evolution.empty: return None
    import plotly.graph_objects as go
    fig = go.Figure()
    if 'INGRESO' in monthly_evolution.columns:
        fig.add_trace(go.Scatter(x=monthly_evolution['month_str'], y=monthly_evolution['INGRESO'],
                                 mode='lines+markers', name='Ingresos',
                                 line=dict(color='#43a047', width=3),
                                 fill='tozeroy', fillcolor='rgba(67,160,71,0.1)'))
    if 'EGRESO' in monthly_evolution.columns:
        fig.add_trace(go.Scatter(x=monthly_evolution['month_str'], y=monthly_evolution['EGRESO'],
                                 mode='lines+markers', name='Egresos',
                                 line=dict(color='#e53935', width=3),
                                 fill='tozeroy', fillcolor='rgba(229,57,53,0.1)'))
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_title='Mes', yaxis_title='Monto ($)', height=400)
    return fig

def plot_stacked_bars(df_cube_f):
    df = df_cube_f[df_cube_f['type'] == 'EGRESO'].copy()
    if df.empty: return None
    import plotly.express as px
    df['month_str'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
    grouped = df.groupby(['month_str', 'category'])['amount'].sum().reset_index()
    pivot = grouped.pivot(index='month_str', columns='category', values='amount').fillna(0)
    fig = px.bar(pivot, x=pivot.index, y=pivot.columns, labels={'value': 'Monto ($)', 'index': 'Mes'}, barmode='stack', color_discrete_sequence=COLORS)
    fig.update_layout(**PLOTLY_LAYOUT, height=400, xaxis_tickangle=-45)
    return fig

def plot_pareto(top_contractors):
    if top_contractors.empty: return None
    import plotly.graph_objects as go
    df = top_contractors.copy().head(15)
    total = df['total'].sum()
    if total <= 0: return None
    df['cum_percent'] = df['total'].cumsum() / total * 100
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['contractor'], y=df['total'], name='Monto', marker_color='#81c784'))
    fig.add_trace(go.Scatter(x=df['contractor'], y=df['cum_percent'], name='% Acumulado',
                             yaxis='y2', mode='lines+markers', line=dict(color='#ff8a65', width=2)))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(
        xaxis_title='Contratista',
        yaxis_title='Monto ($)',
        yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 110]),
        height=400,
        xaxis_tickangle=-45,
        margin=dict(r=50)
    )
    return fig

def plot_top_contractors(top_contractors, top_n=5):
    if top_contractors.empty: return None
    import plotly.express as px
    df = top_contractors.head(top_n).copy()
    df['label'] = df['contractor'].apply(lambda x: x[:20] + '...' if len(x) > 20 else x)
    df = df.sort_values('total', ascending=True)
    fig = px.bar(df, y='label', x='total', orientation='h', labels={'total': 'Monto ($)', 'label': 'Contratista'}, color='total', color_continuous_scale='Greens')
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(height=400, margin=dict(l=0, r=0))
    return fig

def plot_cashflow(df_cashflow):
    if df_cashflow.empty: return None
    import plotly.express as px
    fig = px.area(df_cashflow, x='Periodo', y='Saldo Proyectado', labels={'Saldo Proyectado': 'Saldo ($)'}, color_discrete_sequence=['#43a047'])
    fig.update_layout(**PLOTLY_LAYOUT, height=350)
    return fig

# Generar el sumario global basado en datos filtrados
summary = get_financial_summary(df_cube_f, {})

# ==================== TABS ====================
tab1, tab2, tab3 = st.tabs(["📊 Panel General", "📈 Estado de Resultados", "🔍 Análisis Avanzado"])

# ================================================================
#                    TAB 1: PANEL GENERAL
# ================================================================
with tab1:
    # --- TOP KPI ROW ---
    kpi_data = [
        ('fa-money-bill-wave', 'Total Pagado', fmt_money(summary['kpis']['egresos'])),
        ('fa-chart-line', 'Total Ingresos', fmt_money(summary['kpis']['ingresos'])),
        ('fa-coins', 'Saldo Disponible', fmt_money(summary['kpis']['balance'])),
        ('fa-university', 'Saldo Bancario', fmt_money(ultimo_saldo)),
        ('fa-gauge-high', '% Ejecución', f'{summary["kpis"]["ejecucion"]:.1f}%'),
        ('fa-clock', 'Ratio Efectivo', f'{ratio_efectivo:.1f} meses'),
    ]
    kpi_html = '<div class="kpi-row">'
    for icon, label, val in kpi_data:
        kpi_html += f'''<div class="kpi-box">
            <div class="kpi-icon"><i class="fas {icon}"></i></div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-val">{val}</div>
        </div>'''
    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- EXECUTIVE CHARTS ---
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### <i class='fas fa-chart-pie section-title'></i> Distribución por Categoría", unsafe_allow_html=True)
        st.plotly_chart(plot_donut(summary['totals_by_category']), use_container_width=True)
    with col2:
        st.markdown("#### <i class='fas fa-gauge section-title'></i> Ejecución Presupuestal", unsafe_allow_html=True)
        st.plotly_chart(plot_gauge(summary['kpis']['ejecucion']), use_container_width=True)
    
    st.markdown("#### <i class='fas fa-layer-group section-title'></i> Ingresos vs Egresos (Evolución)", unsafe_allow_html=True)
    st.plotly_chart(plot_monthly_evolution(summary['monthly_evolution']), use_container_width=True)
    
    st.markdown("#### <i class='fas fa-chart-bar section-title'></i> Egresos por Categoría", unsafe_allow_html=True)
    st.plotly_chart(plot_stacked_bars(df_cube_f), use_container_width=True)
    
    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### <i class='fas fa-chart-area section-title'></i> Pareto de Contratistas", unsafe_allow_html=True)
        st.plotly_chart(plot_pareto(summary['top_contractors']), use_container_width=True)
    with col4:
        st.markdown("#### <i class='fas fa-ranking-star section-title'></i> Top 5 Contratistas", unsafe_allow_html=True)
        st.plotly_chart(plot_top_contractors(summary['top_contractors']), use_container_width=True)
        
    if not df_cashflow.empty:
        st.markdown("---")
        st.markdown("#### <i class='fas fa-money-bill-transfer section-title'></i> Flujo de Caja (FIDUCOLDEX)", unsafe_allow_html=True)
        st.plotly_chart(plot_cashflow(df_cashflow), use_container_width=True)

    # --- INTERACTIVE ALERTS ---
    st.markdown("---")

    # Initialize dismissed alerts in session state
    if 'dismissed_alerts' not in st.session_state:
        st.session_state.dismissed_alerts = set()

    # Generate alerts with IDs
    alerts = []
    now_str = datetime.now().strftime('%H:%M')

    if not df_pagos.empty:
        hoy = datetime.now().date()
        futuros = df_pagos[df_pagos['Fecha'].notna() & (df_pagos['Fecha'].dt.date > hoy)]
        if not futuros.empty:
            alerts.append({
                'id': 'future_payments',
                'type': 'info',
                'icon': 'fa-calendar-day',
                'title': 'Pagos Programados',
                'msg': f'Hay <b>{len(futuros)}</b> pagos programados por un total de <b>{fmt_money(futuros["Valor Neto"].sum())}</b>. Verifique las fechas de vencimiento.',
            })
        prox = df_pagos[(df_pagos['Fecha'].notna()) & (df_pagos['Fecha'].dt.date > hoy) & (df_pagos['Fecha'].dt.date <= hoy + timedelta(days=30))]
        if not prox.empty:
            alerts.append({
                'id': 'urgent_30d',
                'type': 'danger',
                'icon': 'fa-exclamation-triangle',
                'title': 'Pagos Urgentes (30 días)',
                'msg': f'<b>{len(prox)}</b> pagos vencen en los próximos 30 días por <b>{fmt_money(prox["Valor Neto"].sum())}</b>. Requiere atención inmediata.',
            })

    # Intelligent alerts based on analytical properties
    ejecucion_pct = summary['kpis']['ejecucion']
    if ejecucion_pct > 100:
        alerts.append({
            'id': 'over_budget', 'type': 'danger', 'icon': 'fa-triangle-exclamation',
            'title': 'Sobreejecución Presupuestal',
            'msg': f'La ejecución global supera el 100% (<b>{ejecucion_pct:.1f}%</b>). Se requiere revisión urgente de los egresos.'
        })
    elif ejecucion_pct > 90:
        alerts.append({
            'id': 'high_budget', 'type': 'warning', 'icon': 'fa-engine-warning',
            'title': 'Ejecución Alta',
            'msg': f'La ejecución está cerca del límite (<b>{ejecucion_pct:.1f}%</b>). Controle el gasto en el próximo ciclo.'
        })

    if not summary['top_contractors'].empty and summary['kpis']['egresos'] > 0:
        top_row = summary['top_contractors'].iloc[0]
        pct_concentration = (top_row['total'] / summary['kpis']['egresos']) * 100
        if pct_concentration > 40:
             alerts.append({
                'id': 'concentration_risk', 'type': 'warning', 'icon': 'fa-scale-unbalanced',
                'title': 'Alta Concentración de Gasto',
                'msg': f'El proveedor <b>{top_row["contractor"]}</b> concentra el <b>{pct_concentration:.0f}%</b> ({fmt_money(top_row["total"])}) de los egresos filtrados.'
            })

    if totals_cp:
        for cat, presup in totals_cp.items():
            if presup > 0:
                real = df_pagos[df_pagos['Categoría'].str.contains(cat, case=False, na=False)]['Valor Neto'].sum() if not df_pagos.empty else 0
                if real > 0:
                    p = real / presup * 100
                    if p > 100:
                        alerts.append({
                            'id': f'over_{cat}',
                            'type': 'danger',
                            'icon': 'fa-triangle-exclamation',
                            'title': f'{cat} — Sobrepresupuesto',
                            'msg': f'Ejecucion al <b>{p:.0f}%</b> (${real:,.0f} de ${presup:,.0f}). Se ha excedido el presupuesto asignado.',
                        })
                    elif p > 90:
                        alerts.append({
                            'id': f'near_{cat}',
                            'type': 'warning',
                            'icon': 'fa-bolt',
                            'title': f'{cat} — Cerca del Limite',
                            'msg': f'Ejecucion al <b>{p:.0f}%</b>. Queda <b>{fmt_money(presup - real)}</b> disponible.',
                        })

    if pct_ejec > 0:
        if pct_ejec > 90:
            alerts.append({
                'id': 'exec_high',
                'type': 'warning',
                'icon': 'fa-gauge-high',
                'title': 'Presupuesto Casi Agotado',
                'msg': f'Ejecucion general al <b>{pct_ejec:.1f}%</b>. Queda <b>{fmt_money(disponible)}</b> disponible.',
            })
        elif pct_ejec < 30:
            alerts.append({
                'id': 'exec_ok',
                'type': 'success',
                'icon': 'fa-check-circle',
                'title': 'Ejecucion Saludable',
                'msg': f'Ejecucion al <b>{pct_ejec:.1f}%</b>. Amplio margen presupuestal con <b>{fmt_money(disponible)}</b> disponible.',
            })

    # Add insight alerts
    if not df_f.empty:
        top_prov = df_f.groupby('Proveedor')['Valor Neto'].sum()
        if not top_prov.empty:
            top_name = top_prov.idxmax()
            top_val = top_prov.max()
            top_pct = (top_val / total_pagado * 100) if total_pagado > 0 else 0
            if top_pct > 30:
                alerts.append({
                    'id': 'concentration',
                    'type': 'info',
                    'icon': 'fa-magnifying-glass-chart',
                    'title': 'Concentracion de Pagos',
                    'msg': f'<b>{top_name[:30]}</b> concentra el <b>{top_pct:.0f}%</b> del total pagado ({fmt_money(top_val)}). Considere diversificar proveedores.',
                })

    # Filter out dismissed alerts
    visible_alerts = [a for a in alerts if a['id'] not in st.session_state.dismissed_alerts]
    total_alerts = len(alerts)
    dismissed_count = total_alerts - len(visible_alerts)

    # Header with counter
    counter_class = 'clear' if not visible_alerts else ''
    counter_text = f'{len(visible_alerts)} activa{"s" if len(visible_alerts) != 1 else ""}' if visible_alerts else 'Sin alertas'
    st.markdown(f'''<div class="alerts-header">
        <span style="font-size:1rem; color:#e0f2e0;"><i class="fas fa-bell" style="margin-right:8px; color:#81c784;"></i> <b>Alertas y Recomendaciones</b></span>
        <span class="alerts-counter {counter_class}"><i class="fas fa-circle-dot" style="font-size:0.5rem; margin-right:4px;"></i> {counter_text}</span>
    </div>''', unsafe_allow_html=True)

    if not visible_alerts:
        st.markdown('''<div class="alert-toast success" style="border-left-color:#4caf50;">
            <div class="at-badge success"><i class="fas fa-shield-check"></i></div>
            <div class="at-content">
                <div class="at-title">Todo en orden</div>
                <div class="at-msg">No hay alertas activas. El estado financiero del proyecto se encuentra dentro de los parametros normales.</div>
            </div>
        </div>''', unsafe_allow_html=True)
    else:
        for i, alert in enumerate(visible_alerts):
            # Render the alert toast
            st.markdown(f'''<div class="alert-toast {alert["type"]}" style="animation-delay:{i*0.1}s;">
                <div class="at-badge {alert["type"]}"><i class="fas {alert["icon"]}"></i></div>
                <div class="at-content">
                    <div class="at-title">{alert["title"]}</div>
                    <div class="at-msg">{alert["msg"]}</div>
                    <div class="at-time"><i class="far fa-clock" style="margin-right:4px;"></i> Hoy {now_str}</div>
                </div>
            </div>''', unsafe_allow_html=True)

            # Dismiss button (Streamlit native — updates session state)
            if st.button(f"Cerrar", key=f"dismiss_{alert['id']}", type="secondary"):
                st.session_state.dismissed_alerts.add(alert['id'])
                st.rerun()

    # Show restore option if any alerts were dismissed
    if dismissed_count > 0:
        col_restore, _ = st.columns([1, 3])
        with col_restore:
            if st.button(f"Restaurar {dismissed_count} alerta{'s' if dismissed_count > 1 else ''}", type="secondary"):
                st.session_state.dismissed_alerts.clear()
                st.rerun()

    # --- DETAIL TABLES ---
    st.markdown("---")
    with st.expander("Ver tabla detallada de pagos"):
        if not df_f.empty:
            display_cols = [c for c in ['Proveedor', 'Valor Bruto', 'Valor Neto', 'Fecha', 'Categoría', 'Origen'] if c in df_f.columns]
            df_display = df_f[display_cols].sort_values('Fecha', ascending=False, na_position='last')
            st.dataframe(df_display, use_container_width=True, height=400)
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", data=csv, file_name="pagos_consolidados.csv", mime="text/csv")
        else:
            st.info("Sin datos")

    if totals_cp:
        with st.expander("Resumen de GASTOS CP (presupuesto)"):
            df_cp = pd.DataFrame(list(totals_cp.items()), columns=['Categoría', 'Valor Presupuesto'])
            df_cp['Valor Presupuesto'] = df_cp['Valor Presupuesto'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(df_cp, use_container_width=True)


# ================================================================
#               TAB 2: ESTADO DE RESULTADOS
# ================================================================
with tab2:
    st.markdown("#### <i class='fas fa-chart-line section-title'></i> Estado de Resultados", unsafe_allow_html=True)

    # Classify costs
    costos_directos = kpis.get('Contratistas P.N.', 0) + kpis.get('Contratistas P.J.', 0) + kpis.get('Incentivos', 0)
    gastos_admin = kpis.get('Comisiones bancarias', 0) + kpis.get('Gastos de viaje', 0)
    impuestos_total = kpis.get('Impuestos', 0)

    utilidad_bruta = total_ingresos - costos_directos
    utilidad_operativa = utilidad_bruta - gastos_admin
    utilidad_neta = utilidad_operativa - impuestos_total

    margen_bruto = (utilidad_bruta / total_ingresos * 100) if total_ingresos > 0 else 0
    margen_operativo = (utilidad_operativa / total_ingresos * 100) if total_ingresos > 0 else 0
    margen_neto = (utilidad_neta / total_ingresos * 100) if total_ingresos > 0 else 0

    # --- KPI Cards Row (individual columns to avoid HTML truncation) ---
    result_kpis = [
        ('fa-money-bill-trend-up', 'Utilidad Neta', fmt_money(utilidad_neta), f'{margen_neto:.1f}%', 'Margen Neto'),
        ('fa-hand-holding-dollar', 'Ingresos Totales', fmt_money(total_ingresos), '', ''),
        ('fa-file-invoice', 'Costos Directos', fmt_money(costos_directos), '', ''),
        ('fa-landmark', 'Utilidad Antes Imp.', fmt_money(utilidad_operativa), f'{margen_operativo:.1f}%', 'Margen Op.'),
        ('fa-receipt', 'Impuestos', fmt_money(impuestos_total), '', ''),
    ]
    kpi_cols = st.columns(len(result_kpis))
    for col, (icon, label, val, pct, pct_label) in zip(kpi_cols, result_kpis):
        extra_html = f'<div style="font-size:0.65rem;color:#a5d6a7;margin-top:0.2rem">{pct_label} <b>{pct}</b></div>' if pct else ''
        card_html = (
            f'<div class="kpi-box">'
            f'<div class="kpi-icon"><i class="fas {icon}"></i></div>'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-val">{val}</div>'
            f'{extra_html}'
            f'</div>'
        )
        with col:
            st.markdown(card_html, unsafe_allow_html=True)

    # --- Utilidades detalladas ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div style='font-size:0.85rem; color:#a5d6a7; margin-bottom:0.5rem;'><i class='fas fa-chart-waterfall' style='margin-right:6px;'></i> <b>Cascada de Utilidades</b></div>", unsafe_allow_html=True)
        fig = go.Figure(go.Waterfall(
            name="", orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=["Ingresos", "(-) Costos<br>Directos", "(-) Gastos<br>Admin", "(-) Impuestos", "Utilidad<br>Neta"],
            y=[total_ingresos, -costos_directos, -gastos_admin, -impuestos_total, utilidad_neta],
            connector={"line": {"color": "rgba(46,125,50,0.3)"}},
            decreasing={"marker": {"color": "#ff8a65"}},
            increasing={"marker": {"color": "#43a047"}},
            totals={"marker": {"color": "#81c784"}},
            textposition="outside",
            text=[fmt_money(total_ingresos), fmt_money(-costos_directos), fmt_money(-gastos_admin), fmt_money(-impuestos_total), fmt_money(utilidad_neta)],
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div style='font-size:0.85rem; color:#a5d6a7; margin-bottom:0.5rem;'><i class='fas fa-chart-pie' style='margin-right:6px;'></i> <b>Composición de Egresos</b></div>", unsafe_allow_html=True)
        egresos_data = {
            'Contratistas P.N.': kpis.get('Contratistas P.N.', 0),
            'Contratistas P.J.': kpis.get('Contratistas P.J.', 0),
            'Incentivos': kpis.get('Incentivos', 0),
            'Impuestos': kpis.get('Impuestos', 0),
            'Comisiones': kpis.get('Comisiones bancarias', 0),
            'Viajes': kpis.get('Gastos de viaje', 0),
        }
        egresos_data = {k: v for k, v in egresos_data.items() if v > 0}
        if egresos_data:
            fig = px.pie(names=list(egresos_data.keys()), values=list(egresos_data.values()),
                         hole=0.5, color_discrete_sequence=COLORS)
            fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=True)
            fig.update_traces(textposition='inside', textinfo='percent+label',
                              hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}')
            st.plotly_chart(fig, use_container_width=True)

    # --- Evolución Mensual Ingresos vs Egresos ---
    st.markdown("#### <i class='fas fa-chart-area section-title'></i> Evolución Mensual: Ingresos vs Egresos", unsafe_allow_html=True)
    if not df_f.empty:
        df_m = df_f.dropna(subset=['Fecha']).copy()
        if not df_m.empty:
            df_m['Periodo'] = df_m['Fecha'].dt.to_period('M').astype(str)
            egresos_mens = df_m.groupby('Periodo')['Valor Neto'].sum().reset_index()
            egresos_mens.columns = ['Periodo', 'Egresos']

            # Try to get monthly income
            if not df_ingresos.empty and 'Fecha' in df_ingresos.columns:
                df_ing_m = df_ingresos.dropna(subset=['Fecha']).copy()
                if not df_ing_m.empty:
                    df_ing_m['Periodo'] = df_ing_m['Fecha'].dt.to_period('M').astype(str)
                    ingresos_mens = df_ing_m.groupby('Periodo')['Valor'].sum().reset_index()
                    ingresos_mens.columns = ['Periodo', 'Ingresos']
                    merged = pd.merge(egresos_mens, ingresos_mens, on='Periodo', how='outer').fillna(0).sort_values('Periodo')
                else:
                    merged = egresos_mens.copy()
                    merged['Ingresos'] = 0
            else:
                merged = egresos_mens.copy()
                merged['Ingresos'] = 0

            fig = go.Figure()
            if 'Ingresos' in merged.columns:
                fig.add_trace(go.Scatter(x=merged['Periodo'], y=merged['Ingresos'], mode='lines+markers',
                                          name='Ingresos', line=dict(color='#43a047', width=3),
                                          marker=dict(size=8), fill='tozeroy', fillcolor='rgba(67,160,71,0.1)'))
            fig.add_trace(go.Scatter(x=merged['Periodo'], y=merged['Egresos'], mode='lines+markers',
                                      name='Egresos', line=dict(color='#ff8a65', width=3),
                                      marker=dict(size=8), fill='tozeroy', fillcolor='rgba(255,138,101,0.1)'))
            fig.update_layout(**PLOTLY_LAYOUT, height=380, xaxis_title='Mes', yaxis_title='Monto ($)', xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # --- Bottom KPI cards: Deuda, Gastos Fijos, Punto de Equilibrio ---
    st.markdown("---")
    c1, c2, c3 = st.columns(3)

    gastos_fijos = kpis.get('Comisiones bancarias', 0) + kpis.get('Impuestos', 0)
    punto_equilibrio = gastos_fijos / (1 - costos_directos / total_ingresos) if total_ingresos > 0 and (1 - costos_directos / total_ingresos) > 0 else 0

    with c1:
        st.markdown(f'''<div class="metric-card">
            <div class="metric-icon"><i class="fas fa-file-invoice-dollar"></i></div>
            <div class="metric-label">Deuda / Compromisos</div>
            <div class="metric-value">{fmt_money(total_pagado - ultimo_saldo if total_pagado > ultimo_saldo else 0)}</div>
        </div>''', unsafe_allow_html=True)

    with c2:
        st.markdown(f'''<div class="metric-card">
            <div class="metric-icon"><i class="fas fa-building-columns"></i></div>
            <div class="metric-label">Gastos Fijos</div>
            <div class="metric-value">{fmt_money(gastos_fijos)}</div>
        </div>''', unsafe_allow_html=True)

    with c3:
        st.markdown(f'''<div class="metric-card">
            <div class="metric-icon"><i class="fas fa-crosshairs"></i></div>
            <div class="metric-label">Punto de Equilibrio</div>
            <div class="metric-value">{fmt_money(punto_equilibrio)}</div>
        </div>''', unsafe_allow_html=True)

# ================================================================
#                    TAB 3: ANÁLISIS AVANZADO
# ================================================================
with tab3:
    st.markdown("<div style='margin-bottom:1rem;'><h3 style='color:#4caf50;'><i class='fas fa-search-dollar' style='margin-right:8px;'></i> Motor Analítico: Filtros Avanzados</h3></div>", unsafe_allow_html=True)
    
    if df_cube_f.empty:
        st.info("No hay datos para los filtros seleccionados.")
    else:
        # Build summary using get_financial_summary
        summary_filters = {}
        if date_range and len(date_range) == 2:
            summary_filters['start_date'] = date_range[0]
            summary_filters['end_date'] = date_range[1]
        if selected_proveedores and len(selected_proveedores) < len(all_proveedores):
            summary_filters['contractors'] = selected_proveedores
        if selected_cats:
            summary_filters['categories'] = selected_cats
        
        summary = get_financial_summary(df_cube, summary_filters)
        s_kpis = summary['kpis']
        
        # --- KPI Row: Ingresos / Egresos / Balance ---
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        with kpi_col1:
            st.markdown(f'''<div class="metric-card">
                <div class="metric-icon" style="color:#43a047;"><i class="fas fa-arrow-down"></i></div>
                <div class="metric-label">Ingresos</div>
                <div class="metric-value" style="color:#43a047;">{fmt_money(s_kpis['ingresos'])}</div>
            </div>''', unsafe_allow_html=True)
        with kpi_col2:
            st.markdown(f'''<div class="metric-card">
                <div class="metric-icon" style="color:#e53935;"><i class="fas fa-arrow-up"></i></div>
                <div class="metric-label">Egresos</div>
                <div class="metric-value" style="color:#e53935;">{fmt_money(s_kpis['egresos'])}</div>
            </div>''', unsafe_allow_html=True)
        with kpi_col3:
            bal_color = '#43a047' if s_kpis['balance'] >= 0 else '#e53935'
            st.markdown(f'''<div class="metric-card">
                <div class="metric-icon" style="color:{bal_color};"><i class="fas fa-scale-balanced"></i></div>
                <div class="metric-label">Balance</div>
                <div class="metric-value" style="color:{bal_color};">{fmt_money(s_kpis['balance'])}</div>
            </div>''', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- Evolución Mensual Ingresos vs Egresos ---
        monthly_data = summary['monthly_by_category']
        if monthly_data:
            df_evol = pd.DataFrame(monthly_data)
            df_ing_m = df_evol[df_evol['type'] == 'INGRESO'].sort_values('month')
            df_egr_m = df_evol[df_evol['type'] == 'EGRESO'].sort_values('month')
            
            fig_evol = go.Figure()
            if not df_ing_m.empty:
                fig_evol.add_trace(go.Scatter(x=df_ing_m['month'], y=df_ing_m['total'], mode='lines+markers',
                    name='Ingresos', line=dict(color='#43a047', width=3), fill='tozeroy', fillcolor='rgba(67,160,71,0.1)'))
            if not df_egr_m.empty:
                fig_evol.add_trace(go.Scatter(x=df_egr_m['month'], y=df_egr_m['total'], mode='lines+markers',
                    name='Egresos', line=dict(color='#e53935', width=3), fill='tozeroy', fillcolor='rgba(229,57,53,0.1)'))
            fig_evol.update_layout(**PLOTLY_LAYOUT, height=350, title='Evolución Mensual: Ingresos vs Egresos',
                xaxis_title='Mes', yaxis_title='Monto ($)')
            st.plotly_chart(fig_evol, use_container_width=True)
        
        st.markdown("---")
        
        # --- Alertas Manuales del Analista ---
        if st.session_state.alertas_manuales:
            st.markdown("<h4 style='color:#ffb74d;'><i class='fas fa-bell' style='margin-right:6px;'></i> Alertas del Analista</h4>", unsafe_allow_html=True)
            for i, alerta in enumerate(st.session_state.alertas_manuales):
                tipo_icon = {'Peligro': 'fa-circle-exclamation', 'Advertencia': 'fa-triangle-exclamation', 'Información': 'fa-circle-info'}
                tipo_color = {'Peligro': '#e53935', 'Advertencia': '#ffb74d', 'Información': '#42a5f5'}
                icon = tipo_icon.get(alerta['tipo'], 'fa-circle-info')
                color = tipo_color.get(alerta['tipo'], '#42a5f5')
                st.markdown(f'''<div style="background:rgba(255,255,255,0.05); border-left:4px solid {color}; padding:0.8rem 1rem; border-radius:8px; margin-bottom:0.5rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <i class="fas {icon}" style="color:{color}; margin-right:8px;"></i>
                            <b style="color:{color};">{alerta['tipo']}</b>
                            <span style="color:#a5d6a7; margin-left:8px;">({alerta['contratista']})</span>
                        </div>
                        <span style="color:#666; font-size:0.7rem;">{alerta['fecha']}</span>
                    </div>
                    <div style="color:#e0f2e0; margin-top:4px; font-size:0.85rem;">{alerta['mensaje']}</div>
                </div>''', unsafe_allow_html=True)
            st.markdown("---")
        
        # --- Columns: Tabla Detalle + Consolidado ---
        col_detail, col_cons = st.columns([1.5, 1])
        
        with col_detail:
            st.markdown("<h4 style='color:#e0f2e0;'><i class='fas fa-table' style='margin-right:6px;'></i> Detalle Mensual por Contratista</h4>", unsafe_allow_html=True)
            detail_data = summary['detail']
            if detail_data:
                df_det = pd.DataFrame(detail_data)
                df_det = df_det.sort_values(['contractor', 'month'])
                df_det.columns = ['Contratista', 'Mes', 'Categoría', 'Tipo', 'Total']
                df_det_disp = df_det.copy()
                df_det_disp['Total'] = df_det_disp['Total'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df_det_disp, use_container_width=True, hide_index=True, height=400)
            else:
                st.info("No hay detalle para los filtros seleccionados.")
        
        with col_cons:
            st.markdown("<h4 style='color:#e0f2e0;'><i class='fas fa-chart-pie' style='margin-right:6px;'></i> Consolidado por Categoría</h4>", unsafe_allow_html=True)
            totals_data = summary['totals_by_category']
            if totals_data:
                df_tots = pd.DataFrame(totals_data)
                df_egresos_only = df_tots[df_tots['type'] == 'EGRESO']
                if not df_egresos_only.empty:
                    fig_dona = px.pie(df_egresos_only, values='total', names='category', hole=0.65,
                        color_discrete_sequence=px.colors.sequential.Greens_r)
                    fig_dona.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=True)
                    st.plotly_chart(fig_dona, use_container_width=True)
                
                df_tots.columns = ['Categoría', 'Tipo', 'Total']
                df_tots_disp = df_tots.copy()
                df_tots_disp['Total'] = df_tots_disp['Total'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df_tots_disp, use_container_width=True, hide_index=True)
            else:
                st.info("No hay consolidado para los filtros seleccionados.")

# ==================== SIDEBAR: ALERTAS MANUALES ====================
with st.sidebar:
    st.markdown("---")
    st.markdown("### <i class='fas fa-bell' style='margin-right:6px; color:#ffb74d;'></i> Alertas Manuales", unsafe_allow_html=True)
    with st.expander("➕ Agregar Alerta"):
        all_proveedores_ext = ['General'] + all_proveedores
        tipo_alerta = st.selectbox("Severidad", ["Peligro", "Advertencia", "Información"])
        contratista_alerta = st.selectbox("Contratista / Proveedor", options=all_proveedores_ext)
        mensaje_alerta = st.text_area("Mensaje de alerta", placeholder="Ej: Falta RUT del proveedor...")
        if st.button("Guardar Alerta", use_container_width=True):
            if mensaje_alerta.strip():
                st.session_state.alertas_manuales.append({
                    'tipo': tipo_alerta,
                    'contratista': contratista_alerta,
                    'mensaje': mensaje_alerta.strip(),
                    'fecha': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
                audit_log(user, 'MANUAL_ALERT', f'tipo={tipo_alerta} contratista={contratista_alerta}')
                st.success("Alerta guardada")
                st.rerun()
            else:
                st.warning("Escribe un mensaje para la alerta")
    
    # Show count
    n_alertas = len(st.session_state.alertas_manuales)
    if n_alertas > 0:
        st.markdown(f"<div style='text-align:center; color:#ffb74d; font-size:0.8rem;'>{n_alertas} alerta{'s' if n_alertas > 1 else ''} activa{'s' if n_alertas > 1 else ''}</div>", unsafe_allow_html=True)
        if st.button("🗑️ Limpiar todas", use_container_width=True):
            st.session_state.alertas_manuales = []
            st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align:center; opacity:0.5; font-size:0.8rem; padding:1rem;">
    <i class="fas fa-leaf" style="margin-right:6px;"></i> CONSERVAR PAGA — Dashboard de Control Financiero<br>
    <i class="fas fa-shield-halved" style="margin-right:4px;"></i> Sesion segura · Ley Colombiana · OWASP Top 10
</div>
""", unsafe_allow_html=True)

