#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 INSERÇÃO DO VÍDEO NA POSTAGEM DO BLOGGER (automático)
=============================================================================
 Depois que o Short é publicado no YouTube, este módulo injeta no fim da
 postagem original um bloco com:
   • player leve (só carrega o iframe do YouTube após o clique)
   • dados estruturados VideoObject (o que faz o vídeo aparecer no Google)
   • transcrição da locução (texto indexável — reforço de SEO)

 Usa a Blogger API v3 com o mesmo login do YouTube (escopo "blogger").
 Basta rodar uma vez o autorizar_youtube.py para obter o refresh token.
=============================================================================
"""

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CFG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))

MARCA_INICIO = "<!-- cev-short:inicio -->"
MARCA_FIM = "<!-- cev-short:fim -->"


def _servico():
    from googleapiclient.discovery import build
    from enviar_youtube import credenciais
    return build("blogger", "v3", credentials=credenciais(), cache_discovery=False)


def _blog_id(srv):
    if CFG.get("blogger", {}).get("blog_id"):
        return CFG["blogger"]["blog_id"]
    info = srv.blogs().getByUrl(blogUrl=CFG["blog_url"]).execute()
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
        "thumbnailUrl": [capa,
                         f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
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
<div class="cev-short-post" data-cev-video="{vid}">
  <p class="cev-short-titulo"><strong>▶ Vídeo-resumo desta matéria</strong></p>
  <div class="cev-short-player" data-yt="{vid}" data-titulo="{titulo}">
    <a class="cev-short-capa" href="{url}" target="_blank" rel="noopener nofollow"
       aria-label="Assistir ao vídeo: {titulo}">
      <img src="{capa}" alt="Vídeo-resumo: {titulo}"
           width="1080" height="1920" loading="lazy" decoding="async"/>
      <span class="cev-short-play" aria-hidden="true"></span>
      <span class="cev-short-tempo">{tempo_legivel}</span>
    </a>
  </div>
  <p class="cev-short-legenda">Resumo em vídeo produzido automaticamente pela redação.
  <a href="{url}" target="_blank" rel="noopener nofollow">Assista no YouTube</a></p>
  <details class="cev-short-transcricao">
    <summary>Transcrição do vídeo</summary>
    <p>{narracao}</p>
  </details>
</div>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
{MARCA_FIM}"""


def inserir_na_postagem(srv, blog_id, url_post, meta):
    """Adiciona (ou substitui) o bloco de vídeo no fim da postagem."""
    pid = url_post.rstrip("/").split("/")[-1].replace(".html", "")
    post = srv.posts().get(blogId=blog_id, postId=pid).execute()
    conteudo = post.get("content", "")

    # remove bloco anterior, se existir (idempotente)
    conteudo = re.sub(re.escape(MARCA_INICIO) + r".*?" + re.escape(MARCA_FIM),
                      "", conteudo, flags=re.S).strip()

    novo = conteudo + "\n\n" + _bloco(meta)
    srv.posts().patch(blogId=blog_id, postId=pid,
                      body={"content": novo}).execute()
    print(f"   Blogger: vídeo inserido em {url_post}")
    return True


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
