#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 ENVIO AUTOMÁTICO PARA O YOUTUBE SHORTS
=============================================================================
 Publica o mini vídeo no canal e, opcionalmente, adiciona à playlist de Shorts
 (usada pelo widget que roda no blog).

 Credenciais (variáveis de ambiente ou arquivo .env na raiz do projeto):
   YT_CLIENT_ID       -> ID do cliente OAuth (Google Cloud Console)
   YT_CLIENT_SECRET   -> Segredo do cliente OAuth
   YT_REFRESH_TOKEN   -> Token de atualização (gerado por autorizar_youtube.py)

 Cota: o YouTube concede 100 uploads por dia, gratuitamente, por projeto.
=============================================================================
"""

import json
import os
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CFG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))

ESCOPOS = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/blogger",
]


def _carregar_env():
    """Lê variáveis do ambiente e, se faltarem, de um arquivo .env local."""
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def credenciais():
    _carregar_env()
    from google.oauth2.credentials import Credentials
    faltando = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
                if not os.environ.get(k)]
    if faltando:
        sys.exit("ERRO: variáveis ausentes -> " + ", ".join(faltando) +
                 "\nRode primeiro: python3 gerador/autorizar_youtube.py")
    return Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=ESCOPOS,
    )


def enviar_short(caminho_video, meta, privacidade=None):
    """Faz o upload do Short. Devolve o ID e o link do vídeo."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    yt = build("youtube", "v3", credentials=credenciais(), cache_discovery=False)
    priv = privacidade or meta.get("privacidade") or CFG["youtube"]["privacidade"]

    corpo = {
        "snippet": {
            "title": meta["titulo"][:100],
            "description": meta["descricao"][:4900],
            "tags": meta["tags"][:18],
            "categoryId": CFG["youtube"].get("categoria_id", "25"),
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {
            "privacyStatus": priv,
            "selfDeclaredMadeForKids": False,
            # ajuda a classificar como Short sem depender do formato
            "madeForKids": False,
        },
    }

    midia = MediaFileUpload(caminho_video, chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=corpo, media_body=midia,
                             notifySubscribers=CFG["youtube"].get("notificar_inscritos", True))

    resposta = None
    while resposta is None:
        status, resposta = req.next_chunk()
        if status:
            print(f"   envio: {int(status.progress() * 100)}%", flush=True)

    vid = resposta["id"]
    print(f"   YouTube: https://www.youtube.com/shorts/{vid}")

    # capa personalizada
    capa = meta.get("capa")
    if capa and Path(capa).exists():
        try:
            yt.thumbnails().set(videoId=vid,
                                media_body=MediaFileUpload(capa, mimetype="image/jpeg")).execute()
            print("   capa personalizada aplicada")
        except Exception as e:
            print(f"   aviso: capa não aplicada ({e})")

    # playlist de Shorts (alimenta o widget do blog automaticamente)
    pl = CFG["youtube"].get("playlist_shorts") or os.environ.get("YT_PLAYLIST_SHORTS")
    if pl:
        try:
            yt.playlistItems().insert(
                part="snippet",
                body={"snippet": {"playlistId": pl,
                                  "resourceId": {"kind": "youtube#video", "videoId": vid}}},
            ).execute()
            print("   adicionado à playlist de Shorts")
        except Exception as e:
            print(f"   aviso: playlist não atualizada ({e})")

    meta["youtube_id"] = vid
    meta["youtube_url"] = f"https://www.youtube.com/shorts/{vid}"
    return meta


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("uso: python3 enviar_youtube.py <video.mp4> <metadados.json>")
    m = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    enviar_short(sys.argv[1], m)