from __future__ import annotations
import re
from typing import Iterable
import numpy as np
import pandas as pd

MONTHS = {'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,'sep':9,'oct':10,'nov':11,'dic':12}


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().upper() for c in out.columns]
    return out


def norm_text(x) -> str:
    if pd.isna(x): return ''
    return re.sub(r'\s+', ' ', str(x).strip()).upper()


def find_header_row(raw: pd.DataFrame, required: Iterable[str], max_rows: int = 30) -> int:
    req = {norm_text(x) for x in required}
    for i in range(min(max_rows, len(raw))):
        vals = {norm_text(v) for v in raw.iloc[i].tolist() if pd.notna(v)}
        if req.issubset(vals) or len(req & vals) >= max(1, len(req)-1):
            return i
    return 0


def load_book(uploaded) -> pd.DataFrame:
    raw = pd.read_excel(uploaded, sheet_name='JUN', header=None)
    h = find_header_row(raw, ['CR', 'ESTADO'])
    df = clean_columns(pd.read_excel(uploaded, sheet_name='JUN', header=h))
    df = df.dropna(how='all')
    if 'CR' in df:
        df['CR'] = df['CR'].astype(str).str.strip().replace({'NAN': np.nan})
        df = df[df['CR'].notna() & ~df['CR'].str.upper().isin(['TOTAL GENERAL','CR'])]
    return df.reset_index(drop=True)


def load_libro_sheets(uploaded) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(uploaded)
    result = {}
    for sheet in xls.sheet_names:
        if norm_text(sheet) == 'INFO TIENDAS':
            continue
        raw = pd.read_excel(uploaded, sheet_name=sheet, header=None)
        if norm_text(sheet) in {'HISTORICO VENTAS', 'HISTORICO CON'}:
            # Pivot tables: row 5 contains month labels and col 0 the store id.
            h = 5 if len(raw) > 5 else 0
            df = raw.iloc[h:].copy()
            df.columns = [str(x).strip() if pd.notna(x) else f'COL_{i}' for i,x in enumerate(df.iloc[0])]
            df = df.iloc[1:].reset_index(drop=True)
            df = df.rename(columns={df.columns[0]: 'CR'})
            # Drop grand total and blank rows; retain month columns only.
            df['CR'] = df['CR'].astype(str).str.strip()
            df = df[~df['CR'].str.upper().isin(['NAN','TOTAL GENERAL','ETIQUETAS DE FILA'])]
            month_cols = [c for c in df.columns if re.match(r'^[a-záéíóú]{3}\s+\d{2}$', str(c).lower())]
            df = df[['CR'] + month_cols]
            for c in month_cols: df[c] = pd.to_numeric(df[c], errors='coerce')
        else:
            # Summary sheets generally have their header at row 3.
            h = find_header_row(raw, ['ETIQUETAS DE FILA'])
            df = clean_columns(pd.read_excel(uploaded, sheet_name=sheet, header=h))
            df = df.dropna(how='all')
            if len(df.columns):
                first = df.columns[0]
                df = df.rename(columns={first:'CR'})
                df['CR'] = df['CR'].astype(str).str.strip()
                df = df[~df['CR'].str.upper().isin(['NAN','TOTAL GENERAL','ETIQUETAS DE FILA'])]
        result[sheet] = df.reset_index(drop=True)
    return result


def month_to_date(label: str):
    m = re.match(r'^([a-záéíóú]{3})\s+(\d{2})$', str(label).lower().strip())
    if not m or m.group(1) not in MONTHS: return pd.NaT
    return pd.Timestamp(year=2000+int(m.group(2)), month=MONTHS[m.group(1)], day=1)


def historic_to_long(df: pd.DataFrame, metric_name: str) -> pd.DataFrame:
    months = [c for c in df.columns if month_to_date(c) is not pd.NaT]
    long = df.melt(id_vars=['CR'], value_vars=months, var_name='MES_LABEL', value_name=metric_name)
    long['FECHA'] = long['MES_LABEL'].map(month_to_date)
    long[metric_name] = pd.to_numeric(long[metric_name], errors='coerce')
    return long.dropna(subset=[metric_name, 'FECHA']).sort_values(['CR','FECHA'])


def merge_book_status(book: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    b = book.copy()
    b['CR'] = b['CR'].astype(str).str.strip()
    cols = [c for c in ['CR','NAME','ESTADO','ESTADO_NORMALIZADO','CLASIFICACION','COLOR_FONDO','COLOR_TEXTO','ZONA','DEPARTAMENTO','MUN','SEG26','TIE26','FECHA APE','VT','ET','TRAFICO UM','TRU6','TICKET UM','TICKET U6M','VENTAS OUM','VU6M','CONTRIBUCION UM','CONTRIBUCION U6M','MARGEN UM','MARGEN U6M','RENTA','RU6M','Y','X','AREA PISO DE VENTA'] if c in b.columns]
    return df.merge(b[cols].drop_duplicates('CR'), on='CR', how='left')


def status_bucket(value: str) -> str:
    s = norm_text(value)
    if 'ABIERTA' in s: return 'ABIERTA'
    if 'CERRAD' in s: return 'CERRADA'
    if 'OBRA' in s or 'CONSTRU' in s: return 'EN OBRA'
    if 'FIRMAD' in s: return 'FIRMADA'
    if not s: return 'SIN ESTADO'
    return s


def sudden_alerts(long: pd.DataFrame, metric='VENTAS', pct_threshold=0.25, z_threshold=2.0, min_value=1000) -> pd.DataFrame:
    d = long.sort_values(['CR','FECHA']).copy()
    d['PREVIO'] = d.groupby('CR')[metric].shift(1)
    d['CAMBIO_ABS'] = d[metric] - d['PREVIO']
    d['CAMBIO_PCT'] = np.where(d['PREVIO'].abs() >= min_value, d['CAMBIO_ABS'] / d['PREVIO'].abs(), np.nan)
    d['MEDIA_6M'] = d.groupby('CR')[metric].transform(lambda s: s.shift(1).rolling(6, min_periods=3).mean())
    d['STD_6M'] = d.groupby('CR')[metric].transform(lambda s: s.shift(1).rolling(6, min_periods=3).std())
    d['Z_SCORE'] = (d[metric] - d['MEDIA_6M']) / d['STD_6M'].replace(0, np.nan)
    d['TIPO_ALERTA'] = np.select([
        (d['CAMBIO_PCT'] >= pct_threshold) | (d['Z_SCORE'] >= z_threshold),
        (d['CAMBIO_PCT'] <= -pct_threshold) | (d['Z_SCORE'] <= -z_threshold),
    ], ['CRECIMIENTO REPENTINO','BAJÓN REPENTINO'], default='')
    out = d[d['TIPO_ALERTA'] != ''].copy()
    out['SEVERIDAD'] = np.select([out['CAMBIO_PCT'].abs() >= pct_threshold*2, out['Z_SCORE'].abs() >= z_threshold*1.5], ['ALTA','MEDIA'], default='BAJA')
    return out.sort_values(['FECHA','CAMBIO_PCT'], ascending=[False, False])
