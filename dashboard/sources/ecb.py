"""Fonte dati: BCE (ECB Data Portal).

Usa l'API pubblica, senza chiave: https://data.ecb.europa.eu/help/api/overview
Il codice di una serie ha la forma "DATASET/CHIAVE", per esempio
  FM/D.U2.EUR.4F.KR.DFR.LEV  -> dataset FM, tasso sui depositi BCE (giornaliero)
È lo stesso codice che si vede sul sito della BCE, con "/" al posto del primo punto.
"""

import io
import time

import pandas as pd
import requests

from .errori import ErroreFonte

URL_DATI = "https://data-api.ecb.europa.eu/service/data/"
TENTATIVI = 3  # quante volte riprovare se la rete o il server hanno un problema
TIMEOUT_SECONDI = 60


def scarica(id_serie: str) -> pd.Series:
    """Scarica tutto lo storico di una serie BCE.

    Restituisce una pandas Series con le date come indice e numeri decimali
    come valori. In caso di problemi solleva ErroreFonte.
    """
    if "/" not in id_serie:
        raise ErroreFonte("codice BCE non valido: serve la forma DATASET/CHIAVE")
    dataset, chiave = id_serie.split("/", 1)

    # csvdata = tabella CSV; dataonly = solo date e valori, senza metadati
    parametri = {"format": "csvdata", "detail": "dataonly"}
    ultimo_errore = "errore sconosciuto"

    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(URL_DATI + dataset + "/" + chiave, params=parametri,
                                    timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            ultimo_errore = f"errore di rete ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                return _converti_in_serie(risposta.text, id_serie)
            if risposta.status_code == 404:
                # La BCE risponde 404 quando il codice non corrisponde a nessuna serie
                ultimo_errore = "serie non trovata presso la BCE (codice errato o dismesso?)"
            else:
                ultimo_errore = f"HTTP {risposta.status_code}"
            # Gli errori 4xx non si risolvono riprovando, tranne il 429 = "troppe richieste"
            if 400 <= risposta.status_code < 500 and risposta.status_code != 429:
                break

        if tentativo < TENTATIVI:
            time.sleep(2 * tentativo)  # attesa crescente: 2s, 4s

    raise ErroreFonte(ultimo_errore)


def _converti_in_serie(testo_csv: str, id_serie: str) -> pd.Series:
    """Trasforma il CSV della BCE in una pandas Series pulita."""
    if not testo_csv.strip():
        raise ErroreFonte("la BCE non ha restituito dati")
    tabella = pd.read_csv(io.StringIO(testo_csv), dtype={"TIME_PERIOD": str})
    if "TIME_PERIOD" not in tabella or "OBS_VALUE" not in tabella:
        raise ErroreFonte("risposta della BCE in un formato inatteso")
    if tabella["KEY"].nunique() > 1:
        raise ErroreFonte("il codice corrisponde a più serie: specificare la chiave completa")

    valori = pd.to_numeric(tabella["OBS_VALUE"], errors="coerce")
    serie = pd.Series(valori.to_numpy(), index=_date_bce(tabella["TIME_PERIOD"]), name=id_serie)
    serie = serie.dropna().sort_index()

    if serie.empty:
        raise ErroreFonte("la serie non contiene valori numerici")
    return serie


def _date_bce(periodi: pd.Series) -> pd.DatetimeIndex:
    """Converte le date della BCE in date vere.

    La BCE usa formati diversi a seconda della frequenza:
      "2026-09-30" (giornaliera), "2026-08" (mensile), "2026-Q2" (trimestrale).
    Come su FRED, un mese o un trimestre è datato al suo primo giorno.
    """
    if periodi.str.contains("Q").any():
        return pd.PeriodIndex(periodi, freq="Q").to_timestamp()
    return pd.DatetimeIndex(pd.to_datetime(periodi))
