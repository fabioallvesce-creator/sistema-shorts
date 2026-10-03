import os
import sys
import json
import argparse
import feedparser
import enviar_youtube  # Importa a função de envio para o YouTube

# Feed público do seu portal (sem dependência de Blogger API)
FEED_URL = "https://www.coletividadeevolutiva.com/feeds/posts/default?alt=rss"
SAIDA_DIR = "saida"
PROCESSED_FILE = os.path.join(SAIDA_DIR, "processados.json")

def carregar_processados():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salvar_processado(link_post):
    os.makedirs(SAIDA_DIR, exist_ok=True)
    processados = carregar_processados()
    if link_post not in processados:
        processados.append(link_post)
        with open(PROCESSED_FILE, 'w', encoding='utf-8') as f:
            json.dump(processados, f, ensure_ascii=False, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Gerador de vídeos-resumo para o YouTube")
    parser.add_argument("--feed", action="store_true", help="Lê as matérias via Feed RSS")
    parser.add_argument("--lote", type=int, default=1, help="Quantidade de vídeos a gerar")
    parser.add_argument("--envio", action="store_true", help="Envia o vídeo gerado para o YouTube")
    parser.add_argument("--todos", action="store_true", help="Ignora o histórico de processados")
    args = parser.parse_args()

    print("Lendo feed público do portal...")
    feed = feedparser.parse(FEED_URL)
    
    if not feed.entries:
        print("Nenhum post encontrado no feed RSS.")
        return

    processados = carregar_processados()
    
    # Filtra os posts pendentes
    if args.todos:
        posts_para_processar = feed.entries[:args.lote]
    else:
        posts_para_processar = [entry for entry in feed.entries if entry.link not in processados][:args.lote]

    if not posts_para_processar:
        print("Nenhum post novo para processar no momento.")
        return

    for post in posts_para_processar:
        titulo = post.title
        link = post.link
        print(f"\n--- Processando: {titulo} ---")
        print(f"URL: {link}")

        # Define o caminho do arquivo de vídeo final em saída
        os.makedirs(SAIDA_DIR, exist_ok=True)
        video_path = os.path.join(SAIDA_DIR, "video_saida.mp4")

        # Exemplo/Lógica de chamada de envio para o YouTube
        if args.envio:
            print("Enviando vídeo para o YouTube...")
            try:
                enviar_youtube.publicar(video_path, titulo, link)
                salvar_processado(link)
                print("Vídeo publicado com sucesso!")
            except Exception as e:
                print(f"Erro ao enviar para o YouTube: {e}")

if __name__ == "__main__":
    main()
