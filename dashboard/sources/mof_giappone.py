"""Fonte dati: Ministero delle Finanze del Giappone (rendimenti giornalieri dei JGB).

File CSV pubblici, senza chiave, con i rendimenti per tutte le scadenze:
  jgbcme_all.csv  storico fino alla fine del mese scorso
  jgbcme.csv      solo il mese in corso
L'id è "JGB_" + la scadenza: "JGB_2Y", "JGB_10Y", "JGB_30Y"... (colonne del file). I file sono in codifica Shift-JIS.
"""

import io
import re
import time

import pandas as pd
import requests

from .errori import ErroreFonte

BASE = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/"
FILE_STORICO = "historical/jgbcme_all.csv"
FILE_MESE = "jgbcme.csv"
TENTATIVI = 3
TIMEOUT_SECONDI = 60
INTESTAZIONI = {"User-Agent": "Mozilla/5.0 (dashboard-macro)"}

_tabella: pd.DataFrame | None = None  # i file contengono tutte le scadenze: si scaricano una volta per esecuzione


def scarica(id_serie: str) -> pd.Series:
    """Rendimento giornaliero (%) di un JGB alla scadenza indicata, es. "JGB_10Y"."""
    global _tabella
    scadenza = id_serie.removeprefix("JGB_")
    if _tabella is None:
        storico = _scarica_file(FILE_STORICO)
        try:
            mese = _scarica_file(FILE_MESE)
        except ErroreFonte:
            mese = None  # il file del mese può mancare nei primi giorni: usiamo solo lo storico
        tabella = storico if mese is None else pd.concat([storico, mese])
        _tabella = tabella[~tabella.index.duplicated(keep="last")].sort_index()
    if scadenza not in _tabella:
        raise ErroreFonte(f"scadenza '{scadenza}' non presente nel file del Ministero")
    serie = _tabella[scadenza].dropna().rename(scadenza)
    if serie.empty:
        raise ErroreFonte("la serie non contiene valori numerici")
    return serie


def _scarica_file(nome: str) -> pd.DataFrame:
    ultimo_errore = "errore sconosciuto"
    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(BASE + nome, headers=INTESTAZIONI, timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            ultimo_errore = f"errore di rete ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                return _leggi_csv(risposta.content)
            ultimo_errore = f"HTTP {risposta.status_code}"
        if tentativo < TENTATIVI:
            time.sleep(2 * tentativo)
    raise ErroreFonte(f"Ministero delle Finanze: {ultimo_errore}")


def _leggi_csv(contenuto: bytes) -> pd.DataFrame:
    righe = contenuto.decode("cp932", errors="replace").splitlines()
    # Tengo l'intestazione ("Date,1Y,2Y,...") e le righe di dati (iniziano con una data 2026/9/30);
    # righe di titolo e avvertenze vengono scartate
    intestazione = next((r for r in righe if r.startswith("Date,")), None)
    if intestazione is None:
        raise ErroreFonte("file del Ministero delle Finanze in un formato inatteso")
    dati = [r for r in righe if re.match(r"\d{4}/\d{1,2}/\d{1,2},", r)]
    tabella = pd.read_csv(io.StringIO("\n".join([intestazione] + dati)), na_values=["-"])
    tabella.index = pd.to_datetime(tabella.pop("Date"), format="%Y/%m/%d")
    return tabella.apply(pd.to_numeric, errors="coerce")
