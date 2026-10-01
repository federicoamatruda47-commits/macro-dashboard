"""Importatore del file WEO scaricato a mano dal sito dell'FMI (alternativa all'API, vedi imf.py).

Il file "By Countries" / "Entire Database" del WEO (es. WEOApr2026all.xls, che in realtà è un testo con le colonne separate da tabulazioni)
ha una riga per Paese e indicatore:
    WEO Country Code | ISO | WEO Subject Code | Country | Subject Descriptor | Subject Notes | Units | Scale |
    Country/Series-specific Notes | 1980 | 1981 | ... | 2031 | Estimates Start After
- `ISO` e `WEO Subject Code` sono gli stessi codici dell'API (ITA, NGDP_RPCH);
- i numeri possono avere la virgola come separatore delle migliaia ("2,370.123"); i valori mancanti sono "n/a", "--" o vuoti;
- `Estimates Start After` è l'ultimo anno con dato reale (lo stesso di LATEST_ACTUAL_ANNUAL_DATA); dopo, stime e proiezioni;
- i valori sono già nella scala dell'indicatore (miliardi, milioni, percentuale), come nell'API; il file li arrotonda a 3 decimali
  (l'API ne dà 6): lo snapshot arrotonda a 3 decimali in tutti e due i casi (annuali.formatta_valore).

Nota: il formato descritto qui è quello documentato dall'FMI e visto nelle edizioni passate; non si poteva scaricare il file dallo
script (il sito blocca le richieste automatiche). Per questo il lettore è tollerante (codifica, separatori, righe di nota in fondo).
"""

import csv
import io
import re

import pandas as pd

from . import errori
from ..annuali import anno_effettivo

COLONNE_NECESSARIE = ("ISO", "WEO Subject Code")
MANCANTI = {"", "n/a", "na", "--", "-", "…", "nan"}


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


def leggi_file_weo(contenuto: bytes | str, codici: set[str]) -> tuple[pd.DataFrame, dict[tuple[str, str], int]]:
    """(dati con colonne paese, indicatore, anno, valore; ultimo anno effettivo per (paese, indicatore)) per i codici richiesti."""
    testo = decodifica(contenuto) if isinstance(contenuto, bytes) else contenuto
    lettore = csv.reader(io.StringIO(testo), delimiter="\t", quotechar='"')
    intestazione = None
    righe_dati, ultimo = [], {}
    for riga in lettore:
        if intestazione is None:
            if all(c in riga for c in COLONNE_NECESSARIE):
                intestazione = [c.strip() for c in riga]
                posizione = {nome: i for i, nome in enumerate(intestazione)}
                anni = [(i, int(nome)) for i, nome in enumerate(intestazione) if re.fullmatch(r"\d{4}", nome)]
                if not anni:
                    raise errori.ErroreFonte("the WEO file has no year columns")
            continue
        if len(riga) <= max(posizione[c] for c in COLONNE_NECESSARIE):
            continue
        paese, codice = riga[posizione["ISO"]].strip(), riga[posizione["WEO Subject Code"]].strip()
        if codice not in codici or not re.fullmatch(r"[A-Z]{3}", paese):
            continue   # righe di nota in fondo, altri indicatori, Paesi senza codice ISO
        for i, anno in anni:
            if i < len(riga):
                valore = _numero(riga[i])
                if valore is not None:
                    righe_dati.append((paese, codice, anno, valore))
        if "Estimates Start After" in posizione and posizione["Estimates Start After"] < len(riga):
            effettivo = anno_effettivo(riga[posizione["Estimates Start After"]].strip().strip('"'))
            if effettivo is not None:
                ultimo[(paese, codice)] = effettivo
    if intestazione is None:
        raise errori.ErroreFonte("the file does not look like a WEO download (no 'ISO' and 'WEO Subject Code' columns)")
    if not righe_dati:
        raise errori.ErroreFonte("the WEO file contains none of the indicators of the catalogue")
    return pd.DataFrame(righe_dati, columns=["paese", "indicatore", "anno", "valore"]), ultimo
