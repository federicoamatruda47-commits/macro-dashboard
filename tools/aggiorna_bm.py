"""Aggiorna lo snapshot della Banca Mondiale (WDI e WGI) in dati/bm/ dall'API api.worldbank.org.

Uso (dalla cartella del progetto, con l'ambiente virtuale attivo):
    python tools/aggiorna_bm.py
    python tools/aggiorna_bm.py --cartella prova/bm      # scrive altrove

Si lancia a mano dopo luglio (WDI) e settembre (WGI), oppure lo lancia il workflow mensile `aggiorna-dati-bm.yml`, che apre una pull request
solo se i dati sono cambiati. Una richiesta per indicatore del catalogo (config.yaml: indicatori, fonte wb) più l'elenco dei Paesi.
Se anche un solo indicatore fallisce non si scrive nulla. Nessuna data "di oggi" nei file: solo le date di aggiornamento dichiarate dalla
Banca Mondiale, così se i dati non cambiano la differenza (git diff) è vuota.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from dashboard import annuali  # noqa: E402
from dashboard.data import carica_config  # noqa: E402
from dashboard.sources import worldbank  # noqa: E402
from dashboard.sources.errori import ErroreFonte  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggiorna lo snapshot della Banca Mondiale (dati/bm)")
    parser.add_argument("--cartella", type=Path, default=RADICE / annuali.CARTELLE[annuali.FONTE_BM])
    argomenti = parser.parse_args()

    catalogo = annuali.indicatori_di(annuali.carica_catalogo(carica_config(RADICE / "config.yaml")), annuali.FONTE_BM)
    pezzi, aggiornamenti = [], {}
    try:
        paesi = worldbank.scarica_paesi()
        for indicatore in catalogo:
            tabella, aggiornato = worldbank.scarica_indicatore(indicatore.codice, indicatore.sorgente_wb)
            print(f"  OK  {indicatore.codice:<22} {len(tabella):>6} dati, {tabella['paese'].nunique():>3} paesi/aggregati, "
                  f"anni {tabella['anno'].min()}-{tabella['anno'].max()}, aggiornato {aggiornato}")
            tabella["indicatore"] = indicatore.codice
            pezzi.append(tabella[["paese", "indicatore", "anno", "valore"]])
            sorgente = "wgi" if indicatore.sorgente_wb == 3 else "wdi"
            aggiornamenti[sorgente] = max(aggiornamenti.get(sorgente, ""), aggiornato)
    except ErroreFonte as errore:
        print(f"ERRORE: {errore}. Non scrivo nulla.")
        return 1

    dati = pd.concat(pezzi, ignore_index=True)
    sconosciuti = sorted(set(dati["paese"]) - set(paesi["paese"]))
    if sconosciuti:
        print(f"Attenzione: {len(sconosciuti)} codici non sono nell'elenco dei Paesi e vengono scartati: {sconosciuti[:8]}")
        dati = dati[dati["paese"].isin(paesi["paese"])]
    meta = {"fonte": "World Bank (World Development Indicators, Worldwide Governance Indicators)",
            "indicatori": sorted(i.codice for i in catalogo),
            **{f"{sorgente}_aggiornato": data for sorgente, data in sorted(aggiornamenti.items())}}
    annuali.scrivi_snapshot(argomenti.cartella, dati, meta, paesi=paesi)
    veri = dati[dati["paese"].isin(set(paesi.loc[paesi["tipo"] == annuali.TIPO_PAESE, "paese"]))]
    print(f"\n{len(dati):,} dati scritti in {argomenti.cartella} ({veri['paese'].nunique()} Paesi, {dati['paese'].nunique() - veri['paese'].nunique()} aggregati)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
