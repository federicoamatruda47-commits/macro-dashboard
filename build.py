"""Comando unico della dashboard: scarica i dati e genera il sito in site/.

Uso (dalla cartella del progetto, con l'ambiente virtuale attivo):
    python build.py
    python build.py --config altro_config.yaml   # per provare una configurazione diversa

Codice di uscita:
    0 = sito generato (anche se alcune serie non sono state scaricate)
    1 = sito generato ma NESSUNA serie scaricata: probabilmente manca la chiave
        o FRED non risponde. Su GitHub questo blocca la pubblicazione, così
        resta online la versione precedente invece di una pagina vuota.
"""

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from dashboard.data import carica_config, scarica_tutte
from dashboard.render import genera_sito

RADICE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera la dashboard macro in site/")
    parser.add_argument("--config", default=RADICE / "config.yaml", type=Path,
                        help="file di configurazione delle serie (predefinito: config.yaml)")
    argomenti = parser.parse_args()

    # In locale la chiave sta nel file .env; su GitHub è già una variabile d'ambiente
    # (load_dotenv non sovrascrive variabili già impostate)
    load_dotenv(RADICE / ".env")

    inizio = time.perf_counter()
    config = carica_config(argomenti.config)
    print(f"Scarico {len(config['serie'])} serie...")
    serie = scarica_tutte(config)

    riuscite = sum(s.ok for s in serie.values())
    fallite = len(serie) - riuscite
    pagina = genera_sito(config, serie, RADICE)

    print(f"\nSito generato: {pagina}")
    print(f"Serie scaricate: {riuscite}/{len(serie)}"
          + (f"  ({fallite} con errore, vedi avviso sul sito)" if fallite else ""))
    print(f"Tempo impiegato: {time.perf_counter() - inizio:.1f} s")

    return 1 if riuscite == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
