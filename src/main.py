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


api = os.getenv("WHATSAPP_API_URL", "")
cnpj = os.getenv("CNPJ", "")
if not cnpj or not api:
    logger.info("❌ CNPJ ou API do WHATSAPP não configurado, retornando")
    sys.exit(1)

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

cfox.page.goto("https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao")

time.sleep(tempo_aleatorio())

gf("#cnpj").iloc[0].bb_fill(cnpj)
time.sleep(tempo_aleatorio())

gf("#continuar").iloc[0].bb_click()


df = pd.DataFrame()
tentativas = 0
while df.empty:
    tentativas += 1
    with contextlib_suppress(Exception):
        df = gf("a")
        df = df.loc[df.aa_text.str.contains("Emitir Guia de Pagamento", na=False)]
logger.info(f"✓ Link de emissão encontrado após {tentativas} tentativas")

time.sleep(tempo_aleatorio())
df.iloc[0].bb_click()
time.sleep(tempo_aleatorio())

gf('button[data-id="anoCalendarioSelect"]').iloc[0].bb_click()
time.sleep(tempo_aleatorio())

df = gf("li")
df.loc[df.aa_text.str.contains(ano_str, na=False)].iloc[0].bb_click()
logger.info(f"✓ Ano {ano_str} selecionado")
time.sleep(tempo_aleatorio())

gf('button[type="submit"].btn-success').iloc[0].bb_click()
time.sleep(tempo_aleatorio())

gf(f'input[value="{ano_mes}"].paSelecionado').iloc[0].bb_click()
logger.info(f"✓ Mês {ano_mes} selecionado")
time.sleep(tempo_aleatorio())

gf("#btnEmitirDas").iloc[0].bb_click()
time.sleep(tempo_aleatorio())

page = cfox.page
try:
    with page.expect_download(timeout=5000) as download_info:
        gf('a[href="/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao/imprimir"]').iloc[0].bb_click()
    download = download_info.value
    pdf_path = download.path()
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

except Exception as e:
    logger.info(f"❌ ERRO NO DOWNLOAD: {type(e).__name__}: {e}")
    raise

pdf_file = io.BytesIO(pdf_bytes)
reader = PdfReader(pdf_file)
logger.info(f"✓ PDF carregado: {len(reader.pages)} páginas")

texto = reader.pages[0].extract_text()

pattern = r"(\d{11}\s+\d{1}\s+\d{11}\s+\d{1}\s+\d{11}\s+\d{1}\s+\d{11}\s+\d{1})"
match = re.search(pattern, texto)

if match:
    codigo_barras_formatado = match.group(1)
    logger.info(f"✅ Código de Barras encontrado: {codigo_barras_formatado}")

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    requests.post(
        f"{api}/send",
        json={
            "barcode": codigo_barras_formatado,
            "pdfBase64": pdf_base64,
        },
    )
else:
    logger.info("❌ Código de barras não encontrado no padrão esperado")
