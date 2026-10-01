"""Importa nello snapshot dati/weo/ il file WEO scaricato a mano dal sito dell'FMI (riserva dello script aggiorna_weo.py).

Uso (dalla cartella del progetto, con l'ambiente virtuale attivo):
    python tools/importa_weo.py FILE                      # scrive dati/weo/
    python tools/importa_weo.py FILE --cartella prova/weo
    python tools/importa_weo.py FILE --confronta         # non scrive: confronta con lo snapshot che c'è già

FILE = il file WEO scaricato dall'FMI: il CSV del portale data.imf.org (es. dataset_..._IMF.RES_WEO_9.0.0.csv, verificato) oppure il file "By Countries"
del vecchio sito (WEOApr2026all.xls, testo con tabulazioni): vedi dashboard/sources/imf_file.py.
La data di pubblicazione si legge dal file (colonna PUBLICATION_DATE del CSV del portale); nel formato vecchio non c'è e va data con
`--pubblicato AAAA-MM-GG` (per il WEO di aprile 2026: 2026-04-14).
Lo snapshot ha lo stesso formato di quello dello script; `--confronta` stampa le differenze con lo snapshot esistente (valori e ultimo anno
effettivo), cioè la verifica che i due modi di arrivarci diano lo stesso risultato.
"""

import argparse
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from dashboard import annuali  # noqa: E402
from dashboard.data import carica_config  # noqa: E402
from dashboard.sources.errori import ErroreFonte  # noqa: E402
from dashboard.sources.imf_file import leggi_file_weo  # noqa: E402

TOLLERANZA = 0.0006   # il file arrotonda a 3 decimali: due arrotondamenti di uno stesso numero a 6 e a 3 cifre differiscono al massimo di 0,0005


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa il file WEO scaricato a mano in dati/weo")
    parser.add_argument("file", type=Path)
    parser.add_argument("--pubblicato", help="data di pubblicazione dell'edizione, AAAA-MM-GG (serve solo se il file non la riporta)")
    parser.add_argument("--cartella", type=Path, default=RADICE / annuali.CARTELLE[annuali.FONTE_IMF])
    parser.add_argument("--confronta", action="store_true", help="non scrive nulla: confronta con lo snapshot già presente")
    argomenti = parser.parse_args()

    catalogo = annuali.indicatori_di(annuali.carica_catalogo(carica_config(RADICE / "config.yaml")), annuali.FONTE_IMF)
    equivalenze = {i.codice: i.ultimo_effettivo_da for i in catalogo if i.ultimo_effettivo_da}
    try:
        dati, ultimo, pubblicazione = leggi_file_weo(argomenti.file.read_bytes(), {i.codice for i in catalogo})
    except ErroreFonte as errore:
        print(f"ERRORE: {errore}")
        return 1
    pubblicazione = argomenti.pubblicato or pubblicazione
    if pubblicazione is None:
        print("ERRORE: il file non riporta la data di pubblicazione: usa --pubblicato AAAA-MM-GG")
        return 1
    ultimo = annuali.completa_ultimo_effettivo(ultimo, dati, equivalenze)
    print(f"Letti {len(dati):,} dati e {len(ultimo)} ultimi anni effettivi da {argomenti.file.name} (WEO pubblicato {pubblicazione})")

    if argomenti.confronta:
        esistente = annuali.leggi_cartella(argomenti.cartella, annuali.FONTE_IMF)
        if esistente is None:
            print("Nessuno snapshot da confrontare in quella cartella.")
            return 1
        # Si confronta con i valori arrotondati come nello snapshot (3 decimali)
        d = annuali.differenze(esistente.dati, dati, tolleranza=TOLLERANZA)
        print(f"Valori: {d.uguali:,} uguali, {d.cambiate} diversi, {d.aggiunte} solo nel file, {d.rimosse} solo nello snapshot")
        for esempio in d.esempi:
            print("   ", esempio)
        du = annuali.differenze_ultimo(esistente.ultimo_effettivo, ultimo)
        print(f"Ultimo anno effettivo: {len(du)} coppie diverse" + (f", es. {du[:6]}" if du else ""))
        return 0 if d.identici and not du else 2

    annuali.scrivi_snapshot(argomenti.cartella, dati, annuali.meta_weo(pubblicazione, [i.codice for i in catalogo], equivalenze), ultimo)
    print(f"Snapshot scritto in {argomenti.cartella}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
