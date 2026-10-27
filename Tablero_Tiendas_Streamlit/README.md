# Tablero de tiendas — Streamlit

Aplicación Streamlit para analizar dos archivos Excel:

- **Book.xlsx**: usa exclusivamente la hoja `JUN`.
- **LibroVentas.xlsx**: usa todas las hojas excepto `INFO TIENDAS` (en especial `HISTORICO VENTAS`, `HISTORICO CON`, `BD U6M` y `BD M`).

La aplicación puede actualizar automáticamente los archivos desde enlaces compartidos de OneDrive/SharePoint. Los enlaces se guardan como Secrets de Streamlit y nunca se incluyen en el repositorio. También conserva la carga manual como respaldo.

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

Después abre la URL local que muestra Streamlit. Para usar la conexión automática, crea `.streamlit/secrets.toml` (este archivo no debe subirse a GitHub):

```toml
ONEDRIVE_BOOK_URL = "https://femcom-my.sharepoint.com/:x:/g/personal/..."
ONEDRIVE_SALES_URL = "https://femcom-my.sharepoint.com/:x:/g/personal/..."
```

La app agrega automáticamente `download=1`, descarga el XLSX y refresca la copia cada 10 minutos. Para que funcione sin inicio de sesión, los enlaces deben tener permiso **Cualquier persona con el vínculo puede ver**. Si la organización exige autenticación, el enlace público no será suficiente y habrá que configurar una aplicación de Microsoft Graph/Azure AD con OAuth; no se deben poner usuario ni contraseña en el código.

## Publicar en GitHub

1. Crea un repositorio nuevo y sube `app.py`, `src/`, `requirements.txt`, `README.md` y `.gitignore`.
2. No subas archivos Excel con información sensible; el `.gitignore` ya excluye `*.xlsx`.
3. En Streamlit Community Cloud selecciona el repositorio, rama y archivo `app.py`.
4. En **Settings → Secrets**, pega las dos variables `ONEDRIVE_BOOK_URL` y `ONEDRIVE_SALES_URL` del ejemplo anterior.
5. Reinicia la app. Verás el aviso `Bases cargadas desde OneDrive` y los archivos manuales quedarán como respaldo.

Los enlaces actuales que compartiste pueden colocarse en esas dos variables; no los agregué al ZIP para no exponerlos en GitHub.

## Criterio de alertas

Una tienda queda marcada cuando el último dato disponible cumple al menos una condición: cambio porcentual absoluto frente al mes anterior mayor o igual al umbral configurado, o desviación absoluta frente a la media de los seis meses previos mayor o igual al z-score configurado. Se exige una venta previa mínima configurable para evitar porcentajes engañosos sobre bases demasiado pequeñas.
