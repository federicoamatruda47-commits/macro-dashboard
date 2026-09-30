"""Fonte dati: Yahoo Finance, tramite la libreria yfinance.

ATTENZIONE: non è un'API ufficiale. Yahoo può cambiare il sito o bloccare le
richieste (succede soprattutto dai server "cloud" come quelli di GitHub Actions).
Per questo le serie Yahoo in config.yaml hanno, dove esiste, una riserva FRED.

Il codice di una serie è il "ticker" di Yahoo, per esempio:
  CL=F   future sul petrolio WTI (il "=F" indica un future continuo)
  GC=F   future sull'oro
  ^N225  indice Nikkei 225 (per le borse asiatiche)
  JPY=X  cambio dollaro/yen

Future "continuo" = Yahoo mostra sempre il contratto con la scadenza più vicina;
quando scade si passa al successivo e nel grafico può comparire un piccolo salto.
"""

import logging
import time

import pandas as pd
import yfinance as yf

from .errori import ErroreFonte

TENTATIVI = 3  # quante volte riprovare se Yahoo non risponde

# yfinance scrive i propri errori sul terminale: li raccogliamo noi in ErroreFonte
logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def scarica(ticker: str) -> pd.Series:
    """Scarica tutto lo storico giornaliero (prezzo di chiusura) di un ticker Yahoo.

    Restituisce una pandas Series con le date come indice e numeri decimali
    come valori. In caso di problemi solleva ErroreFonte.
    """
    ultimo_errore = "errore sconosciuto"

    for tentativo in range(1, TENTATIVI + 1):
        try:
            # auto_adjust=False: prezzi così come sono (per i future non ci sono dividendi da correggere)
            tabella = yf.Ticker(ticker).history(period="max", interval="1d", auto_adjust=False)
        except Exception as errore:  # yfinance può sollevare errori di tipi diversi
            ultimo_errore = f"Yahoo non risponde ({type(errore).__name__})"
        else:
            if tabella is not None and not tabella.empty and "Close" in tabella:
                return _pulisci(tabella["Close"], ticker)
            # Tabella vuota: ticker inesistente oppure richiesta bloccata da Yahoo
            ultimo_errore = "Yahoo non ha restituito dati (ticker errato o richiesta bloccata)"

        if tentativo < TENTATIVI:
            time.sleep(3 * tentativo)  # attesa crescente: 3s, 6s

    raise ErroreFonte(ultimo_errore)


def _pulisci(chiusure: pd.Series, ticker: str) -> pd.Series:
    """Date senza fuso orario (solo il giorno), niente valori mancanti, ordine cronologico."""
    serie = pd.to_numeric(chiusure, errors="coerce").dropna()
    indice = pd.DatetimeIndex(serie.index)
    if indice.tz is not None:
        indice = indice.tz_localize(None)  # tiene l'ora locale della borsa, poi la togliamo
    serie.index = indice.normalize()
    # Stesso giorno ripetuto (raro, succede con il dato del giorno in corso): teniamo l'ultimo
    serie = serie[~serie.index.duplicated(keep="last")].sort_index().rename(ticker)
    if serie.empty:
        raise ErroreFonte("la serie non contiene valori numerici")
    # Nota: i valori negativi NON si scartano (il WTI il 20/04/2020 ha chiuso a −37 $)
    return serie
