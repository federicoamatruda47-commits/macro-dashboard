"""Compone il testo (Markdown) della pull request dei dati della Banca Mondiale, dall'esito dei controlli e dal riepilogo delle differenze.

Uso (lo chiama il workflow `aggiorna-dati-bm.yml`; i file li scrive il workflow):
    python tools/descrizione_pr.py --esiti esiti/esiti.txt --riepilogo riepilogo.md [--titolo]

`esiti.txt`: una riga per controllo, `nome|superato` oppure `nome|FALLITO`. Con --titolo stampa solo il titolo della PR
("[checks failed] ..." se un controllo è fallito: la PR si apre in bozza, così non si unisce per distrazione).
Esce con 0 se tutti i controlli sono superati, 4 se qualcuno è fallito.
"""

import argparse
import sys
from pathlib import Path

NOMI = {
    "test": "Tests (`python -m unittest discover -s tests -t .`)",
    "build": "Site build (`python build.py`)",
    "inventario-controlla": "Charts and series inventory (`tools/inventario.py controlla`)",
    "inventario-sito": "Generated pages check (`tools/inventario.py sito`)",
    "link": "Internal links (`tools/controlla_link.py`)",
}


def leggi_esiti(testo: str) -> list[tuple[str, bool]]:
    esiti = []
    for riga in testo.splitlines():
        if "|" in riga:
            nome, _, stato = riga.partition("|")
            esiti.append((nome.strip(), stato.strip() == "superato"))
    return esiti


def titolo(esiti: list[tuple[str, bool]], mese: str) -> str:
    base = f"World Bank data snapshot {mese}"
    return base if all(ok for _, ok in esiti) else f"[checks failed] {base}"


def descrizione(esiti: list[tuple[str, bool]], riepilogo: str) -> str:
    righe = ["Automatic update of the World Bank snapshot (`dati/bm/`), made by the monthly workflow `aggiorna-dati-bm.yml`.",
             "The data changed since the last snapshot. **Review the differences below before merging**: merging publishes the new values on the site "
             "at the next build.", "", "## Checks run by the workflow before opening this pull request",
             "(Pull requests opened with `GITHUB_TOKEN` do not start other workflows, so the checks run inside this one.)", "",
             "| Check | Result |", "|---|---|"]
    for nome, ok in esiti:
        righe.append(f"| {NOMI.get(nome, nome)} | {'✅ passed' if ok else '❌ **FAILED** (see the log of the workflow run)'} |")
    if not all(ok for _, ok in esiti):
        righe += ["", "> ❌ **At least one check failed**: this pull request is a draft. Do not merge it until the cause is understood."]
    righe += ["", "## Differences", "", riepilogo.strip() or "(no summary)", "",
              "_Values are rounded to 3 decimals (integers from one million up) and sorted by country, indicator and year, "
              "so the diff of `dati.csv` shows only the values that changed._"]
    return "\n".join(righe) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Testo della pull request dei dati della Banca Mondiale")
    parser.add_argument("--esiti", type=Path, required=True)
    parser.add_argument("--riepilogo", type=Path)
    parser.add_argument("--mese", default="", help="es. 2026-10 (solo per il titolo)")
    parser.add_argument("--titolo", action="store_true")
    argomenti = parser.parse_args()

    esiti = leggi_esiti(argomenti.esiti.read_text(encoding="utf-8")) if argomenti.esiti.exists() else []
    if argomenti.titolo:
        print(titolo(esiti, argomenti.mese))
    else:
        print(descrizione(esiti, argomenti.riepilogo.read_text(encoding="utf-8") if argomenti.riepilogo else ""), end="")
    return 0 if all(ok for _, ok in esiti) else 4


if __name__ == "__main__":
    sys.exit(main())
