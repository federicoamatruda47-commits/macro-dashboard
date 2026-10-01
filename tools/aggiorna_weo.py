"""Aggiorna lo snapshot dell'FMI (WEO) in dati/weo/ dall'API api.imf.org.

Uso (dalla cartella del progetto, con l'ambiente virtuale attivo), a mano, a ogni nuovo WEO (metà aprile e metà ottobre):
    python tools/aggiorna_weo.py
    python tools/aggiorna_weo.py --cartella prova/weo      # scrive altrove (per provare senza toccare dati/weo)

Una richiesta per indicatore del catalogo (config.yaml: indicatori, fonte imf), poco più di 0,6 MB l'una. Se anche un solo indicatore
fallisce non si scrive nulla: uno snapshot a metà sarebbe peggio di quello vecchio. Non si lancia dal workflow di GitHub: i termini
d'uso dell'FMI chiedono richieste avviate da una persona (vedi docs/economies-fonti.md). Se l'API cambiasse o l'FMI chiedesse di non usarla,
l'alternativa è tools/importa_weo.py con il file scaricato a mano dal sito (stesso formato di snapshot).

Cosa scrive (formato in dashboard/annuali.py): dati.csv, ultimo_effettivo.csv, meta.json. Nessuna data "di oggi": se il WEO non è cambiato,
la differenza (git diff) è vuota.
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from dashboard import annuali  # noqa: E402
from dashboard.data import carica_config  # noqa: E402
from dashboard.sources import imf  # noqa: E402
from dashboard.sources.errori import ErroreFonte  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggiorna lo snapshot WEO (dati/weo) dall'API api.imf.org")
    parser.add_argument("--cartella", type=Path, default=RADICE / annuali.CARTELLE[annuali.FONTE_IMF])
    argomenti = parser.parse_args()

    catalogo = annuali.indicatori_di(annuali.carica_catalogo(carica_config(RADICE / "config.yaml")), annuali.FONTE_IMF)
    equivalenze = {i.codice: i.ultimo_effettivo_da for i in catalogo if i.ultimo_effettivo_da}
    pezzi, ultimo = [], {}
    try:
        for indicatore in catalogo:
            tabella = imf.scarica_indicatore(indicatore.codice)
            print(f"  OK  {indicatore.codice:<14} {len(tabella):>6} dati, {tabella['paese'].nunique():>3} paesi/aggregati, "
                  f"anni {tabella['anno'].min()}-{tabella['anno'].max()}")
            tabella["indicatore"] = indicatore.codice
            pezzi.append(tabella[["paese", "indicatore", "anno", "valore"]])
            effettivi = tabella.drop_duplicates("paese").set_index("paese")["ultimo_effettivo"].map(annuali.anno_effettivo)
            ultimo.update({(p, indicatore.codice): int(a) for p, a in effettivi.items() if pd.notna(a)})
        pubblicazione = imf.data_pubblicazione()
    except ErroreFonte as errore:
        print(f"ERRORE: {errore}. Non scrivo nulla.")
        return 1

    dati = pd.concat(pezzi, ignore_index=True)
    # Solo i Paesi (codici ISO di 3 lettere): gli aggregati dell'FMI (G001, GX123...: mondo, economie avanzate...) stanno in un altro file del
    # sito dell'FMI e non hanno l'ultimo anno effettivo; così l'API e l'importatore del file danno lo stesso snapshot
    aggregati = sorted(set(dati["paese"]) - set(dati.loc[dati["paese"].str.fullmatch(r"[A-Z]{3}"), "paese"]))
    dati = dati[~dati["paese"].isin(aggregati)]
    ultimo = {chiave: anno for chiave, anno in ultimo.items() if chiave[0] not in set(aggregati)}
    print(f"Scartati {len(aggregati)} aggregati dell'FMI ({', '.join(aggregati[:5])}...): lo snapshot ha solo i Paesi")
    ultimo = annuali.completa_ultimo_effettivo(ultimo, dati, equivalenze)
    mancanti = annuali.senza_ultimo_effettivo(dati, ultimo)
    annuali.scrivi_snapshot(argomenti.cartella, dati, annuali.meta_weo(pubblicazione, [i.codice for i in catalogo], equivalenze), ultimo)
    print(f"\nWEO {annuali.edizione_weo(date.fromisoformat(pubblicazione))} (pubblicato {pubblicazione}): "
          f"{len(dati):,} dati scritti in {argomenti.cartella}")
    print(f"Ultimo anno effettivo: noto per {len(ultimo)} coppie Paese-indicatore; "
          f"mancante per {len(mancanti)} coppie di veri Paesi" + (f", es. {mancanti[:5]}" if mancanti else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
