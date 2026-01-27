import base64
import datetime
import io
import logging
import os
import random
import re
import sys
import time
from contextlib import suppress as contextlib_suppress
from pathlib import Path

import pandas as pd
import requests
from camoufox.utils import DefaultAddons
from pandascamoufox import CamoufoxDf
from PyPDF2 import PdfReader

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout, force=True
)
logger = logging.getLogger(__name__)

# Força flush imediato
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


def tempo_aleatorio(min_segundos=0.3, max_segundos=0.7):
    return random.uniform(min_segundos, max_segundos)



logger.info("=== INICIO DA FUNÇÃO ===")

cnpj = os.getenv("CNPJ", "")
if not cnpj:
    logger.info("❌ CNPJ não configurado, retornando")
    sys.exit(1)
logger.info(f"✓ CNPJ carregado: {cnpj[:6]}...")

logger.info("\n=== INICIALIZANDO CAMOUFOX ===")
cfox = CamoufoxDf(humanize=False, headless=True, **{"exclude_addons": [DefaultAddons.UBO]})
logger.info("✓ Camoufox inicializado")


def gf(selector="*"):
    while True:
        with contextlib_suppress(Exception):
            df = cfox.get_df(selector)
            if "aa_text" in df.columns:
                return df


agora = datetime.datetime.now(tz=datetime.UTC)
ano_str = agora.strftime("%Y")
ano_mes = agora.strftime("%Y%m")
logger.info(f"✓ Período: {ano_mes}")

logger.info("\n=== CARREGANDO PÁGINA INICIAL ===")
cfox.page.goto("https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao")
logger.info("✓ Página carregada")
time.sleep(tempo_aleatorio())

logger.info("\n=== PREENCHENDO CNPJ ===")
gf("#cnpj").iloc[0].bb_fill(cnpj)
logger.info("✓ CNPJ preenchido")
time.sleep(tempo_aleatorio())

logger.info("\n=== CLICANDO EM CONTINUAR ===")
gf("#continuar").iloc[0].bb_click()
logger.info("✓ Botão continuar clicado")

logger.info("\n=== AGUARDANDO PÁGINA DE EMISSÃO ===")
df = pd.DataFrame()
tentativas = 0
while df.empty:
    tentativas += 1
    with contextlib_suppress(Exception):
        df = gf("a")
        df = df.loc[df.aa_text.str.contains("Emitir Guia de Pagamento", na=False)]
logger.info(f"✓ Link de emissão encontrado após {tentativas} tentativas")

time.sleep(tempo_aleatorio())
logger.info("\n=== ACESSANDO EMISSÃO ===")
df.iloc[0].bb_click()
logger.info("✓ Link de emissão clicado")
time.sleep(tempo_aleatorio())

logger.info("\n=== SELECIONANDO ANO ===")
gf('button[data-id="anoCalendarioSelect"]').iloc[0].bb_click()
logger.info("✓ Dropdown de ano aberto")
time.sleep(tempo_aleatorio())

logger.info(f"=== PROCURANDO ANO {ano_str} ===")
df = gf("li")
df.loc[df.aa_text.str.contains(ano_str, na=False)].iloc[0].bb_click()
logger.info(f"✓ Ano {ano_str} selecionado")
time.sleep(tempo_aleatorio())

logger.info("\n=== SUBMETENDO FORMULÁRIO ===")
gf('button[type="submit"].btn-success').iloc[0].bb_click()
logger.info("✓ Formulário submetido")
time.sleep(tempo_aleatorio())

logger.info(f"\n=== SELECIONANDO MÊS {ano_mes} ===")
gf(f'input[value="{ano_mes}"].paSelecionado').iloc[0].bb_click()
logger.info(f"✓ Mês {ano_mes} selecionado")
time.sleep(tempo_aleatorio())

logger.info("\n=== CLICANDO EM EMITIR DAS ===")
gf("#btnEmitirDas").iloc[0].bb_click()
logger.info("✓ Botão emitir DAS clicado")
time.sleep(tempo_aleatorio())

page = cfox.page
logger.info("\n=== INICIANDO DOWNLOAD DO PDF ===")
try:
    with page.expect_download(timeout=5000) as download_info:
        logger.info("  Aguardando download...")
        gf('a[href="/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao/imprimir"]').iloc[0].bb_click()
        logger.info("  Link de impressão clicado")

    download = download_info.value
    logger.info(f"✓ Download iniciado: {download}")

    pdf_path = download.path()
    logger.info(f"✓ PDF salvo em: {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    logger.info(f"✓ PDF lido: {len(pdf_bytes)} bytes")

except Exception as e:
    logger.info(f"❌ ERRO NO DOWNLOAD: {type(e).__name__}: {e}")
    raise

logger.info("\n=== PROCESSANDO PDF ===")
pdf_file = io.BytesIO(pdf_bytes)
reader = PdfReader(pdf_file)
logger.info(f"✓ PDF carregado: {len(reader.pages)} páginas")

texto = reader.pages[0].extract_text()
logger.info("✓ Texto extraído")

logger.info("\n=== TEXTO EXTRAÍDO ===")
logger.info(texto)
logger.info("=" * 80)

logger.info("\n=== PROCURANDO CÓDIGO DE BARRAS ===")
pattern = r"(\d{11}\s+\d{1}\s+\d{11}\s+\d{1}\s+\d{11}\s+\d{1}\s+\d{11}\s+\d{1})"
match = re.search(pattern, texto)

if match:
    codigo_barras_formatado = match.group(1)
    logger.info(f"✅ Código de Barras encontrado: {codigo_barras_formatado}")
    api = os.getenv("WHATSAPP_API_URL", "")
    if api:
        logging.info("Enviando para o zap")
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        requests.post(
            f"{api}/send",
            json={
                "barcode": codigo_barras_formatado,
                "pdfBase64": pdf_base64,
            },
        )
    else:
        logging.info("sem api configurada")
else:
    logger.info("❌ Código de barras não encontrado no padrão esperado")
