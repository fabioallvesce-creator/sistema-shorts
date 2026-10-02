# Robô de Shorts — Coletividade Evolutiva

Sistema automático que transforma cada postagem do portal em um **vídeo-resumo
vertical de 30 a 45 segundos**, publica no **YouTube Shorts** e insere o player com
**dados estruturados de vídeo** dentro da própria postagem do Blogger.

**Custo: R$ 0,00.** Sem marca d'água de terceiros, sem limite mensal de vídeos.

![Arquitetura do sistema](docs/arquitetura.png)

---

## O que está pronto nesta pasta

| Arquivo | Para que serve |
|---|---|
| `config.json` | Identidade do portal: cores, voz, textos do vídeo, trilhas |
| `gerador/gerar_video.py` | Motor: lê o blog e produz o vídeo-resumo de 45 s |
| `gerador/enviar_youtube.py` | Publica no YouTube Shorts e na playlist |
| `gerador/publicar_blogger.py` | Insere player + `VideoObject` na postagem |
| `gerador/autorizar_youtube.py` | Autorização única do Google (gera o token) |
| `blogger/1-player-e-estilos.html` | CSS + JS do player leve (colar no tema) |
| `blogger/2-vitrine-de-shorts.html` | Vitrine de vídeos na home/barra lateral |
| `.github/workflows/gerar-shorts.yml` | Robô que roda sozinho a cada 30 min |
| `saida/` | Pasta onde os vídeos, capas e metadados são gravados |
| `docs/GUIA-DO-SISTEMA.md` | **Guia completo: instalação, SEO e uso diário** |
| `docs/arquitetura.png` | Diagrama do fluxo completo |

## Comece por aqui

1. Leia **[docs/GUIA-DO-SISTEMA.md](docs/GUIA-DO-SISTEMA.md)** — tem o passo a
   passo de instalação, o comparativo das ferramentas gratuitas do mercado e as
   regras de SEO aplicadas.
2. Teste localmente (precisa só de FFmpeg e Python):

   ```bash
   pip install -r requirements.txt
   python gerador/gerar_video.py --feed --lote 1
   ```

   O vídeo aparece em `saida/`.

3. Para publicar sozinho todos os dias: siga a seção *Instalação* do guia.

## Comandos do dia a dia

```bash
python gerador/gerar_video.py --feed                 # postagem mais recente
python gerador/gerar_video.py --feed --lote 3        # três postagens
python gerador/gerar_video.py --url <link-do-post>   # uma matéria específica
python gerador/gerar_video.py --feed --envio         # gera e publica no YouTube
python gerador/gerar_video.py --feed --todos         # ignora o histórico
```

---

© Coletividade Evolutiva — sistema sob medida para o portal.
