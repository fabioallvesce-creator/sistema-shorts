import os
import re
import sys
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# =========================================================
# CONFIGURAÇÕES DE AMBIENTE (LIDO DOS SECRETS DO GITHUB)
# =========================================================
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

def obter_servico_blogger():
    """Autentica na API do Blogger utilizando o Refresh Token."""
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build("blogger", "v3", credentials=creds)

def gerar_html_sticky_video(video_url, poster_url):
    """
    Gera o bloco autossuficiente (HTML + CSS + JavaScript)
    para criar o efeito de vídeo flutuante (Sticky/Picture-in-Picture)
    ao rolar a página.
    """
    return f'''<!-- INÍCIO DO PLAYER FLUTUANTE CEV -->
<style type="text/css">
  .cev-sticky-wrapper {{
    width: 100%;
    max-width: 680px;
    margin: 0 auto 25px auto;
    min-height: 220px;
  }}
  .cev-sticky-box {{
    position: relative;
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
    background: #000;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    transition: all 0.35s ease-in-out;
  }}
  .cev-sticky-box video {{
    width: 100%;
    height: auto;
    display: block;
    max-height: 480px;
  }}
  .cev-sticky-close {{
    display: none;
    position: absolute;
    top: 8px;
    right: 8px;
    width: 28px;
    height: 28px;
    background: rgba(0, 0, 0, 0.75);
    color: #ffffff;
    border: none;
    border-radius: 50%;
    font-size: 18px;
    cursor: pointer;
    z-index: 99;
    align-items: center;
    justify-content: center;
    line-height: 1;
  }}
  .cev-sticky-box.is-floating {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 280px;
    z-index: 99999;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    animation: cevSlideIn 0.3s forwards;
  }}
  .cev-sticky-box.is-floating .cev-sticky-close {{
    display: flex;
  }}
  @keyframes cevSlideIn {{
    from {{ transform: translateY(40px); opacity: 0; }}
    to {{ transform: translateY(0); opacity: 1; }}
  }}
  @media (max-width: 600px) {{
    .cev-sticky-box.is-floating {{
      width: 210px;
      bottom: 15px;
      right: 15px;
    }}
  }}
</style>

<div class="cev-sticky-wrapper" id="cevStickyWrapper">
  <div class="cev-sticky-box" id="cevStickyBox">
    <button class="cev-sticky-close" onclick="fecharStickyVideoCEV()" title="Fechar vídeo">&#215;</button>
    <video id="cevVideoElement" controls="controls" poster="{poster_url}" playsinline="playsinline">
      <source src="{video_url}" type="video/mp4" />
      O seu navegador não suporta a reprodução de vídeo.
    </video>
  </div>
</div>

<script type="text/javascript">
//<![CDATA[
(function() {{
  document.addEventListener("DOMContentLoaded", function() {{
    var wrapper = document.getElementById("cevStickyWrapper");
    var box = document.getElementById("cevStickyBox");
    var video = document.getElementById("cevVideoElement");
    var fechoManual = false;

    if (!wrapper || !box || !video) return;

    if ('IntersectionObserver' in window) {{
      var observer = new IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
          if (!entry.isIntersecting && !fechoManual) {{
            box.classList.add("is-floating");
          }} else {{
            box.classList.remove("is-floating");
          }}
        }});
      }}, {{ threshold: 0.1 }});

      observer.observe(wrapper);
    }}

    window.fecharStickyVideoCEV = function() {{
      fechoManual = true;
      box.classList.remove("is-floating");
      if (video) {{
        video.pause();
      }}
    }};
  }});
}})();
//]]>
</script>
<!-- FIM DO PLAYER FLUTUANTE CEV -->
'''

def processar_proximo_post():
    """Procura o post mais recente sem vídeo e injeta o vídeo flutuante."""
    service = obter_servico_blogger()
    
    # Procura os últimos posts do blog
    res = service.posts().list(blogId=BLOG_ID, maxResults=15).execute()
    posts = res.get('items', [])

    post_alvo = None
    for p in posts:
        # Se a marcação do vídeo ainda não estiver no HTML do post
        if "cevStickyWrapper" not in p.get('content', ''):
            post_alvo = p
            break

    if not post_alvo:
        print("Nenhum post pendente encontrado para geração de vídeo.")
        return

    post_id = post_alvo['id']
    titulo = post_alvo['title']
    conteudo_original = post_alvo.get('content', '')

    print(f"Processando vídeo para o post: '{titulo}' (ID: {post_id})")

    # =========================================================
    # LÓGICA DE GERAÇÃO DO VÍDEO MP4 (Sua pipeline atual de IA/TTS)
    # =========================================================
    # Substitua pelas URLs geradas pelo seu processo de criação/upload
    video_mp4_url = f"https://sua-cdn-ou-servidor.com/videos/{post_id}.mp4"
    imagem_poster_url = f"https://sua-cdn-ou-servidor.com/capas/{post_id}.jpg"

    # Gera o bloco HTML do leitor flutuante
    bloco_video = gerar_html_sticky_video(video_mp4_url, imagem_poster_url)

    # Injeta o bloco no topo da matéria
    novo_conteudo = bloco_video + "\n" + conteudo_original

    # Atualiza o post na API do Blogger
    post_alvo['content'] = novo_conteudo
    
    # Opcional: Adiciona a etiqueta 'Com Vídeo'
    labels = post_alvo.get('labels', [])
    if "Com Vídeo" not in labels:
        labels.append("Com Vídeo")
    post_alvo['labels'] = labels

    service.posts().update(blogId=BLOG_ID, postId=post_id, body=post_alvo).execute()
    print(f"Post '{titulo}' atualizado com sucesso!")

if __name__ == "__main__":
    processar_proximo_post()
