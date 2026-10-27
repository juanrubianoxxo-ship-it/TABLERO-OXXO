from __future__ import annotations

from io import BytesIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests


def with_download_flag(url: str) -> str:
    """Add download=1 while preserving the original SharePoint sharing token."""
    parts = urlsplit(url.strip())
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["download"] = "1"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def download_excel(url: str, timeout: int = 90) -> BytesIO:
    if not url or not url.startswith(("https://", "http://")):
        raise ValueError("La URL de OneDrive debe comenzar por http:// o https://")
    response = requests.get(
        with_download_flag(url),
        timeout=timeout,
        allow_redirects=True,
        headers={"User-Agent": "streamlit-tiendas/1.0"},
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "html" in content_type and not response.content.startswith(b"PK"):
        raise ValueError(
            "OneDrive devolvió una página HTML en vez de un Excel. "
            "Verifica que el enlace tenga permiso 'Cualquier persona con el vínculo puede ver'."
        )
    if not response.content.startswith(b"PK"):
        raise ValueError("La respuesta no parece ser un archivo XLSX válido.")
    return BytesIO(response.content)
