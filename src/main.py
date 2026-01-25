import datetime
import io
import os
import random
import re
import sys
import time
from contextlib import suppress as contextlib_suppress
from pathlib import Path

import pandas as pd
from camoufox.utils import DefaultAddons
from pandascamoufox import CamoufoxDf
from PyPDF2 import PdfReader

# from dotenv import load_dotenv
# load_dotenv()
#if not (Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()):
    #from PrettyColorPrinter import add_printer

    #add_printer(1)

def tempo_aleatorio(min_segundos=0.3, max_segundos=0.7):
    return random.uniform(min_segundos, max_segundos)


def handler(_, __):
    cnpj = os.getenv("CNPJ", "")
    if not cnpj:
        print("sem cnpj, retornando")
        return

    cfox = CamoufoxDf(humanize=False, headless=True, **{"exclude_addons": [DefaultAddons.UBO]})

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
    while df.empty:
        with contextlib_suppress(Exception):
            df = gf('a[href="/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao"]')

    time.sleep(tempo_aleatorio())
    df.iloc[0].bb_click()
    time.sleep(tempo_aleatorio())

    gf('button[data-id="anoCalendarioSelect"]').iloc[0].bb_click()
    time.sleep(tempo_aleatorio())

    df = gf("li")
    df.loc[df.aa_text.str.contains(ano_str, na=False)].iloc[0].bb_click()
    time.sleep(tempo_aleatorio())

    gf('button[type="submit"].btn-success').iloc[0].bb_click()
    time.sleep(tempo_aleatorio())

    gf(f'input[value="{ano_mes}"].paSelecionado').iloc[0].bb_click()
    time.sleep(tempo_aleatorio())

    gf("#btnEmitirDas").iloc[0].bb_click()
    time.sleep(tempo_aleatorio())

    page = cfox.page

    with page.expect_download(timeout=5000) as download_info:
        gf('a[href="/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao/imprimir"]').iloc[0].bb_click()

    download = download_info.value
    pdf_path = download.path()
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    pdf_file = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)

    texto = reader.pages[0].extract_text()

    print("=== TEXTO EXTRAÍDO ===")
    print(texto)
    print("=" * 80)

    pattern = r"(\d{11}\s+\d{1}\s+\d{11}\s+\d{1}\s+\d{11}\s+\d{1}\s+\d{11}\s+\d{1})"

    match = re.search(pattern, texto)

    if match:
        codigo_barras_formatado = match.group(1)
        print(f"✅ Código de Barras (formatado): {codigo_barras_formatado}")
    else:
        print("❌ Código de barras não encontrado")


if __name__ == "__main__" and "--no-run" not in sys.argv:
    handler(None, None)
