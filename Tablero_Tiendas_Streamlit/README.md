# Tablero de tiendas — Streamlit

Aplicación Streamlit para analizar dos archivos Excel:

- **Book.xlsx**: usa exclusivamente la hoja `JUN`.
- **LibroVentas.xlsx**: usa todas las hojas excepto `INFO TIENDAS` (en especial `HISTORICO VENTAS`, `HISTORICO CON`, `BD U6M` y `BD M`).

La aplicación actualiza automáticamente los archivos desde enlaces compartidos de OneDrive/SharePoint. OneDrive es la única fuente de datos; no hay carga manual de bases. Los enlaces se guardan como Secrets de Streamlit y nunca se incluyen en el repositorio.

## Funcionalidades

- KPIs de tiendas totales, abiertas, cerradas, en obra y firmadas.
- Explorador interactivo de tiendas inspirado en la hoja `INICIO`: búsqueda por CR/nombre, tarjeta de estado, ubicación, apertura, operación y métricas.
- Sistema visual por capas independientes: el nombre de la tienda usa el color del estado (`ABIERTA`, `CERRADA`, `EN OBRA`, `FIRMADA`); si está abierta, `BA` y `-R` aparecen como distintivos separados; `SEG26` colorea `BASE`, `HOGAR` y `RECESO`; `TIE26` colorea `TMCB` y cualquier `EXP`.
- Histórico individual de ventas y contribución para la tienda seleccionada.
- Torre de control por clasificación con ventas, contribución, margen, renta, batting y contribución como porcentaje de ventas.
- Matriz de ventas vs contribución y ranking de oportunidades/riesgos contra U6M.
- Distribución por estado, zona, departamento, segmento y tipo de local.
- Mapa de tiendas cuando existen coordenadas `Y` y `X`.
- Ventas y contribución mensual: total, promedio, conteo y rankings.
- Alertas de crecimiento/bajón repentino mediante cambio contra mes previo y z-score contra una ventana móvil de seis meses.
- Panel de señales tipo bolsa: tarjetas de tiendas que subieron, bajaron o quedaron estables; mapa de movimiento; ranking de mayores subidas/bajadas; ficha individual con gráfico histórico y media móvil de seis meses.
- Pestaña `Versus` para seleccionar hasta ocho tiendas y comparar ventas, contribución, variación mensual, tráfico, ticket, renta, margen y segmentación en gráficos y tabla exportable.
- Filtros por segmento, generación (`TIE26`), departamento, municipio, estrato, generador, zona y tipo de local.
- Búsqueda de tiendas y exportación CSV.
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
5. Reinicia la app. Verás el aviso `Bases cargadas desde OneDrive`.

Los enlaces actuales que compartiste pueden colocarse en esas dos variables; no los agregué al ZIP para no exponerlos en GitHub.

## Criterio de alertas

Una tienda queda marcada cuando el último dato disponible cumple al menos una condición: cambio porcentual absoluto frente al mes anterior mayor o igual al umbral configurado, o desviación absoluta frente a la media de los seis meses previos mayor o igual al z-score configurado. Se exige una venta previa mínima configurable para evitar porcentajes engañosos sobre bases demasiado pequeñas.
