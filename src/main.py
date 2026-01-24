import io
import random
import re
import sys
from contextlib import suppress as contextlib_suppress
from pathlib import Path

import pandas as pd
from camoufox.utils import DefaultAddons
from pandascamoufox import CamoufoxDf
from PyPDF2 import PdfReader

if not (Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()):
    from PrettyColorPrinter import add_printer

    add_printer(1)

def tempo_aleatorio(min_segundos, max_segundos):
    return random.uniform(min_segundos, max_segundos)

def handler(_, __):
    cfox = CamoufoxDf(humanize=False, headless=True, **{"exclude_addons": [DefaultAddons.UBO]})

    def gf(selector="*"):
        while True:
            with contextlib_suppress(Exception):
                df = cfox.get_df(selector)
                if "aa_text" in df.columns:
                    return df

    cnpj = ""
    cfox.page.goto("https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao")

    gf("#cnpj").iloc[0].bb_fill(cnpj)
    gf("#continuar").iloc[0].bb_click()
    df = pd.DataFrame()
    while df.empty:
        with contextlib_suppress(Exception):
            df = gf('a[href="/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao"]')

    df.iloc[0].bb_click()

    gf('button[data-id="anoCalendarioSelect"]').iloc[0].bb_click()
    df = gf("li")
    df.loc[df.aa_text.str.contains("2026", na=False)].iloc[0].bb_click()
    gf('button[type="submit"].btn-success').iloc[0].bb_click()
    gf('input[value="202601"].paSelecionado').iloc[0].bb_click()
    gf("#btnEmitirDas").iloc[0].bb_click()
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
