import os
import re
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# =========================================================
# CONFIGURAÇÕES E CREDENCIAIS (LIDAS DOS SECRETS DO GITHUB)
# =========================================================
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID")

# Credenciais OAuth2 para Blogger e YouTube
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")

def obter_credenciais():
    """Retorna as credenciais OAuth2 válidas."""
    return Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

def upload_para_youtube(caminho_video, titulo, descricao, tags):
    """Realiza o upload do vídeo MP4 gerado diretamente para o YouTube."""
    creds = obter_credenciais()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        'snippet': {
            'title': titulo[:100],  # Limite do YouTube
            'description': descricao,
            'tags': tags,
            'categoryId': '22'  # Categoria: Pessoas e Blogs (ou Saúde/Ciência)
        },
        'status': {
            'privacyStatus': 'public',  # 'public', 'unlisted' ou 'private'
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

    print(f"✅ Vídeo enviado com sucesso para o YouTube! ID: {response.get('id')}")
    return response.get('id')

def processar_e_postar_no_youtube():
    """Identifica o post mais recente do Blogger e envia o resumo para o YouTube."""
    creds = obter_credenciais()
    blogger = build("blogger", "v3", credentials=creds)

    # 1. Busca matérias recentes do blog
    res = blogger.posts().list(blogId=BLOG_ID, maxResults=10).execute()
    posts = res.get('items', [])

    if not posts:
        print("Nenhum post encontrado no Blogger.")
        return

    # Pega o post mais recente
    post_alvo = posts[0]
    titulo = post_alvo['title']
    url_post = post_alvo['url']
    
    print(f"Criando vídeo de resumo para a matéria: '{titulo}'")

    # 2. Lógica para gerar o arquivo MP4 (voz/vídeo/IA)
    # Supondo que o seu pipeline gera o arquivo local 'video_resumo.mp4'
    caminho_video_local = "video_resumo.mp4"

    # Monta descrição com link de retorno para o portal Coletividade Evolutiva
    descricao = (
        f"{titulo}\n\n"
        f"📖 Leia a matéria completa no portal Coletividade Evolutiva:\n{url_post}\n\n"
        f"#coletividadeevolutiva #saude #ciencia #noticias"
    )
    tags = ["Coletividade Evolutiva", "Saúde", "Ciência", "Notícias", "Resumo"]

    # 3. Faz o upload diretamente para o YouTube
    if os.path.exists(caminho_video_local):
        upload_para_youtube(caminho_video_local, titulo, descricao, tags)
    else:
        print(f"Erro: O arquivo de vídeo '{caminho_video_local}' não foi gerado.")

if __name__ == "__main__":
    processar_e_postar_no_youtube()
