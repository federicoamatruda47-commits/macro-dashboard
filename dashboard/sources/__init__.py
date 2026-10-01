"""Registro delle fonti dati.

Ogni fonte è un modulo con una funzione `scarica(id_serie) -> pandas.Series`.
Il campo `fonte` di config.yaml sceglie quale funzione usare.

Per aggiungere una fonte (es. OCSE):
  1. crea dashboard/sources/ocse.py con una funzione `scarica(id_serie)`
  2. aggiungi una riga qui sotto:  "ocse": ocse.scarica,
  3. in config.yaml usa `fonte: ocse`

Nota: le serie con `fonte: calcolata` (es. uno spread = serie A − serie B)
non passano da qui: le calcola dashboard/data.py dopo aver scaricato le altre.
"""

from . import bis, ecb, fred, mof_giappone, statjp, yahoo
from .errori import ErroreFonte

FONTI = {
    "fred": fred.scarica,
    "ecb": ecb.scarica,
    "yahoo": yahoo.scarica,
    "bis": bis.scarica,
    "mof": mof_giappone.scarica,
    "statjp": statjp.scarica,
}

__all__ = ["FONTI", "ErroreFonte"]
