"""Registro delle fonti dati.

Ogni fonte è un modulo con una funzione `scarica(id_serie) -> pandas.Series`.
Il campo `fonte` di config.yaml sceglie quale funzione usare.

Per aggiungere una fonte (es. BIS):
  1. crea dashboard/sources/bis.py con una funzione `scarica(id_serie)`
  2. aggiungi una riga qui sotto:  "bis": bis.scarica,
  3. in config.yaml usa `fonte: bis`

Nota: le serie con `fonte: calcolata` (es. uno spread = serie A − serie B)
non passano da qui: le calcola dashboard/data.py dopo aver scaricato le altre.
"""

from . import ecb, fred, yahoo
from .errori import ErroreFonte

FONTI = {
    "fred": fred.scarica,
    "ecb": ecb.scarica,
    "yahoo": yahoo.scarica,
}

__all__ = ["FONTI", "ErroreFonte"]
