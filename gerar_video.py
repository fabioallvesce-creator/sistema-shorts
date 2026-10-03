import os
import sys
import json
import argparse
import subprocess
import feedparser
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

FEED_URL = "https://www.coletividadeevolutiva.com/feeds/posts/default?alt=rss"
RAIZ = Path(__file__).resolve().parent
SAIDA_DIR = RAIZ / "saida"
PROCESSED_FILE = SAIDA_DIR / "processados.json"

def carregar_processados():
    if PROCESSED_FILE.exists():
        try:
            return json.loads(PROCESSED_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def salvar_processado(link_post):
    SAIDA_DIR.mkdir(exist_ok=True)
    processados = carregar_processados()
    if link_post not in processados:
        processados.append(link_post)
        PROCESSED_FILE.write_text(json.dumps(processados, ensure_ascii=False, indent=4), encoding="utf-8")

def obter_credenciais_yt():
    return Credentials(
        None,
        refresh_token=os.environ.get("YT_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("YT_CLIENT_ID"),
        client_secret=os.environ.get("YT_CLIENT_SECRET")
    )

def criar_video_ffmpeg(titulo, arquivo_saida):
    SAIDA_DIR.mkdir(exist_ok=True)
    
    # Sanitização de string para os filtros de texto do FFmpeg
    titulo_formatado = titulo.replace(":", "\\:").replace("'", "").replace('"', '').replace("%", "\\%")
    
    fonte_path = RAIZ / "Inter-Bold.ttf"
    filtro_fonte = f":fontfile='{fonte_path}'" if fonte_path.exists() else ""

    filter_complex = (
        f"drawtext=text='{titulo_formatado}'{filtro_fonte}:"
        f"fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2:"
        f"box=1:boxcolor=black@0.6:boxborderw=20"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x0f172a:s=1920x1080:d=30",
        "-vf", filter_complex,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(arquivo_saida)
    ]

    print(f"🎬 Renderizando vídeo via FFmpeg: {arquivo_saida}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"Erro na renderização do FFmpeg: {res.stderr.decode('utf-8', errors='ignore')}")

def enviar_para_youtube(caminho_video, titulo, url_materia):
    print("🚀 Iniciando envio para o YouTube...")
    creds = obter_credenciais_yt()
    youtube = build("youtube", "v3", credentials=creds)

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
            'tags': ["Coletividade Evolutiva", "Saúde", "Ciência", "Notícias", "Resumo"],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(str(caminho_video), chunksize=-1, resumable=True, mimetype='video/mp4')
    
    try:
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Progresso do Upload: {int(status.progress() * 100)}%")

        video_id = response.get('id')
        print(f"✅ VÍDEO PUBLICADO COM SUCESSO! URL: https://www.youtube.com/watch?v={video_id}")
        return video_id

    except HttpError as e:
        if "uploadLimitExceeded" in str(e):
            print("\n⚠️ AVISO DA API DO YOUTUBE:")
            print("O limite diário de uploads da cota da API ou da verificação do canal foi atingido.")
            print("O vídeo foi gerado corretamente e o envio será reprocessado na próxima janela de 24 horas.\n")
            return None
        else:
            print(f"❌ Erro HTTP na API do YouTube: {e}")
            raise e

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", action="store_true")
    parser.add_argument("--lote", type=int, default=1)
    parser.add_argument("--envio", action="store_true")
    parser.add_argument("--todos", action="store_true")
    args = parser.parse_args()

    print("🔍 Lendo feed do portal...")
    feed = feedparser.parse(FEED_URL)

    if not feed.entries:
        print("❌ Nenhum post localizado no RSS.")
        sys.exit(1)

    processados = carregar_processados()
    posts = feed.entries[:args.lote] if args.todos else [e for e in feed.entries if e.link not in processados][:args.lote]

    if not posts:
        print("ℹ️ Nenhuma matéria pendente para processar.")
        return

    for post in posts:
        titulo = post.title
        link = post.link
        print(f"\n==========================================")
        print(f"📌 Processando: {titulo}")
        print(f"🔗 Link: {link}")

        video_file = SAIDA_DIR / "video_resumo.mp4"
        criar_video_ffmpeg(titulo, video_file)

        if args.envio:
            video_id = enviar_para_youtube(video_file, titulo, link)
            if video_id:
                salvar_processado(link)

if __name__ == "__main__":
    main()
