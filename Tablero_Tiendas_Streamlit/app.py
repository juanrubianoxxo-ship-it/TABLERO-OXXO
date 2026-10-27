from pathlib import Path
import io
import pandas as pd
import plotly.express as px
import streamlit as st
from src.analysis import load_book, load_libro_sheets, historic_to_long, merge_book_status, sudden_alerts, status_bucket

st.set_page_config(page_title='Control de tiendas', page_icon='📊', layout='wide')

st.markdown('''<style>.block-container{padding-top:1.4rem}.kpi{padding:1rem;border-radius:.7rem;background:#f5f7fb;border:1px solid #e5e7eb}.small{color:#667085;font-size:.85rem}</style>''', unsafe_allow_html=True)
st.title('Control integral de tiendas')
st.caption('Análisis local de Book (hoja JUN) y LibroVentas. No se realiza ninguna conexión automática a SharePoint.')

with st.sidebar:
    st.header('1. Cargar archivos')
    book_file = st.file_uploader('Book.xlsx — se usa únicamente JUN', type=['xlsx'], key='book')
    sales_file = st.file_uploader('LibroVentas.xlsx — se excluye INFO TIENDAS', type=['xlsx'], key='sales')
    st.divider()
    st.header('Alertas')
    pct = st.slider('Cambio mínimo contra mes previo', 0.05, 1.0, 0.25, 0.05)
    zthr = st.slider('Z-score mínimo contra ventana de 6 meses', 1.0, 4.0, 2.0, 0.25)
    minval = st.number_input('Venta mínima para comparar', min_value=0, value=1000, step=500)

if not book_file or not sales_file:
    st.info('Carga los dos archivos Excel en la barra lateral para iniciar el análisis.')
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
cols = st.columns(6)
for col, label, value in zip(cols, ['Tiendas en Book','Abiertas','Cerradas','En obra','Firmadas','Venta promedio último mes'], [total, int(status_counts.get('ABIERTA',0)), int(status_counts.get('CERRADA',0)), int(status_counts.get('EN OBRA',0)), int(status_counts.get('FIRMADA',0)), avg_sales]):
    display = f'${value:,.0f}' if label.startswith('Venta') else f'{value:,}'
    col.markdown(f'<div class="kpi"><div class="small">{label}</div><h3>{display}</h3></div>', unsafe_allow_html=True)

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

with t2:
    metric = st.selectbox('Métrica histórica', ['VENTAS','CONTRIBUCION'])
    data = ventas if metric == 'VENTAS' else con
    if data.empty: st.warning('No hay datos disponibles para esta métrica.')
    else:
        monthly=data.groupby('FECHA',as_index=False)[metric].agg(['sum','mean','count']).reset_index()
        monthly.columns=['FECHA','TOTAL','PROMEDIO','TIENDAS']
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
