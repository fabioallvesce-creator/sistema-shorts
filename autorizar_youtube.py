#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 AUTORIZAÇÃO ÚNICA (roda uma vez na sua máquina)
=============================================================================
 Gera o YT_REFRESH_TOKEN que o robô usará para publicar sem pedir login.

 Passo a passo:
  1. No Google Cloud Console crie um projeto e ative as APIs:
       • YouTube Data API v3
       • Blogger API v3
  2. Em "Credenciais" crie um ID de cliente OAuth do tipo
     "App para computador" e baixe o JSON como:  credenciais-cliente.json
  3. Execute:  python3 gerador/autorizar_youtube.py
  4. Copie as três linhas impressas para o arquivo .env (ou para os
     "Secrets" do GitHub).
=============================================================================
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ_CLIENTE = RAIZ / "credenciais-cliente.json"
ESCOPOS = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/blogger",
]


def main():
    if not ARQ_CLIENTE.exists():
        sys.exit(f"ERRO: coloque o arquivo de credenciais em {ARQ_CLIENTE}\n"
                 "(Google Cloud Console -> Credenciais -> ID do cliente OAuth -> App para computador)")

    from google_auth_oauthlib.flow import InstalledAppFlow
    fluxo = InstalledAppFlow.from_client_secrets_file(str(ARQ_CLIENTE), ESCOPOS)
    # abre o navegador para você escolher a conta do canal
    cred = fluxo.run_oauth_console() if hasattr(fluxo, "run_oauth_console") else fluxo.run_local_server(port=0)

    dados = json.loads(ARQ_CLIENTE.read_text(encoding="utf-8"))
    cfg = dados.get("installed", dados.get("web", {}))

    print("\n" + "=" * 68)
    print("Copie as linhas abaixo para o arquivo .env (e para os Secrets do GitHub):")
    print("=" * 68)
    print(f"YT_CLIENT_ID={cfg.get('client_id','')}")
    print(f"YT_CLIENT_SECRET={cfg.get('client_secret','')}")
    print(f"YT_REFRESH_TOKEN={cred.refresh_token}")
    print("=" * 68)
    if not cred.refresh_token:
        print("AVISO: o provedor não devolveu refresh_token. Revogue o acesso em "
              "https://myaccount.google.com/permissions e tente novamente.")


if __name__ == "__main__":
    main()