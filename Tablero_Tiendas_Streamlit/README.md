# Tablero de tiendas — Streamlit

Aplicación local para analizar dos archivos Excel:

- **Book.xlsx**: usa exclusivamente la hoja `JUN`.
- **LibroVentas.xlsx**: usa todas las hojas excepto `INFO TIENDAS` (en especial `HISTORICO VENTAS`, `HISTORICO CON`, `BD U6M` y `BD M`).

La aplicación **no se conecta a SharePoint**. Los archivos se cargan manualmente con los controles de Streamlit y se procesan en memoria.

## Funcionalidades

- KPIs de tiendas totales, abiertas, cerradas, en obra y firmadas.
- Distribución por estado, zona, departamento, segmento y tipo de local.
- Mapa de tiendas cuando existen coordenadas `Y` y `X`.
- Ventas y contribución mensual: total, promedio, conteo y rankings.
- Alertas de crecimiento/bajón repentino mediante cambio contra mes previo y z-score contra una ventana móvil de seis meses.
- Filtros por zona y estado, búsqueda de tiendas y exportación CSV.
- Validaciones básicas de cobertura y datos faltantes.

## Ejecución local

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Después abre la URL local que muestra Streamlit y carga ambos archivos.

## Publicar en GitHub

1. Crea un repositorio nuevo y sube `app.py`, `src/`, `requirements.txt`, `README.md` y `.gitignore`.
2. No subas archivos Excel con información sensible; el `.gitignore` ya excluye `*.xlsx`.
3. En Streamlit Community Cloud selecciona el repositorio, rama y archivo `app.py`.
4. Los usuarios deberán cargar los dos archivos en cada sesión.

## Criterio de alertas

Una tienda queda marcada cuando el último dato disponible cumple al menos una condición: cambio porcentual absoluto frente al mes anterior mayor o igual al umbral configurado, o desviación absoluta frente a la media de los seis meses previos mayor o igual al z-score configurado. Se exige una venta previa mínima configurable para evitar porcentajes engañosos sobre bases demasiado pequeñas.
