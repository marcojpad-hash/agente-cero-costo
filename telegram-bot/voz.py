#!/usr/bin/env python3
"""Voz gratis para el bot de Telegram (sin pagar nada).

Pipeline 100% gratis y offline en la VM de Pecas:
  voz de Telegram (ogg opus) -> ffmpeg -> wav 16k mono
  -> faster-whisper (base, es) -> texto
  -> agregador (Groq + Gemini, gratis) -> respuesta
  -> Piper (es_MX, offline) -> wav -> ffmpeg opus -> ogg
  -> sendVoice de Telegram

No usa la API de Telegram para la voz (no hay servicio de voz propio
de Telegram: el bot solo reenvia audio). STT y TTS son open source
y corren en la VM. faster-whisper se llama por subprocess al venv
de Piper para no mezclar dependencias con el bot (que es stdlib).

El bug de av: faster-whisper 1.2.1 con av 19 falla en decode_audio
(metadata_errors). Por eso se decodifica con ffmpeg + wave a un
arreglo numpy y se le pasa el arreglo a transcribe, no la ruta.
"""
import json
import os
import subprocess
import sys
import urllib.request
import uuid

PIPER_BIN = os.path.expanduser(os.environ.get(
    "PIPER_BIN", "~/workspace/piper-venv/bin/piper"))
PIPER_MODEL = os.path.expanduser(os.environ.get(
    "PIPER_MODEL", "~/workspace/piper-voices/es_MX-ald-medium.onnx"))
VOZ_PYTHON = os.path.expanduser(os.environ.get(
    "VOZ_PYTHON", "~/workspace/piper-venv/bin/python"))

_STT_SCRIPT = r"""
import sys
import wave
import numpy as np
from faster_whisper import WhisperModel

ruta = sys.argv[1]
with wave.open(ruta, "rb") as w:
    raw = w.readframes(w.getnframes())
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, _info = model.transcribe(audio, language="es")
print(" ".join(s.text for s in segments))
"""


def descargar_voz(token, file_id):
    """Baja el ogg de un mensaje de voz de Telegram a /tmp."""
    url_info = ("https://api.telegram.org/bot%s/getFile?file_id=%s"
                % (token, file_id))
    with urllib.request.urlopen(url_info, timeout=60) as r:
        info = json.load(r)
    ruta = info["result"]["file_path"]
    url_archivo = "https://api.telegram.org/file/bot%s/%s" % (token, ruta)
    local = "/tmp/%s.ogg" % uuid.uuid4()
    urllib.request.urlretrieve(url_archivo, local)
    return local


def ogg_a_wav16k(ruta_ogg):
    """Convierte ogg a wav 16 kHz mono (lo que pide faster-whisper)."""
    ruta_wav = os.path.splitext(ruta_ogg)[0] + ".wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", ruta_ogg,
         "-ar", "16000", "-ac", "1", ruta_wav],
        check=True, capture_output=True)
    return ruta_wav


def transcribir(ruta_wav):
    """STT gratis con faster-whisper (base, es). Devuelve el texto.
    Re-muestrea a 16 kHz primero: faster-whisper supone 16 kHz y un
    wav de Piper (22050 Hz) o de Telegram sin convertir lo confunde."""
    ruta_16k = os.path.splitext(ruta_wav)[0] + "-16k.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", ruta_wav,
         "-ar", "16000", "-ac", "1", ruta_16k],
        check=True, capture_output=True)
    try:
        r = subprocess.run(
            [VOZ_PYTHON, "-c", _STT_SCRIPT, ruta_16k],
            capture_output=True, text=True, timeout=300)
    finally:
        try:
            os.remove(ruta_16k)
        except OSError:
            pass
    if r.returncode != 0:
        raise RuntimeError(
            "faster-whisper fallo: %s" % (r.stderr or r.stdout)[:300])
    return r.stdout.strip()


def hablar(texto):
    """TTS gratis con Piper (es_MX). Devuelve la ruta del ogg opus
    listo para mandar como mensaje de voz de Telegram."""
    ruta_wav = "/tmp/%s.wav" % uuid.uuid4()
    r = subprocess.run(
        [PIPER_BIN, "--model", PIPER_MODEL,
         "--output_file", ruta_wav],
        input=texto.encode("utf-8"),
        capture_output=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(
            "piper fallo: %s" % (r.stderr or r.stdout)[:300])
    ruta_ogg = os.path.splitext(ruta_wav)[0] + ".ogg"
    subprocess.run(
        ["ffmpeg", "-y", "-i", ruta_wav,
         "-c:a", "libopus", ruta_ogg],
        check=True, capture_output=True)
    try:
        os.remove(ruta_wav)
    except OSError:
        pass
    return ruta_ogg


def enviar_voz(token, chat_id, ruta_ogg):
    """Manda un ogg opus como mensaje de voz (multipart, stdlib)."""
    boundary = "----%s" % uuid.uuid4()
    with open(ruta_ogg, "rb") as f:
        datos = f.read()
    cuerpo = (
        ("--%s\r\n"
         'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
         "%s\r\n"
         "--%s\r\n"
         'Content-Disposition: form-data; name="voice"; '
         'filename="voice.ogg"\r\n'
         "Content-Type: audio/ogg\r\n\r\n" % (boundary, chat_id, boundary)
         ).encode("utf-8")
        + datos
        + ("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendVoice" % token,
        data=cuerpo,
        headers={"Content-Type":
                 "multipart/form-data; boundary=%s" % boundary})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def limpiar(*rutas):
    for ruta in rutas:
        if not ruta:
            continue
        try:
            os.remove(ruta)
        except OSError:
            pass


if __name__ == "__main__":
    # Prueba local sin Telegram: transcribe y habla.
    if len(sys.argv) < 2:
        print("uso: voz.py <wav> [texto para hablar]")
        sys.exit(1)
    print("STT:", transcribir(sys.argv[1]))
    if len(sys.argv) > 2:
        print("TTS:", hablar(" ".join(sys.argv[2:])))
