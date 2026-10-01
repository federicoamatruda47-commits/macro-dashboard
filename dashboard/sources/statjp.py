"""Fonte dati: Statistics Bureau of Japan, tramite DBnomics.

DBnomics (https://db.nomics.world) è un aggregatore gratuito, senza chiave, di dati di enti statistici.
Qui serve per l'indice dei prezzi al consumo giapponese per componenti (l'ente non ha un'API semplice).
L'id ha la forma "DATASET/CODICE", per esempio
  CPIm/733  -> CPI senza alimentari freschi (il "core" ufficiale), indice mensile
  CPIm/740  -> CPI senza alimentari freschi né energia ("core-core")
Sono indici: la variazione annua si calcola in config.yaml con `trasformazione: yoy`.
"""

import time

import pandas as pd
import requests

from .errori import ErroreFonte

URL = "https://api.db.nomics.world/v22/series/STATJP/"
TENTATIVI = 3
TIMEOUT_SECONDI = 90
INTESTAZIONI = {"User-Agent": "Mozilla/5.0 (dashboard-macro)"}


def scarica(id_serie: str) -> pd.Series:
    ultimo_errore = "errore sconosciuto"
    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(URL + id_serie, params={"observations": 1},
                                    headers=INTESTAZIONI, timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            ultimo_errore = f"errore di rete ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                return _converti_in_serie(risposta.json(), id_serie)
            ultimo_errore = ("serie non trovata su DBnomics (codice errato?)" if risposta.status_code == 404
                             else f"HTTP {risposta.status_code}")
            if 400 <= risposta.status_code < 500 and risposta.status_code != 429:
                break
        if tentativo < TENTATIVI:
            time.sleep(2 * tentativo)
    raise ErroreFonte(ultimo_errore)


def _converti_in_serie(risposta: dict, id_serie: str) -> pd.Series:
    try:
        voce = risposta["series"]["docs"][0]
        periodi, valori = voce["period"], voce["value"]
    except (KeyError, IndexError, TypeError):
        raise ErroreFonte("risposta di DBnomics in un formato inatteso") from None
    numeri = pd.to_numeric(pd.Series(valori, dtype=object), errors="coerce")  # "NA" -> NaN
    serie = pd.Series(numeri.to_numpy(), index=pd.DatetimeIndex(pd.to_datetime(periodi)),
                      name=id_serie).dropna().sort_index()
    if serie.empty:
        raise ErroreFonte("la serie non contiene valori numerici")
    return serie
