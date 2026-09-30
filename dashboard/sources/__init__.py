"""Registro delle fonti dati.

Ogni fonte è un modulo con una funzione `scarica(id_serie) -> pandas.Series`.
Il campo `fonte` di config.yaml sceglie quale funzione usare.

Per aggiungere una fonte (es. BCE):
  1. crea dashboard/sources/ecb.py con una funzione `scarica(id_serie)`
  2. aggiungi una riga qui sotto:  "ecb": ecb.scarica,
  3. in config.yaml usa `fonte: ecb`
"""

from . import fred
from .errori import ErroreFonte

FONTI = {
    "fred": fred.scarica,
}

__all__ = ["FONTI", "ErroreFonte"]
