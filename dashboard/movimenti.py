"""Calcolo di "What changed this week": i movimenti più grandi rispetto alla volatilità normale di ogni serie.

Come funziona (le stesse regole sono spiegate sul sito, nella pagina Sources & method):
  1. Candidate: le serie con `movimenti: true` in config.yaml, giornaliere o settimanali, disponibili e non "in ritardo".
  2. Movimento: ultimo dato meno il dato di 7 giorni di calendario prima (l'ultimo valido a quella data).
     In punti base (bp) per i tassi e gli spread (unità "%"), in % per prezzi, indici e VIX.
  3. Normalità: deviazione standard dei movimenti a 7 giorni delle stesse serie nei 3 anni PRIMA dell'ultima settimana
     (finestre sovrapposte, una per ogni data). Con meno di 100 osservazioni la serie è esclusa.
  4. Punteggio: movimento / deviazione standard, con segno. Si mostra "×normal" = |punteggio|.
  5. Si tiene solo chi supera la soglia (2×), al massimo UNA serie per gruppo (`gruppo_movimenti`), le prime 5 per |punteggio|.

Il punteggio NON è una probabilità: dice "quante volte il movimento tipico di una settimana", non quanto sia raro.
Funzioni pure (niente rete, niente file): si provano con i test in tests/test_movimenti.py.
"""

from dataclasses import dataclass

import pandas as pd

from .data import Serie, tipo_variazione

GIORNI = 7                 # orizzonte del movimento (giorni di calendario)
ANNI_STORICO = 3           # quanta storia serve per stimare "una settimana normale"
MIN_OSSERVAZIONI = 100     # sotto questa soglia la stima della deviazione standard non è affidabile
SOGLIA = 2.0               # punteggio minimo per comparire in lista (vedi la motivazione in Sources & method)
MASSIMO = 5                # righe al massimo
FREQUENZE_AMMESSE = ("giornaliera", "settimanale")  # le serie mensili non hanno una "settimana"


@dataclass
class Movimento:
    """Un movimento già calcolato per una serie."""

    id: str
    etichetta: str
    gruppo: str | None
    unita: str                  # unità della serie (serve a formattare il movimento)
    tipo: str                   # "bp" (tassi e spread) oppure "%" (prezzi e indici)
    mossa: float                # in bp o in %, con segno
    dev_std: float              # deviazione standard dei movimenti a 7 giorni (nelle stesse unità)
    punteggio: float            # mossa / dev_std, con segno
    data_ultimo: pd.Timestamp   # data dell'ultimo dato usato
    n_osservazioni: int         # quanti movimenti storici hanno prodotto la deviazione standard


@dataclass
class Classifica:
    """Il risultato per l'Overview: le righe da mostrare e quante serie sono state controllate."""

    righe: list[Movimento]
    n_controllate: int
    n_sopra_soglia: int = 0     # quante serie superano la soglia, prima di tenerne una sola per gruppo
    soglia: float = SOGLIA
    massimo: int = MASSIMO


def _variazioni_a_7_giorni(dati: pd.Series, tipo: str, giorni: int = GIORNI) -> pd.Series:
    """Per ogni data: il movimento rispetto al valore di `giorni` giorni di calendario prima (l'ultimo valido a quella data).

    "bp": differenza × 100 (i tassi sono in %); "%": variazione percentuale (solo dove il valore di partenza è positivo).
    """
    dati = dati.dropna()
    dati = dati[~dati.index.duplicated(keep="last")].sort_index()
    prima = pd.Series(dati.asof(dati.index - pd.Timedelta(days=giorni)).to_numpy(), index=dati.index)
    if tipo == "bp":
        movimenti = (dati - prima) * 100
    else:
        movimenti = (dati / prima.where(prima > 0) - 1) * 100
    return movimenti.dropna()


def calcola(dati: pd.Series, tipo: str, giorni: int = GIORNI, anni: int = ANNI_STORICO,
            minimo: int = MIN_OSSERVAZIONI) -> tuple[float, float, int] | None:
    """(movimento dell'ultima settimana, deviazione standard storica, n. osservazioni) oppure None se non si può calcolare.

    La deviazione standard usa solo i movimenti che finiscono PRIMA dell'ultima settimana, così il movimento
    di oggi non "sporca" il suo stesso termine di paragone.
    """
    movimenti = _variazioni_a_7_giorni(dati, tipo, giorni)
    if movimenti.empty:
        return None
    ultimo = movimenti.index[-1]
    storico = movimenti[(movimenti.index < ultimo - pd.Timedelta(days=giorni))
                        & (movimenti.index >= ultimo - pd.DateOffset(years=anni))]
    if len(storico) < minimo:
        return None
    dev_std = float(storico.std())
    if not dev_std > 1e-9:   # serie ferma (es. un tasso che non cambia): ogni mossa sembrerebbe enorme
        return None
    return float(movimenti.iloc[-1]), dev_std, len(storico)


def movimento_serie(s: Serie, oggi: pd.Timestamp) -> Movimento | None:
    """Il movimento di una serie, o None se la serie non è candidata o non si può calcolare."""
    if not s.movimenti or not s.ok or s.frequenza not in FREQUENZE_AMMESSE or s.in_ritardo(oggi):
        return None
    tipo = "bp" if tipo_variazione(s.unita) == "bp" else "%"
    risultato = calcola(s.dati, tipo)
    if risultato is None:
        return None
    mossa, dev_std, n = risultato
    return Movimento(id=s.id, etichetta=s.etichetta, gruppo=s.gruppo_movimenti, unita=s.unita, tipo=tipo, mossa=mossa,
                     dev_std=dev_std, punteggio=mossa / dev_std, data_ultimo=s.ultima_data, n_osservazioni=n)


def classifica(serie: dict[str, Serie], oggi: pd.Timestamp, soglia: float = SOGLIA, massimo: int = MASSIMO) -> Classifica:
    """I movimenti più grandi rispetto alla normalità: sopra soglia, una serie per gruppo, al massimo `massimo` righe."""
    calcolati = [m for m in (movimento_serie(s, oggi) for s in serie.values()) if m is not None]
    sopra = sorted((m for m in calcolati if abs(m.punteggio) >= soglia), key=lambda m: abs(m.punteggio), reverse=True)
    scelti, gruppi_visti = [], set()
    for m in sopra:
        chiave = m.gruppo or m.id          # una serie senza gruppo conta come gruppo a sé
        if chiave in gruppi_visti:
            continue
        gruppi_visti.add(chiave)
        scelti.append(m)
        if len(scelti) == massimo:
            break
    return Classifica(righe=scelti, n_controllate=len(calcolati), n_sopra_soglia=len(sopra), soglia=soglia, massimo=massimo)
