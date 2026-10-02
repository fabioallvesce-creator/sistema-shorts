# Guia do Sistema de Shorts Automáticos
### Coletividade Evolutiva — vídeo curto automático, SEO e conversão

---

## 1. Resumo em uma página

Você pediu três coisas:

1. um **sistema automático** que crie vídeos-resumo profissionais de **30 a 45 segundos** a partir das postagens do portal;
2. que eu **buscasse alguma solução gratuita mundial** que já faça isso;
3. que o resultado fosse **bom de SEO** e ajudasse a **atrair e converter** visitantes.

Fiz as três. A resposta curta:

> **Nenhuma ferramenta gratuita do mundo entrega, ao mesmo tempo, geração automática, sem marca d'água, sem limite mensal e integração com o Blogger.** Todas falham em pelo menos um desses pontos. Por isso montei um sistema próprio, com peças gratuitas e consagradas (FFmpeg, vozes neurais da Microsoft, Pillow), que roda de graça na nuvem e faz o ciclo completo: **postagem publicada → vídeo-resumo de 45 s → YouTube Shorts → player e dados estruturados dentro da postagem → vitrine de vídeos na home.**

O sistema já está **construído e testado**: os dois vídeos de demonstração em `saida/` foram gerados a partir de matérias reais do seu portal.

---

## 2. Diagnóstico: por que o vídeo é a alavanca que falta

Seu portal já tem uma base técnica boa: tema responsável, modo escuro, meta tags, Open Graph, dados de autor, AdSense no lugar. O que falta é **presença nas superfícies de vídeo**, e é justamente ali que o jornalismo digital brasileiro está ganhando tráfego agora:

| Fato | Impacto no seu portal |
|---|---|
| O Google mistura Shorts e vídeos verticais nos resultados de busca e no Discover | Você fica invisível nessa fatia sem publicar vídeo |
| Vídeo na página aumenta o tempo de permanência | Sinal de qualidade que ajuda **todas** as páginas do domínio |
| O YouTube é o segundo maior buscador do mundo | Cada Short é uma nova porta de entrada para a marca |
| Postagens de notícia têm vida curta | O Short recircula a matéria por semanas, não por horas |
| Anúncios em página com vídeo têm mais inventário | Mais receita de AdSense com o mesmo conteúdo |

Sua estrutura de conteúdo ajuda: matérias de saúde, ciência, meio ambiente e governo têm **imagens fortes** (capa obrigatória no feed), o que é exatamente o que um Short precisa.

---

## 3. As opções gratuitas do mercado — comparativo honesto

Testei/verifiquei os planos gratuitos disponíveis em 2026. A coluna decisiva é a última.

| Ferramenta | O que o plano grátis dá | Marca d'água | Automático (sem você abrir o site)? | Serve para o portal? |
|---|---|---|---|---|
| **Sistema deste guia** (FFmpeg + edge-tts + Pillow) | Ilimitado, 1080x1920 | **Não** | **Sim**, 100% pela API | **Sim** ✅ |
| **Lumen5** | 5 vídeos/mês, 720p, máx. 2 min | Sim | Não | Parcial ⚠️ |
| **InVideo AI** | Limite semanal de geração por IA | Sim | Não | Parcial ⚠️ |
| **Fliki** | ~3 créditos/mês (≈5 min), 720p | Sim | Não | Parcial ⚠️ |
| **Pictory** | Só teste gratuito | Sim | Não | Não ❌ |
| **HeyGen** | Créditos limitados | Sim | Não | Não ❌ |
| **VEED** | Exportação limitada | Sim | Não | Não ❌ |
| **Canva** | Editor completo, exportação MP4 | Não (com recursos limitados) | Não | Manual ⚠️ |
| **Clipchamp** (Microsoft) | Exporta 1080p, conta Microsoft | Não | Não | Manual ⚠️ |
| **Google Vids** (conta Google) | Geração com Gemini, créditos mensais | Não | Não | Manual ⚠️ |
| **CapCut** | Edição vertical excelente | Não | Não | Manual ⚠️ |
| **Opus Clip / Vizard / Klap** | Cortes de vídeos longos | Sim / limites | Parcial | Não gera de texto ❌ |
| **dlvr.it** | Distribui RSS para 21 redes | — | Sim, mas **não gera vídeo** | Complementar 🔸 |

### O veredito

- Para **Volume baixo e manual** (1 a 2 vídeos por semana, feitos à mão): **Canva** ou **Clipchamp** entregam qualidade sem marca d'água. É o caminho se você quiser edição artesanal.
- Para **produção automática em escala**: nenhuma ferramenta gratuita serve — todas cobram justamente na automação. É aí que entra o sistema deste guia.
- **dlvr.it** continua valendo como complemento: ele distribui o link da matéria no Facebook, X e Telegram automaticamente, sem gerar vídeo.

---

## 4. Como o sistema funciona

![Arquitetura](../docs/arquitetura.png)

**Ciclo completo, sem intervenção humana:**

1. Você publica a matéria no Blogger, como já faz hoje.
2. A cada 30 minutos, o robô lê o **feed Atom** do portal e identifica o que é novo.
3. Extrai **capa, título, resumo, categoria e link**.
4. Gera a **locução** em português com voz neural da Microsoft (`edge-tts`), gratuita.
5. Monta a **arte 1080x1920** com a identidade visual do portal (azul `#0174DF`, logo, tipografia Inter).
6. Mixa voz + trilha sonora original e codifica o **MP4 de 30 a 45 s** com FFmpeg. Artigos curtos ficam menores; matérias mais completas usam os 45 s.
7. Sobe o vídeo no **YouTube Shorts** via API oficial (cota gratuita de 100 uploads/dia).
8. **Insere dentro da postagem** o player leve, a transcrição e os dados estruturados `VideoObject`.
9. Adiciona o vídeo à **playlist de Shorts**, que alimenta a vitrine na home.

### O que cada vídeo entrega

| Elemento | Como aparece |
|---|---|
| Fundo | Capa da matéria com movimento suave de zoom e deslocamento (efeito Ken Burns) |
| Etiqueta de categoria | Pílula azul com o rótulo do post (ex.: `MEIO AMBIENTE`) |
| Manchete | Revelada palavra por palavra, com entrada animada |
| Locução | Voz neural pt-BR, ~33 palavras, ritmo natural |
| Legendas | Faixa sincronizada palavra a palavra com a fala |
| Marca | Logo do portal no topo direito, texto do domínio no rodapé |
| Encerramento | Cartão `LEIA A MATÉRIA COMPLETA` + domínio, nos últimos 1,5 s |
| Barra de progresso | Faixa azul no rodapé, do início ao fim |

### Linha do tempo dos vídeos-resumo

```
0,0 s ─ barra azul de marca + imagem entrando em movimento
0,3 s ─ etiqueta de categoria
0,6 s ─ manchete começa a ser revelada palavra por palavra
1,0 s ─ começa a locução; legendas acompanham a fala
13,5 s ─ manchete sai de cena
últimos 3 s ─ cartão final "LEIA A MATÉRIA COMPLETA"
fim ─ duração entre 30 e 45 s, conforme o tamanho do resumo
```

### Estrutura de arquivos

```
cev-video/
├── config.json                       identidade: cores, voz, textos, trilhas
├── requirements.txt
├── .github/workflows/
│   └── gerar-shorts.yml              o robô que roda sozinho
├── gerador/
│   ├── gerar_video.py                motor de geração (coração do sistema)
│   ├── enviar_youtube.py             upload para o Shorts + playlist
│   ├── publicar_blogger.py           player + VideoObject na postagem
│   └── autorizar_youtube.py          autorização única do Google
├── blogger/
│   ├── 1-player-e-estilos.html       colar no tema (CSS + JS)
│   └── 2-vitrine-de-shorts.html      gadget da home
├── assets/
│   ├── fontes/                       Inter (licença SIL Open Font)
│   ├── img/logo-branco.png
│   └── audio/                        trilhas originais geradas para o portal
├── docs/
│   ├── GUIA-DO-SISTEMA.md            este documento
│   └── arquitetura.png
└── saida/                            vídeos, capas e metadados gerados
```

---

## 5. Instalação passo a passo

Tempo estimado: **30 a 40 minutos**, uma única vez.

### 5.1 O que você precisa

- Uma conta Google (a mesma do canal do YouTube e do Blogger).
- Uma conta no **GitHub** (grátis).
- Nenhum cartão de crédito. Nenhum pagamento em nenhuma etapa.

### 5.2 Passo 1 — Ligar as APIs no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com) e crie um projeto chamado `Shorts CEV`.
2. Em **APIs e serviços → Biblioteca**, ative as duas:
   - **YouTube Data API v3**
   - **Blogger API v3**
3. Em **APIs e serviços → Tela de permissão OAuth**, configure como **Externo**, tipo **Teste**, e adicione seu próprio e-mail em **Usuários de teste**.
4. Em **Credenciais → Criar credenciais → ID do cliente OAuth**:
   - Tipo de aplicativo: **App para computador**
   - Baixe o JSON e renomeie para **`credenciais-cliente.json`**, colocando-o na raiz desta pasta.

> **Por que "Em teste" resolve:** o modo de teste do Google não expira para o seu próprio e-mail e não exige o processo de verificação. Um robô de uso pessoal nunca precisa sair do modo de teste.

### 5.3 Passo 2 — Gerar o token de acesso

```bash
pip install -r requirements.txt
python gerador/autorizar_youtube.py
```

O navegador abre, você escolhe a conta (a do canal) e aceita as permissões. O terminal imprime três linhas:

```
YT_CLIENT_ID=...
YT_CLIENT_SECRET=...
YT_REFRESH_TOKEN=...
```

Guarde-as. Elas são a chave do robô — **nunca** comite esse arquivo num repositório público.

### 5.4 Passo 3 — Subir para o GitHub

```bash
git init
git add .
git commit -m "Sistema de Shorts do portal"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/cev-shorts.git
git push -u origin main
```

No repositório, em **Settings → Secrets and variables → Actions → New repository secret**, crie:

| Nome do secret | Valor |
|---|---|
| `YT_CLIENT_ID` | o valor impresso no passo 2 |
| `YT_CLIENT_SECRET` | o valor impresso no passo 2 |
| `YT_REFRESH_TOKEN` | o valor impresso no passo 2 |
| `YT_PLAYLIST_SHORTS` | ID da playlist de Shorts (passo 6) |

> **Público ou privado?** Os *secrets* são criptografados nos dois casos. A diferença é a cota: repositório **público** tem minutos ilimitados; **privado** tem 2.000 min/mês, e rodar de 30 em 30 minutos estouraria essa cota. Se preferir privado, troque no arquivo `gerar-shorts.yml` o cron para `0 */2 * * *` (a cada 2 horas) — fica em ~1.080 min/mês e sobra folga.

### 5.5 Passo 4 — Ligar o robô

1. Em **Actions**, aceite habilitar os workflows.
2. Selecione **Gerar Shorts do portal → Run workflow**, com `lote = 1` e `todos = nao`.
3. Acompanhe o log. Em cerca de 3 minutos o vídeo estará no YouTube e a postagem atualizada.

Depois disso ele roda sozinho. Dois avisos úteis:

- O agendador do GitHub pode atrasar 5 a 15 minutos em horários de pico — é normal e não afeta o resultado.
- O GitHub **desativa** workflows agendados após 60 dias sem atividade no repositório. Se isso acontecer, basta reativar em Actions (ou fazer qualquer commit).

### 5.6 Passo 5 — Aplicar os blocos no Blogger

No painel: **Tema → Editar HTML**. São duas colagens:

1. Abra `blogger/1-player-e-estilos.html` e cole a **PARTE A** (CSS) logo antes de `]]></b:skin>`; cole a **PARTE B** (JS) logo antes de `</body>`. Salve.
2. Vá em **Layout → Adicionar gadget → HTML/JavaScript**, cole o conteúdo de `blogger/2-vitrine-de-shorts.html` e substitua `COLE_AQUI_O_ID_DA_PLAYLIST_DE_SHORTS` e a chave da API. Salve.

O robô faz o resto: ele injeta o bloco do vídeo dentro de cada postagem automaticamente, sem você tocar no post.

### 5.7 Passo 6 — Playlist de Shorts

1. No YouTube, crie uma playlist pública chamada **“Shorts — Coletividade Evolutiva”**.
2. Copie o ID (o trecho depois de `list=` na URL).
3. Coloque no secret `YT_PLAYLIST_SHORTS` e no gadget da vitrine.

A partir daí, todo vídeo novo entra na playlist e aparece na home do portal **sem nenhuma ação sua**.

### 5.8 Passo 7 — Teste de ponta a ponta

Rode localmente, sem publicar nada, para conferir o resultado:

```bash
python gerador/gerar_video.py --feed --lote 1
```

Abra o MP4 em `saida/`. Se quiser ajustar voz, cores ou textos, tudo está em `config.json`.

---

## 6. SEO: o que já está implementado e por quê

### 6.1 `VideoObject` dentro da postagem (automático)

Esta é a peça central. O robô insere, no fim de cada matéria com vídeo:

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "Título da matéria",
  "description": "Resumo falado no vídeo",
  "thumbnailUrl": ["https://i.ytimg.com/vi/ID/maxresdefault.jpg"],
  "uploadDate": "2026-10-02T11:49:52",
  "duration": "PT45S",
  "embedUrl": "https://www.youtube.com/embed/ID",
  "contentUrl": "https://www.youtube.com/shorts/ID",
  "publisher": { "@type": "Organization", "name": "Coletividade Evolutiva" }
}
```

É esse bloco que torna a página elegível para **resultados enriquecidos de vídeo** no Google — miniatura, duração e selo de vídeo no resultado de busca. Também é o que sustenta a presença no **Discover**.

### 6.2 Transcrição na página (automático)

Todo vídeo vem acompanhado da **transcrição completa** dentro de um `<details>`. Isso adiciona texto único e indexável à página, reforçando o tema da matéria — e ajuda quem chegou pelo vídeo a entender o contexto.

### 6.3 Player leve (automático)

O player **não** carrega o iframe do YouTube de imediato: mostra a capa e um botão de play. O iframe só entra no DOM depois do clique. Resultado:

- o peso da página não muda praticamente nada;
- as métricas de Core Web Vitals (LCP e INP) seguem boas;
- somado ao AdSense, não há competição por carregamento.

Isso importa porque **velocidade é fator de ranking** e porque páginas lentas derrubam a receita de anúncio.

### 6.4 Vitrine com links internos

A vitrine na home cria uma malha de ligações internas para as páginas que têm `VideoObject`. Para o Google, isso é sinal de relevância e ajuda a distribuir autoridade pelo domínio.

### 6.5 Regras que o gerador já aplica em cada vídeo

- **Título até 88 caracteres + `#Shorts`** — evita corte no app e usa a etiqueta que mais ajuda a distribuição.
- **Descrição com a matéria completa em primeiro lugar**, depois o domínio, depois um convite para inscrever-se — nessa ordem, porque os primeiros 100 caracteres são os que aparecem antes do “mostrar mais”.
- **Primeiro link da descrição aponta para o post** (tráfego direto de volta ao portal, não para o YouTube).
- **Etiquetas geradas a partir dos rótulos do Blogger** + variações de cauda longa (`últimas notícias`, `notícias hoje`, `análise`).
- **Idioma declarado como `pt-BR`** (áudio e texto), o que ajuda a segmentação regional.

### 6.6 O que ainda vale fazer no portal

| Ação | Por quê |
|---|---|
| Validar o `VideoObject` no [Teste de Resultados Enriquecidos](https://search.google.com/test/rich-results) | Confirma que o Google lê o bloco sem erro |
| Enviar `https://www.coletividadeevolutiva.com/sitemap.xml` no Search Console | Faz o Google rastrear as páginas com vídeo mais rápido |
| Padronizar a capa das matérias (1200x675 ou 1080x1350, com rosto ou elemento forte) | A capa vira o quadro do vídeo e a miniatura do Short |
| Fixar 3 a 5 Shorts na página `p/ultimas-noticias.html` | Aproveita a página mais visitada para distribuir vídeo |
| Medir no Search Console a aba **Vídeos** | Mostra quantas impressões de vídeo o portal já ganha |

### 6.7 O vídeo não canibaliza o texto — ele multiplica

A dúvida é comum: “o Short não tira o leitor do site?”. Não, quando o desenho é o correto — que é o que está implementado:

- o vídeo entrega **o resumo**; a matéria entrega o **detalhe**;
- a chamada final manda para a matéria, não para um canal genérico;
- o player fica **dentro** da postagem, então o Short também trabalha como retenção de quem já está no site.

---

## 7. Padrão editorial dos 45 segundos

### Regras de escrita que o gerador segue

| Regra | Motivo |
|---|---|
| Até ~105 palavras (manchete + resumo) | Permite explicar contexto, informação principal e conclusão em 30–45 s |
| Resumo cortado no fim de frase | Evita frase pela metade na locução |
| Manchete com no máximo 4 linhas, fonte ajustada automaticamente | Preserva legibilidade sem cortar palavra |
| Uma ideia por vídeo | Quem assiste decide em 2 segundos se para |
| Encerramento sempre com o domínio | O objetivo é levar para o portal, não acumular views |

### Voz

- **Notícias e mundo** → `pt-BR-ThalitaMultilingualNeural`
- **Saúde, ciência, curas naturais** → `pt-BR-AntonioNeural` (detectado pelos rótulos do post)

Trocar a voz é uma linha em `config.json`. Para ouvir outras opções: `edge-tts --list-voices | grep pt-BR`.

### Trilha sonora

As duas trilhas em `assets/audio/` foram **geradas originalmente para o portal** (uma de urgência para notícias, uma reflexiva para saúde/ciência). São livres de royalties e não geram reivindicação de direitos autorais no YouTube — problema típico de quem usa banco de músicas gratuitas.

---

## 8. Reaproveitar para Reels, TikTok e Facebook

O mesmo MP4 é vertical 1080x1920 em H.264/AAC — formato aceito por todas as plataformas:

| Plataforma | Como usar |
|---|---|
| **YouTube Shorts** | Já é automático |
| **Instagram Reels** | Publicação automática exige conta profissional e aprovação no app da Meta; no começo, publique com o mesmo MP4 da pasta `saida/` |
| **TikTok** | Idem — API aberta só para apps aprovados |
| **Facebook Reels** | Mesma regra do Instagram |
| **WhatsApp / Telegram** | O MP4 já serve como peça de envio direto |

Como o robô tem um **robozinho de controle de postagens já processadas** (`saida/processados.json`), ele nunca gera o mesmo vídeo duas vezes — você pode rodar à vontade.

---

## 9. Custos, limites e capacidade

| Item | Custo | Limite |
|---|---|---|
| FFmpeg, Pillow, edge-tts | R$ 0 | Sem limite |
| GitHub Actions | R$ 0 | Ilimitado em repositório público |
| YouTube Data API | R$ 0 | **100 uploads/dia** (cota própria do `videos.insert`) |
| Blogger API v3 | R$ 0 | Uso pessoal é folgado |
| Músicas do sistema | R$ 0 | Geradas para o portal, sem royalties |

**Capacidade real:** com 100 uploads/dia, o gargalo nunca será a cota — será o volume de matérias. Na cadência de 30 minutos, o sistema dá conta de **até 48 vídeos por dia** com folga.

---

## 10. Manutenção e problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Workflow não roda | Agendador pausado após 60 dias sem commits | Actions → reativar, ou fazer um commit |
| “variáveis ausentes” no log | Secrets não cadastrados | Repetir o passo 5.4 |
| Vídeo gerado sem imagem | Capa do post não carregou | O sistema já usa um fundo de marca como reserva; verifique se o post tem imagem |
| Locução muito rápida | Resumo longo | Reduza `max_palavras_narracao` em `config.json` |
| “Nenhuma postagem nova” | Controle de já processados | Use `--todos` para reprocessar |
| Falha de upload | Token revogado | Gerar novo `YT_REFRESH_TOKEN` |
| Vídeo não aparece na vitrine | Playlist não informada | Preencher o ID nos secrets e no gadget |

---

## 11. Próximos passos que eu recomendo

1. **Rodar por 30 dias** e medir no Search Console a aba **Vídeos** — é o número que prova o ganho.
2. **Padronizar as capas** das matérias. É o item de maior impacto visual e o mais barato de resolver.
3. **Ampliar para Reels e TikTok** quando houver cadência estabelecida — mesma peça, distribuição nova.
4. **Criar uma página “Vídeos”** no portal, reunindo os Shorts por categoria, para consolidar autoridade temática.
5. **Testar variações de abertura** nas três primeiras palavras do título. Em Shorts, a abertura decide a retenção — e é o dado que o YouTube entrega de graça.

---

*Guia produzido para o portal Coletividade Evolutiva — sistema sob medida, com peças gratuitas e auditáveis.*
