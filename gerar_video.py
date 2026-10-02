import os
import re
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# =========================================================
# CONFIGURAÇÕES E CREDENCIAIS (SECRETS DO GITHUB)
# =========================================================
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID")

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")

def obter_credenciais():
    """Retorna as credenciais OAuth2 para as APIs do Google."""
    return Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

def upload_para_youtube(caminho_video, titulo, descricao, tags):
    """Envia o vídeo completo gerado diretamente para o YouTube."""
    creds = obter_credenciais()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        'snippet': {
            'title': titulo[:100],  # Limite máximo do YouTube para títulos
            'description': descricao,
            'tags': tags,
            'categoryId': '22'  # Categoria: Pessoas e Blogs (ou Notícias)
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(caminho_video, chunksize=-1, resumable=True, mimetype='video/mp4')

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progresso do upload para o YouTube: {int(status.progress() * 100)}%")

    print(f"✅ Vídeo de resumo completo enviado com sucesso! ID no YouTube: {response.get('id')}")
    return response.get('id')

def processar_e_postar_resumo_completo():
    """Busca o post mais recente do Blogger e cria o resumo em vídeo no formato 16:9."""
    creds = obter_credenciais()
    blogger = build("blogger", "v3", credentials=creds)

    # Busca postagens recentes do portal Coletividade Evolutiva
    res = blogger.posts().list(blogId=BLOG_ID, maxResults=10).execute()
    posts = res.get('items', [])

    if not posts:
        print("Nenhum post encontrado no Blogger.")
        return

    # Pega a matéria mais recente
    post_alvo = posts[0]
    titulo = post_alvo['title']
    url_post = post_alvo['url']
    
    print(f"🎬 Gerando resumo completo em vídeo (16:9) para: '{titulo}'")

    # =========================================================
    # LÓGICA DE MONTAGEM DO VÍDEO COMPLETO (16:9)
    # Certifique-se de que a resolução na renderização seja 1920x1080
    # =========================================================
    caminho_video_local = "video_resumo_completo.mp4"

    # Descrição completa direcionando leitores para o artigo no portal
    descricao = (
        f"📺 Resumo Completo em Vídeo | {titulo}\n\n"
        f"Confira os principais detalhes desta reportagem especial.\n\n"
        f"📖 Leia o artigo completo na íntegra no portal Coletividade Evolutiva:\n{url_post}\n\n"
        f"--- \n"
        f"Inscreva-se no canal e ative as notificações para acompanhar atualizações sobre Saúde, Ciência e Sociedade."
    )
    tags = ["Coletividade Evolutiva", "Saúde", "Ciência", "Notícias", "Resumo Completo", "Artigo"]

    # Faz o upload no YouTube se o arquivo do vídeo existir
    if os.path.exists(caminho_video_local):
        upload_para_youtube(caminho_video_local, titulo, descricao, tags)
    else:
        print(f"Aviso: Arquivo de vídeo '{caminho_video_local}' não localizado na pasta de execução.")

if __name__ == "__main__":
    processar_e_postar_resumo_completo()
