"""Importatore del file WEO scaricato a mano dall'FMI (alternativa all'API, vedi imf.py). Legge due formati.

1. **File CSV del portale data.imf.org** (formato verificato sul file vero scaricato il 01/10/2026, "IMF.RES_WEO_9.0.0", UTF-8 con BOM, separatore
   virgola, valori tra virgolette). Una riga per serie, colonne `SERIES_CODE` ("ITA.NGDP_RPCH.A" = Paese.indicatore.frequenza), `COUNTRY` (nome),
   `INDICATOR` (nome lungo), `SCALE`, `UNIT`, `PUBLICATION_DATE` ("2026-04-14T13:00:00Z"), `LATEST_ACTUAL_ANNUAL_DATA` ("2025", "FY2024/25" o vuoto),
   poi una colonna per anno (1980...2031) con valori a 3 decimali o vuoti. Contiene le stesse serie dell'API (8.200: 197 Paesi e 13 aggregati).
2. **File "By Countries" del vecchio sito** (WEOApr2026all.xls: testo con tabulazioni; formato documentato dall'FMI, NON verificato su un file recente):
   colonne `ISO`, `WEO Subject Code`, ..., una per anno, `Estimates Start After`; numeri con la virgola delle migliaia, "n/a" per i mancanti.

In tutti e due: i codici del Paese e dell'indicatore sono quelli dell'API (ITA, NGDP_RPCH); i valori sono già nella scala dell'indicatore
(miliardi, milioni, percentuale); il file li arrotonda a 3 decimali (l'API ne dà 6) e lo snapshot arrotonda a 3 decimali in tutti e due i casi
(annuali.formatta_valore). L'ultimo anno effettivo di PPPPC manca anche nel file vero (come nell'API): lo completa annuali.completa_ultimo_effettivo.
Gli aggregati (G001...) si scartano: lo snapshot ha solo i Paesi.
"""

import csv
import io
import re

import pandas as pd

from . import errori
from ..annuali import anno_effettivo

COLONNE_NECESSARIE = ("ISO", "WEO Subject Code")     # formato tabulato
MANCANTI = {"", "n/a", "na", "--", "-", "…", "nan"}
Risultato = tuple[pd.DataFrame, dict[tuple[str, str], int], str | None]


def decodifica(contenuto: bytes) -> str:
    """Testo del file: riconosce UTF-16 e UTF-8 con BOM, poi prova UTF-8 e infine Windows-1252."""
    if contenuto.startswith((b"\xff\xfe", b"\xfe\xff")):
        return contenuto.decode("utf-16")
    if contenuto.startswith(b"\xef\xbb\xbf"):
        return contenuto.decode("utf-8-sig")
    try:
        return contenuto.decode("utf-8")
    except UnicodeDecodeError:
        return contenuto.decode("cp1252")


def _numero(testo: str) -> float | None:
    pulito = testo.strip().strip('"').replace(",", "").replace(" ", "")
    if pulito.lower() in MANCANTI:
        return None
    try:
        return float(pulito)
    except ValueError:
        return None


def _anni(intestazione: list[str]) -> list[tuple[int, int]]:
    """Le colonne degli anni: [(posizione, anno)]."""
    anni = [(i, int(nome)) for i, nome in enumerate(intestazione) if re.fullmatch(r"\d{4}", nome)]
    if not anni:
        raise errori.ErroreFonte("the WEO file has no year columns")
    return anni


def _aggiungi_anni(righe_dati: list, riga: list[str], anni: list[tuple[int, int]], paese: str, codice: str) -> None:
    for i, anno in anni:
        if i < len(riga):
            valore = _numero(riga[i])
            if valore is not None:
                righe_dati.append((paese, codice, anno, valore))


def leggi_file_weo(contenuto: bytes | str, codici: set[str]) -> Risultato:
    """(dati con colonne paese, indicatore, anno, valore; ultimo anno effettivo per (paese, indicatore); data di pubblicazione "2026-04-14" se il file la riporta)
    per i codici richiesti. Riconosce da solo il formato del file (vedi la descrizione in alto)."""
    testo = decodifica(contenuto) if isinstance(contenuto, bytes) else contenuto
    testo = testo.lstrip("﻿")
    if "SERIES_CODE" in testo.split("\n", 1)[0]:
        return _leggi_csv_portale(testo, codici)
    return _leggi_testo_tabulato(testo, codici)


def _leggi_csv_portale(testo: str, codici: set[str]) -> Risultato:
    righe = list(csv.reader(io.StringIO(testo), delimiter=",", quotechar='"'))
    intestazione = [c.strip() for c in righe[0]]
    posizione = {nome: i for i, nome in enumerate(intestazione)}
    anni = _anni(intestazione)
    righe_dati: list = []
    ultimo: dict[tuple[str, str], int] = {}
    pubblicazione = None
    for riga in righe[1:]:
        if len(riga) <= posizione["SERIES_CODE"]:
            continue
        parti = riga[posizione["SERIES_CODE"]].strip().split(".")
        if len(parti) != 3 or parti[2] != "A" or parti[1] not in codici or not re.fullmatch(r"[A-Z]{3}", parti[0]):
            continue   # altri indicatori, serie non annuali, aggregati (G001...)
        paese, codice = parti[0], parti[1]
        _aggiungi_anni(righe_dati, riga, anni, paese, codice)
        if "LATEST_ACTUAL_ANNUAL_DATA" in posizione and posizione["LATEST_ACTUAL_ANNUAL_DATA"] < len(riga):
            effettivo = anno_effettivo(riga[posizione["LATEST_ACTUAL_ANNUAL_DATA"]])
            if effettivo is not None:
                ultimo[(paese, codice)] = effettivo
        if pubblicazione is None and "PUBLICATION_DATE" in posizione and posizione["PUBLICATION_DATE"] < len(riga):
            pubblicazione = riga[posizione["PUBLICATION_DATE"]].strip()[:10] or None
    if not righe_dati:
        raise errori.ErroreFonte("the WEO file contains none of the indicators of the catalogue")
    return pd.DataFrame(righe_dati, columns=["paese", "indicatore", "anno", "valore"]), ultimo, pubblicazione


def _leggi_testo_tabulato(testo: str, codici: set[str]) -> Risultato:
    lettore = csv.reader(io.StringIO(testo), delimiter="\t", quotechar='"')
    intestazione = None
    righe_dati: list = []
    ultimo: dict[tuple[str, str], int] = {}
    for riga in lettore:
        if intestazione is None:
            if all(c in riga for c in COLONNE_NECESSARIE):
                intestazione = [c.strip() for c in riga]
                posizione = {nome: i for i, nome in enumerate(intestazione)}
                anni = _anni(intestazione)
            continue
        if len(riga) <= max(posizione[c] for c in COLONNE_NECESSARIE):
            continue
        paese, codice = riga[posizione["ISO"]].strip(), riga[posizione["WEO Subject Code"]].strip()
        if codice not in codici or not re.fullmatch(r"[A-Z]{3}", paese):
            continue   # righe di nota in fondo, altri indicatori, Paesi senza codice ISO
        _aggiungi_anni(righe_dati, riga, anni, paese, codice)
        if "Estimates Start After" in posizione and posizione["Estimates Start After"] < len(riga):
            effettivo = anno_effettivo(riga[posizione["Estimates Start After"]].strip().strip('"'))
            if effettivo is not None:
                ultimo[(paese, codice)] = effettivo
    if intestazione is None:
        raise errori.ErroreFonte("the file does not look like a WEO download (no 'SERIES_CODE' or 'ISO' and 'WEO Subject Code' columns)")
    if not righe_dati:
        raise errori.ErroreFonte("the WEO file contains none of the indicators of the catalogue")
    return pd.DataFrame(righe_dati, columns=["paese", "indicatore", "anno", "valore"]), ultimo, None
