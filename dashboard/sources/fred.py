"""Fonte dati: FRED (Federal Reserve Bank of St. Louis).

Usa l'API ufficiale: https://fred.stlouisfed.org/docs/api/fred/
La chiave viene letta dalla variabile d'ambiente FRED_API_KEY
(in locale la carica build.py dal file .env, su GitHub arriva da un "secret").
"""

import os
import time

import pandas as pd
import requests

from .errori import ErroreFonte

URL_OSSERVAZIONI = "https://api.stlouisfed.org/fred/series/observations"
TENTATIVI = 3  # quante volte riprovare se la rete o il server hanno un problema
TIMEOUT_SECONDI = 30


def scarica(id_serie: str) -> pd.Series:
    """Scarica tutto lo storico di una serie FRED.

    Restituisce una pandas Series con le date come indice e numeri decimali
    come valori. In caso di problemi solleva ErroreFonte.
    """
    chiave = os.environ.get("FRED_API_KEY", "").strip()
    if not chiave:
        raise ErroreFonte("FRED_API_KEY variable not set")

    parametri = {"series_id": id_serie, "api_key": chiave, "file_type": "json"}
    ultimo_errore = "unknown error"

    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(URL_OSSERVAZIONI, params=parametri, timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            # Non usiamo str(errore): conterrebbe l'URL completo, chiave inclusa
            ultimo_errore = f"network error ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                return _converti_in_serie(risposta.json(), id_serie)
            ultimo_errore = _messaggio_errore(risposta, chiave)
            # Gli errori 4xx (es. serie inesistente) non si risolvono riprovando,
            # tranne il 429 = "troppe richieste, rallenta"
            if 400 <= risposta.status_code < 500 and risposta.status_code != 429:
                break

        if tentativo < TENTATIVI:
            time.sleep(2 * tentativo)  # attesa crescente: 2s, 4s

    raise ErroreFonte(ultimo_errore)


def _converti_in_serie(json_fred: dict, id_serie: str) -> pd.Series:
    """Trasforma la risposta JSON di FRED in una pandas Series pulita."""
    osservazioni = json_fred.get("observations", [])
    if not osservazioni:
        raise ErroreFonte("FRED returned no observations")

    tabella = pd.DataFrame(osservazioni)
    # FRED indica i giorni senza dato (es. festivi) con "." -> diventano NaN
    valori = pd.to_numeric(tabella["value"], errors="coerce")
    serie = pd.Series(valori.to_numpy(), index=pd.to_datetime(tabella["date"]), name=id_serie)
    serie = serie.dropna().sort_index()

    if serie.empty:
        raise ErroreFonte("the series contains no numeric values")
    return serie


def _messaggio_errore(risposta: requests.Response, chiave: str) -> str:
    """Estrae un messaggio d'errore leggibile, senza mai mostrare la chiave."""
    try:
        dettaglio = risposta.json().get("error_message", "")
    except ValueError:
        dettaglio = ""
    messaggio = f"HTTP {risposta.status_code}" + (f": {dettaglio}" if dettaglio else "")
    return messaggio.replace(chiave, "***")[:200]
