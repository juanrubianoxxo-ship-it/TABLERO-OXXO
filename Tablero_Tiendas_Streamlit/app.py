import pandas as pd
import plotly.express as px
import streamlit as st
from src.analysis import load_book, load_book_sheets, load_libro_sheets, historic_to_long, merge_book_status, sudden_alerts, status_bucket
from src.onedrive import download_excel

st.set_page_config(page_title='OXXO · Control Room 2.0', page_icon='📊', layout='wide', initial_sidebar_state='expanded')
px.defaults.template = 'plotly_white'

st.markdown('''<style>
.block-container{padding-top:1.1rem;padding-bottom:2.5rem}.stTabs [data-baseweb=tab-list]{gap:.35rem}.stTabs [data-baseweb=tab]{padding:.65rem .95rem;border-radius:10px 10px 0 0;font-weight:650}.stTabs [aria-selected="true"]{background:#eef4ff;color:#175cd3}.section-kicker{font-size:.76rem;letter-spacing:.08em;text-transform:uppercase;color:#667085;font-weight:750;margin:.8rem 0 .25rem}.kpi{padding:1rem 1.1rem;border-radius:.9rem;background:linear-gradient(145deg,#ffffff 0%,#f5f7fb 62%,#eaf2ff 100%);border:1px solid #e1e7f0;box-shadow:0 8px 22px rgba(55,89,140,.12), inset 0 1px 0 rgba(255,255,255,.95);min-height:124px}.kpi h3,.kpi h2{margin:.45rem 0;color:#e8f1fb;font-size:1.55rem;white-space:nowrap}.small{color:#667085;font-size:.85rem}
.layer-plate{padding:.6rem .75rem;border-radius:10px;margin:.35rem 0;box-shadow:0 5px 14px rgba(16,24,40,.13), inset 0 1px 0 rgba(255,255,255,.35);transition:transform .15s ease}.layer-plate:hover{transform:translateY(-2px)}
.store-card{padding:1.1rem 1.25rem;border-radius:16px;border:1px solid #d0d5dd;background:linear-gradient(135deg,#ffffff,#f8fafc);box-shadow:0 10px 26px rgba(16,24,40,.12), inset 0 1px 0 rgba(255,255,255,.95);margin:.35rem 0 1rem}
.store-title{font-size:1.35rem;font-weight:750;color:#e8f1fb;margin:0}.store-subtitle{color:#667085;margin:.2rem 0 .7rem}.badge{display:inline-block;padding:.3rem .7rem;border-radius:999px;color:#fff;font-weight:700;font-size:.82rem;box-shadow:0 3px 8px rgba(16,24,40,.16)}.fact{padding:.65rem .8rem;background:#f8fafc;border-radius:9px;border:1px solid #eaecf0;box-shadow:0 4px 12px rgba(16,24,40,.06)}.fact-label{font-size:.76rem;color:#667085}.fact-value{font-weight:650;color:#e8f1fb;margin-top:.15rem}.mesop-card{height:100%;padding:1rem;border-radius:16px;text-align:center;background:linear-gradient(145deg,#fffdf5,#fff7d6);border:1px solid #f2c94c;box-shadow:0 10px 26px rgba(242,183,5,.22), inset 0 1px 0 rgba(255,255,255,.9)}.mesop-number{font-size:3.2rem;line-height:1;font-weight:850;color:#9a6700;margin:.6rem 0}.energy-card{position:relative;overflow:hidden;padding:1.35rem 1.45rem;border-radius:22px;margin:.45rem 0 1rem;border:1px solid var(--energy-border);background:var(--energy-bg);color:var(--energy-text);box-shadow:var(--energy-shadow);transition:transform .2s ease,box-shadow .2s ease}.energy-card:hover{transform:translateY(-3px);box-shadow:var(--energy-shadow-hover)}.energy-card::after{content:'';position:absolute;top:-70px;right:-45px;width:190px;height:190px;border-radius:50%;background:var(--energy-orb);filter:blur(2px);opacity:.65}.energy-card.energy-high{--energy-border:#86efac;--energy-bg:linear-gradient(135deg,#062e24 0%,#0b5d45 52%,#0f8f67 100%);--energy-text:#ecfdf5;--energy-shadow:0 0 0 1px rgba(52,211,153,.16),0 0 25px rgba(16,185,129,.42),0 14px 32px rgba(6,78,59,.3);--energy-shadow-hover:0 0 0 1px rgba(134,239,172,.3),0 0 38px rgba(16,185,129,.65),0 18px 38px rgba(6,78,59,.38);--energy-orb:radial-gradient(circle,#86efac 0%,rgba(52,211,153,.24) 36%,transparent 70%)}.energy-card.energy-mid{--energy-border:#fcd34d;--energy-bg:linear-gradient(135deg,#33200a 0%,#755116 58%,#a86f13 100%);--energy-text:#fffbeb;--energy-shadow:0 0 0 1px rgba(251,191,36,.12),0 0 18px rgba(245,158,11,.24),0 14px 30px rgba(92,50,4,.24);--energy-shadow-hover:0 0 0 1px rgba(252,211,77,.22),0 0 27px rgba(245,158,11,.4),0 18px 35px rgba(92,50,4,.32);--energy-orb:radial-gradient(circle,#fde68a 0%,rgba(251,191,36,.18) 38%,transparent 70%)}.energy-card.energy-low{--energy-border:#64748b;--energy-bg:linear-gradient(135deg,#202938 0%,#364152 58%,#475569 100%);--energy-text:#e2e8f0;--energy-shadow:0 8px 20px rgba(15,23,42,.26);--energy-shadow-hover:0 10px 24px rgba(15,23,42,.34);--energy-orb:radial-gradient(circle,#94a3b8 0%,rgba(100,116,139,.12) 38%,transparent 70%)}.energy-head{position:relative;z-index:1;display:flex;justify-content:space-between;gap:1rem;align-items:flex-start}.energy-name{font-size:1.55rem;font-weight:800;letter-spacing:-.02em}.energy-cr{font-size:.8rem;opacity:.8;margin-top:.18rem}.energy-status{display:inline-block;padding:.42rem .72rem;border:1px solid rgba(255,255,255,.24);border-radius:999px;background:rgba(255,255,255,.12);font-size:.74rem;font-weight:800;letter-spacing:.06em;white-space:nowrap}.energy-badges{position:relative;z-index:1;margin:.85rem 0 .65rem}.energy-badges .badge{box-shadow:0 2px 9px rgba(0,0,0,.2)}.energy-summary{position:relative;z-index:1;display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem;margin-top:.75rem}.energy-stat{padding:.65rem .75rem;border-radius:12px;background:rgba(0,0,0,.18);border:1px solid rgba(255,255,255,.12)}.energy-stat-label{font-size:.7rem;opacity:.78}.energy-stat-value{font-size:1.08rem;font-weight:800;margin-top:.15rem}.energy-note{position:relative;z-index:1;margin-top:.8rem;font-size:.8rem;opacity:.88}.energy-key{display:flex;gap:.55rem;align-items:center;flex-wrap:wrap;margin:.2rem 0 1rem;color:#667085;font-size:.8rem}.energy-dot{width:10px;height:10px;border-radius:50%;display:inline-block}.signal-list{max-height:520px;overflow-y:auto;padding-right:.25rem}
</style>''', unsafe_allow_html=True)

st.markdown('''<style>
:root{--ink:#14213d;--muted:#64748b;--line:#dbe3ef;--navy:#0b1736;--blue:#2563eb;--cyan:#06b6d4;--surface:#ffffff}
.stApp{background:#f3f6fb}.block-container{max-width:1500px;padding-left:2.2rem;padding-right:2.2rem}
[data-testid=stSidebar]{background:linear-gradient(180deg,#0b1736 0%,#101f48 56%,#162b5b 100%);border-right:1px solid #253b6e}
[data-testid=stSidebar] *{color:#e7eefc} [data-testid=stSidebar] .stCaption{color:#a9badb}
[data-testid=stSidebar] input,[data-testid=stSidebar] textarea,[data-testid=stSidebar] [data-baseweb=select]>div{background:#142653!important;border-color:#37518a!important;color:#f8fbff!important}
[data-testid=stSidebar] [data-baseweb=multi-select] span{background:#264582!important;color:#f8fbff!important;border-color:#5272b4!important}
[data-testid=stSidebar] hr{border-color:#314879}.stButton>button{border-radius:10px;border:1px solid #cbd5e1}
.dashboard-hero{position:relative;overflow:hidden;background:linear-gradient(120deg,#0b1736 0%,#15336b 58%,#087e9c 100%);border-radius:24px;padding:1.55rem 1.8rem;margin:.25rem 0 1.35rem;color:white;box-shadow:0 18px 40px rgba(20,55,110,.2)}.dashboard-hero:after{content:'';position:absolute;right:-50px;top:-80px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(103,232,249,.42),transparent 68%)}.hero-eyebrow{position:relative;z-index:1;letter-spacing:.14em;text-transform:uppercase;font-size:.7rem;color:#8be9fa;font-weight:800}.hero-title{position:relative;z-index:1;font-size:2.2rem;line-height:1.05;font-weight:850;letter-spacing:-.045em;margin:.35rem 0}.hero-copy{position:relative;z-index:1;color:#c8d7f4;font-size:.93rem;max-width:730px;margin:0}.hero-meta{position:relative;z-index:1;display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1.05rem}.hero-pill{border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.1);padding:.35rem .65rem;border-radius:999px;font-size:.75rem;color:#e8f2ff}
.section-band{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid var(--line);margin:1.5rem 0 .85rem;padding-bottom:.55rem}.section-band h2{font-size:1.2rem;color:var(--ink);margin:0}.section-band p{font-size:.78rem;color:var(--muted);margin:0}.overview-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin:.8rem 0 1rem}.overview-tile{padding:1rem 1.05rem;border-radius:16px;background:var(--surface);border:1px solid var(--line);box-shadow:0 7px 18px rgba(20,45,90,.07)}.overview-tile .tile-label{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:750}.overview-tile .tile-value{font-size:1.55rem;font-weight:850;color:var(--ink);margin:.28rem 0}.overview-tile .tile-note{font-size:.75rem;color:var(--muted)}.overview-tile.good{border-top:4px solid #10b981}.overview-tile.warn{border-top:4px solid #f59e0b}.overview-tile.risk{border-top:4px solid #64748b}.overview-tile.blue{border-top:4px solid #2563eb}
.energy-ribbon{display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:.75rem;margin:1rem 0 1.25rem}.energy-ribbon-main,.energy-ribbon-card{border-radius:16px;padding:1rem 1.1rem;color:#fff;min-height:96px}.energy-ribbon-main{background:linear-gradient(135deg,#0b1736,#1d4ed8)}.energy-ribbon-card{background:#fff;color:var(--ink);border:1px solid var(--line);box-shadow:0 7px 18px rgba(20,45,90,.06)}.ribbon-label{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;font-weight:800;opacity:.78}.ribbon-value{font-size:1.65rem;font-weight:850;margin:.25rem 0}.ribbon-note{font-size:.76rem;opacity:.76}.energy-ribbon-card.good{border-left:5px solid #10b981}.energy-ribbon-card.mid{border-left:5px solid #f59e0b}.energy-ribbon-card.low{border-left:5px solid #64748b}
[data-testid=stMetric]{background:#fff;border:1px solid var(--line);border-radius:14px;padding:.8rem 1rem;box-shadow:0 5px 16px rgba(20,45,90,.05)}[data-testid=stMetricLabel]{color:var(--muted)!important}[data-testid=stMetricValue]{color:var(--ink)!important}
.stTabs [data-baseweb=tab-list]{background:#e8eef8;border-radius:14px;padding:.28rem;gap:.25rem}.stTabs [data-baseweb=tab]{border-radius:10px;padding:.7rem .9rem;color:#52627e;font-size:.82rem;font-weight:750}.stTabs [aria-selected=true]{background:#fff;color:#1d4ed8;box-shadow:0 3px 10px rgba(37,99,235,.14)}
[data-testid=stExpander]{border:1px solid var(--line);border-radius:14px;background:#fff}.stDataFrame{border:1px solid var(--line);border-radius:12px;overflow:hidden}.nav-kicker{font-size:.68rem;letter-spacing:.16em;color:#06b6d4;font-weight:850;text-transform:uppercase;margin:1rem 0 .5rem}.nav-help{font-size:.72rem;color:#a9badb;line-height:1.45;padding:.65rem 0}.tech-divider{height:1px;background:linear-gradient(90deg,transparent,#5272b4,transparent);margin:1rem 0}
@media(max-width:900px){.overview-grid,.energy-ribbon{grid-template-columns:repeat(2,1fr)}.hero-title{font-size:1.7rem}.block-container{padding-left:1rem;padding-right:1rem}}.store-data-tabs [data-baseweb=tab-list]{background:#f0f4fa}.store-data-hint{padding:.65rem .85rem;border-radius:10px;background:#eef6ff;border:1px solid #c7ddff;color:#24508c;font-size:.8rem;margin:.4rem 0 .8rem}.stDownloadButton>button{background:#0b1736;color:#fff;border:0;font-weight:700}.stDownloadButton>button:hover{background:#1d4ed8;color:#fff}.stButton>button:hover{border-color:#2563eb;color:#1d4ed8}.sidebar-brand{padding:.8rem 0 1rem;border-bottom:1px solid #314879;margin-bottom:1rem}.sidebar-brand-title{font-size:1.05rem;font-weight:850;letter-spacing:-.02em}.sidebar-brand-sub{font-size:.74rem;color:#a9badb;margin-top:.2rem}.refresh-chip{display:inline-block;padding:.28rem .55rem;border-radius:999px;background:#e8f7ef;color:#087443;border:1px solid #a6e3c0;font-size:.74rem;font-weight:750}.muted-callout{padding:.8rem 1rem;border-radius:12px;background:#f8fafc;border:1px solid #e2e8f0;color:#475569;font-size:.84rem}
</style>''', unsafe_allow_html=True)

st.markdown('''<div class="dashboard-hero"><div class="hero-eyebrow">OXXO · RETAIL CONTROL ROOM 2.0</div><div class="hero-title">Pulso de la red de tiendas</div><p class="hero-copy">Una vista operativa para decidir más rápido: identifica crecimiento, prioriza riesgos y entiende el movimiento de cada tienda desde una sola pantalla.</p><div class="hero-meta"><span class="hero-pill">Book / JUN</span><span class="hero-pill">LibroVentas</span><span class="hero-pill">Actualización automática desde OneDrive</span><span class="hero-pill">Vista ejecutiva + detalle operativo</span></div></div>''', unsafe_allow_html=True)



def secret_value(name: str):
    """Read flat or [onedrive] nested Streamlit secrets without exposing them."""
    try:
        if name in st.secrets:
            return st.secrets[name]
        if 'onedrive' in st.secrets and name in st.secrets['onedrive']:
            return st.secrets['onedrive'][name]
    except Exception:
        pass
    return ''


def text_upper(value) -> str:
    return '' if pd.isna(value) else str(value).upper().strip()


def status_profile(row) -> tuple[str, str, str]:
    """Main store-name color: only the operational state controls this layer."""
    state = text_upper(row.get('ESTADO_NORMALIZADO', row.get('ESTADO', '')))
    if 'CERRAD' in state: return 'CERRADA', '#D92D20', '#FFFFFF'
    if 'OBRA' in state or 'CONSTRU' in state: return 'EN OBRA', '#D9F3FF', '#0077B6'
    if 'FIRMAD' in state: return 'FIRMADA', '#98A2B3', '#101828'
    if 'ABIERTA' in state: return 'ABIERTA', '#111111', '#FFFFFF'
    return state or 'SIN ESTADO', '#667085', '#FFFFFF'


def modifier_profile(row) -> tuple[str, str, str]:
    """BA and -R are independent name distinctions and apply only to open stores."""
    state = text_upper(row.get('ESTADO_NORMALIZADO', row.get('ESTADO', '')))
    name = text_upper(row.get('NAME', ''))
    if 'ABIERTA' not in state: return '', '', ''
    name_tokens = name.replace('(', ' ').replace(')', ' ').replace('/', ' ').split()
    if 'BA' in name_tokens or '(BA)' in name:
        return 'BA', '#D6BBFB', '#3B0764'
    if '-R' in name:
        return '-R', '#54208A', '#FFFFFF'
    return '', '', ''


def segment_profile(row) -> tuple[str, str, str]:
    """SEG26 is independent from status, BA/-R and TIE26."""
    segment = text_upper(row.get('SEG26', ''))
    if 'HOGAR' in segment: return 'HOGAR', '#111111', '#FFFFFF'
    if 'RECESO' in segment: return 'RECESO', '#B42318', '#FFFFFF'
    if 'BASE' in segment: return 'BASE', '#FFD400', '#111111'
    return segment or 'SIN SEGMENTO', '#E4E7EC', '#344054'


def format_profile(row) -> tuple[str, str, str]:
    """TIE26 format/type is independent from the other visual layers."""
    fmt = text_upper(row.get('TIE26', ''))
    if 'TMCB' in fmt: return 'TMCB', '#E31B23', '#FFD400'
    if 'EXP' in fmt: return 'EXP', '#003B73', '#FFFFFF'
    return fmt or 'SIN FORMATO', '#E4E7EC', '#344054'


def state_color(state: str) -> str:
    return {'ABIERTA':'#111111', 'CERRADA':'#D92D20', 'EN OBRA':'#D9F3FF', 'FIRMADA':'#98A2B3'}.get(state, '#667085')


def energy_profile(row, monthly_change=None):
    """Clasifica la energía comercial de la tienda con señales explicables."""
    state = text_upper(row.get('ESTADO_NORMALIZADO', row.get('ESTADO', '')))
    sales_um = pd.to_numeric(pd.Series([row.get('VENTAS OUM')]), errors='coerce').iloc[0]
    sales_u6m = pd.to_numeric(pd.Series([row.get('VU6M')]), errors='coerce').iloc[0]
    contribution = pd.to_numeric(pd.Series([row.get('CONTRIBUCION UM')]), errors='coerce').iloc[0]
    vs_u6m = (sales_um / sales_u6m - 1) if pd.notna(sales_um) and pd.notna(sales_u6m) and sales_u6m else None
    score = 0
    reasons = []
    if vs_u6m is not None:
        if vs_u6m >= .05: score += 1; reasons.append(f'Ventas {vs_u6m:+.1%} vs U6M')
        elif vs_u6m <= -.10: score -= 1; reasons.append(f'Ventas {vs_u6m:+.1%} vs U6M')
    if monthly_change is not None:
        if monthly_change >= .05: score += 1; reasons.append(f'Último mes {monthly_change:+.1%}')
        elif monthly_change <= -.10: score -= 1; reasons.append(f'Último mes {monthly_change:+.1%}')
    if pd.notna(contribution):
        if contribution > 0: score += 1
        elif contribution < 0: score -= 1
    if 'ABIERTA' not in state: score = min(score, 0)
    if score >= 2:
        return 'energy-high', 'ALTA ENERGÍA', 'Desempeño fuerte · mantener impulso', reasons, vs_u6m
    if score <= -1:
        return 'energy-low', 'REQUIERE ATENCIÓN', 'Desempeño bajo · revisar operación', reasons, vs_u6m
    return 'energy-mid', 'ENERGÍA ESTABLE', 'Desempeño mixto · monitorear evolución', reasons, vs_u6m


def pct_change(current, previous):
    try:
        if pd.isna(current) or pd.isna(previous) or float(previous) == 0: return None
        return float(current) / float(previous) - 1
    except (TypeError, ValueError):
        return None


def display_value(value, money=False):
    if pd.isna(value): return 'Sin dato'
    try:
        return f'${float(value):,.0f}' if money else f'{float(value):,.0f}'
    except (TypeError, ValueError):
        return str(value)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_from_onedrive(url: str) -> bytes:
    return download_excel(url).getvalue()


# Cargar y transformar una vez por versión de los archivos; los filtros usan estas copias.
@st.cache_data(ttl=600, show_spinner='Leyendo Book…')
def load_book_cached(uploaded: bytes) -> pd.DataFrame:
    return load_book(uploaded)


@st.cache_data(ttl=600, show_spinner='Inventariando hojas de Book…')
def load_book_sheets_cached(uploaded: bytes) -> dict:
    return load_book_sheets(uploaded)


@st.cache_data(ttl=600, show_spinner='Leyendo hojas de ventas…')
def load_libro_sheets_cached(uploaded: bytes) -> dict:
    return load_libro_sheets(uploaded)


@st.cache_data(ttl=600, show_spinner=False)
def historic_to_long_cached(frame: pd.DataFrame, metric_name: str) -> pd.DataFrame:
    return historic_to_long(frame, metric_name)


@st.cache_data(ttl=600, show_spinner=False)
def decorate_book_cached(raw_book: pd.DataFrame) -> pd.DataFrame:
    book = raw_book.copy()
    book['ESTADO_NORMALIZADO'] = book.get('ESTADO', pd.Series('', index=book.index)).map(status_bucket)
    book[['ESTADO_ETIQUETA','ESTADO_COLOR','ESTADO_TEXTO']] = book.apply(lambda row: pd.Series(status_profile(row)), axis=1)
    book[['DISTINTIVO','DISTINTIVO_COLOR','DISTINTIVO_TEXTO']] = book.apply(lambda row: pd.Series(modifier_profile(row)), axis=1)
    book[['SEGMENTO_VISUAL','SEGMENTO_COLOR','SEGMENTO_TEXTO']] = book.apply(lambda row: pd.Series(segment_profile(row)), axis=1)
    book[['FORMATO_VISUAL','FORMATO_COLOR','FORMATO_TEXTO']] = book.apply(lambda row: pd.Series(format_profile(row)), axis=1)
    return book


@st.cache_data(ttl=600, show_spinner=False)
def merge_book_status_cached(book_frame: pd.DataFrame, long_frame: pd.DataFrame) -> pd.DataFrame:
    return merge_book_status(book_frame, long_frame)

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><div class="sidebar-brand-title">OXXO / CONTROL ROOM</div><div class="sidebar-brand-sub">Panel operativo de tiendas · versión 2.0</div></div>', unsafe_allow_html=True)
    if st.button('↻  Actualizar datos', use_container_width=True, help='Limpia la caché y vuelve a leer los archivos desde OneDrive'):
        st.cache_data.clear()
        st.rerun()
    st.markdown('<div class="tech-divider"></div><div class="nav-kicker">Navegación</div>', unsafe_allow_html=True)
    active_section = st.radio('Módulo', ['Resumen operativo','Finanzas','Alertas','Directorio','Calidad','Comparador'], index=0, label_visibility='collapsed', key='active_section')
    st.markdown('<div class="nav-help">Selecciona un módulo para concentrarte en una sola lectura. Los filtros de red permanecen disponibles abajo.</div>', unsafe_allow_html=True)
    st.header('Conexión de datos')
    book_url = secret_value('ONEDRIVE_BOOK_URL')
    sales_url = secret_value('ONEDRIVE_SALES_URL')
    st.caption('Fuente única: OneDrive/SharePoint')
    book_file = sales_file = None
    if book_url and sales_url:
        try:
            book_file = fetch_from_onedrive(book_url)
            sales_file = fetch_from_onedrive(sales_url)
            st.success('Bases cargadas desde OneDrive')
        except Exception as exc:
            st.error(f'No fue posible actualizar desde OneDrive: {exc}')
    else:
        st.warning('Faltan ONEDRIVE_BOOK_URL y/o ONEDRIVE_SALES_URL en Secrets.')
    st.divider()
    st.header('Sensibilidad de alertas')
    pct = st.slider('Cambio mínimo contra mes previo', 0.05, 1.0, 0.25, 0.05)
    zthr = st.slider('Z-score mínimo contra ventana de 6 meses', 1.0, 4.0, 2.0, 0.25)
    minval = st.number_input('Venta mínima para comparar', min_value=0, value=1000, step=500)

if not book_file or not sales_file:
    st.info('Configura ONEDRIVE_BOOK_URL y ONEDRIVE_SALES_URL en Streamlit Cloud → Settings → Secrets para iniciar el análisis.')
    st.markdown('### Qué incluye el tablero')
    st.markdown('- Conteo y porcentaje de tiendas por estado: abiertas, cerradas, en obra, firmadas y otros.\n- Distribución por zona, departamento, segmento y tipo de tienda.\n- KPIs operativos de ventas, contribución, margen, tráfico, ticket, renta y batting.\n- Histórico mensual de ventas y contribución con rankings.\n- Alertas de crecimiento o bajón repentino, configurables por porcentaje y desviación estadística.\n- Descarga de datos filtrados y alertas en CSV.')
    st.stop()

try:
    book_all = decorate_book_cached(load_book_cached(book_file))
    book = book_all.copy()
    book_sheets = load_book_sheets_cached(book_file)
    sheets = load_libro_sheets_cached(sales_file)
except Exception as e:
    st.error(f'No se pudieron leer los archivos: {e}')
    st.stop()

# Filters
with st.sidebar:
    st.markdown('<div class="muted-callout">Usa los filtros para construir una vista ejecutiva o bajar hasta una tienda específica. Los gráficos y descargas respetan la selección.</div>', unsafe_allow_html=True)
    st.header('Explorar la red')
    store_query = st.text_input('Buscar tienda por CR o nombre', placeholder='Ej. 1234 o Reforma', key='store_query')
    def choose(column, label):
        if column not in book: return []
        values = sorted(v for v in book[column].dropna().astype(str).unique() if v.strip())
        return st.multiselect(label, values, key=f'filter_{column}')

    selected_statuses = choose('ESTADO_NORMALIZADO', 'Estado operativo')
    selected_segments = choose('SEGMENTO_VISUAL', 'Segmento: BASE / HOGAR / RECESO')
    selected_generations = choose('TIE26', 'Generación')
    selected_departments = choose('DEPARTAMENTO', 'Departamento')
    selected_municipalities = choose('MUN', 'Municipio')
    selected_strata = choose('ESTRATO', 'Estrato')
    selected_generator = choose('GENERADOR', 'Generador')
    selected_zones = choose('ZONA', 'Zona')
    selected_local_types = choose('TIPO DE LOCAL', 'Tipo de local')

    filters = {
        'ESTADO_NORMALIZADO': selected_statuses,
        'SEGMENTO_VISUAL': selected_segments, 'TIE26': selected_generations,
        'DEPARTAMENTO': selected_departments, 'MUN': selected_municipalities,
        'ESTRATO': selected_strata, 'GENERADOR': selected_generator,
        'ZONA': selected_zones, 'TIPO DE LOCAL': selected_local_types,
    }
    for column, values in filters.items():
        if values: book = book[book[column].astype(str).isin(values)]
    if store_query:
        needle = store_query.strip().lower()
        search_mask = book[['CR', 'NAME']].fillna('').astype(str).apply(lambda col: col.str.lower().str.contains(needle, na=False)).any(axis=1)
        book = book[search_mask]
    st.caption(f'Vista actual · {len(book):,} tiendas' + (f' · búsqueda: “{store_query}”' if store_query else ''))

ventas_sheet = next((k for k in sheets if str(k).upper() == 'HISTORICO VENTAS'), None)
con_sheet = next((k for k in sheets if str(k).upper() == 'HISTORICO CON'), None)
if not ventas_sheet:
    st.error('No se encontró la hoja HISTORICO VENTAS.')
    st.stop()
sales_long = historic_to_long_cached(sheets[ventas_sheet], 'VENTAS')
ventas_all = merge_book_status_cached(book_all, sales_long)
con_all = merge_book_status_cached(book_all, historic_to_long_cached(sheets[con_sheet], 'CONTRIBUCION')) if con_sheet else pd.DataFrame()
visible_crs = set(book['CR'].astype(str))
ventas = ventas_all[ventas_all['CR'].astype(str).isin(visible_crs)].copy()
con = con_all[con_all['CR'].astype(str).isin(visible_crs)].copy() if not con_all.empty else pd.DataFrame()

# Overview
st.markdown('<div class="section-band"><div><h2>Resumen de la red</h2><p>Lectura rápida del estado operativo y financiero de la vista actual</p></div></div>', unsafe_allow_html=True)
status_counts = book['ESTADO_NORMALIZADO'].value_counts()
total = len(book)
latest = ventas['FECHA'].max() if not ventas.empty else None
latest_sales = ventas[ventas['FECHA'] == latest] if latest is not None else ventas
avg_sales = latest_sales['VENTAS'].mean() if not latest_sales.empty else 0
avg_con = con[con['FECHA'] == latest]['CONTRIBUCION'].mean() if latest is not None and not con.empty else 0
u6m_sales = pd.to_numeric(book.get('VU6M', pd.Series(dtype=float)), errors='coerce').mean()
u6m_con = pd.to_numeric(book.get('CONTRIBUCION U6M', pd.Series(dtype=float)), errors='coerce').mean()
sales_delta = pct_change(avg_sales, u6m_sales)
con_delta = pct_change(avg_con, u6m_con)
latest_label = latest.strftime('%b %Y').upper() if latest is not None else 'SIN PERIODO'
st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;gap:.75rem;flex-wrap:wrap;margin:-.25rem 0 .85rem"><span class="small">Vista filtrada · {total:,} tiendas · periodo de referencia {latest_label}</span><span class="refresh-chip">● Datos listos para análisis</span></div>', unsafe_allow_html=True)
indicators = [
    ('Tiendas', total, None, False),
    ('Abiertas', int(status_counts.get('ABIERTA', 0)), None, False),
    ('Cerradas', int(status_counts.get('CERRADA', 0)), None, False),
    ('En obra', int(status_counts.get('EN OBRA', 0)), None, False),
    ('Firmadas', int(status_counts.get('FIRMADA', 0)), None, False),
    ('Venta último mes', avg_sales, sales_delta, True),
    ('Contribución último mes', avg_con, con_delta, True),
    ('Venta promedio U6M', u6m_sales, None, True),
]
st.markdown('##### Indicadores de cobertura')
count_cols = st.columns(5)
for col, (label, value, delta, money) in zip(count_cols, indicators[:5]):
    share = '100.0% del total' if label == 'Tiendas' else f'{value / max(total, 1):.1%} del total'
    col.markdown(f'<div class="kpi"><div class="small">{label}</div><h3>{display_value(value, money)}</h3><div class="small">{share}</div></div>', unsafe_allow_html=True)
st.markdown('##### Indicadores financieros')
financial_cols = st.columns(3)
for col, (label, value, delta, money) in zip(financial_cols, indicators[5:]):
    delta_text = f'{delta:+.1%} vs U6M' if delta is not None else ''
    col.markdown(f'<div class="kpi"><div class="small">{label}</div><h3>{display_value(value, money)}</h3><div class="small">{delta_text}</div></div>', unsafe_allow_html=True)

st.markdown('#### Capas independientes de clasificación')
layer_cols = st.columns(3)
for col, title, label_col, bg_col, fg_col in zip(
    layer_cols,
    ['Estado operativo', 'Segmentación', 'Formato / tipo'],
    ['ESTADO_ETIQUETA', 'SEGMENTO_VISUAL', 'FORMATO_VISUAL'],
    ['ESTADO_COLOR', 'SEGMENTO_COLOR', 'FORMATO_COLOR'],
    ['ESTADO_TEXTO', 'SEGMENTO_TEXTO', 'FORMATO_TEXTO'],
):
    counts = book[label_col].value_counts().rename_axis('Etiqueta').reset_index(name='Tiendas')
    col.markdown(f'**{title}**')
    for _, item in counts.head(8).iterrows():
        label = item['Etiqueta']
        sample = book[book[label_col].eq(label)].iloc[0]
        bg, fg = sample[bg_col], sample[fg_col]
        share = int(item['Tiendas']) / max(total, 1)
        col.markdown(f'<div class="layer-plate" style="display:flex;justify-content:space-between;align-items:center;background:{bg};color:{fg};font-weight:650"><span>{label}</span><span>{int(item["Tiendas"]):,} <small>({share:.1%})</small></span></div>', unsafe_allow_html=True)
legend = [('ABIERTA','#111111','#FFFFFF'),('FIRMADA','#98A2B3','#101828'),('EN OBRA','#D9F3FF','#0077B6'),('CERRADA','#D92D20','#FFFFFF'),('(BA)','#D6BBFB','#3B0764'),('-R','#54208A','#FFFFFF'),('TMCB','#E31B23','#FFD400'),('EXP','#003B73','#FFFFFF'),('RECESO','#B42318','#FFFFFF'),('HOGAR','#111111','#FFFFFF'),('BASE','#FFD400','#111111')]
legend_html = ' '.join([f'<span style="display:inline-block;background:{bg};color:{fg};padding:.25rem .55rem;border-radius:999px;margin:.15rem;font-size:.78rem;font-weight:700">{label}</span>' for label,bg,fg in legend])
st.markdown(f'<div class="small"><b>Leyenda visual:</b> {legend_html}</div>', unsafe_allow_html=True)

# Health ribbon: a network-level reading of the new visual language.
energy_overview = book.apply(lambda row: energy_profile(row), axis=1, result_type='expand') if not book.empty else pd.DataFrame()
if not energy_overview.empty:
    energy_overview.columns = ['ENERGIA_CLASE','ENERGIA_LABEL','ENERGIA_NOTA','ENERGIA_RAZONES','ENERGIA_VS_U6M']
    energy_counts = energy_overview['ENERGIA_CLASE'].value_counts()
    high_count = int(energy_counts.get('energy-high', 0)); mid_count = int(energy_counts.get('energy-mid', 0)); low_count = int(energy_counts.get('energy-low', 0))
    st.markdown(f'''<div class="energy-ribbon"><div class="energy-ribbon-main"><div class="ribbon-label">SALUD DE LA VISTA</div><div class="ribbon-value">{len(book):,} tiendas activas</div><div class="ribbon-note">Clasificación por ventas, contribución y estado</div></div><div class="energy-ribbon-card good"><div class="ribbon-label">Alta energía</div><div class="ribbon-value">{high_count:,}</div><div class="ribbon-note">Impulsores de la red</div></div><div class="energy-ribbon-card mid"><div class="ribbon-label">Estables</div><div class="ribbon-value">{mid_count:,}</div><div class="ribbon-note">Monitoreo normal</div></div><div class="energy-ribbon-card low"><div class="ribbon-label">Atención</div><div class="ribbon-value">{low_count:,}</div><div class="ribbon-note">Prioridad de revisión</div></div></div>''', unsafe_allow_html=True)

# Explorador de tienda inspirado en la hoja INICIO de Book.
st.markdown('<div class="section-kicker">Consulta individual</div>', unsafe_allow_html=True)
st.subheader('Ficha de tienda')
st.caption('Filtra por CR o nombre en la barra lateral y selecciona una tienda para ver su placa operativa completa.')
store_options = book[['CR','NAME']].fillna('').drop_duplicates('CR').sort_values(['NAME','CR'])
store_labels = [f"{r.CR} — {r.NAME}" for r in store_options.itertuples()]
selected_label = st.selectbox('Selecciona una tienda', store_labels, index=0 if store_labels else None, placeholder='Escribe para buscar una tienda…', key='selected_store')
if not store_labels:
    st.info('No hay tiendas que coincidan con los filtros actuales. Ajusta la búsqueda o limpia algún filtro.')
elif selected_label:
    selected_cr = selected_label.split(' — ', 1)[0]
    selected = book[book['CR'].astype(str) == selected_cr].iloc[0]
    selected_state = selected.get('ESTADO_NORMALIZADO', 'SIN ESTADO')
    selected_sales = ventas[ventas['CR'].astype(str) == selected_cr].sort_values('FECHA')
    selected_con = con[con['CR'].astype(str) == selected_cr].sort_values('FECHA') if not con.empty else pd.DataFrame()
    last_sale = selected_sales.iloc[-1] if not selected_sales.empty else None
    prev_sale = selected_sales.iloc[-2] if len(selected_sales) > 1 else None
    change = pct_change(last_sale['VENTAS'], prev_sale['VENTAS']) if last_sale is not None and prev_sale is not None else None
    status_label, status_bg, status_fg = status_profile(selected)
    modifier_label, modifier_bg, modifier_fg = modifier_profile(selected)
    segment_label, segment_bg, segment_fg = segment_profile(selected)
    format_label, format_bg, format_fg = format_profile(selected)
    badges = f'<span class="badge" style="background:{status_bg};color:{status_fg}">{status_label}</span>'
    if modifier_label:
        badges += f' <span class="badge" style="background:{modifier_bg};color:{modifier_fg}">{modifier_label}</span>'
    badges += f' <span class="badge" style="background:{segment_bg};color:{segment_fg}">SEG: {segment_label}</span>'
    badges += f' <span class="badge" style="background:{format_bg};color:{format_fg}">TIPO: {format_label}</span>'
    mesop_raw = selected.get('MESOP', 'ND')
    try:
        mesop_num = float(mesop_raw)
        if pd.isna(mesop_num): raise ValueError
        mesop_display = f'{mesop_num:,.0f}'; mesop_color = '#B7791F' if mesop_num > 100 else '#344054'; mesop_note = 'MESOP > 100' if mesop_num > 100 else 'MESOP'
    except (TypeError, ValueError):
        mesop_display = str(mesop_raw); mesop_color = '#667085'; mesop_note = 'MESOP'
    energy_class, energy_label, energy_note, energy_reasons, vs_u6m = energy_profile(selected, change)
    energy_reason_text = ' · '.join(energy_reasons) if energy_reasons else 'Sin variación suficiente para clasificar'
    st.markdown('#### Placa de energía comercial')
    st.markdown('<div class="energy-key"><span class="energy-dot" style="background:#34d399;box-shadow:0 0 8px #34d399"></span>Buen desempeño / luminoso <span class="energy-dot" style="background:#fbbf24"></span>Estable <span class="energy-dot" style="background:#64748b"></span>Requiere atención / opaco</div>', unsafe_allow_html=True)
    sales_display = display_value(selected.get('VENTAS OUM'), True)
    contrib_display = display_value(selected.get('CONTRIBUCION UM'), True)
    change_display = f'{change:+.1%}' if change is not None else 'Sin dato'
    vs_u6m_display = f'{vs_u6m:+.1%}' if vs_u6m is not None else 'Sin dato'
    ficha_html = f'''<div class="energy-card {energy_class}"><div class="energy-head"><div><div class="energy-name">{selected.get('NAME', 'Sin nombre')}</div><div class="energy-cr">CR {selected_cr} · {selected.get('ZONA','Sin zona')} · {selected.get('MUN','Sin municipio')}</div></div><div class="energy-status">{energy_label}</div></div><div class="energy-badges">{badges}</div><div class="energy-summary"><div class="energy-stat"><div class="energy-stat-label">VENTAS UM</div><div class="energy-stat-value">{sales_display}</div></div><div class="energy-stat"><div class="energy-stat-label">VS U6M</div><div class="energy-stat-value">{vs_u6m_display}</div></div><div class="energy-stat"><div class="energy-stat-label">CAMBIO MENSUAL</div><div class="energy-stat-value">{change_display}</div></div></div><div class="energy-note">{energy_note} · {energy_reason_text}</div></div>'''
    ficha_left, ficha_right = st.columns([3.8, 1.15])
    with ficha_left:
        st.markdown(ficha_html, unsafe_allow_html=True)
    with ficha_right:
        st.markdown(f'''<div class="mesop-card"><div class="small">{mesop_note}</div><div class="mesop-number" style="color:{mesop_color}">{mesop_display}</div><div class="small">Indicador MESOP de Book</div></div>''', unsafe_allow_html=True)
    st.markdown('#### Indicadores rápidos')
    fact_cols = st.columns(6)
    area_value = selected.get('PISO DE VENTA', selected.get('AREA PISO DE VENTA', selected.get('AREA', 'Sin dato')))
    facts = [('Apertura', selected.get('FECHA APE','Sin dato'), False), ('Área venta', area_value, False), ('Tráfico UM', selected.get('TRAFICO UM','Sin dato'), False), ('Ticket UM', selected.get('TICKET UM','Sin dato'), True), ('Ventas UM', selected.get('VENTAS OUM','Sin dato'), True), ('Contribución UM', selected.get('CONTRIBUCION UM','Sin dato'), True)]
    for col, (label, value, money) in zip(fact_cols, facts):
        if isinstance(value, pd.Timestamp): value = value.strftime('%d/%m/%Y')
        col.markdown(f'<div class="fact"><div class="fact-label">{label}</div><div class="fact-value">{display_value(value, money)}</div></div>', unsafe_allow_html=True)
    st.markdown('#### Desempeño operativo')
    m1,m2,m3,m4 = st.columns(4)
    m1.metric('Venta último mes', display_value(last_sale['VENTAS'], True) if last_sale is not None else 'Sin dato', f'{change:.1%}' if change is not None else None)
    m2.metric('Margen UM', display_value(selected.get('MARGEN UM'), True))
    m3.metric('Renta UM', display_value(selected.get('RENTA'), True))
    m4.metric('Batting', f"{float(selected.get('%BATTING')):.1%}" if pd.notna(selected.get('%BATTING')) else 'Sin dato')
    # Ficha interactiva completa: toda la fila original de Book/JUN, organizada por temas y con búsqueda.
    st.markdown('#### Centro de datos de la tienda')
    st.markdown('<div class="store-data-hint">Explora la información por categoría o entra en “Todos los datos” para consultar cada columna original de esta tienda.</div>', unsafe_allow_html=True)
    def value_for_table(value):
        if pd.isna(value): return 'Sin dato'
        if isinstance(value, pd.Timestamp): return value.strftime('%d/%m/%Y')
        return str(value)

    raw_fields = pd.DataFrame({'Campo': [str(c) for c in selected.index], 'Valor': [value_for_table(v) for v in selected.values]})
    def fields_by_keywords(keywords):
        mask = raw_fields['Campo'].str.upper().apply(lambda name: any(k in name for k in keywords))
        return raw_fields[mask].copy()

    identity_fields = fields_by_keywords(['CR','NAME','ESTADO','SEG26','TIE26','DISTINTIVO','ENERGIA'])
    location_fields = fields_by_keywords(['ZONA','DEPARTAMENTO','MUN','UPZ','COMUNA','ESTRATO','DIRECCION','BARRIO','LOCALIDAD','Y','X','COORD'])
    finance_fields = fields_by_keywords(['VENTA','CONTRIB','MARGEN','RENTA','TICKET','BATTING','MESOP','U6M','UM','TRAFICO','TRU6'])
    operation_fields = fields_by_keywords(['FECHA','APERT','AREA','PISO','TIPO','PARQUE','GENERADOR','FORMATO','LOCAL','OPER'])
    categorized = set(identity_fields['Campo']) | set(location_fields['Campo']) | set(finance_fields['Campo']) | set(operation_fields['Campo'])
    other_fields = raw_fields[~raw_fields['Campo'].isin(categorized)].copy()

    data_tabs = st.tabs(['Resumen','Ubicación y operación','Ventas y rentabilidad','Todos los datos'])
    with data_tabs[0]:
        summary_cols = st.columns(3)
        summary_cols[0].metric('Campos disponibles', f'{len(raw_fields):,}')
        summary_cols[1].metric('Datos con valor', f'{int((raw_fields.Valor != "Sin dato").sum()):,}')
        summary_cols[2].metric('CR de tienda', str(selected.get('CR', selected_cr)))
        st.dataframe(identity_fields if not identity_fields.empty else raw_fields.head(12), hide_index=True, use_container_width=True, height=360)
    with data_tabs[1]:
        op_left, op_right = st.columns(2)
        with op_left:
            st.markdown('**Ubicación y clasificación**')
            st.dataframe(location_fields if not location_fields.empty else raw_fields.head(1), hide_index=True, use_container_width=True, height=420)
        with op_right:
            st.markdown('**Operación y apertura**')
            st.dataframe(operation_fields if not operation_fields.empty else raw_fields.head(1), hide_index=True, use_container_width=True, height=420)
    with data_tabs[2]:
        st.markdown('**Indicadores comerciales y financieros disponibles en Book/JUN**')
        st.dataframe(finance_fields if not finance_fields.empty else raw_fields.head(1), hide_index=True, use_container_width=True, height=480)
    with data_tabs[3]:
        search_fields = st.text_input('Buscar dentro de todos los datos', placeholder='Ej. renta, municipio, área, fecha…', key=f'field_search_{selected_cr}')
        all_data = raw_fields.copy()
        if search_fields:
            q = search_fields.strip().lower()
            all_data = all_data[all_data.astype(str).apply(lambda col: col.str.lower().str.contains(q, na=False)).any(axis=1)]
        st.caption(f'Mostrando {len(all_data):,} de {len(raw_fields):,} campos originales de la tienda.')
        st.dataframe(all_data, hide_index=True, use_container_width=True, height=520)
        st.download_button('Descargar ficha completa de esta tienda', raw_fields.to_csv(index=False).encode('utf-8-sig'), f'ficha_tienda_{selected_cr}.csv', 'text/csv', key=f'download_store_{selected_cr}')
    if not selected_sales.empty:
        chart_data = selected_sales[['FECHA','VENTAS']].copy().rename(columns={'VENTAS':'Ventas'})
        if not selected_con.empty:
            chart_data = chart_data.merge(selected_con[['FECHA','CONTRIBUCION']].rename(columns={'CONTRIBUCION':'Contribución'}), on='FECHA', how='left')
        st.plotly_chart(px.line(chart_data, x='FECHA', y=[c for c in ['Ventas','Contribución'] if c in chart_data], markers=True, title=f'Histórico de {selected.get("NAME", selected_cr)}'), use_container_width=True)

# Tabs
if active_section == 'Resumen operativo':

        st.markdown('<div class="section-band"><div><h2>Mapa operativo</h2><p>Distribución, cobertura y productividad por clasificación</p></div></div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            st.markdown('#### Estado de tiendas')
            d = status_counts.rename_axis('Estado').reset_index(name='Tiendas')
            st.plotly_chart(px.pie(d, names='Estado', values='Tiendas', hole=.45, color_discrete_sequence=px.colors.qualitative.Set2), use_container_width=True)
        with c2:
            st.markdown('#### Tiendas por zona')
            if 'ZONA' in book:
                dz = book.groupby('ZONA', dropna=False).size().reset_index(name='Tiendas').sort_values('Tiendas', ascending=False)
                st.plotly_chart(px.bar(dz, x='Tiendas', y='ZONA', orientation='h', color='Tiendas', color_continuous_scale='Blues'), use_container_width=True)
        c3,c4 = st.columns(2)
        with c3:
            for col in ['DEPARTAMENTO','SEG26','TIE26','TIPO DE LOCAL']:
                if col in book:
                    st.markdown(f'#### Distribución por {col.title()}')
                    x=book[col].fillna('Sin dato').astype(str).value_counts().head(15).rename_axis(col).reset_index(name='Tiendas')
                    st.dataframe(x, use_container_width=True, hide_index=True)
                    break
        with c4:
            if {'X','Y'}.issubset(book.columns):
                geo=book.copy(); geo['LAT']=pd.to_numeric(geo['Y'],errors='coerce'); geo['LON']=pd.to_numeric(geo['X'],errors='coerce'); geo=geo.dropna(subset=['LAT','LON'])
                if not geo.empty:
                    st.markdown('#### Mapa de tiendas')
                    st.map(geo.rename(columns={'LAT':'latitude','LON':'longitude'})[['latitude','longitude']])
        st.markdown('#### Torre de control por segmento')
        class_stats = book.groupby('SEGMENTO_VISUAL', dropna=False).agg(
            Tiendas=('CR','nunique'),
            Ventas_UM=('VENTAS OUM','mean'),
            Contribucion_UM=('CONTRIBUCION UM','mean'),
            Margen_UM=('MARGEN UM','mean'),
            Renta_UM=('RENTA','mean'),
            Batting=('%BATTING','mean'),
        ).reset_index().sort_values('Ventas_UM', ascending=False)
        class_stats['Contribucion_%_ventas'] = class_stats['Contribucion_UM'] / class_stats['Ventas_UM'].replace(0, pd.NA)
        st.dataframe(class_stats.style.format({'Ventas_UM':'${:,.0f}','Contribucion_UM':'${:,.0f}','Margen_UM':'${:,.0f}','Renta_UM':'${:,.0f}','Batting':'{:.1%}','Contribucion_%_ventas':'{:.1%}'}), use_container_width=True, hide_index=True)
        q1, q2 = st.columns(2)
        with q1:
            st.plotly_chart(px.bar(class_stats, x='SEGMENTO_VISUAL', y='Ventas_UM', color='SEGMENTO_VISUAL', title='Venta promedio UM por segmento'), use_container_width=True)
        with q2:
            st.plotly_chart(px.scatter(class_stats, x='Ventas_UM', y='Contribucion_UM', size='Tiendas', color='SEGMENTO_VISUAL', hover_name='SEGMENTO_VISUAL', title='Matriz de ventas vs contribución por segmento'), use_container_width=True)
        type_stats = book.groupby('FORMATO_VISUAL', dropna=False).agg(Tiendas=('CR','nunique'), Ventas_UM=('VENTAS OUM','mean'), Contribucion_UM=('CONTRIBUCION UM','mean')).reset_index().sort_values('Ventas_UM', ascending=False)
        st.markdown('#### Torre de control por formato / tipo')
        st.dataframe(type_stats.style.format({'Ventas_UM':'${:,.0f}','Contribucion_UM':'${:,.0f}'}), use_container_width=True, hide_index=True)
        st.markdown('#### Oportunidades y riesgos operativos')
        op = book.copy()
        op['CONTRIBUCION_%_VENTAS'] = pd.to_numeric(op.get('CONTRIBUCION UM'), errors='coerce') / pd.to_numeric(op.get('VENTAS OUM'), errors='coerce').replace(0, pd.NA)
        op['VENTA_VS_U6M'] = pd.to_numeric(op.get('VENTAS OUM'), errors='coerce') / pd.to_numeric(op.get('VU6M'), errors='coerce').replace(0, pd.NA) - 1
        op['RENTABILIDAD_NETA'] = pd.to_numeric(op.get('CONTRIBUCION UM'), errors='coerce') - pd.to_numeric(op.get('RENTA'), errors='coerce')
        opp = op.sort_values('VENTA_VS_U6M', ascending=False).head(10)
        risk = op.sort_values('VENTA_VS_U6M', ascending=True).head(10)
        oc1, oc2 = st.columns(2)
        with oc1:
            st.caption('Top 10 crecimiento vs U6M')
            st.dataframe(opp[[c for c in ['CR','NAME','ESTADO_ETIQUETA','DISTINTIVO','SEGMENTO_VISUAL','FORMATO_VISUAL','VENTA_VS_U6M','VENTAS OUM','VU6M','RENTABILIDAD_NETA'] if c in opp]].style.format({'VENTA_VS_U6M':'{:+.1%}','VENTAS OUM':'${:,.0f}','VU6M':'${:,.0f}','RENTABILIDAD_NETA':'${:,.0f}'}), use_container_width=True, hide_index=True)
        with oc2:
            st.caption('Top 10 riesgo por caída vs U6M')
            st.dataframe(risk[[c for c in ['CR','NAME','ESTADO_ETIQUETA','DISTINTIVO','SEGMENTO_VISUAL','FORMATO_VISUAL','VENTA_VS_U6M','VENTAS OUM','VU6M','RENTABILIDAD_NETA'] if c in risk]].style.format({'VENTA_VS_U6M':'{:+.1%}','VENTAS OUM':'${:,.0f}','VU6M':'${:,.0f}','RENTABILIDAD_NETA':'${:,.0f}'}), use_container_width=True, hide_index=True)

if active_section == 'Finanzas':

        st.markdown('<div class="section-band"><div><h2>Desempeño financiero</h2><p>Evolución mensual, ranking y lectura por zona</p></div></div>', unsafe_allow_html=True)
        metric = st.selectbox('Métrica histórica', ['VENTAS','CONTRIBUCION'])
        data = ventas if metric == 'VENTAS' else con
        if data.empty: st.warning('No hay datos disponibles para esta métrica.')
        else:
            monthly = data.groupby('FECHA', as_index=False).agg(
                TOTAL=(metric, 'sum'),
                PROMEDIO=(metric, 'mean'),
                TIENDAS=(metric, 'count'),
            )
            st.plotly_chart(px.line(monthly, x='FECHA', y=['TOTAL','PROMEDIO'], markers=True, title=f'{metric.title()} mensual'), use_container_width=True)
            latest_date=data['FECHA'].max(); rank=data[data['FECHA']==latest_date].sort_values(metric,ascending=False).head(20)
            st.markdown(f'#### Top 20 tiendas — {latest_date:%b %Y}')
            st.dataframe(rank[[c for c in ['CR','NAME','ZONA','ESTADO_NORMALIZADO',metric] if c in rank]].style.format({metric:'${:,.0f}'}), use_container_width=True, hide_index=True)
            if 'ZONA' in data:
                byz=data[data['FECHA']==latest_date].groupby('ZONA',as_index=False)[metric].mean().sort_values(metric,ascending=False)
                st.plotly_chart(px.bar(byz, x='ZONA', y=metric, title=f'{metric.title()} promedio por zona'), use_container_width=True)

if active_section == 'Alertas':

        st.markdown('<div class="section-band"><div><h2>Radar de señales</h2><p>Detecta aceleraciones, caídas y tiendas que piden revisión</p></div></div>', unsafe_allow_html=True)
        st.markdown('#### Mercado de tiendas — señales de movimiento')
        st.caption('Cada tienda se comporta como un indicador: subió, bajó o se mantuvo estable frente al último mes disponible. La señal combina variación mensual y desviación frente a su histórico.')
        trend = ventas.sort_values(['CR','FECHA']).copy()
        trend['PREVIO'] = trend.groupby('CR')['VENTAS'].shift(1)
        trend['CAMBIO_PCT'] = (trend['VENTAS'] / trend['PREVIO'].abs().replace(0, pd.NA)) - 1
        snapshot = trend.groupby('CR', as_index=False).tail(1).copy()
        snapshot['DIRECCION'] = snapshot['CAMBIO_PCT'].apply(lambda x: 'SUBIÓ' if pd.notna(x) and x >= pct else ('BAJÓ' if pd.notna(x) and x <= -pct else 'ESTABLE'))
        snapshot['SEÑAL'] = snapshot['DIRECCION'].map({'SUBIÓ':'↑','BAJÓ':'↓','ESTABLE':'→'})
        snapshot['INTENSIDAD'] = snapshot['CAMBIO_PCT'].abs().fillna(0)
        snapshot['RANKING'] = snapshot['INTENSIDAD'].rank(method='first', ascending=False).astype(int)
        alerts = sudden_alerts(ventas, 'VENTAS', pct, zthr, minval)
        latest_alerts = alerts.sort_values('FECHA').groupby('CR', as_index=False).tail(1) if not alerts.empty else alerts
        snapshot = snapshot.merge(latest_alerts[['CR','Z_SCORE','TIPO_ALERTA','SEVERIDAD']] if not latest_alerts.empty else pd.DataFrame(columns=['CR','Z_SCORE','TIPO_ALERTA','SEVERIDAD']), on='CR', how='left')
        up = int((snapshot['DIRECCION'] == 'SUBIÓ').sum()); down = int((snapshot['DIRECCION'] == 'BAJÓ').sum()); stable = int((snapshot['DIRECCION'] == 'ESTABLE').sum())
        avg_move = snapshot['CAMBIO_PCT'].mean()
        k1,k2,k3,k4 = st.columns(4)
        k1.markdown(f'<div class="kpi" style="border-left:6px solid #12B76A"><div class="small">↑ SUBIERON</div><h2 style="color:#12B76A">{up:,}</h2><div class="small">Señal positiva</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi" style="border-left:6px solid #F04438"><div class="small">↓ BAJARON</div><h2 style="color:#F04438">{down:,}</h2><div class="small">Requieren revisión</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi" style="border-left:6px solid #667085"><div class="small">→ ESTABLES</div><h2>{stable:,}</h2><div class="small">Sin movimiento brusco</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi" style="border-left:6px solid #7F56D9"><div class="small">VARIACIÓN MEDIA</div><h2>{avg_move:+.1%}</h2><div class="small">Último mes vs previo</div></div>', unsafe_allow_html=True)
        st.markdown('#### Mapa de movimiento')
        plot_snapshot = snapshot.dropna(subset=['CAMBIO_PCT','VENTAS']).copy()
        if not plot_snapshot.empty:
            plot_snapshot['COLOR'] = plot_snapshot['DIRECCION'].map({'SUBIÓ':'Subió','BAJÓ':'Bajó','ESTABLE':'Estable'})
            fig = px.scatter(plot_snapshot, x='CAMBIO_PCT', y='VENTAS', color='COLOR', size='INTENSIDAD', hover_name='NAME' if 'NAME' in plot_snapshot else 'CR', hover_data=['CR','ZONA','DIRECCION','SEVERIDAD'], color_discrete_map={'Subió':'#12B76A','Bajó':'#F04438','Estable':'#98A2B3'}, title='Variación mensual vs nivel de ventas')
            fig.add_vline(x=0, line_dash='dash', line_color='#667085')
            fig.update_xaxes(tickformat='.0%')
            fig.update_layout(height=460, legend_title_text='Señal')
            st.plotly_chart(fig, use_container_width=True)
        ticker_options = [f"{r.CR} — {r.NAME}" for r in snapshot[['CR','NAME']].fillna('').sort_values('NAME').itertuples()]
        if not ticker_options:
            st.info('No hay señales suficientes para mostrar una ficha individual con los umbrales actuales.')
        else:
            selected_ticker = st.selectbox('Selecciona una tienda para ver su ficha bursátil', ticker_options)
            ticker_cr = selected_ticker.split(' — ', 1)[0]
            ticker_row = snapshot[snapshot['CR'].astype(str) == ticker_cr].iloc[0]
            direction = ticker_row['DIRECCION']; direction_color = {'SUBIÓ':'#12B76A','BAJÓ':'#F04438','ESTABLE':'#667085'}[direction]
            arrow = ticker_row['SEÑAL']; variation = ticker_row['CAMBIO_PCT']
            st.markdown(f'<div class="store-card" style="border-left:8px solid {direction_color}"><div class="store-title">{ticker_row.get("NAME", ticker_cr)} <span class="badge" style="background:{direction_color};color:#FFFFFF">{arrow} {direction}</span></div><div class="store-subtitle">CR: {ticker_cr} · Variación último mes: <b>{variation:+.1%}</b> · Venta actual: <b>{display_value(ticker_row["VENTAS"], True)}</b></div></div>', unsafe_allow_html=True)
            ticker_history = ventas[ventas['CR'].astype(str) == ticker_cr].sort_values('FECHA').copy()
            if not ticker_history.empty:
                ticker_history['MEDIA_6M'] = ticker_history['VENTAS'].rolling(6, min_periods=1).mean()
                fig2 = px.line(ticker_history, x='FECHA', y=['VENTAS','MEDIA_6M'], markers=True, title=f'Precio histórico de ventas — {ticker_row.get("NAME", ticker_cr)}')
                fig2.update_traces(selector={'name':'VENTAS'}, line_color=direction_color, line_width=3)
                fig2.update_layout(legend_title_text='Indicador')
                st.plotly_chart(fig2, use_container_width=True)
        rank_up, rank_down = st.columns(2)
        with rank_up:
            st.markdown(f'#### Mayores subidas ({up:,})')
            rising = snapshot[snapshot['DIRECCION'] == 'SUBIÓ'].sort_values('CAMBIO_PCT', ascending=False)
            rising_preview = rising.head(10)
            for _, r in rising_preview.iterrows():
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:.35rem .55rem;border-bottom:1px solid #EAECF0"><span><b style="color:#12B76A">↑</b> {r.get("NAME", r.CR)}</span><b style="color:#12B76A">{r["CAMBIO_PCT"]:+.1%}</b></div>', unsafe_allow_html=True)
            with st.expander(f'Ver todas las tiendas con alza ({up:,})'):
                st.dataframe(rising[[c for c in ['CR','NAME','ZONA','SEGMENTO_VISUAL','FORMATO_VISUAL','VENTAS','PREVIO','CAMBIO_PCT','SEVERIDAD'] if c in rising]].style.format({'VENTAS':'${:,.0f}','PREVIO':'${:,.0f}','CAMBIO_PCT':'{:+.1%}'}), use_container_width=True, hide_index=True)
        with rank_down:
            st.markdown(f'#### Mayores bajadas ({down:,})')
            falling = snapshot[snapshot['DIRECCION'] == 'BAJÓ'].sort_values('CAMBIO_PCT')
            falling_preview = falling.head(10)
            for _, r in falling_preview.iterrows():
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:.35rem .55rem;border-bottom:1px solid #EAECF0"><span><b style="color:#F04438">↓</b> {r.get("NAME", r.CR)}</span><b style="color:#F04438">{r["CAMBIO_PCT"]:+.1%}</b></div>', unsafe_allow_html=True)
            with st.expander(f'Ver todas las tiendas con bajón ({down:,})'):
                st.dataframe(falling[[c for c in ['CR','NAME','ZONA','SEGMENTO_VISUAL','FORMATO_VISUAL','VENTAS','PREVIO','CAMBIO_PCT','SEVERIDAD'] if c in falling]].style.format({'VENTAS':'${:,.0f}','PREVIO':'${:,.0f}','CAMBIO_PCT':'{:+.1%}'}), use_container_width=True, hide_index=True)
        show=[c for c in ['FECHA','CR','NAME','ZONA','ESTADO_NORMALIZADO','VENTAS','PREVIO','CAMBIO_PCT','Z_SCORE','TIPO_ALERTA','SEVERIDAD'] if c in latest_alerts]
        if not latest_alerts.empty:
            st.download_button('Descargar señales detectadas CSV', latest_alerts[show].to_csv(index=False).encode('utf-8-sig'), 'alertas_tiendas.csv', 'text/csv')

if active_section == 'Directorio':

        st.markdown('<div class="section-band"><div><h2>Directorio operativo</h2><p>Consulta, filtra y descarga la base de tiendas</p></div></div>', unsafe_allow_html=True)
        st.markdown('#### Base filtrada de tiendas · Book / JUN')
        q=st.text_input('Buscar por CR o nombre')
        detail=book.copy()
        if q:
            mask=detail.astype(str).apply(lambda col: col.str.contains(q,case=False,na=False)).any(axis=1); detail=detail[mask]
        st.caption(f'{len(detail):,} tienda(s) encontrada(s). El color principal de la fila corresponde al estado; segmento, formato y BA/-R permanecen independientes.')
        if 'ESTADO_COLOR' in detail.columns:
            def paint_store_row(row):
                styles = {'ESTADO_ETIQUETA': ('ESTADO_COLOR','ESTADO_TEXTO'), 'SEGMENTO_VISUAL': ('SEGMENTO_COLOR','SEGMENTO_TEXTO'), 'FORMATO_VISUAL': ('FORMATO_COLOR','FORMATO_TEXTO'), 'DISTINTIVO': ('DISTINTIVO_COLOR','DISTINTIVO_TEXTO')}
                output = []
                for c in row.index:
                    if c in styles and row.get(c, ''):
                        bg = row.get(styles[c][0], '#667085') or '#667085'; fg = row.get(styles[c][1], '#FFFFFF') or '#FFFFFF'
                        output.append(f'background-color: {bg}; color: {fg}; font-weight: 700')
                    else:
                        output.append('')
                return output
            st.dataframe(detail.style.apply(paint_store_row, axis=1), use_container_width=True, hide_index=True)
        else:
            st.dataframe(detail, use_container_width=True, hide_index=True)
        dl1, dl2 = st.columns([1, 1])
        with dl1:
            st.download_button('Descargar detalle filtrado CSV', detail.to_csv(index=False).encode('utf-8-sig'), 'detalle_tiendas.csv', 'text/csv', use_container_width=True)
        with dl2:
            st.download_button('Descargar vista ejecutiva CSV', book.to_csv(index=False).encode('utf-8-sig'), 'vista_ejecutiva_oxxo.csv', 'text/csv', use_container_width=True)

if active_section == 'Calidad':

        st.markdown('<div class="section-band"><div><h2>Calidad y cobertura</h2><p>Confianza en fuentes, campos y periodos disponibles</p></div></div>', unsafe_allow_html=True)
        st.markdown('#### Validaciones y cobertura')
        st.markdown('##### Hojas detectadas')
        book_sheet_rows = [{'Fuente': 'Book', 'Hoja': str(name), 'Filas': len(frame), 'Columnas': len(frame.columns)} for name, frame in book_sheets.items()]
        sales_sheet_rows = [{'Fuente': 'LibroVentas', 'Hoja': str(name), 'Filas': len(frame), 'Columnas': len(frame.columns)} for name, frame in sheets.items()]
        st.dataframe(pd.DataFrame(book_sheet_rows + sales_sheet_rows), use_container_width=True, hide_index=True)
        unused_book_sheets = [name for name in book_sheets if str(name).upper().strip() != 'JUN']
        loaded_aux_sheets = [name for name in sheets if str(name).upper().strip() in {'BD U6M', 'BD M'}]
        if unused_book_sheets:
            st.info('Hojas adicionales del Book detectadas y disponibles para auditoría: ' + ', '.join(map(str, unused_book_sheets)))
        if loaded_aux_sheets:
            st.success('Hojas auxiliares de LibroVentas cargadas: ' + ', '.join(map(str, loaded_aux_sheets)))
        checks=[]
        for col in ['CR','NAME','ESTADO','ZONA','Y','X','AREA PISO DE VENTA','VENTAS OUM','CONTRIBUCION UM']:
            if col in book:
                checks.append({'Campo':col,'No vacíos':int(book[col].notna().sum()),'Vacíos':int(book[col].isna().sum()),'% cobertura':book[col].notna().mean()})
        st.dataframe(pd.DataFrame(checks).style.format({'% cobertura':'{:.1%}'}), use_container_width=True, hide_index=True)
        duplicate_cr = int(book['CR'].duplicated().sum()) if 'CR' in book else 0
        st.write(f'Filas Book/JUN: **{len(book):,}** · Tiendas con históricos de ventas: **{ventas.CR.nunique():,}** · CR duplicados: **{duplicate_cr:,}** · Periodo: **{ventas.FECHA.min():%b %Y} a {ventas.FECHA.max():%b %Y}**')

if active_section == 'Comparador':

        st.markdown('<div class="section-band"><div><h2>Comparador de tiendas</h2><p>Contrasta hasta ocho tiendas con la misma métrica</p></div></div>', unsafe_allow_html=True)
        st.markdown('#### Comparar tiendas lado a lado')
        st.caption('Selecciona dos o más tiendas para comparar su evolución histórica y sus indicadores actuales. Los filtros de la barra lateral se respetan.')
        versus_options = book[['CR','NAME']].fillna('').drop_duplicates('CR').sort_values(['NAME','CR'])
        versus_labels = [f"{r.CR} — {r.NAME}" for r in versus_options.itertuples()]
        selected_versus = st.multiselect('Selecciona las tiendas a comparar', versus_labels, max_selections=8, key='versus_stores')
        if len(selected_versus) < 2:
            st.info('Selecciona al menos dos tiendas para activar la comparación.')
        else:
            versus_crs = [label.split(' — ', 1)[0] for label in selected_versus]
            versus_sales = ventas[ventas['CR'].astype(str).isin(versus_crs)].copy()
            versus_sales['TIENDA'] = versus_sales['CR'].astype(str) + ' — ' + versus_sales['NAME'].fillna('Sin nombre').astype(str)
            versus_sales = versus_sales.sort_values(['TIENDA','FECHA'])
            v1, v2 = st.columns(2)
            with v1:
                fig_vs = px.line(versus_sales, x='FECHA', y='VENTAS', color='TIENDA', markers=True, title='Evolución de ventas')
                fig_vs.update_layout(legend_title_text='Tienda')
                st.plotly_chart(fig_vs, use_container_width=True)
            with v2:
                if not con.empty:
                    versus_con = con[con['CR'].astype(str).isin(versus_crs)].copy()
                    versus_con['TIENDA'] = versus_con['CR'].astype(str) + ' — ' + versus_con['NAME'].fillna('Sin nombre').astype(str)
                    fig_con_vs = px.line(versus_con, x='FECHA', y='CONTRIBUCION', color='TIENDA', markers=True, title='Evolución de contribución')
                    fig_con_vs.update_layout(legend_title_text='Tienda')
                    st.plotly_chart(fig_con_vs, use_container_width=True)
            versus_sales['PREVIO'] = versus_sales.groupby('CR')['VENTAS'].shift(1)
            versus_sales['CAMBIO_PCT'] = versus_sales['VENTAS'] / versus_sales['PREVIO'].abs().replace(0, pd.NA) - 1
            latest_versus = versus_sales.sort_values('FECHA').groupby('CR', as_index=False).tail(1)
            compare_cols = ['CR','NAME','ESTADO_ETIQUETA','DISTINTIVO','SEGMENTO_VISUAL','FORMATO_VISUAL','ZONA','VENTAS','PREVIO','CAMBIO_PCT','TRAFICO UM','TICKET UM','VENTAS OUM','VU6M','CONTRIBUCION UM','MARGEN UM','RENTA']
            compare_cols = [c for c in compare_cols if c in latest_versus.columns]
            st.markdown('#### Comparativo de indicadores actuales')
            st.dataframe(latest_versus[compare_cols].style.format({'VENTAS':'${:,.0f}','PREVIO':'${:,.0f}','CAMBIO_PCT':'{:+.1%}','TICKET UM':'${:,.0f}','VENTAS OUM':'${:,.0f}','VU6M':'${:,.0f}','CONTRIBUCION UM':'${:,.0f}','MARGEN UM':'${:,.0f}','RENTA':'${:,.0f}'}), use_container_width=True, hide_index=True)
            st.download_button('Descargar comparativo CSV', latest_versus[compare_cols].to_csv(index=False).encode('utf-8-sig'), 'comparativo_tiendas.csv', 'text/csv')
