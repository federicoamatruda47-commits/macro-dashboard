"""Fonte dati: BIS (Banca dei Regolamenti Internazionali).

API pubblica, senza chiave: https://stats.bis.org/api-doc/v1/
Il codice di una serie ha la forma "DATASET/CHIAVE", per esempio
  WS_CBPOL/D.JP        -> tasso di policy del Giappone (giornaliero)
  WS_LONG_CPI/M.JP.771 -> inflazione annua (unità 771 = variazione % annua) del Giappone, mensile
Il BIS è l'unica fonte coerente per i tassi di policy di tutte le banche centrali.
"""

import io
import time

import pandas as pd
import requests

from .errori import ErroreFonte

URL_DATI = "https://stats.bis.org/api/v1/data/"
TENTATIVI = 3
TIMEOUT_SECONDI = 60
INTESTAZIONI = {"User-Agent": "Mozilla/5.0 (dashboard-macro)"}


def scarica(id_serie: str) -> pd.Series:
    """Scarica tutto lo storico di una serie BIS. In caso di problemi solleva ErroreFonte."""
    if "/" not in id_serie:
        raise ErroreFonte("invalid BIS code: the form DATASET/KEY is required")
    ultimo_errore = "unknown error"

    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(URL_DATI + id_serie, params={"format": "csv"},
                                    headers=INTESTAZIONI, timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            ultimo_errore = f"network error ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                return _converti_in_serie(risposta.text, id_serie)
            ultimo_errore = ("series not found at the BIS (wrong code?)" if risposta.status_code == 404
                             else f"HTTP {risposta.status_code}")
            if 400 <= risposta.status_code < 500 and risposta.status_code != 429:
                break
        if tentativo < TENTATIVI:
            time.sleep(2 * tentativo)

    raise ErroreFonte(ultimo_errore)


def _converti_in_serie(testo_csv: str, id_serie: str) -> pd.Series:
    if not testo_csv.strip():
        raise ErroreFonte("the BIS returned no data")
    tabella = pd.read_csv(io.StringIO(testo_csv))
    tabella.columns = [c.upper() for c in tabella.columns]
    if "TIME_PERIOD" not in tabella or "OBS_VALUE" not in tabella:
        raise ErroreFonte("unexpected BIS response format")
    chiavi = [c for c in ("FREQ", "REF_AREA", "UNIT_MEASURE") if c in tabella]
    if tabella[chiavi].drop_duplicates().shape[0] > 1:
        raise ErroreFonte("the code matches several series: give the full key")

    valori = pd.to_numeric(tabella["OBS_VALUE"], errors="coerce")
    # Date "2026-09-29" (giornaliere) o "2026-08" (mensili, datate al primo giorno del mese)
    serie = pd.Series(valori.to_numpy(), index=pd.DatetimeIndex(pd.to_datetime(tabella["TIME_PERIOD"])),
                      name=id_serie).dropna().sort_index()
    if serie.empty:
        raise ErroreFonte("the series contains no numeric values")
    return serie
