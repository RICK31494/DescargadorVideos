import os
import shutil
import tempfile
import ipaddress
import socket
from urllib.parse import urlparse

import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

MAX_DURATION_SECONDS = 60 * 60  # rechaza videos de más de 1 hora

# Cada red social y los dominios que aceptamos para ella.
PLATFORMS = {
    "youtube": ["youtube.com", "youtu.be"],
    "instagram": ["instagram.com"],
    "facebook": ["facebook.com", "fb.watch", "fb.com"],
    "tiktok": ["tiktok.com"],
    "twitter": ["twitter.com", "x.com"],
    "reddit": ["reddit.com", "redd.it"],
    "vimeo": ["vimeo.com"],
    "twitch": ["twitch.tv"],
    "pinterest": ["pinterest.com", "pin.it"],
    "dailymotion": ["dailymotion.com", "dai.ly"],
}



class UserError(Exception):
    pass

def is_public_host(host: str) -> bool:
    """Evita que alguien use la página para acceder a direcciones internas."""
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except socket.gaierror:
        return False
    return True

def validate(url: str, platform: str) -> str:
    url = (url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UserError("Pega un enlace completo que empiece con https://")
    if platform == "otro":
        if not is_public_host(parsed.hostname):
            raise UserError("Ese enlace no es válido.")
        return url
    if platform not in PLATFORMS:
        raise UserError("Elige una red social de la lista.")
    host = parsed.hostname.lower()
    if not any(host == d or host.endswith("." + d) for d in PLATFORMS[platform]):
        raise UserError("Ese enlace no parece ser de la red social que elegiste.")
    return url


def base_opts() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        # Para videos privados o con restricción de edad, exporta tus cookies
        # del navegador y descomenta la siguiente línea:
        # "cookiefile": "cookies.txt",
    }


def human_error(e: Exception) -> str:
    msg = str(e).lower()
    if "private" in msg or "login" in msg or "sign in" in msg:
        return "Este video es privado o necesita iniciar sesión, no se puede descargar."
    if "unsupported url" in msg:
        return "No se reconoce ese enlace. Revisa que sea el link directo a un video."
    if "unavailable" in msg or "not found" in msg or "404" in msg:
        return "El video no está disponible o fue eliminado."
    return "No se pudo procesar el enlace. Inténtalo de nuevo o prueba con otro video."


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/info")
def info():
    data = request.get_json(silent=True) or {}
    try:
        url = validate(data.get("url"), data.get("platform"))
        with yt_dlp.YoutubeDL(base_opts()) as ydl:
            meta = ydl.extract_info(url, download=False)
    except UserError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:  # yt-dlp lanza muchos tipos de error
        return jsonify(error=human_error(e)), 400

    if (meta.get("duration") or 0) > MAX_DURATION_SECONDS:
        return jsonify(error="El video dura más de 1 hora, es demasiado largo."), 400

    # Una opción por cada altura de video disponible.
    best_by_height = {}
    for f in meta.get("formats", []):
        h = f.get("height")
        if not h or f.get("vcodec") in (None, "none"):
            continue
        size = f.get("filesize") or f.get("filesize_approx")
        if h not in best_by_height or (size or 0) > (best_by_height[h] or 0):
            best_by_height[h] = size

    options = [
        {"id": f"v{h}", "label": f"{h}p", "kind": "video", "size": best_by_height[h]}
        for h in sorted(best_by_height, reverse=True)
    ]
    if not options:
        options.append({"id": "best", "label": "Mejor calidad", "kind": "video", "size": None})
    options.append({"id": "audio", "label": "Solo audio (MP3)", "kind": "audio", "size": None})

    return jsonify(
        title=meta.get("title") or "Sin título",
        uploader=meta.get("uploader") or "",
        duration=meta.get("duration"),
        thumbnail=meta.get("thumbnail"),
        options=options,
    )


@app.get("/api/download")
def download():
    platform = request.args.get("platform")
    choice = request.args.get("option", "best")
    try:
        url = validate(request.args.get("url"), platform)
    except UserError as e:
        return jsonify(error=str(e)), 400

    tmp = tempfile.mkdtemp(prefix="bajalo_")
    opts = base_opts()
    opts["outtmpl"] = os.path.join(tmp, "%(title).80s.%(ext)s")
    opts["restrictfilenames"] = True

    if choice == "audio":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    elif choice.startswith("v") and choice[1:].isdigit():
        h = int(choice[1:])
        opts["format"] = (
            f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/bv*[height<={h}]+ba/b[height<={h}]/b"
        )
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b"
        opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
        files = [os.path.join(tmp, n) for n in os.listdir(tmp)]
        if not files:
            raise RuntimeError("sin archivo")
        path = max(files, key=os.path.getsize)
    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        print("ERROR DESCARGA:", e)
        return jsonify(error=human_error(e)), 400

    response = send_file(path, as_attachment=True, download_name=os.path.basename(path))
    response.call_on_close(lambda: shutil.rmtree(tmp, ignore_errors=True))
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)
