"""
styles.py — CSS, HTML templates y constantes de diseño.
CONSERVAR PAGA — Dashboard de Control Financiero
"""

# ==================== PALETA DE COLORES ====================
COLORS = ['#2e7d32', '#43a047', '#66bb6a', '#81c784', '#a5d6a7', '#c8e6c9', '#ffb74d', '#ff8a65']
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Poppins', color='#e0f2e0'),
    legend=dict(bgcolor='rgba(0,0,0,0)'),
    margin=dict(l=40, r=20, t=50, b=40),
)

# ==================== FONT AWESOME CDN ====================
FA_CDN = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'

# ==================== CSS PRINCIPAL ====================
MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
* { font-family: 'Poppins', sans-serif; }

/* ---- Top KPI Row (compact) ---- */
.kpi-row { display: flex; gap: 10px; margin-bottom: 1rem; flex-wrap: wrap; }
.kpi-box {
    flex: 1; min-width: 130px;
    background: rgba(30, 50, 30, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(46,125,50,0.3);
    border-radius: 14px; padding: 0.8rem 0.6rem;
    text-align: center; transition: all 0.3s ease;
}
.kpi-box:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(46,125,50,0.2); border-color: #4caf50; }
.kpi-box .kpi-icon { font-size: 1.1rem; color: #66bb6a; margin-bottom: 0.2rem; }
.kpi-box .kpi-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.2px; color: #a5d6a7; opacity: 0.85; }
.kpi-box .kpi-val { font-size: 1.3rem; font-weight: 700; color: #81c784; }

/* ---- Large Summary Panel ---- */
.summary-panel {
    background: rgba(20, 40, 20, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(46,125,50,0.3);
    border-radius: 18px; padding: 1.5rem;
    margin-bottom: 1rem;
}
.summary-panel .big-number { font-size: 2.2rem; font-weight: 700; color: #81c784; margin: 0.3rem 0; }
.summary-panel .big-label { font-size: 0.85rem; color: #a5d6a7; text-transform: uppercase; letter-spacing: 1px; }

/* ---- Sub-metric with progress bar ---- */
.sub-metric {
    display: flex; align-items: center; gap: 12px;
    padding: 0.6rem 0; border-bottom: 1px solid rgba(46,125,50,0.15);
}
.sub-metric:last-child { border-bottom: none; }
.sub-metric .sm-icon {
    width: 36px; height: 36px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; flex-shrink: 0;
}
.sm-icon.green  { background: rgba(46,125,50,0.25); color: #66bb6a; }
.sm-icon.blue   { background: rgba(33,150,243,0.2);  color: #64b5f6; }
.sm-icon.orange { background: rgba(255,152,0,0.2);   color: #ffb74d; }
.sm-icon.purple { background: rgba(156,39,176,0.2);  color: #ce93d8; }
.sm-icon.red    { background: rgba(244,67,54,0.15);  color: #ef9a9a; }
.sub-metric .sm-info { flex: 1; }
.sub-metric .sm-label { font-size: 0.75rem; color: #a5d6a7; }
.sub-metric .sm-val { font-size: 1.05rem; font-weight: 600; color: #e0f2e0; }
.sub-metric .sm-pct { font-size: 0.7rem; color: #81c784; }

/* ---- Progress Bar ---- */
.progress-wrap {
    height: 6px; background: rgba(255,255,255,0.08);
    border-radius: 3px; overflow: hidden; margin-top: 4px;
}
.progress-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
.pf-green  { background: linear-gradient(90deg, #2e7d32, #66bb6a); }
.pf-blue   { background: linear-gradient(90deg, #1565c0, #64b5f6); }
.pf-orange { background: linear-gradient(90deg, #e65100, #ffb74d); }
.pf-purple { background: linear-gradient(90deg, #6a1b9a, #ce93d8); }
.pf-red    { background: linear-gradient(90deg, #c62828, #ef9a9a); }

/* ---- Target Comparison Card ---- */
.target-card {
    background: rgba(30, 50, 30, 0.55);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(46,125,50,0.25);
    border-radius: 14px; padding: 1rem; text-align: center;
    margin-bottom: 0.5rem; transition: all 0.3s ease;
}
.target-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(46,125,50,0.18); }
.target-card .tc-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; color: #a5d6a7; margin-bottom: 0.3rem; }
.target-card .tc-val { font-size: 1.4rem; font-weight: 700; color: #81c784; }
.target-card .tc-diff { font-size: 0.7rem; margin-top: 0.2rem; }
.tc-diff.positive { color: #66bb6a; }
.tc-diff.negative { color: #ef9a9a; }

/* ---- Horizontal Bar Item ---- */
.hbar-item { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.hbar-item .hbar-label { font-size: 0.7rem; color: #c8e6c9; width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 0; }
.hbar-item .hbar-track { flex: 1; height: 16px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; position: relative; }
.hbar-item .hbar-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px; font-size: 0.6rem; color: white; font-weight: 600; }
.hbar-item .hbar-pct { font-size: 0.65rem; color: #a5d6a7; width: 45px; text-align: right; flex-shrink: 0; }

/* ---- Metric Card ---- */
.metric-card {
    background: rgba(30, 50, 30, 0.6);
    backdrop-filter: blur(10px);
    border-radius: 20px; padding: 1.2rem 1.5rem;
    border: 1px solid rgba(46, 125, 50, 0.3);
    transition: all 0.3s ease; text-align: center; margin-bottom: 0.5rem;
}
.metric-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(46,125,50,0.25); border-color: #4caf50; }
.metric-value { font-size: 1.6rem; font-weight: 700; color: #81c784; margin: 0.3rem 0; }
.metric-label { font-size: 0.8rem; font-weight: 400; text-transform: uppercase; letter-spacing: 1.5px; color: #a5d6a7; opacity: 0.85; }
.metric-icon { font-size: 1.6rem; margin-bottom: 0.3rem; color: #66bb6a; }
.metric-card i { font-size: 1.4rem; vertical-align: middle; }

/* ---- Interactive Alert Toasts ---- */
@keyframes slideInRight { from { transform:translateX(40px); opacity:0; } to { transform:translateX(0); opacity:1; } }
@keyframes fadeOut { from { opacity:1; max-height:200px; } to { opacity:0; max-height:0; padding:0; margin:0; border:0; } }
.alert-toast {
    display: flex; align-items: flex-start; gap: 12px;
    background: rgba(20, 40, 20, 0.85); backdrop-filter: blur(12px);
    border-radius: 14px; padding: 1rem 1.2rem; margin: 0.6rem 0;
    border-left: 4px solid #ffc107; position: relative;
    animation: slideInRight 0.4s ease-out forwards;
    transition: all 0.3s ease;
}
.alert-toast:hover { transform: translateX(4px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }
.alert-toast.warning { border-left-color: #ffc107; }
.alert-toast.danger { border-left-color: #f44336; }
.alert-toast.success { border-left-color: #4caf50; }
.alert-toast.info { border-left-color: #29b6f6; }
.alert-toast .at-badge {
    width: 40px; height: 40px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.at-badge.warning { background: rgba(255,193,7,0.15); color: #ffd54f; }
.at-badge.danger  { background: rgba(244,67,54,0.15); color: #ef9a9a; }
.at-badge.success { background: rgba(76,175,80,0.15); color: #81c784; }
.at-badge.info    { background: rgba(41,182,246,0.15); color: #81d4fa; }
.alert-toast .at-content { flex: 1; }
.alert-toast .at-title { font-size: 0.8rem; font-weight: 600; color: #e0f2e0; margin-bottom: 2px; }
.alert-toast .at-msg { font-size: 0.73rem; color: #a5d6a7; line-height: 1.4; }
.alert-toast .at-time { font-size: 0.6rem; color: rgba(165,214,167,0.5); margin-top: 4px; }
.alert-toast .at-actions { display: flex; gap: 6px; margin-top: 6px; }
.at-actions .at-btn {
    font-size: 0.65rem; padding: 3px 10px; border-radius: 6px; cursor: pointer;
    border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05);
    color: #a5d6a7; transition: all 0.2s;
}
.at-actions .at-btn:hover { background: rgba(46,125,50,0.3); border-color: #4caf50; }
.alerts-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }
.alerts-counter {
    font-size: 0.7rem; background: rgba(255,193,7,0.15); color: #ffd54f;
    padding: 2px 10px; border-radius: 10px; font-weight: 600;
}
.alerts-counter.clear { background: rgba(76,175,80,0.15); color: #81c784; }

/* ---- Header Bar ---- */
.header-bar {
    background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #43a047 100%);
    padding: 1.2rem 2rem; border-radius: 16px; margin-bottom: 1rem; text-align: center;
}
.header-bar h1 { color: white; margin: 0; font-size: 1.6rem; }
.header-bar h1 i { margin-right: 10px; }
.header-bar p { color: #c8e6c9; margin: 0.2rem 0 0 0; font-size: 0.85rem; }

.section-title i { margin-right: 8px; color: #81c784; }
div[data-testid="stExpander"] { border: 1px solid rgba(46,125,50,0.2); border-radius: 12px; }

/* ---- Login Form ---- */
.login-container {
    max-width: 420px; margin: 8vh auto; padding: 2.5rem;
    background: rgba(20, 40, 20, 0.85);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(46,125,50,0.3);
    border-radius: 24px;
}
.login-container h2 { color: #81c784; text-align: center; margin-bottom: 0.3rem; }
.login-container p { color: #a5d6a7; text-align: center; font-size: 0.85rem; margin-bottom: 1.5rem; }
.login-logo { text-align: center; font-size: 3rem; color: #66bb6a; margin-bottom: 1rem; }
/* ---- Privacy Banner ---- */
.privacy-banner {
    background: rgba(20, 40, 20, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(46,125,50,0.25);
    border-radius: 12px; padding: 0.8rem 1.2rem;
    margin-bottom: 1rem; display: flex; align-items: center; gap: 12px;
}
.privacy-banner .pb-icon { font-size: 1.3rem; color: #66bb6a; flex-shrink: 0; }
.privacy-banner .pb-text { font-size: 0.72rem; color: #a5d6a7; line-height: 1.4; }
.privacy-banner .pb-text b { color: #81c784; }
</style>
"""

# ==================== LOGIN HTML ====================
LOGIN_HEADER = """
<div class="login-container" style="pointer-events:none; margin-bottom:-1rem;">
    <div class="login-logo"><i class="fas fa-leaf"></i></div>
    <h2>CONSERVAR PAGA</h2>
    <p>Dashboard de Control Financiero</p>
</div>
"""

# ==================== PRIVACY BANNER ====================
PRIVACY_BANNER = """
<div class="privacy-banner">
    <div class="pb-icon"><i class="fas fa-shield-halved"></i></div>
    <div class="pb-text">
        <b>Datos 100% Confidenciales</b> — La información financiera cargada en este sistema se procesa
        exclusivamente en memoria de sesión y <b>no se almacena, copia ni transmite a terceros</b>.
        Sus datos están protegidos bajo los principios de Confidencialidad, Integridad y Disponibilidad.
        Al cerrar sesión, los datos se eliminan completamente.
    </div>
</div>
"""
