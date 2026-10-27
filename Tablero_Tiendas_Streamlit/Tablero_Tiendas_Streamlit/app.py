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
st.caption('Análisis de Book (hoja JUN) y LibroVentas. La fuente puede ser OneDrive/SharePoint o una carga manual.')


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


def visual_profile(row) -> tuple[str, str, str]:
    """Return label, background and text using the business visual rules supplied by the user."""
    state = text_upper(row.get('ESTADO_NORMALIZADO', row.get('ESTADO', '')))
    name = text_upper(row.get('NAME', ''))
    tie = text_upper(row.get('TIE26', ''))
    seg = text_upper(row.get('SEG26', ''))
    haystack = ' '.join([name, tie, seg])
    # Explicit operating status has priority for closed, signed and construction stores.
    if 'CERRAD' in state: return 'CERRADA', '#D92D20', '#FFFFFF'
    if 'OBRA' in state or 'CONSTRU' in state: return 'EN OBRA', '#D9F3FF', '#0077B6'
    if 'FIRMAD' in state: return 'FIRMADA', '#98A2B3', '#101828'
    if '(BA)' in haystack: return '(BA)', '#D6BBFB', '#3B0764'
    if '-R' in name or '-R' in tie: return '-R', '#54208A', '#FFFFFF'
    if 'TMCB' in haystack: return 'TMCB', '#E31B23', '#FFD400'
    if 'RECESO' in haystack: return 'RECESO', '#B42318', '#FFFFFF'
    if 'HOGAR' in haystack: return 'HOGAR', '#111111', '#FFFFFF'
    if 'EXP' in haystack: return 'EXP', '#003B73', '#FFFFFF'
    if 'BASE' in haystack: return 'BASE', '#FFD400', '#111111'
    if 'ABIERTA' in state: return 'ABIERTA', '#111111', '#FFFFFF'
    return state or 'SIN CLASIFICAR', '#667085', '#FFFFFF'


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
    use_cloud = st.checkbox('Actualizar desde OneDrive', value=bool(book_url and sales_url), disabled=not (book_url and sales_url), help='Las URLs se configuran en .streamlit/secrets.toml o en Streamlit Cloud → Settings → Secrets.')
    manual_book = st.file_uploader('Book.xlsx — respaldo manual', type=['xlsx'], key='book')
    manual_sales = st.file_uploader('LibroVentas.xlsx — respaldo manual', type=['xlsx'], key='sales')
    book_file = sales_file = None
    if use_cloud and book_url and sales_url:
        try:
            book_file = fetch_from_onedrive(book_url)
            sales_file = fetch_from_onedrive(sales_url)
            st.success('Bases cargadas desde OneDrive')
        except Exception as exc:
            st.error(f'No fue posible actualizar desde OneDrive: {exc}')
            st.info('Puedes usar los cargadores manuales como respaldo.')
    if book_file is None: book_file = manual_book
    if sales_file is None: sales_file = manual_sales
    st.divider()
    st.header('Alertas')
    pct = st.slider('Cambio mínimo contra mes previo', 0.05, 1.0, 0.25, 0.05)
    zthr = st.slider('Z-score mínimo contra ventana de 6 meses', 1.0, 4.0, 2.0, 0.25)
    minval = st.number_input('Venta mínima para comparar', min_value=0, value=1000, step=500)

if not book_file or not sales_file:
    st.info('Configura los enlaces de OneDrive en Secrets o carga ambos Excel manualmente para iniciar el análisis.')
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
book[['CLASIFICACION','COLOR_FONDO','COLOR_TEXTO']] = book.apply(
    lambda row: pd.Series(visual_profile(row)), axis=1
)

# Filters
with st.sidebar:
    st.header('2. Filtros')
    zones = sorted(book['ZONA'].dropna().astype(str).unique()) if 'ZONA' in book else []
    selected_zones = st.multiselect('Zona', zones)
    states = sorted(book['ESTADO_NORMALIZADO'].dropna().astype(str).unique())
    selected_states = st.multiselect('Estado', states)
    if selected_zones: book = book[book['ZONA'].astype(str).isin(selected_zones)]
    if selected_states: book = book[book['ESTADO_NORMALIZADO'].isin(selected_states)]

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

st.markdown('#### Mix visual de tiendas')
mix = book['CLASIFICACION'].value_counts().rename_axis('Clasificación').reset_index(name='Tiendas')
mix['Porcentaje'] = mix['Tiendas'] / max(total, 1)
mix_cols = st.columns(min(6, max(1, len(mix))))
for col, (_, item) in zip(mix_cols, mix.head(6).iterrows()):
    label = item['Clasificación']
    bg = book.loc[book['CLASIFICACION'].eq(label), 'COLOR_FONDO'].iloc[0]
    fg = book.loc[book['CLASIFICACION'].eq(label), 'COLOR_TEXTO'].iloc[0]
    col.markdown(f'<div class="kpi" style="background:{bg};color:{fg};border-color:{bg}"><div style="font-size:.8rem">{label}</div><h3 style="color:{fg}">{int(item["Tiendas"]):,}</h3><div style="font-size:.8rem">{item["Porcentaje"]:.1%} de la red</div></div>', unsafe_allow_html=True)
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
    selected_label_visual, badge, badge_text = visual_profile(selected)
    st.markdown(f'''<div class="store-card" style="border-left:8px solid {badge}"><div class="store-title">{selected.get('NAME', 'Sin nombre')} <span class="badge" style="background:{badge};color:{badge_text}">{selected_label_visual}</span></div><div class="store-subtitle">CR: {selected_cr} · {selected.get('ZONA','Sin zona')} · {selected.get('MUN','Sin municipio')}</div></div>''', unsafe_allow_html=True)
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
    st.markdown('#### Torre de control por clasificación')
    class_stats = book.groupby('CLASIFICACION', dropna=False).agg(
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
        st.plotly_chart(px.bar(class_stats, x='CLASIFICACION', y='Ventas_UM', color='CLASIFICACION', title='Venta promedio UM por clasificación'), use_container_width=True)
    with q2:
        st.plotly_chart(px.scatter(class_stats, x='Ventas_UM', y='Contribucion_UM', size='Tiendas', color='CLASIFICACION', hover_name='CLASIFICACION', title='Matriz de ventas vs contribución'), use_container_width=True)
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
        st.dataframe(opp[[c for c in ['CR','NAME','CLASIFICACION','VENTA_VS_U6M','VENTAS OUM','VU6M','RENTABILIDAD_NETA'] if c in opp]].style.format({'VENTA_VS_U6M':'{:+.1%}','VENTAS OUM':'${:,.0f}','VU6M':'${:,.0f}','RENTABILIDAD_NETA':'${:,.0f}'}), use_container_width=True, hide_index=True)
    with oc2:
        st.caption('Top 10 riesgo por caída vs U6M')
        st.dataframe(risk[[c for c in ['CR','NAME','CLASIFICACION','VENTA_VS_U6M','VENTAS OUM','VU6M','RENTABILIDAD_NETA'] if c in risk]].style.format({'VENTA_VS_U6M':'{:+.1%}','VENTAS OUM':'${:,.0f}','VU6M':'${:,.0f}','RENTABILIDAD_NETA':'${:,.0f}'}), use_container_width=True, hide_index=True)

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
    st.markdown('#### Alertas detectadas en el histórico de ventas')
    alerts=sudden_alerts(ventas, 'VENTAS', pct, zthr, minval)
    st.caption('Se compara el último dato disponible de cada tienda contra el mes previo y contra su media/desviación de los seis meses anteriores. Es una señal para investigar, no un diagnóstico causal.')
    if alerts.empty: st.success('No se detectaron alertas con los parámetros actuales.')
    else:
        a1,a2,a3=st.columns(3); a1.metric('Alertas',len(alerts)); a2.metric('Crecimientos',int((alerts.TIPO_ALERTA=='CRECIMIENTO REPENTINO').sum())); a3.metric('Bajones',int((alerts.TIPO_ALERTA=='BAJÓN REPENTINO').sum()))
        show=[c for c in ['FECHA','CR','NAME','ZONA','ESTADO_NORMALIZADO','VENTAS','PREVIO','CAMBIO_PCT','Z_SCORE','TIPO_ALERTA','SEVERIDAD'] if c in alerts]
        st.dataframe(alerts[show].style.format({'VENTAS':'${:,.0f}','PREVIO':'${:,.0f}','CAMBIO_PCT':'{:.1%}','Z_SCORE':'{:.2f}'}), use_container_width=True, hide_index=True)
        st.download_button('Descargar alertas CSV', alerts[show].to_csv(index=False).encode('utf-8-sig'), 'alertas_tiendas.csv', 'text/csv')

with t4:
    st.markdown('#### Base de tiendas — Book / JUN')
    q=st.text_input('Buscar por CR o nombre')
    detail=book.copy()
    if q:
        mask=detail.astype(str).apply(lambda col: col.str.contains(q,case=False,na=False)).any(axis=1); detail=detail[mask]
    st.caption(f'{len(detail):,} tienda(s) encontrada(s). El color corresponde a la clasificación visual de negocio.')
    if 'CLASIFICACION' in detail.columns:
        def paint_store_row(row):
            color = row.get('COLOR_FONDO', '#667085')
            text = row.get('COLOR_TEXTO', '#FFFFFF')
            return [f'background-color: {color}22' if c not in ['CLASIFICACION', 'ESTADO_NORMALIZADO'] else f'background-color: {color}; color: {text}; font-weight: 700' for c in row.index]
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
