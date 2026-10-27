import pandas as pd
import plotly.express as px
import streamlit as st
from src.analysis import load_book, load_libro_sheets, historic_to_long, merge_book_status, sudden_alerts, status_bucket
from src.onedrive import download_excel

st.set_page_config(page_title='Control de tiendas', page_icon='📊', layout='wide')

st.markdown('''<style>
.block-container{padding-top:1.4rem}.kpi{padding:1rem;border-radius:.7rem;background:#f5f7fb;border:1px solid #e5e7eb}.small{color:#667085;font-size:.85rem}
.store-card{padding:1.1rem 1.25rem;border-radius:14px;border:1px solid #d0d5dd;background:linear-gradient(135deg,#ffffff,#f8fafc);box-shadow:0 3px 12px rgba(16,24,40,.08);margin:.35rem 0 1rem}
.store-title{font-size:1.35rem;font-weight:750;color:#101828;margin:0}.store-subtitle{color:#667085;margin:.2rem 0 .7rem}.badge{display:inline-block;padding:.3rem .7rem;border-radius:999px;color:#fff;font-weight:700;font-size:.82rem}.fact{padding:.65rem .8rem;background:#f8fafc;border-radius:9px;border:1px solid #eaecf0}.fact-label{font-size:.76rem;color:#667085}.fact-value{font-weight:650;color:#101828;margin-top:.15rem}
</style>''', unsafe_allow_html=True)
st.title('Control integral de tiendas')
st.caption('Análisis de Book (hoja JUN) y LibroVentas. Fuente única: OneDrive/SharePoint.')


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

with st.sidebar:
    st.header('1. Fuente de datos')
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
    st.header('Alertas')
    pct = st.slider('Cambio mínimo contra mes previo', 0.05, 1.0, 0.25, 0.05)
    zthr = st.slider('Z-score mínimo contra ventana de 6 meses', 1.0, 4.0, 2.0, 0.25)
    minval = st.number_input('Venta mínima para comparar', min_value=0, value=1000, step=500)

if not book_file or not sales_file:
    st.info('Configura ONEDRIVE_BOOK_URL y ONEDRIVE_SALES_URL en Streamlit Cloud → Settings → Secrets para iniciar el análisis.')
    st.markdown('### Qué incluye el tablero')
    st.markdown('- Conteo y porcentaje de tiendas por estado: abiertas, cerradas, en obra, firmadas y otros.\n- Distribución por zona, departamento, segmento y tipo de tienda.\n- KPIs operativos de ventas, contribución, margen, tráfico, ticket, renta y batting.\n- Histórico mensual de ventas y contribución con rankings.\n- Alertas de crecimiento o bajón repentino, configurables por porcentaje y desviación estadística.\n- Descarga de datos filtrados y alertas en CSV.')
    st.stop()

try:
    book = load_book(book_file)
    sheets = load_libro_sheets(sales_file)
except Exception as e:
    st.error(f'No se pudieron leer los archivos: {e}')
    st.stop()

book['ESTADO_NORMALIZADO'] = book.get('ESTADO', pd.Series('', index=book.index)).map(status_bucket)
book[['ESTADO_ETIQUETA','ESTADO_COLOR','ESTADO_TEXTO']] = book.apply(lambda row: pd.Series(status_profile(row)), axis=1)
book[['DISTINTIVO','DISTINTIVO_COLOR','DISTINTIVO_TEXTO']] = book.apply(lambda row: pd.Series(modifier_profile(row)), axis=1)
book[['SEGMENTO_VISUAL','SEGMENTO_COLOR','SEGMENTO_TEXTO']] = book.apply(lambda row: pd.Series(segment_profile(row)), axis=1)
book[['FORMATO_VISUAL','FORMATO_COLOR','FORMATO_TEXTO']] = book.apply(lambda row: pd.Series(format_profile(row)), axis=1)

# Filters
with st.sidebar:
    st.header('2. Filtros')
    def choose(column, label):
        if column not in book: return []
        values = sorted(v for v in book[column].dropna().astype(str).unique() if v.strip())
        return st.multiselect(label, values, key=f'filter_{column}')

    selected_states = choose('ESTADO_NORMALIZADO', 'Estado operativo')
    selected_modifiers = choose('DISTINTIVO', 'Distintivo BA / -R')
    selected_segments = choose('SEGMENTO_VISUAL', 'Segmento: BASE / HOGAR / RECESO')
    selected_formats = choose('FORMATO_VISUAL', 'Formato: TMCB / EXP')
    selected_zones = choose('ZONA', 'Zona')
    selected_departments = choose('DEPARTAMENTO', 'Departamento')
    selected_municipalities = choose('MUN', 'Municipio')
    selected_local_types = choose('TIPO DE LOCAL', 'Tipo de local')
    selected_parking = choose('PARQUEADERO', 'Parqueadero')
    selected_generator = choose('GENERADOR', 'Generador')
    selected_24h = choose('24H', 'Operación 24H')
    selected_strata = choose('ESTRATO', 'Estrato')
    selected_te = choose('TE', 'Clasificación TE')
    selected_pth = choose('PTH', 'Clasificación PTH')

    date_min = date_max = None
    if 'FECHA APE' in book:
        dates = pd.to_datetime(book['FECHA APE'], errors='coerce').dropna()
        if not dates.empty:
            date_range = st.date_input('Rango de fecha de apertura', value=(dates.min().date(), dates.max().date()), min_value=dates.min().date(), max_value=dates.max().date())
            if isinstance(date_range, tuple) and len(date_range) == 2:
                date_min, date_max = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])

    numeric_filters = {}
    for column, label, money in [
        ('VENTAS OUM','Ventas operativas UM',True), ('VU6M','Ventas promedio U6M',True),
        ('CONTRIBUCION UM','Contribución UM',True), ('MARGEN UM','Margen UM',True),
        ('RENTA','Renta',True), ('TRAFICO UM','Tráfico UM',False), ('TICKET UM','Ticket UM',True),
        ('AREA','Área total',False), ('PISO DE VENTA','Piso de venta',False), ('%BATTING','Batting',False),
    ]:
        if column in book:
            values = pd.to_numeric(book[column], errors='coerce').dropna()
            if not values.empty and float(values.min()) < float(values.max()):
                step = 0.01 if column == '%BATTING' else max(1.0, round((float(values.max())-float(values.min()))/100, 0))
                default = (float(values.min()), float(values.max()))
                selected_range = st.slider(label, min_value=float(values.min()), max_value=float(values.max()), value=default, step=step, format='%.1f' if not money else '$%.0f')
                numeric_filters[column] = selected_range

    filters = {
        'ESTADO_NORMALIZADO': selected_states, 'DISTINTIVO': selected_modifiers,
        'SEGMENTO_VISUAL': selected_segments, 'FORMATO_VISUAL': selected_formats,
        'ZONA': selected_zones, 'DEPARTAMENTO': selected_departments, 'MUN': selected_municipalities,
        'TIPO DE LOCAL': selected_local_types, 'PARQUEADERO': selected_parking, 'GENERADOR': selected_generator,
        '24H': selected_24h, 'ESTRATO': selected_strata, 'TE': selected_te, 'PTH': selected_pth,
    }
    for column, values in filters.items():
        if values: book = book[book[column].astype(str).isin(values)]
    if date_min is not None:
        dates = pd.to_datetime(book['FECHA APE'], errors='coerce')
        book = book[dates.between(date_min, date_max)]
    for column, (low, high) in numeric_filters.items():
        values = pd.to_numeric(book[column], errors='coerce')
        book = book[values.between(low, high)]
    st.caption(f'Filtros activos: {len(book):,} tiendas')

ventas_sheet = next((k for k in sheets if str(k).upper() == 'HISTORICO VENTAS'), None)
con_sheet = next((k for k in sheets if str(k).upper() == 'HISTORICO CON'), None)
if not ventas_sheet:
    st.error('No se encontró la hoja HISTORICO VENTAS.')
    st.stop()
ventas = merge_book_status(book, historic_to_long(sheets[ventas_sheet], 'VENTAS'))
con = merge_book_status(book, historic_to_long(sheets[con_sheet], 'CONTRIBUCION')) if con_sheet else pd.DataFrame()

# Overview
st.subheader('Resumen ejecutivo')
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
cols = st.columns(8)
for col, (label, value, delta, money) in zip(cols, indicators):
    value_text = display_value(value, money)
    delta_text = f'{delta:+.1%} vs U6M' if delta is not None else ''
    col.markdown(f'<div class="kpi"><div class="small">{label}</div><h3>{value_text}</h3><div class="small">{delta_text}</div></div>', unsafe_allow_html=True)

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
        col.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.3rem .5rem;margin:.15rem 0;border-radius:6px;background:{bg};color:{fg};font-weight:650"><span>{label}</span><span>{int(item["Tiendas"]):,}</span></div>', unsafe_allow_html=True)
legend = [('ABIERTA','#111111','#FFFFFF'),('FIRMADA','#98A2B3','#101828'),('EN OBRA','#D9F3FF','#0077B6'),('CERRADA','#D92D20','#FFFFFF'),('(BA)','#D6BBFB','#3B0764'),('-R','#54208A','#FFFFFF'),('TMCB','#E31B23','#FFD400'),('EXP','#003B73','#FFFFFF'),('RECESO','#B42318','#FFFFFF'),('HOGAR','#111111','#FFFFFF'),('BASE','#FFD400','#111111')]
legend_html = ' '.join([f'<span style="display:inline-block;background:{bg};color:{fg};padding:.25rem .55rem;border-radius:999px;margin:.15rem;font-size:.78rem;font-weight:700">{label}</span>' for label,bg,fg in legend])
st.markdown(f'<div class="small"><b>Leyenda visual:</b> {legend_html}</div>', unsafe_allow_html=True)

# Explorador de tienda inspirado en la hoja INICIO de Book.
st.subheader('Explorador interactivo de tiendas')
store_options = book[['CR','NAME']].fillna('').drop_duplicates('CR').sort_values(['NAME','CR'])
store_labels = [f"{r.CR} — {r.NAME}" for r in store_options.itertuples()]
selected_label = st.selectbox('Busca y selecciona una tienda por CR o nombre', store_labels, index=0 if store_labels else None)
if selected_label:
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
    st.markdown(f'''<div class="store-card" style="border-left:8px solid {status_bg}"><div class="store-title">{selected.get('NAME', 'Sin nombre')} {badges}</div><div class="store-subtitle">CR: {selected_cr} · {selected.get('ZONA','Sin zona')} · {selected.get('MUN','Sin municipio')}</div></div>''', unsafe_allow_html=True)
    fact_cols = st.columns(6)
    facts = [('Apertura', selected.get('FECHA APE','Sin dato'), False), ('Área venta', selected.get('PISO DE VENTA', selected.get('AREA','Sin dato')), False), ('Tráfico UM', selected.get('TRAFICO UM','Sin dato'), False), ('Ticket UM', selected.get('TICKET UM','Sin dato'), True), ('Ventas UM', selected.get('VENTAS OUM','Sin dato'), True), ('Contribución UM', selected.get('CONTRIBUCION UM','Sin dato'), True)]
    for col, (label, value, money) in zip(fact_cols, facts):
        if isinstance(value, pd.Timestamp): value = value.strftime('%d/%m/%Y')
        col.markdown(f'<div class="fact"><div class="fact-label">{label}</div><div class="fact-value">{display_value(value, money)}</div></div>', unsafe_allow_html=True)
    m1,m2,m3,m4 = st.columns(4)
    m1.metric('Venta último mes', display_value(last_sale['VENTAS'], True) if last_sale is not None else 'Sin dato', f'{change:.1%}' if change is not None else None)
    m2.metric('Margen UM', display_value(selected.get('MARGEN UM'), True))
    m3.metric('Renta UM', display_value(selected.get('RENTA'), True))
    m4.metric('Batting', f"{float(selected.get('%BATTING')):.1%}" if pd.notna(selected.get('%BATTING')) else 'Sin dato')
    with st.expander('Ver ficha completa tipo INICIO', expanded=False):
        left, right = st.columns(2)
        left_fields = ['CR','ESTADO_NORMALIZADO','ZONA','DEPARTAMENTO','MUN','UPZ/COMUNA','ESTRATO','TIPO DE LOCAL','PARQUEADERO','SEG26','TIE26']
        right_fields = ['TRAFICO UM','TRU6','TICKET UM','TICKET U6M','VENTAS OUM','VU6M','CONTRIBUCION UM','CONTRIBUCION U6M','MARGEN UM','MARGEN U6M','RENTA','RU6M']
        left.dataframe(pd.DataFrame({'Campo':left_fields, 'Valor':[selected.get(c, 'Sin dato') for c in left_fields]}), hide_index=True, use_container_width=True)
        right.dataframe(pd.DataFrame({'Campo':right_fields, 'Valor':[display_value(selected.get(c), c not in ['TRAFICO UM','TRU6']) for c in right_fields]}), hide_index=True, use_container_width=True)
    if not selected_sales.empty:
        chart_data = selected_sales[['FECHA','VENTAS']].copy().rename(columns={'VENTAS':'Ventas'})
        if not selected_con.empty:
            chart_data = chart_data.merge(selected_con[['FECHA','CONTRIBUCION']].rename(columns={'CONTRIBUCION':'Contribución'}), on='FECHA', how='left')
        st.plotly_chart(px.line(chart_data, x='FECHA', y=[c for c in ['Ventas','Contribución'] if c in chart_data], markers=True, title=f'Histórico de {selected.get("NAME", selected_cr)}'), use_container_width=True)

# Tabs
t1,t2,t3,t4,t5 = st.tabs(['Estados y cobertura','Ventas y contribución','Alertas','Detalle de tiendas','Calidad de datos'])
with t1:
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

with t2:
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

with t3:
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
    selected_ticker = st.selectbox('Selecciona una tienda para ver su ficha bursátil', [f"{r.CR} — {r.NAME}" for r in snapshot[['CR','NAME']].fillna('').sort_values('NAME').itertuples()])
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
        st.markdown('#### Mayores subidas')
        rising = snapshot[snapshot['DIRECCION'] == 'SUBIÓ'].sort_values('CAMBIO_PCT', ascending=False).head(10)
        for _, r in rising.iterrows():
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:.35rem .55rem;border-bottom:1px solid #EAECF0"><span><b style="color:#12B76A">↑</b> {r.get("NAME", r.CR)}</span><b style="color:#12B76A">{r["CAMBIO_PCT"]:+.1%}</b></div>', unsafe_allow_html=True)
    with rank_down:
        st.markdown('#### Mayores bajadas')
        falling = snapshot[snapshot['DIRECCION'] == 'BAJÓ'].sort_values('CAMBIO_PCT').head(10)
        for _, r in falling.iterrows():
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:.35rem .55rem;border-bottom:1px solid #EAECF0"><span><b style="color:#F04438">↓</b> {r.get("NAME", r.CR)}</span><b style="color:#F04438">{r["CAMBIO_PCT"]:+.1%}</b></div>', unsafe_allow_html=True)
    show=[c for c in ['FECHA','CR','NAME','ZONA','ESTADO_NORMALIZADO','VENTAS','PREVIO','CAMBIO_PCT','Z_SCORE','TIPO_ALERTA','SEVERIDAD'] if c in latest_alerts]
    if not latest_alerts.empty:
        st.download_button('Descargar señales detectadas CSV', latest_alerts[show].to_csv(index=False).encode('utf-8-sig'), 'alertas_tiendas.csv', 'text/csv')

with t4:
    st.markdown('#### Base de tiendas — Book / JUN')
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
    st.download_button('Descargar detalle filtrado CSV', detail.to_csv(index=False).encode('utf-8-sig'), 'detalle_tiendas.csv', 'text/csv')

with t5:
    st.markdown('#### Validaciones y cobertura')
    checks=[]
    for col in ['CR','NAME','ESTADO','ZONA','Y','X','VENTAS OUM','CONTRIBUCION UM']:
        if col in book:
            checks.append({'Campo':col,'No vacíos':int(book[col].notna().sum()),'Vacíos':int(book[col].isna().sum()),'% cobertura':book[col].notna().mean()})
    st.dataframe(pd.DataFrame(checks).style.format({'% cobertura':'{:.1%}'}), use_container_width=True, hide_index=True)
    st.write(f'Filas Book/JUN: **{len(book):,}** · Tiendas con históricos de ventas: **{ventas.CR.nunique():,}** · Periodo: **{ventas.FECHA.min():%b %Y} a {ventas.FECHA.max():%b %Y}**')
