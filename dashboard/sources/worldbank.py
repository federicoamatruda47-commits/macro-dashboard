"""Fonte dati: Banca Mondiale (WDI e WGI), API v2 senza chiave: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

Come l'FMI (vedi imf.py) NON è in `FONTI` e non si chiama a ogni build: i dati sono annuali e finiscono nello snapshot `dati/bm/`
(dashboard/annuali.py), scritto da `python tools/aggiorna_bm.py` (anche dal workflow mensile che apre una pull request se i dati cambiano).

  - WDI (sorgente 2): es. SL.UEM.TOTL.ZS (disoccupazione, stima modellata ILO), SP.POP.TOTL, NY.GDP.MKTP.KD.ZG.
  - WGI (sorgente 3, Worldwide Governance Indicators): i codici ora iniziano con GOV_WGI_ (es. GOV_WGI_CC.SC, punteggio 0-100 del controllo
    della corruzione, con gli estremi dell'intervallo al 90% _LB e _UB). Il vecchio codice del percentile (CC.PER.RNK) non esiste più dal 2025.
  - Una chiamata con country/all e per_page=20000 restituisce tutti i Paesi e gli aggregati in una pagina (provato anche da GitHub Actions).
"""

import time

import pandas as pd
import requests

from .errori import ErroreFonte

URL = "https://api.worldbank.org/v2/"
TENTATIVI = 3
TIMEOUT_SECONDI = 120
INTESTAZIONI = {"User-Agent": "Mozilla/5.0 (dashboard-macro)"}
PER_PAGINA = 20000


def _richiedi(percorso: str, parametri: dict) -> list:
    """Una richiesta all'API (risposta JSON = [meta, righe]) con qualche tentativo; solleva ErroreFonte in caso di problemi."""
    ultimo_errore = "unknown error"
    for tentativo in range(1, TENTATIVI + 1):
        try:
            risposta = requests.get(URL + percorso, params={"format": "json", **parametri}, headers=INTESTAZIONI,
                                    timeout=TIMEOUT_SECONDI)
        except requests.RequestException as errore:
            ultimo_errore = f"network error ({type(errore).__name__})"
        else:
            if risposta.status_code == 200:
                try:
                    contenuto = risposta.json()
                except ValueError:
                    raise ErroreFonte("the World Bank returned a response that is not JSON") from None
                if isinstance(contenuto, list) and len(contenuto) == 2 and isinstance(contenuto[1], list):
                    return contenuto
                # Es. un codice sbagliato risponde con [{"message": [...]}]: nessuna riga
                raise ErroreFonte("the World Bank returned no data (wrong indicator code?)")
            ultimo_errore = f"HTTP {risposta.status_code}"
            if 400 <= risposta.status_code < 500 and risposta.status_code != 429:
                break
        if tentativo < TENTATIVI:
            time.sleep(2 * tentativo)
    raise ErroreFonte(ultimo_errore)


def scarica_indicatore(codice: str, sorgente: int = 2) -> tuple[pd.DataFrame, str]:
    """Un indicatore per tutti i Paesi e gli aggregati: (colonne paese, anno, valore; data di aggiornamento della fonte "2026-07-13")."""
    righe: list[dict] = []
    pagina, pagine, aggiornato = 1, 1, ""
    while pagina <= pagine:
        # Il parametro `page` si manda solo dalla seconda pagina: con page=1 esplicito la Banca Mondiale a volte risponde con un'altra
        # sorgente dello stesso codice (provato il 01/10/2026 con SP.POP.TOTL: sorgente 25 invece della 2, aggiornata un anno prima).
        parametri = {"per_page": PER_PAGINA, "source": sorgente, **({"page": pagina} if pagina > 1 else {})}
        meta, voci = _richiedi(f"country/all/indicator/{codice}", parametri)
        if str(meta.get("sourceid")) != str(sorgente):
            raise ErroreFonte(f"the World Bank answered with source {meta.get('sourceid')} instead of {sorgente} for {codice}")
        pagine = int(meta.get("pages", 1))
        aggiornato = str(meta.get("lastupdated", ""))
        righe += voci
        pagina += 1
    dati = pd.DataFrame([{"paese": r["countryiso3code"], "anno": int(r["date"]), "valore": r["value"]}
                         for r in righe if r.get("countryiso3code") and r.get("value") is not None])
    if dati.empty:
        raise ErroreFonte("the indicator contains no values")
    return dati, aggiornato


def scarica_paesi() -> pd.DataFrame:
    """Elenco dei Paesi e degli aggregati: colonne paese (ISO3), nome, regione, tipo ("country" o "aggregate")."""
    _, voci = _richiedi("country", {"per_page": 400})
    return pd.DataFrame([{"paese": v["id"], "nome": v["name"], "regione": v["region"]["value"] if v["region"]["value"] != "Aggregates" else "",
                          "tipo": "aggregate" if v["region"]["value"] == "Aggregates" else "country"} for v in voci])
