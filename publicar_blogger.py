#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 INSERÇÃO DO VÍDEO NA POSTAGEM DO BLOGGER (Embed Nativo e Posição no Topo)
=============================================================================
"""
import os
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
CFG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))

MARCA_INICIO = "<!-- cev-short:inicio -->"
MARCA_FIM = "<!-- cev-short:fim -->"


def _servico():
    from googleapiclient.discovery import build
    from enviar_youtube import credenciais
    return build("blogger", "v3", credentials=credenciais(), cache_discovery=False)


def _blog_id(srv):
    blog_id = os.getenv("BLOGGER_BLOG_ID")
    if blog_id:
        return blog_id
    info = srv.blogs().getByUrl(url=CFG["blog_url"]).execute()
    return info["id"]


def _bloco(meta):
    vid = meta["youtube_id"]
    titulo = meta["titulo_curto"]
    capa = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
    url = meta["youtube_url"]
    narracao = meta.get("narracao", "")
    descricao = re.sub(r"\s+", " ", narracao)[:600]
    duracao = int(meta.get("duracao_segundos", CFG.get("duracao", 45)))
    minutos, segundos = divmod(duracao, 60)
    tempo_legivel = f"{minutos}:{segundos:02d}" if minutos else f"0:{segundos:02d}"
    iso_duracao = f"PT{minutos}M{segundos}S" if minutos else f"PT{segundos}S"

    schema = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": titulo,
        "description": descricao or titulo,
        "thumbnailUrl": [capa, f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
        "uploadDate": meta.get("gerado_em", ""),
        "duration": iso_duracao,
        "contentUrl": url,
        "embedUrl": f"https://www.youtube.com/embed/{vid}",
        "publisher": {
            "@type": "Organization",
            "name": CFG["site_name"],
            "url": CFG["blog_url"],
        },
        "inLanguage": "pt-BR",
        "isFamilyFriendly": True,
    }

    return f"""{MARCA_INICIO}
<div class="cev-short-wrapper">
  <div class="cev-short-header">
    <span>🎬 ASSISTIR EM VÍDEO (0:45)</span>
  </div>
  <div class="cev-short-frame">
    <iframe 
      src="https://www.youtube.com/embed/{vid}?autoplay=0&rel=0" 
      title="{titulo}" 
      loading="lazy" 
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
      allowfullscreen>
    </iframe>
  </div>
</div>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
{MARCA_FIM}"""


def inserir_na_postagem(srv, blog_id, url_origem, meta):
    parsed = urlparse(url_origem)
    path = parsed.path

    try:
        post = srv.posts().getByPath(blogId=blog_id, path=path).execute()
    except Exception:
        post = srv.posts().get(blogId=blog_id, postId=url_origem).execute()

    content = post.get("content", "")
    bloco_html = _bloco(meta)

    # 1. Se já existe o bloco antigo/existente, substitui
    if MARCA_INICIO in content and MARCA_FIM in content:
        pattern = re.escape(MARCA_INICIO) + r".*?" + re.escape(MARCA_FIM)
        new_content = re.sub(pattern, bloco_html, content, flags=re.DOTALL)
    else:
        # 2. Tenta inserir logo após o primeiro parágrafo no topo
        if "</p>" in content:
            partes = content.split("</p>", 1)
            new_content = partes[0] + "</p>\n\n" + bloco_html + "\n\n" + partes[1]
        else:
            # Caso o texto não tenha marcação de parágrafo, insere no topo
            new_content = bloco_html + "\n\n" + content

    post["content"] = new_content
    res = srv.posts().update(blogId=blog_id, postId=post["id"], body=post).execute()
    print(f"    Blogger: vídeo incorporado no topo de {url_origem}")
    return res


def publicar(meta):
    srv = _servico()
    bid = _blog_id(srv)
    return inserir_na_postagem(srv, bid, meta["url_origem"], meta)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python3 publicar_blogger.py <metadados.json>")
    m = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if "youtube_id" not in m:
        sys.exit("ERRO: rode o envio ao YouTube antes (metadados sem youtube_id).")
    publicar(m)
