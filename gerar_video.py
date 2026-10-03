import os
import sys
import json
import argparse
import feedparser
import enviar_youtube

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

    print("🔍 Lendo feed público do portal...")
    feed = feedparser.parse(FEED_URL)
    
    if not feed.entries:
        print("❌ Nenhum post encontrado no feed RSS.")
        return

    processados = carregar_processados()
    
    if args.todos:
        posts_para_processar = feed.entries[:args.lote]
    else:
        posts_para_processar = [entry for entry in feed.entries if entry.link not in processados][:args.lote]

    if not posts_para_processar:
        print("ℹ️ Nenhuma matéria nova pendente. Todas as matérias recentes já foram registradas em processados.json.")
        print("💡 Dica: Para forçar a geração de uma matéria já processada, execute o workflow com 'todos = sim'.")
        return

    for post in posts_para_processar:
        titulo = post.title
        link = post.link
        print(f"\n🎬 Processando matéria: {titulo}")
        print(f"🔗 Link: {link}")

        os.makedirs(SAIDA_DIR, exist_ok=True)
        
        # Procurar por algum vídeo MP4 existente na pasta de saída ou utilizar o padrão
        video_path = os.path.join(SAIDA_DIR, "video_saida.mp4")
        
        # Procura se existe outro .mp4 na raiz ou em saída gerado anteriormente
        mp4_files = [f for f in os.listdir(".") if f.endswith(".mp4")] + \
                    [os.path.join(SAIDA_DIR, f) for f in os.listdir(SAIDA_DIR) if f.endswith(".mp4")] if os.path.exists(SAIDA_DIR) else []

        if mp4_files:
            video_path = mp4_files[0]
            print(f"📁 Arquivo de vídeo localizado para upload: {video_path}")

        if args.envio:
            if os.path.exists(video_path):
                print("🚀 Enviando vídeo para o YouTube...")
                try:
                    video_id = enviar_youtube.publicar(video_path, titulo, link)
                    if video_id:
                        salvar_processado(link)
                        print(f"✅ Sucesso! Vídeo no ar: https://www.youtube.com/watch?v={video_id}")
                except Exception as e:
                    print(f"❌ Erro na API do YouTube: {e}")
            else:
                print(f"⚠️ Atenção: O arquivo de vídeo '{video_path}' não foi encontrado. Certifique-se de que a etapa de renderização (FFmpeg) gerou o arquivo .mp4 antes do envio.")

if __name__ == "__main__":
    main()
