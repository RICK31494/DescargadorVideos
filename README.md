# Bájalo

Página web para descargar videos de redes sociales: eliges la red, pegas el link y escoges la calidad.
Backend en Flask + yt-dlp. Redes incluidas: YouTube, Instagram, Facebook, TikTok, X, Reddit, Vimeo, Twitch, Pinterest y Dailymotion.

## Instalación

1. Instala Python 3.9 o superior.
2. Instala **FFmpeg** (necesario para unir video y audio y para el MP3):
   - Windows: `winget install ffmpeg`
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
3. En la carpeta del proyecto:

```bash
python -m venv venv
venv\Scripts\activate        # en Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

4. Abre http://127.0.0.1:5000

## Estructura

```
bajalo/
├── app.py              # API: /api/info (datos y calidades) y /api/download
├── templates/
│   └── index.html      # Interfaz
└── requirements.txt
```

## Cosas que debes saber

- **Mantén yt-dlp actualizado.** Las plataformas cambian seguido y se rompe si no: `pip install -U yt-dlp`.
- **Videos privados:** no se pueden descargar sin tu sesión. Puedes exportar las cookies de tu navegador a `cookies.txt` y activar la línea `cookiefile` en `app.py`, pero úsalo solo con tu propia cuenta.
- **Publicarla en internet:** YouTube e Instagram suelen bloquear las IPs de servidores en la nube, y una página pública necesita límites de uso (rate limiting), más espacio en disco y ancho de banda. Para uso personal, correrla en tu computador es lo más estable.
- **Legal:** descargar contenido va contra los términos de servicio de la mayoría de plataformas y puede violar derechos de autor. Úsala con videos tuyos o con permiso del autor.
