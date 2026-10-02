#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 GERADOR AUTOMÁTICO DE VÍDEOS-RESUMO  |  Coletividade Evolutiva
=============================================================================
 Lê as últimas postagens do Blogger (feed Atom), transforma cada uma em um
 vídeo vertical de 45 segundos (1080x1920) com resumo narrado do artigo,
 Instagram Reels, TikTok, Facebook Reels e para embed no próprio blog.

 100% gratuito e sem marca d'água de terceiros:
   - FFmpeg            -> codificação do vídeo
   - edge-tts          -> narração neural em português (vozes da Microsoft)
   - Pillow            -> arte e tipografia (identidade do portal)
   - Fontes Inter     -> licença SIL Open Font License

 Uso:
   python3 gerar_video.py --feed          # pega a postagem mais recente e gera
   python3 gerar_video.py --url <link>    # gera de um link específico
   python3 gerar_video.py --feed --lote 3 # gera as 3 mais recentes
   python3 gerar_video.py --feed --envio  # gera e envia para o YouTube
=============================================================================
"""

import argparse
import asyncio
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
except ImportError:
    sys.exit("ERRO: instale o Pillow -> sudo pip3 install pillow")

RAIZ = Path(__file__).resolve().parent.parent
CFG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))


# =============================================================================
# 1. UTILITÁRIOS
# =============================================================================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def hex2rgb(h, alpha=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def baixar(url, destino):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; CEV-VideoBot/1.0)",
        "Accept": "*/*",
    })
    with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)
    return Path(destino)


def limpar_texto(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    t = unicodedata.normalize("NFC", t)
    t = t.replace("\u00a0", " ").replace("&nbsp;", " ")
    t = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def resumir(texto, max_palavras):
    """Resume sem cortar uma frase antes de atingir o limite de palavras."""
    palavras = texto.split()
    if len(palavras) <= max_palavras:
        return texto
    corte = " ".join(palavras[:max_palavras])
    # tenta terminar numa pontuação forte
    m = list(re.finditer(r"[.!?]", corte))
    if m and m[-1].end() > len(corte) * 0.78:
        return corte[: m[-1].end()]
    return corte.rstrip(",;:") + "..."


def quebrar_em_linhas(draw, texto, fonte, largura_max, max_linhas=None):
    palavras = texto.split()
    linhas, atual = [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if draw.textlength(teste, font=fonte) <= largura_max or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    if max_linhas and len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        linhas[-1] = linhas[-1].rstrip(",;:.") + "…"
    return linhas


# =============================================================================
# 2. COLETA DA POSTAGEM (Blogger / Atom)
# =============================================================================

def ler_feed(qtd=10):
    base = CFG["blog_url"].rstrip("/")
    url = f"{base}/feeds/posts/default?alt=json&max-results={qtd}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        dados = json.loads(r.read().decode("utf-8", "replace"))

    posts = []
    for e in dados.get("feed", {}).get("entry", []):
        link = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), "")
        thumb = e.get("media$thumbnail", {}).get("url", "")
        # o feed entrega a miniatura em s72 -> pedimos a versão grande
        img = re.sub(r"/(s\d+|w\d+-h\d+)(-c)?(/\w+)*$", "/s1600", thumb) if thumb else ""
        img = re.sub(r"=s\d+(-c)?$", "=s1600", img)
        conteudo = limpar_texto(e.get("content", {}).get("$t", "")) or limpar_texto(
            e.get("summary", {}).get("$t", ""))
        posts.append({
            "id": e.get("id", {}).get("$t", "").split("post-")[-1],
            "titulo": limpar_texto(e.get("title", {}).get("$t", "")),
            "url": link,
            "publicado": e.get("published", {}).get("$t", ""),
            "rotulos": [c["term"] for c in e.get("category", [])],
            "resumo": conteudo,
            "imagem": img,
            "autor": e.get("author", [{}])[0].get("name", {}).get("$t", CFG["site_name"]),
        })
    return posts


def ler_post(url):
    """Extrai metadados direto da página HTML (fallback / modo --url)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        html = r.read().decode("utf-8", "replace")

    def meta(prop):
        m = re.search(r'<meta[^>]*content=[\'"]([^\'"]*)[\'"][^>]*property=[\'"]%s[\'"]' % prop, html)
        if not m:
            m = re.search(r'<meta[^>]*property=[\'"]%s[\'"]\s*content=[\'"]([^\'"]*)[\'"]' % prop, html)
        return m.group(1) if m else ""

    titulo = meta("og:title") or (re.search(r"<title>(.*?)</title>", html, re.S).group(1) if re.search(r"<title>(.*?)</title>", html, re.S) else "")
    corpo = re.search(r'<div[^>]*class=[\'"][^\'"]*post-body[^\'"]*[\'"][^>]*>(.*?)</div>', html, re.S)
    texto = limpar_texto(corpo.group(1)) if corpo else limpar_texto(meta("og:description"))
    rot = re.findall(r'rel=[\'"]tag[\'"]\s*title=[\'"]([^\'"]+)[\'"]', html)
    return {
        "id": re.sub(r"\W+", "-", url)[-60:],
        "titulo": limpar_texto(titulo),
        "url": url,
        "publicado": "",
        "rotulos": rot[:4],
        "resumo": texto,
        "imagem": meta("og:image"),
        "autor": CFG["site_name"],
    }


# =============================================================================
# 3. NARRAÇÃO (edge-tts com sincronia palavra a palavra)
# =============================================================================

def duracao_audio(caminho):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(caminho)],
        capture_output=True, text=True)
    try:
        return float(saida.stdout.strip())
    except ValueError:
        return 0.0


async def _tts(texto, voz, destino, taxa):
    import edge_tts
    # edge-tts 7.x usa "SentenceBoundary" por padrão; queremos palavra a palavra
    com = edge_tts.Communicate(texto, voz, rate=taxa, boundary="WordBoundary")
    marcas = []
    with open(destino, "wb") as f:
        async for bloco in com.stream():
            if bloco["type"] == "audio":
                f.write(bloco["data"])
            elif bloco["type"] in ("WordBoundary", "SentenceBoundary"):
                # offset e duration em 100 nanossegundos
                marcas.append({
                    "palavra": bloco["text"],
                    "inicio": bloco["offset"] / 1e7,
                    "fim": (bloco["offset"] + bloco["duration"]) / 1e7,
                })
    return marcas


def narrar(texto, destino, voz, alvo_seg):
    """Gera o áudio e ajusta levemente a velocidade até caber no tempo alvo."""
    taxa = "+0%"
    marcas = []
    anterior = 0.0
    for tentativa in range(3):
        marcas = asyncio.run(_tts(texto, voz, destino, taxa))
        dur = duracao_audio(destino)
        if dur <= alvo_seg or taxa == "+15%":
            return dur, marcas
        if anterior and abs(dur - anterior) < 0.05:
            return dur, marcas          # a velocidade já não muda o suficiente
        anterior = dur
        atual = float(taxa.replace("%", "").replace("+", ""))
        novo = min(int(atual + max(4, (dur - alvo_seg) / dur * 100)), 15)
        taxa = f"+{novo}%"
        log(f"   narração longa ({dur:.1f}s > {alvo_seg}s) -> reacelerando para {taxa}")
    return duracao_audio(destino), marcas


# =============================================================================
# 4. RENDERIZAÇÃO DOS QUADROS (Pillow)
# =============================================================================

class Arte:
    def __init__(self):
        c = CFG
        self.L, self.A = c["largura"], c["altura"]
        self.fps = c["fps"]
        self.azul = hex2rgb(c["cor_primaria"])
        self.azul_claro = hex2rgb(c["cor_primaria_clara"])
        self.vermelho = hex2rgb(c["cor_destaque"])
        self.branco = (255, 255, 255, 255)
        f = RAIZ / "assets" / "fontes"
        self.f_titulo = ImageFont.truetype(str(f / "InterDisplay-Black.ttf"), 104)
        self.f_titulo_m = ImageFont.truetype(str(f / "InterDisplay-Black.ttf"), 84)
        self.f_badge = ImageFont.truetype(str(f / "Inter-Bold.ttf"), 34)
        self.f_legenda = ImageFont.truetype(str(f / "Inter-Bold.ttf"), 46)
        self.f_cta = ImageFont.truetype(str(f / "InterDisplay-Bold.ttf"), 52)
        self.f_cta2 = ImageFont.truetype(str(f / "Inter-Bold.ttf"), 36)
        self.f_rodape = ImageFont.truetype(str(f / "Inter-SemiBold.ttf"), 32)
        self.logo = self._logo()
        self.gradiente = self._gradiente()
        self.overlay_fixo = self._overlay_fixo()

    # ---- elementos estáticos -------------------------------------------------
    def _logo(self):
        p = RAIZ / "assets" / "img" / "logo-branco.png"
        lg = Image.open(p).convert("RGBA")
        # O arquivo do logo tem fundo azul-escuro: usamos a luminância como
        # canal alfa para deixá-lo transparente e recortamos o excesso.
        r, g, b = lg.split()[:3]
        mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
        alfa = mx.point(lambda v: min(255, max(0, int((v - 30) * 1.5))))
        lg.putalpha(alfa)
        lg = lg.crop(lg.getbbox())
        lg.thumbnail((190, 190), Image.LANCZOS)
        return lg

    def _gradiente(self):
        """Vinheta + degradê para garantir contraste do texto."""
        g = Image.new("RGBA", (self.L, self.A), (0, 0, 0, 0))
        d = ImageDraw.Draw(g)
        for y in range(self.A):
            p = y / self.A
            if p > 0.42:
                alfa = min(int(((p - 0.42) / 0.58) ** 1.35 * 250), 250)
            else:
                alfa = int((1 - p / 0.42) * 118)
            d.line([(0, y), (self.L, y)], fill=(2, 8, 20, alfa))
        # faixa azul de marca no alto
        d.rectangle([0, 0, self.L, 10], fill=self.azul)
        return g

    def _overlay_fixo(self):
        """Camada desenhada uma única vez e reutilizada em todos os quadros."""
        ov = Image.new("RGBA", (self.L, self.A), (0, 0, 0, 0))
        ov.alpha_composite(self.gradiente)
        d = ImageDraw.Draw(ov)
        # marca d'água (logo) no topo direito
        lg = self.logo.copy()
        ov.alpha_composite(lg, (self.L - lg.width - 52, 56))
        # rodapé fixo
        rod = f"{CFG['site_name']}  •  {CFG['dominio_curto']}"
        w = d.textlength(rod, font=self.f_rodape)
        d.text(((self.L - w) / 2, self.A - 96), rod, font=self.f_rodape, fill=(255, 255, 255, 168))
        return ov

    # ---- fundo com efeito Ken Burns ------------------------------------------
    def preparar_fundo(self, caminho_img):
        im = Image.open(caminho_img).convert("RGB")
        if max(im.size) > 2200:
            r = 2200 / max(im.size)
            im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        s = max(self.L / im.width, self.A / im.height)   # cobre a tela
        self.fundo = im
        self.base_w, self.base_h = self.L / s, self.A / s

    def fundo_do_quadro(self, p):
        """p = progresso 0..1 -> recorte com zoom e leve deslocamento."""
        z = 1.0 + 0.30 * p
        w = self.base_w / z
        h = self.base_h / z
        sobra_x = self.fundo.width - w
        sobra_y = self.fundo.height - h
        cx = 0.5 + 0.20 * math.sin(p * math.pi * 0.9)      # deriva suave
        cy = 0.42 - 0.14 * p
        x = max(0.0, min(sobra_x, sobra_x * cx))
        y = max(0.0, min(sobra_y, sobra_y * cy))
        q = self.fundo.resize((self.L, self.A), Image.LANCZOS, box=(x, y, x + w, y + h))
        return q

    # ---- blocos dinâmicos ----------------------------------------------------
    def ajustar_titulo(self, titulo):
        """Escolhe o maior corpo de fonte em que o título cabe em até 4 linhas."""
        d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        fonte, linhas = self.f_titulo_m, []
        for size in (104, 98, 92, 86, 80, 74, 68, 62):
            fonte = ImageFont.truetype(str(RAIZ / "assets" / "fontes" / "InterDisplay-Black.ttf"), size)
            linhas = quebrar_em_linhas(d, titulo, fonte, 950)
            if len(linhas) <= 4:
                return fonte, linhas
        return fonte, quebrar_em_linhas(d, titulo, fonte, 950, max_linhas=5)

    def badge(self, img, texto, t, fade=1.0):
        """Etiqueta de categoria com entrada animada."""
        if t < 0.30 or fade <= 0:
            return
        fase = min(1.0, (t - 0.30) / 0.35)
        d = ImageDraw.Draw(img)
        txt = texto.upper()[:34]
        w = d.textlength(txt, font=self.f_badge)
        larg, alt = w + 62, 66
        x, y = 64, 268
        desl = int((1 - fase) * -46)
        camada = Image.new("RGBA", (int(larg + 8), alt + 8), (0, 0, 0, 0))
        dc = ImageDraw.Draw(camada)
        dc.rounded_rectangle([0, 0, larg, alt], radius=14, fill=self.azul)
        dc.rounded_rectangle([0, 0, 10, alt], radius=5, fill=self.branco)
        dc.text((34, alt / 2), txt, font=self.f_badge, fill=self.branco, anchor="lm")
        camada.putalpha(camada.getchannel("A").point(lambda v: int(v * fase * fade)))
        img.alpha_composite(camada, (x + desl, y))

    def titular(self, img, linhas, t, t0, fonte=None, fade=1.0):
        """Título com revelação animada palavra por palavra."""
        if fade <= 0:
            return
        d = ImageDraw.Draw(img)
        fonte = fonte or self.f_titulo_m
        alt_linha = int(fonte.size * 1.16)
        bloco = alt_linha * len(linhas)
        y0 = 1000 - bloco / 2
        por_linha = [len(l.split()) for l in linhas]
        passo = 0.07
        acumulado = 0
        for i, linha in enumerate(linhas):
            palavras = linha.split()
            largura = d.textlength(linha, font=fonte)
            x = (self.L - largura) / 2
            for j, pal in enumerate(palavras):
                t_pal = t0 + (acumulado + j) * passo
                fase = min(1.0, max(0.0, (t - t_pal) / 0.30))
                wpal = d.textlength(pal, font=fonte)
                if fase > 0:
                    alfa = int(255 * fase * fade)
                    sobe = int((1 - fase) * 30)
                    esc = 1.0 + 0.12 * (1 - fase)
                    if esc > 1.002:
                        cap = Image.new("RGBA", (int(wpal) + 28, alt_linha + 28), (0, 0, 0, 0))
                        ImageDraw.Draw(cap).text(
                            (14, 14), pal, font=fonte, fill=(255, 255, 255, 255),
                            stroke_width=6, stroke_fill=(3, 10, 24, 255))
                        cap = cap.resize((max(1, int(cap.width * esc)), max(1, int(cap.height * esc))),
                                         Image.LANCZOS)
                        cap.putalpha(cap.getchannel("A").point(lambda v: int(v * alfa / 255)))
                        img.alpha_composite(cap, (int(x) - 14, int(y0 + i * alt_linha) - 14 + sobe))
                    else:
                        d.text((x, y0 + i * alt_linha + sobe), pal, font=fonte,
                               fill=(255, 255, 255, alfa),
                               stroke_width=6, stroke_fill=(3, 10, 24, alfa))
                x += wpal + d.textlength(" ", font=fonte)
            acumulado += len(palavras)

    def legenda(self, img, palavras, marcas, t_narr):
        """Faixa de legenda sincronizada com a fala."""
        if not marcas:
            return
        idx = [i for i, m in enumerate(marcas) if m["inicio"] <= t_narr <= m["fim"] + 0.35]
        if not idx:
            return
        ini = max(0, (idx[0] // 4) * 4)
        grupo = marcas[ini:ini + 4]
        txt = " ".join(m["palavra"] for m in grupo).upper()
        d = ImageDraw.Draw(img)
        larg = d.textlength(txt, font=self.f_legenda)
        caixa_w = larg + 56
        x = (self.L - caixa_w) / 2
        y = self.A - 330
        caixa = Image.new("RGBA", (int(caixa_w) + 8, 108), (0, 0, 0, 0))
        dc = ImageDraw.Draw(caixa)
        dc.rounded_rectangle([0, 0, caixa_w, 96], radius=16, fill=(4, 12, 26, 214))
        dc.rounded_rectangle([0, 0, 8, 96], radius=4, fill=self.azul_claro)
        dc.text((caixa_w / 2 + 4, 48), txt, font=self.f_legenda, fill=self.branco, anchor="mm")
        img.alpha_composite(caixa, (int(x), int(y)))

    def cartao_final(self, img, t_fim):
        """Encerramento com chamada para ação."""
        if t_fim < 0:
            return
        fase = min(1.0, t_fim / 0.55)
        d = ImageDraw.Draw(img)
        larg, alt = 900, 300
        x, y = (self.L - larg) / 2, self.A / 2 - 150
        caixa = Image.new("RGBA", (larg + 16, alt + 16), (0, 0, 0, 0))
        dc = ImageDraw.Draw(caixa)
        dc.rounded_rectangle([0, 0, larg, alt], radius=28, fill=(6, 16, 34, 236),
                             outline=self.azul, width=4)
        dc.rounded_rectangle([0, 0, larg, 12], radius=6, fill=self.azul)
        lg = self.logo.copy()
        lg.thumbnail((300, 300), Image.LANCZOS)
        caixa.alpha_composite(lg, (int((larg - lg.width) / 2), 26))
        dc.text((larg / 2, 196), CFG["cta"], font=self.f_cta, fill=self.branco, anchor="mm")
        dc.text((larg / 2, 252), CFG["dominio_curto"], font=self.f_cta2,
                fill=self.azul_claro, anchor="mm")
        caixa.putalpha(caixa.getchannel("A").point(lambda v: int(v * fase)))
        img.alpha_composite(caixa, (int(x - 8), int(y - 8 + (1 - fase) * 40)))

    def barra_progresso(self, img, p):
        d = ImageDraw.Draw(img)
        d.rectangle([0, self.A - 12, self.L, self.A], fill=(255, 255, 255, 46))
        d.rectangle([0, self.A - 12, int(self.L * p), self.A], fill=self.azul)


# =============================================================================
# 5. MONTAGEM
# =============================================================================

def gerar(post, pasta_saida, enviar=False):
    c = CFG
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", post["titulo"].lower())
                  .encode("ascii", "ignore").decode())[:60].strip("-")
    tmp = pasta_saida / f".tmp-{slug}"
    tmp.mkdir(exist_ok=True)

    log(f"▶ Postagem: {post['titulo']}")

    # --- imagem de capa -------------------------------------------------------
    img_path = tmp / "capa.jpg"
    try:
        baixar(post["imagem"], img_path)
        Image.open(img_path).verify()
        log("   capa baixada")
    except Exception as e:
        log(f"   aviso: capa indisponível ({e}) -> usando fundo de marca")
        fundo = Image.new("RGB", (1080, 1920), (15, 23, 42))
        fundo.save(img_path, quality=92)

    # --- narração -------------------------------------------------------------
    rot = post["rotulos"][0] if post["rotulos"] else "Notícias"
    # O orçamento é dividido entre manchete e resumo. Como o feed traz o texto
    # integral da postagem, o vídeo consegue explicar contexto e conclusão,
    # em vez de apenas repetir uma chamada de 15 segundos.
    palavras_manchete = len(post["titulo"].split())
    restante = max(8, c["max_palavras_narracao"] - palavras_manchete)
    texto = post["titulo"].rstrip(".") + ". " + resumir(post["resumo"], restante)
    texto = re.sub(r"\s*\.\.\.$", "", texto)
    voz = c["voz"]
    if any(r.lower() in [x.lower() for x in c["rotulos_saude"]] for r in post["rotulos"]):
        voz = c.get("voz_alternativa", voz)
    audio_nar = tmp / "narracao.mp3"
    dur_nar, marcas = narrar(texto, audio_nar, voz, c["duracao"] - 4.5)
    log(f"   narração: {dur_nar:.2f}s | voz {voz} | {len(marcas)} marcas de palavra")

    # --- arte -----------------------------------------------------------------
    arte = Arte()
    arte.preparar_fundo(img_path)
    t_ini_fala = 1.2
    # Mantém o resumo entre 30 e 45 s: artigos maiores usam todo o orçamento;
    # artigos com feed mais curto não ficam com vários segundos sem conteúdo.
    dur_total = min(float(c["duracao"]), max(30.0, dur_nar + t_ini_fala + 3.0))
    n = int(round(dur_total * arte.fps))
    # chamada para ação apenas no encerramento, sempre nos últimos 3 segundos
    t_cta = dur_total - 3.0

    fonte_titulo, linhas = arte.ajustar_titulo(post["titulo"])
    log(f"   título em {len(linhas)} linha(s), corpo {fonte_titulo.size}px")

    # --- quadros --------------------------------------------------------------
    dir_quadros = tmp / "quadros"
    dir_quadros.mkdir(exist_ok=True)
    musica = RAIZ / c["musica"]["arquivo_noticias"]
    if any(r.lower() in [x.lower() for x in c["rotulos_saude"]] for r in post["rotulos"]):
        musica = RAIZ / c["musica"]["arquivo_saude"]

    for i in range(n):
        t = i / arte.fps
        p = i / max(1, n - 1)
        quadro = arte.fundo_do_quadro(p).convert("RGBA")
        quadro.alpha_composite(arte.overlay_fixo)
        # no encerramento o título sai de cena para dar lugar à chamada
        fade = min(1.0, max(0.0, (t_cta - 0.30 - t) / 0.35))
        arte.badge(quadro, rot, t, fade)
        arte.titular(quadro, linhas, t, 0.62, fonte_titulo, fade)
        if t >= t_ini_fala:
            arte.legenda(quadro, texto.split(), marcas, t - t_ini_fala)
        arte.cartao_final(quadro, t - t_cta)
        arte.barra_progresso(quadro, p)
        quadro.convert("RGB").save(dir_quadros / f"{i:05d}.png", compress_level=1)
        if i % 60 == 0:
            log(f"   ... quadro {i}/{n}")

    # --- áudio: narração + trilha --------------------------------------------
    log("   mixando áudio")
    vol = c["musica"]["volume"]
    mix = tmp / "mix.m4a"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(audio_nar),
        "-stream_loop", "-1", "-i", str(musica),
        "-filter_complex",
        f"[0:a]adelay={int(t_ini_fala*1000)}|{int(t_ini_fala*1000)},"
        f"dynaudnorm=f=200:g=5[nar];"
        f"[1:a]volume={vol},afade=t=in:st=0:d=1.2,"
        f"afade=t=out:st={max(0,dur_total-1.6):.2f}:d=1.6[mus];"
        f"[nar][mus]amix=inputs=2:duration=longest:dropout_transition=0,"
        f"alimiter=limit=0.94[a]",
        "-map", "[a]", "-t", f"{dur_total:.3f}",
        "-c:a", "aac", "-b:a", "160k", str(mix)
    ], check=True)

    # --- encode final ---------------------------------------------------------
    saida = pasta_saida / f"{slug}.mp4"
    log("   codificando MP4")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(arte.fps), "-i", str(dir_quadros / "%05d.png"),
        "-i", str(mix),
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-vf", "scale=1080:1920:flags=lanczos",
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-movflags", "+faststart", "-shortest", str(saida)
    ], check=True)

    capa = pasta_saida / f"{slug}-capa.jpg"
    quadro_capa = Image.open(dir_quadros / f"{int(min(t_cta-0.2, dur_total-0.5)*arte.fps):05d}.png")
    quadro_capa.convert("RGB").save(capa, quality=90)

    meta = montar_metadados(post, texto, saida, capa, dur_total)
    (pasta_saida / f"{slug}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)

    log(f"   OK -> {saida}  ({saida.stat().st_size/1048576:.1f} MB)")
    return {"video": str(saida), "capa": str(capa), "metadados": meta}


def montar_metadados(post, narracao, video, capa, duracao_segundos=None):
    rot = ", ".join(post["rotulos"][:3])
    titulo = post["titulo"]
    if len(titulo) > 88:
        titulo = titulo[:85].rstrip(" ,;:") + "..."
    descricao = (
        f"{narracao}\n\n"
        f"▶ Leia a matéria completa: {post['url']}\n\n"
        f"📍 {CFG['site_name']} — informação que desperta novas escolhas.\n"
        f"👉 {CFG['blog_url']}\n\n"
        f"🔔 Inscreva-se e ative o sininho para não perder as próximas análises.\n\n"
        f"Categorias: {rot}\n\n"
        f"#Shorts #Notícias #Brasil #"
        + " #".join(re.sub(r"[^\w]", "", r) for r in post["rotulos"][:3])
    )
    tags = list(dict.fromkeys(
        post["rotulos"] + CFG["hashtags_base"] +
        ["notícias hoje", "últimas notícias", "informação", "análise", CFG["site_name"]]
    ))
    return {
        "titulo": f"{titulo} #Shorts",
        "titulo_curto": titulo,
        "descricao": descricao,
        "tags": tags[:18],
        "categoria": "News & Politics",
        "privacidade": "public",
        "url_origem": post["url"],
        "rotulos": post["rotulos"],
        "narracao": narracao,
        "video": str(video),
        "capa": str(capa),
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "duracao_segundos": int(round(duracao_segundos or CFG.get("duracao", 45))),
    }


# =============================================================================
# 6. CONTROLE DE POSTS JÁ PROCESSADOS
# =============================================================================

def carregar_estado():
    p = RAIZ / "saida" / "processados.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"ids": []}


def salvar_estado(estado):
    p = RAIZ / "saida" / "processados.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


# =============================================================================
# 7. LINHA DE COMANDO
# =============================================================================

def main():
    ap = argparse.ArgumentParser(description="Gerador de Shorts do Coletividade Evolutiva")
    ap.add_argument("--feed", action="store_true", help="pega as postagens mais recentes do blog")
    ap.add_argument("--url", help="gera a partir de um link específico")
    ap.add_argument("--lote", type=int, default=1, help="quantas postagens processar (modo --feed)")
    ap.add_argument("--todos", action="store_true", help="ignora o controle de já processados")
    ap.add_argument("--envio", action="store_true", help="envia para o YouTube após gerar")
    ap.add_argument("--saida", default=str(RAIZ / "saida"), help="pasta de saída")
    a = ap.parse_args()

    if a.url:
        posts = [ler_post(a.url)]
    else:
        posts = ler_feed(max(a.lote * 3, 8))
        estado = carregar_estado()
        if not a.todos:
            posts = [p for p in posts if p["id"] not in estado["ids"]]
        posts = posts[:a.lote]

    if not posts:
        log("Nenhuma postagem nova para processar.")
        return

    resultados = []
    for post in posts:
        try:
            r = gerar(post, a.saida, a.envio)
            resultados.append(r)
            est = carregar_estado()
            if post["id"] not in est["ids"]:
                est["ids"].append(post["id"])
            salvar_estado(est)
            if a.envio:
                from enviar_youtube import enviar_short
                meta_publicada = enviar_short(r["video"], r["metadados"])
                # Depois do upload, injeta o player, a transcrição e o
                # VideoObject na postagem original do Blogger.
                from publicar_blogger import publicar
                publicar(meta_publicada)
        except Exception as e:
            log(f"ERRO ao gerar '{post['titulo'][:50]}': {e}")
            raise

    log(f"Concluído: {len(resultados)} vídeo(s) em {a.saida}")


if __name__ == "__main__":
    main()
