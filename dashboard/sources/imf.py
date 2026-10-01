"""Fonte dati: FMI, World Economic Outlook (WEO), tramite la nuova API SDMX `api.imf.org` (senza chiave).

ATTENZIONE: a differenza delle altre fonti NON è registrata in `FONTI` e non si chiama a ogni build. I dati WEO (annuali, ~200 Paesi,
uscita ad aprile e ottobre) si scaricano a mano con `python tools/aggiorna_weo.py` e finiscono nello snapshot `dati/weo/`
(vedi dashboard/annuali.py). Si chiama poco di proposito: una richiesta per indicatore, due volte l'anno, avviata da una persona
(i termini d'uso dell'FMI vietano lo scarico automatico "in massa").

Si usa l'endpoint SDMX 3.0 con `attributes=LATEST_ACTUAL_ANNUAL_DATA`: restituisce solo 6 colonne (paese, indicatore, frequenza, anno,
valore, ultimo anno effettivo) invece delle ~60 dell'endpoint 2.1: circa 0,6 MB per indicatore invece di ~20 MB.
Provato il 01/10/2026 anche dai computer di GitHub Actions.

Dettagli verificati sui dati:
  - la chiave è PAESE.INDICATORE.FREQUENZA (es. `*.NGDP_RPCH.A` = crescita reale, tutti i Paesi, annuale);
  - `LATEST_ACTUAL_ANNUAL_DATA` è lo stesso su tutte le righe di una serie; vale "2025", oppure "FY2024/25" per i Paesi con anno fiscale;
    manca per gli aggregati (G001, GX123...) e per interi indicatori (PPPPC): vedi `annuali.completa_ultimo_effettivo`;
  - gli anni dopo l'ultimo anno effettivo sono stime o proiezioni (fino al 2031).
"""

import io
import time

import pandas as pd
import requests

from .errori import ErroreFonte

URL_DATI = "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.RES/WEO/+/"
TENTATIVI = 3
TIMEOUT_SECONDI = 180
INTESTAZIONI = {"Accept": "application/vnd.sdmx.data+csv", "User-Agent": "Mozilla/5.0 (dashboard-macro)"}


def _richiedi(chiave: str, attributi: str) -> str:
    """Una richiesta all'API con qualche tentativo; in caso di problemi solleva ErroreFonte."""
    ultimo_errore = "unknown error"
    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(URL_DATI + chiave, params={"attributes": attributi, "measures": "all"},
                                    headers=INTESTAZIONI, timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            ultimo_errore = f"network error ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                return risposta.content.decode("utf-8")
            ultimo_errore = ("not found at the IMF (wrong code?)" if risposta.status_code == 404 else f"HTTP {risposta.status_code}")
            if 400 <= risposta.status_code < 500 and risposta.status_code != 429:
                break
        if tentativo < TENTATIVI:
            time.sleep(2 * tentativo)
    raise ErroreFonte(ultimo_errore)


def scarica_indicatore(codice: str) -> pd.DataFrame:
    """Un indicatore WEO per tutti i Paesi: colonne paese, anno (int), valore (float), ultimo_effettivo (testo come lo scrive l'FMI)."""
    testo = _richiedi(f"*.{codice}.A", "LATEST_ACTUAL_ANNUAL_DATA")
    if not testo.strip():
        raise ErroreFonte("the IMF returned no data")
    tabella = pd.read_csv(io.StringIO(testo), dtype=str, keep_default_na=False)
    attese = {"COUNTRY", "INDICATOR", "TIME_PERIOD", "OBS_VALUE", "LATEST_ACTUAL_ANNUAL_DATA"}
    if not attese <= set(tabella.columns):
        raise ErroreFonte("unexpected IMF response format")
    if set(tabella["INDICATOR"]) != {codice}:
        raise ErroreFonte(f"the IMF returned a different indicator than {codice}")
    valori = pd.to_numeric(tabella["OBS_VALUE"], errors="coerce")
    risultato = pd.DataFrame({
        "paese": tabella["COUNTRY"], "anno": pd.to_numeric(tabella["TIME_PERIOD"], errors="coerce"),
        "valore": valori, "ultimo_effettivo": tabella["LATEST_ACTUAL_ANNUAL_DATA"],
    }).dropna(subset=["anno", "valore"])
    if risultato.empty:
        raise ErroreFonte("the indicator contains no numeric values")
    risultato["anno"] = risultato["anno"].astype(int)
    return risultato


def data_pubblicazione() -> str:
    """Data di pubblicazione dell'edizione corrente del WEO ("2026-04-14"), letta da una serie di prova (Italia, crescita reale)."""
    testo = _richiedi("ITA.NGDP_RPCH.A", "PUBLICATION_DATE")
    tabella = pd.read_csv(io.StringIO(testo), dtype=str, keep_default_na=False)
    if "PUBLICATION_DATE" not in tabella or tabella.empty or not tabella["PUBLICATION_DATE"].iloc[0]:
        raise ErroreFonte("the IMF did not return the publication date")
    return tabella["PUBLICATION_DATE"].iloc[0][:10]
