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
PAUSE_SECONDI = (10, 30)       # attesa dopo il 1° e il 2° tentativo: il vuoto del BIS dura più di qualche secondo (Action del 01/10/2026: 3 vuoti a 2 e 4 secondi)
TIMEOUT_SECONDI = 60
# detail=dataonly: il BIS toglie i campi di testo che ripete su ogni riga (COMPILATION, SUPP_INFO_BREAKS, ~2,4 KB l'una riga). Senza, il tasso BoJ pesa 62 MB
# invece di 0,5 MB (stessi 24.894 valori, verificato su tutte le serie) e il BIS risponde spesso con un corpo vuoto (01/10/2026). Alla serie servono solo FREQ, REF_AREA, UNIT_MEASURE, TIME_PERIOD, OBS_VALUE.
PARAMETRI = {"format": "csv", "detail": "dataonly"}
INTESTAZIONI = {"User-Agent": "Mozilla/5.0 (dashboard-macro)"}


class _RispostaVuota(ErroreFonte):
    """Il BIS ha risposto 200 ma senza dati (corpo vuoto o solo l'intestazione): capita a volte e di solito passa al tentativo dopo."""


def scarica(id_serie: str) -> pd.Series:
    """Scarica tutto lo storico di una serie BIS. In caso di problemi solleva ErroreFonte."""
    if "/" not in id_serie:
        raise ErroreFonte("invalid BIS code: the form DATASET/KEY is required")
    ultimo_errore = "unknown error"

    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(URL_DATI + id_serie, params=PARAMETRI,
                                    headers=INTESTAZIONI, timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            ultimo_errore = f"network error ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                try:
                    serie = _converti_in_serie(risposta.text, id_serie)
                    print(f"  BIS {id_serie}: {len(risposta.content) / 1024:,.0f} KB, {len(serie):,} values", flush=True)   # il peso si vede nel log dell'Action
                    return serie
                except _RispostaVuota as errore:
                    ultimo_errore = str(errore)
                    print(f"  BIS {id_serie}: empty response (attempt {tentativo} of {TENTATIVI})"
                          + ("; trying again" if tentativo < TENTATIVI else "; giving up"), flush=True)
                    if tentativo < TENTATIVI:
                        time.sleep(PAUSE_SECONDI[tentativo - 1])
                    continue
            ultimo_errore = ("series not found at the BIS (wrong code?)" if risposta.status_code == 404
                             else f"HTTP {risposta.status_code}")
            if 400 <= risposta.status_code < 500 and risposta.status_code != 429:
                break
        if tentativo < TENTATIVI:
            time.sleep(PAUSE_SECONDI[tentativo - 1])

    raise ErroreFonte(ultimo_errore)


def _converti_in_serie(testo_csv: str, id_serie: str) -> pd.Series:
    if not testo_csv.strip():
        raise _RispostaVuota("the BIS returned no data")
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
        raise _RispostaVuota("the series contains no numeric values")
    return serie
