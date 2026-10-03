import os
import sys
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Aponta para o diretório atual onde o arquivo enviar_youtube.py e config.json estão localizados
RAIZ = Path(__file__).resolve().parent
CONFIG_PATH = RAIZ / "config.json"

# Carrega as configurações do config.json se ele existir
if CONFIG_PATH.exists():
    CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
else:
    CFG = {}

def obter_credenciais():
    """Recupera credenciais dos Secrets do GitHub."""
    return Credentials(
        None,
        refresh_token=os.environ.get("YT_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("YT_CLIENT_ID"),
        client_secret=os.environ.get("YT_CLIENT_SECRET")
    )

def publicar(caminho_video, titulo, url_materia):
    """Realiza o upload do vídeo gerado para o YouTube Shorts / Vídeo normal."""
    if not os.path.exists(caminho_video):
        print(f"Erro: O arquivo de vídeo {caminho_video} não foi localizado.")
        return None

    creds = obter_credenciais()
    youtube = build("youtube", "v3", credentials=creds)

    # Descrição contendo o link de direcionamento para o portal Coletividade Evolutiva
    descricao = (
        f"{titulo}\n\n"
        f"▶ Leia a matéria completa no portal:\n{url_materia}\n\n"
        f"📍 Coletividade Evolutiva\n👉 https://www.coletividadeevolutiva.com\n\n"
        f"#coletividadeevolutiva #saude #ciencia #noticias"
    )

    body = {
        'snippet': {
            'title': titulo[:100],
            'description': descricao,
            'tags': ["Coletividade Evolutiva", "Saúde", "Ciência", "Notícias"],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(caminho_video, chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progresso do upload: {int(status.progress() * 100)}%")

    video_id = response.get('id')
    print(f"✅ Vídeo publicado com sucesso no YouTube: https://www.youtube.com/watch?v={video_id}")
    return video_id
