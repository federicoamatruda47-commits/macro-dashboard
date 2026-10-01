"""Pagina del Paese (economies/country.html?c=ISO3) e collegamenti Markets <-> Economies: elenco dei Paesi, dati di ogni Paese, destinazione dei link.

Funzioni pure (testate in tests/test_paesi.py) tranne `scrivi_dati`, che scrive i file JSON in site/economies/dati/.

Il blocco `paesi:` di config.yaml dice, per ogni chiave del campo `paese` delle serie (us, it, jp...), il codice ISO3, il nome, l'eventuale pagina di
livello A (economies/usa...) e le serie del riquadro Markets. REGOLA DELLA DESTINAZIONE (`destinazione`):
  1. se il Paese ha una pagina di livello A e quella pagina è `completa: true` (campo del blocco `pagine`) -> la pagina A;
  2. altrimenti, se ha un codice ISO3 presente nei dati -> economies/country.html?c=<ISO3>;
  3. altrimenti nessun link (l'area euro non ha il livello B; `global` e i gruppi di materie prime non sono Paesi).
Un link non porta mai a una pagina "in-arrivo" o incompleta, né a un codice che non è nei dati.
"""

import json
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import annuali

PAGINA_PAESE = "economies/country.html"
CARTELLA_DATI = "economies/dati"
ID_HUB_ECONOMIES = "economies"
# Per i Paesi senza dati FMI: l'indicatore della Banca Mondiale che prende il posto di quello del WEO (stesso significato, mai mescolati)
SOSTITUTI_BM = {"gdp_nominal": "gdp_nominal_wb", "gdp_growth": "gdp_growth_wb", "gdp_per_capita_ppp": "gdp_per_capita_ppp_wb"}
# Indicatori del grafico/scheda che compaiono nell'elenco "ultimi valori" (per la mappa dell'Overview, step 14)
INDICATORI_MAPPA = ["gdp_per_capita_ppp", "gdp_growth", "inflation_average", "unemployment_ilo", "government_debt", "corruption_score"]
CIFRE_SIGNIFICATIVE = 6


@dataclass(frozen=True)
class PaeseConfig:
    """Una voce del blocco `paesi:` di config.yaml."""

    chiave: str                       # chiave del campo `paese` delle serie (us, jp...)
    nome: str
    nome_fonte: str | None = None     # nome originale della fonte (Banca Mondiale), se il nome mostrato è diverso
    iso3: str | None = None
    pagina: str | None = None         # id della pagina di livello A (economies/usa)
    mercati: tuple[str, ...] = ()     # serie del riquadro Markets
    vai: tuple[str, ...] = ()         # pagine Markets a cui rimanda il riquadro


def carica_paesi(config: dict) -> dict[str, PaeseConfig]:
    """Legge il blocco `paesi:` e controlla che i riferimenti esistano (serie, pagine, colori); solleva ValueError."""
    pagine = {p["id"]: p for p in config.get("pagine", [])}
    id_serie = {s["id"] for s in config.get("serie", [])}
    risultato = {}
    for chiave, voce in config.get("paesi", {}).items():
        if chiave not in config.get("colori", {}):
            raise ValueError(f"paesi.{chiave}: la chiave deve essere definita anche in 'colori'")
        iso3 = voce.get("iso3")
        if iso3 is not None and not re.fullmatch(r"[A-Z]{3}", iso3):
            raise ValueError(f"paesi.{chiave}: iso3 '{iso3}' non valido")
        if "nome" not in voce:
            raise ValueError(f"paesi.{chiave}: manca il nome")
        if voce.get("pagina") and voce["pagina"] not in pagine:
            raise ValueError(f"paesi.{chiave}: la pagina '{voce['pagina']}' non è nel blocco 'pagine'")
        sconosciute = [i for i in voce.get("mercati", []) if i not in id_serie]
        if sconosciute:
            raise ValueError(f"paesi.{chiave}: serie sconosciute nel riquadro Markets: {sconosciute}")
        for vai in voce.get("vai", []):
            if vai not in pagine:
                raise ValueError(f"paesi.{chiave}: la pagina '{vai}' non è nel blocco 'pagine'")
        risultato[chiave] = PaeseConfig(chiave, voce["nome"], voce.get("nome_fonte"), iso3, voce.get("pagina"), tuple(voce.get("mercati", [])), tuple(voce.get("vai", [])))
    return risultato


# ---------------------------------------------------------------------
# Destinazione dei link
# ---------------------------------------------------------------------

def _relativo(destinazione: str, da_pagina: str) -> str:
    """Percorso relativo di `destinazione` (id di pagina o file) visto dalla cartella della pagina `da_pagina`."""
    return posixpath.relpath(destinazione, start=da_pagina)


def pagina_completa(config: dict, id_pagina: str | None) -> bool:
    """True se la pagina esiste, è `attiva` ed è segnata `completa: true`."""
    if not id_pagina:
        return False
    voce = next((p for p in config.get("pagine", []) if p["id"] == id_pagina), None)
    return bool(voce and voce.get("stato") == "attiva" and voce.get("completa"))


def destinazione(chiave: str, config: dict, da_pagina: str, codici_validi: set[str]) -> str | None:
    """Indirizzo relativo a cui porta il link "→ Economy" di un Paese, visto dalla pagina `da_pagina`; None se non c'è destinazione valida."""
    paese = carica_paesi(config).get(chiave)
    if paese is None:
        return None
    if pagina_completa(config, paese.pagina):
        return _relativo(paese.pagina, da_pagina) + "/"
    if paese.iso3 and paese.iso3 in codici_validi:
        return f"{_relativo(PAGINA_PAESE, da_pagina)}?c={paese.iso3}"
    return None


def pagina_completa_del_paese(iso3: str, config: dict) -> str | None:
    """Per il "Full page →" della pagina del Paese (che sta in economies/): l'indirizzo della pagina di livello A, solo se è completa."""
    for paese in carica_paesi(config).values():
        if paese.iso3 == iso3 and pagina_completa(config, paese.pagina):
            return _relativo(paese.pagina, ID_HUB_ECONOMIES) + "/"
    return None


def link_economia_per_serie(serie_paesi: list[str], config: dict, da_pagina: str, codici_validi: set[str]) -> list[dict]:
    """I link "→ Economy" di un grafico Markets: uno per ogni Paese diverso presente tra le sue serie (nell'ordine in cui compaiono)."""
    paesi = carica_paesi(config)
    link, visti = [], set()
    for chiave in serie_paesi:
        if chiave in visti or chiave not in paesi:
            continue
        visti.add(chiave)
        href = destinazione(chiave, config, da_pagina, codici_validi)
        if href:
            link.append({"nome": paesi[chiave].nome, "href": href})
    return link


# ---------------------------------------------------------------------
# Elenco dei Paesi e dati di ogni Paese
# ---------------------------------------------------------------------

def elenco_paesi(imf: annuali.Snapshot | None, bm: annuali.Snapshot | None, config: dict) -> list[dict]:
    """Tutti i Paesi della pagina, in ordine alfabetico: {c, nome, regione, fmi, bm}. I Paesi sono quelli dell'FMI e della Banca Mondiale insieme."""
    codici_imf = imf.codici_paesi() if imf else set()
    codici_bm = bm.codici_paesi() if bm else set()
    nomi_wb = dict(zip(bm.paesi["paese"], bm.paesi["nome"])) if bm is not None and bm.paesi is not None else {}
    regioni_wb = dict(zip(bm.paesi["paese"], bm.paesi["regione"])) if bm is not None and bm.paesi is not None else {}
    nomi_config = {c: v["nome"] for c, v in config.get("nomi_paesi", {}).items()}
    nomi_config.update({p.iso3: p.nome for p in carica_paesi(config).values() if p.iso3})
    extra = config.get("paesi_aggiuntivi", {})
    elenco = []
    for codice in sorted(codici_imf | codici_bm):
        voce = extra.get(codice, {})
        nome_fonte = voce.get("nome") or nomi_wb.get(codice) or codice          # il nome come lo scrive la fonte
        nome = nomi_config.get(codice) or nome_fonte
        regione = (voce.get("regione") or regioni_wb.get(codice) or "").strip()
        elenco.append({"c": codice, "nome": nome, "nome_fonte": nome_fonte, "regione": regione, "fmi": codice in codici_imf, "bm": codice in codici_bm})
    return sorted(elenco, key=lambda p: (p["nome"].casefold(), p["c"]))


def _cifre(valore: float) -> float:
    """Il valore con 6 cifre significative: abbastanza per i grafici e dà file piccoli (un numero come 2550.11 invece di 2550.110691)."""
    return float(f"{float(valore):.{CIFRE_SIGNIFICATIVE}g}")


def _serie_compatta(serie: pd.Series, divisore: float) -> dict | None:
    """{"y": primo anno, "v": [valori...]} con i buchi come null; senza zeri iniziali né finali di dati mancanti."""
    serie = serie.dropna()
    if serie.empty:
        return None
    anni = list(range(int(serie.index.min()), int(serie.index.max()) + 1))
    return {"y": anni[0], "v": [(_cifre(serie[a] / divisore) if a in serie.index else None) for a in anni]}


def dati_paese(codice: str, imf: annuali.Snapshot | None, bm: annuali.Snapshot | None, catalogo: list[annuali.Indicatore]) -> dict | None:
    """I dati di un Paese per la pagina (None se non ha dati in nessuna delle due fonti).

    {"c", "fonte": "imf" | "wb" (da dove vengono PIL, crescita, PIL pro capite: Banca Mondiale solo se il Paese non ha dati FMI),
     "serie": {id catalogo: {"y", "v"}}, "ultimo": {id: [anno, valore]} (ultimo anno EFFETTIVO), "effettivo": {id: anno} (solo FMI),
     "fiscale": [id con anni fiscali], "finale": {id: ultimo anno con dato} (per riconoscere le proiezioni mancanti)}
    """
    ha_imf = bool(imf is not None and (imf.dati["paese"] == codice).any())
    per_id = {i.id: i for i in catalogo}
    scelti: dict[str, tuple[annuali.Indicatore, annuali.Snapshot | None, str]] = {}   # chiave pagina -> (indicatore, snapshot, id del catalogo)
    for ind in catalogo:
        if ind.id in SOSTITUTI_BM.values():
            continue
        if ind.fonte == annuali.FONTE_IMF:
            if ha_imf:
                scelti[ind.id] = (ind, imf, ind.id)
        else:
            scelti[ind.id] = (ind, bm, ind.id)
    if not ha_imf:
        for chiave, sostituto in SOSTITUTI_BM.items():
            scelti[chiave] = (per_id[sostituto], bm, sostituto)

    serie, ultimo, effettivo, fiscale, finale = {}, {}, {}, [], {}
    for chiave, (ind, snapshot, _) in sorted(scelti.items()):
        if snapshot is None:
            continue
        compatta = _serie_compatta(snapshot.serie(codice, ind.codice), ind.divisore)
        if compatta is None:
            continue
        serie[chiave] = compatta
        anni = list(range(compatta["y"], compatta["y"] + len(compatta["v"])))
        finale[chiave] = anni[-1]
        if ind.fonte == annuali.FONTE_IMF:
            anno = snapshot.ultimo_effettivo.get((codice, ind.codice))
            if anno is not None:
                effettivo[chiave] = anno
            if (codice, ind.codice) in snapshot.fiscale:
                fiscale.append(chiave)
        else:
            anno = anni[-1]                       # Banca Mondiale: tutti dati effettivi, l'ultimo anno con dato è l'ultimo effettivo
            effettivo[chiave] = anno
        if anno is not None:
            # L'ultimo valore effettivo: quello dell'ultimo anno effettivo o, se in quell'anno non c'è il dato (l'FMI lo segna "effettivo" ma i dati
            # finiscono prima: Siria, Sri Lanka...), l'ultimo anno precedente che ce l'ha
            presenti = [a for a in anni if a <= anno and compatta["v"][a - compatta["y"]] is not None]
            if presenti:
                ultimo[chiave] = [presenti[-1], compatta["v"][presenti[-1] - compatta["y"]]]
    if not serie:
        return None
    return {"c": codice, "fonte": "imf" if ha_imf else "wb", "serie": serie, "ultimo": ultimo, "effettivo": effettivo,
            "fiscale": sorted(fiscale), "finale": finale}


def ultimi_valori(dati: dict[str, dict]) -> dict:
    """{id indicatore: {ISO3: [valore, anno]}} per gli indicatori della mappa: il file piccolo che servirà alla mappa dell'Overview (step 14)."""
    risultato: dict[str, dict] = {i: {} for i in INDICATORI_MAPPA}
    for codice, d in dati.items():
        for ind in INDICATORI_MAPPA:
            if ind in d["ultimo"]:
                anno, valore = d["ultimo"][ind]
                risultato[ind][codice] = [valore, anno]
    return risultato


def _json(oggetto) -> str:
    return json.dumps(oggetto, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def scrivi_dati(cartella_site: Path, imf: annuali.Snapshot | None, bm: annuali.Snapshot | None, catalogo: list[annuali.Indicatore],
                elenco: list[dict]) -> dict[str, dict]:
    """Scrive site/economies/dati/<ISO3>.json per ogni Paese con dati e ultimi-valori.json; restituisce i dati scritti."""
    cartella = cartella_site / CARTELLA_DATI
    cartella.mkdir(parents=True, exist_ok=True)
    for vecchio in cartella.glob("*.json"):
        vecchio.unlink()                                   # un Paese tolto dall'elenco non deve restare nel sito
    scritti = {}
    for paese in elenco:
        dati = dati_paese(paese["c"], imf, bm, catalogo)
        if dati is None:
            continue
        (cartella / f"{paese['c']}.json").write_text(_json(dati), encoding="utf-8", newline="\n")
        scritti[paese["c"]] = dati
    (cartella / "ultimi-valori.json").write_text(_json(ultimi_valori(scritti)), encoding="utf-8", newline="\n")
    return scritti


# ---------------------------------------------------------------------
# Contenuto della pagina (contenuti/paese.yaml)
# ---------------------------------------------------------------------

FORME = {"barre", "linea", "barre-linea", "banda"}
FONTI_GRAFICO = {"imf", "wb"}


def carica_contenuto(percorso: Path, catalogo: list[annuali.Indicatore], note: dict | None = None) -> dict:
    """Legge contenuti/paese.yaml e controlla che indicatori, forme, righe "How to read it" e note esistano; solleva ValueError."""
    import yaml
    contenuto = yaml.safe_load(percorso.read_text(encoding="utf-8"))
    ids = {i.id for i in catalogo}
    note_ammesse = set(note["note"]) if note else None
    visti: set[str] = set()

    def controlla_note(dove: str, elenco: list[str]) -> None:
        if note_ammesse is not None:
            ignote = [n for n in elenco if n not in note_ammesse]
            if ignote:
                raise ValueError(f"{dove}: note mancanti in contenuti/note.yaml: {ignote}")

    for i in [k["id"] for k in contenuto["numeri_chiave"]] + contenuto["outlook"]["indicatori"]:
        if i not in ids:
            raise ValueError(f"paese.yaml: indicatore sconosciuto '{i}'")
    if not contenuto["outlook"].get("come_leggerlo"):
        raise ValueError("paese.yaml: manca come_leggerlo di outlook")
    controlla_note("outlook", contenuto["outlook"].get("note", []))
    for sezione in contenuto["sezioni"]:
        for g in sezione["grafici"]:
            if g["id"] in visti:
                raise ValueError(f"paese.yaml: grafico ripetuto '{g['id']}'")
            visti.add(g["id"])
            if g.get("forma") not in FORME:
                raise ValueError(f"grafico {g['id']}: forma '{g.get('forma')}' non valida (usa una tra {sorted(FORME)})")
            if g.get("fonte") not in FONTI_GRAFICO:
                raise ValueError(f"grafico {g['id']}: fonte '{g.get('fonte')}' non valida")
            if not g.get("come_leggerlo"):
                raise ValueError(f"grafico {g['id']}: manca la riga \"How to read it\" (come_leggerlo)")
            for i in list(g["serie"]) + list(g.get("tooltip_extra", [])):
                if i not in ids:
                    raise ValueError(f"grafico {g['id']}: indicatore sconosciuto '{i}'")
            controlla_note(f"grafico {g['id']}", g.get("note", []))
    return contenuto


def metadati_indicatori(catalogo: list[annuali.Indicatore]) -> dict[str, dict]:
    """Nome, unità e decimali di ogni indicatore (per le schede e i tooltip della pagina)."""
    return {i.id: {"nome": i.nome, "unita": i.unita, "decimali": i.decimali} for i in catalogo}
