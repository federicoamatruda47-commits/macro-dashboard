"""Dati annuali per Paese (FMI WEO e Banca Mondiale): catalogo, snapshot nel repository e controllo di freschezza.

Perché esiste (vedi docs/ristrutturazione.md, step 10a): questi dati cambiano 2-3 volte l'anno (WEO ad aprile e a ottobre,
Banca Mondiale a luglio e a settembre) e riguardano ~200 Paesi. Non passano da `Serie` e da `config.yaml: serie` (sarebbero
migliaia di voci) e non si scaricano a ogni build: stanno in file CSV dentro il repository (`dati/weo/`, `dati/bm/`), scritti da
`tools/aggiorna_weo.py` (o dall'importatore del file WEO) e da `tools/aggiorna_bm.py`. La build giornaliera legge solo quei file.

Formato dello snapshot (uguale per le due fonti, scelto perché le differenze tra due versioni mostrino solo i valori cambiati):
  <cartella>/dati.csv                    paese,indicatore,anno,valore       ordinato per (paese, indicatore, anno), valori a 3 decimali
  <cartella>/ultimo_effettivo.csv        paese,indicatore,anno,anno_fiscale  solo FMI: ultimo anno con dato reale (dopo = stima/proiezione); anno_fiscale = 1 se
                                         l'FMI lo scrive come anno fiscale ("FY2024/25": si legge 2024, l'anno in cui inizia)
  <cartella>/paesi.csv                   paese,nome,regione,tipo            solo Banca Mondiale: nome, regione e se è un Paese o un aggregato (World, Euro area...)
  <cartella>/meta.json                   date di pubblicazione dell'FMI e di aggiornamento della Banca Mondiale (nessuna data "di oggi")

Le funzioni di questo modulo sono pure (testate in tests/test_annuali.py) tranne `leggi_snapshot` e `scrivi_snapshot`.
"""

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd

FONTE_IMF = "imf"
FONTE_BM = "wb"
FONTI_ANNUALI = {FONTE_IMF: "IMF World Economic Outlook (WEO)", FONTE_BM: "World Bank (WDI, WGI)"}
CARTELLE = {FONTE_IMF: "dati/weo", FONTE_BM: "dati/bm"}

# Frequenza di aggiornamento della fonte e soglia di freschezza (giorni): lo snapshot FMI conta dalla data di pubblicazione
# del WEO (6 mesi + circa 4 settimane di margine: il WEO successivo esce a metà aprile e a metà ottobre); quello della Banca Mondiale
# dalla data di aggiornamento dichiarata dalla fonte (15 mesi: WDI a luglio, WGI a settembre, ogni anno).
FREQUENZA_FONTE = {FONTE_IMF: "semestrale", FONTE_BM: "annuale"}
SOGLIA_ANNUALI_GIORNI = {"semestrale": 210, "annuale": 456}

DECIMALI_SNAPSHOT = 3
SOGLIA_INTERI = 1_000_000      # da qui in su i valori si scrivono interi (PIL in dollari, popolazione)
COLONNE_DATI = ["paese", "indicatore", "anno", "valore"]
COLONNE_ULTIMO = ["paese", "indicatore", "anno", "anno_fiscale"]
# Codici dell'FMI diversi da quelli ISO usati dalla Banca Mondiale: nello snapshot si usano sempre i secondi
ALIAS_PAESI = {"KOS": "XKX", "WBG": "PSE"}      # Kosovo, Cisgiordania e Gaza
COLONNE_PAESI = ["paese", "nome", "regione", "tipo"]
TIPO_PAESE = "country"
TIPO_AGGREGATO = "aggregate"
CAMPI_INDICATORE = ["id", "nome", "unita", "fonte", "codice", "sezione"]


@dataclass(frozen=True)
class Indicatore:
    """Una voce del catalogo `indicatori:` di config.yaml."""

    id: str                              # id interno (es. gdp_growth)
    nome: str                            # nome sul sito (inglese)
    unita: str
    fonte: str                           # "imf" o "wb"
    codice: str                          # codice presso la fonte (es. NGDP_RPCH, SL.UEM.TOTL.ZS)
    sezione: str                         # sezione della pagina del Paese (step 10b)
    decimali: int = 1
    sorgente_wb: int = 2                 # solo Banca Mondiale: 2 = WDI, 3 = WGI
    ultimo_effettivo_da: str | None = None  # solo FMI: codice di un altro indicatore da cui prendere l'ultimo anno effettivo, se il proprio manca
    nota: str | None = None
    divisore: float = 1.0                # per portare il valore dello snapshot all'unità mostrata (es. dollari -> miliardi: 1e9)


@dataclass
class Snapshot:
    """Un snapshot letto dal repository."""

    fonte: str
    dati: pd.DataFrame                   # colonne paese, indicatore, anno (int), valore (float)
    ultimo_effettivo: dict[tuple[str, str], int]  # (paese, codice) -> ultimo anno con dato reale
    meta: dict = field(default_factory=dict)
    paesi: pd.DataFrame | None = None    # solo Banca Mondiale: colonne paese, nome, regione, tipo
    fiscale: set[tuple[str, str]] = field(default_factory=set)   # coppie (paese, codice) con anni fiscali (l'anno 2024 è il 2024/25)

    def codici_paesi(self) -> set[str]:
        """I codici dei veri Paesi presenti nei dati (esclusi gli aggregati: World, gruppi di reddito, G001...)."""
        presenti = set(self.dati["paese"].unique())
        if self.paesi is not None:
            return presenti & set(self.paesi.loc[self.paesi["tipo"] == TIPO_PAESE, "paese"])
        return {p for p in presenti if re.fullmatch(r"[A-Z]{3}", p)}   # FMI: gli aggregati hanno codici come G001 o GX123

    def serie(self, paese: str, codice: str) -> pd.Series:
        """Valori di un indicatore per un Paese, indicizzati per anno."""
        righe = self.dati[(self.dati["paese"] == paese) & (self.dati["indicatore"] == codice)]
        return pd.Series(righe["valore"].to_numpy(), index=righe["anno"].to_numpy(), name=codice)

    def e_stima(self, paese: str, codice: str, anno: int) -> bool | None:
        """True se l'anno è dopo l'ultimo dato reale (stima o proiezione); None se l'ultimo anno effettivo non è noto."""
        ultimo = self.ultimo_effettivo.get((paese, codice))
        return None if ultimo is None else anno > ultimo


# ---------------------------------------------------------------------
# Catalogo (config.yaml: indicatori)
# ---------------------------------------------------------------------

def carica_catalogo(config: dict) -> list[Indicatore]:
    """Legge `indicatori:` di config.yaml e controlla i campi; solleva ValueError se qualcosa non torna."""
    voci = config.get("indicatori", [])
    catalogo = []
    visti: set[str] = set()
    codici = {(v.get("fonte"), v.get("codice")) for v in voci}
    for voce in voci:
        mancanti = [c for c in CAMPI_INDICATORE if c not in voce]
        if mancanti:
            raise ValueError(f"Indicatore {voce.get('id', '?')}: mancano i campi {mancanti} in config.yaml")
        if voce["fonte"] not in FONTI_ANNUALI:
            raise ValueError(f"Indicatore {voce['id']}: la fonte deve essere una tra {list(FONTI_ANNUALI)}")
        if voce["id"] in visti:
            raise ValueError(f"Indicatore ripetuto in config.yaml: {voce['id']}")
        visti.add(voce["id"])
        da = voce.get("ultimo_effettivo_da")
        if da is not None and (voce["fonte"] != FONTE_IMF or (FONTE_IMF, da) not in codici):
            raise ValueError(f"Indicatore {voce['id']}: 'ultimo_effettivo_da' deve essere un codice FMI del catalogo")
        if voce["fonte"] == FONTE_BM and voce.get("sorgente_wb", 2) not in (2, 3):
            raise ValueError(f"Indicatore {voce['id']}: 'sorgente_wb' deve essere 2 (WDI) o 3 (WGI)")
        catalogo.append(Indicatore(**{c: voce[c] for c in CAMPI_INDICATORE}, decimali=int(voce.get("decimali", 1)),
                                   sorgente_wb=int(voce.get("sorgente_wb", 2)), ultimo_effettivo_da=da, nota=voce.get("nota"),
                                   divisore=float(voce.get("divisore", 1))))
    return catalogo


def indicatori_di(catalogo: list[Indicatore], fonte: str) -> list[Indicatore]:
    return [i for i in catalogo if i.fonte == fonte]


# ---------------------------------------------------------------------
# Formato dei valori e dell'ultimo anno effettivo
# ---------------------------------------------------------------------

def formatta_valore(valore: float) -> str:
    """Valore come testo, sempre uguale per lo stesso numero: 3 decimali senza zeri inutili; da un milione in su solo l'intero
    (a 13 cifre i decimali sono rumore dei numeri in virgola mobile, e cambierebbero a ogni lettura e scrittura del file).
    Si arrotonda "per eccesso a metà" (1282.9475 -> 1282.948) sulla rappresentazione decimale più breve del numero: è l'arrotondamento
    del file del WEO, così lo snapshot dell'API e quello del file coincidono (con round() di Python, che arrotonda al pari, 93 valori su 95.000
    differivano di 0,001). Leggere il testo e riscriverlo dà lo stesso testo: i diff mostrano solo i valori cambiati davvero."""
    numero = Decimal(repr(float(valore)))
    if abs(numero) >= SOGLIA_INTERI:
        return str(int(numero.quantize(Decimal(1), rounding=ROUND_HALF_UP)))
    testo = f"{numero.quantize(Decimal(1).scaleb(-DECIMALI_SNAPSHOT), rounding=ROUND_HALF_UP):f}"
    testo = testo.rstrip("0").rstrip(".") if "." in testo else testo
    return "0" if testo in ("-0", "") else testo


_ANNO_EFFETTIVO = re.compile(r"^(?:FY)?\s*(\d{4})(?:\s*/\s*\d{2,4})?$")


def anno_effettivo(testo) -> int | None:
    """Ultimo anno con dato reale scritto dall'FMI: "2025" -> 2025; "FY2024/25" -> 2024 (l'anno fiscale è indicato dall'anno di inizio, come
    nelle tabelle del WEO: l'India "2024" è l'anno fiscale 2024/25); vuoto o formato sconosciuto -> None."""
    if testo is None or (isinstance(testo, float) and pd.isna(testo)):
        return None
    trovato = _ANNO_EFFETTIVO.match(str(testo).strip())
    return int(trovato.group(1)) if trovato else None


def e_anno_fiscale(testo) -> bool:
    """True se l'FMI scrive l'ultimo anno effettivo come anno fiscale ("FY2024/25")."""
    return isinstance(testo, str) and testo.strip().upper().startswith("FY")


def completa_fiscale(fiscale: set[tuple[str, str]], ultimo_originale: dict[tuple[str, str], int], dati: pd.DataFrame,
                     equivalenze: dict[str, str]) -> set[tuple[str, str]]:
    """Come completa_ultimo_effettivo, per il segno "anno fiscale": un indicatore senza attributo (es. PPPPC) eredita quello di NGDPD."""
    risultato = set(fiscale)
    for codice, riferimento in equivalenze.items():
        for paese in dati.loc[dati["indicatore"] == codice, "paese"].unique():
            if (paese, codice) not in ultimo_originale and (paese, riferimento) in fiscale:
                risultato.add((paese, codice))
    return risultato


def applica_alias(dati: pd.DataFrame) -> pd.DataFrame:
    """Sostituisce i codici dell'FMI diversi dall'ISO (KOS, WBG) con quelli della Banca Mondiale (XKX, PSE)."""
    copia = dati.copy()
    copia["paese"] = copia["paese"].replace(ALIAS_PAESI)
    return copia


def alias_chiavi(chiavi):
    """Lo stesso per un dizionario o un insieme con chiavi (paese, codice)."""
    nuove = {(ALIAS_PAESI.get(p, p), i): v for (p, i), v in chiavi.items()} if isinstance(chiavi, dict) else \
        {(ALIAS_PAESI.get(p, p), i) for p, i in chiavi}
    return nuove


def completa_ultimo_effettivo(ultimo: dict[tuple[str, str], int], dati: pd.DataFrame,
                              equivalenze: dict[str, str]) -> dict[tuple[str, str], int]:
    """Aggiunge l'ultimo anno effettivo mancante usando quello di un indicatore "equivalente" (es. PPPPC <- NGDPD).

    `equivalenze`: {codice che manca: codice da cui copiare}. Si copia solo per i Paesi che hanno dati per l'indicatore che manca
    e solo se l'indicatore di riferimento ha un ultimo anno effettivo per quel Paese.
    """
    risultato = dict(ultimo)
    for codice, riferimento in equivalenze.items():
        for paese in dati.loc[dati["indicatore"] == codice, "paese"].unique():
            if (paese, codice) not in risultato and (paese, riferimento) in ultimo:
                risultato[(paese, codice)] = ultimo[(paese, riferimento)]
    return risultato


def senza_ultimo_effettivo(dati: pd.DataFrame, ultimo: dict[tuple[str, str], int], solo_paesi: bool = True) -> list[tuple[str, str]]:
    """Coppie (paese, indicatore) con dati ma senza ultimo anno effettivo (per default solo codici di 3 lettere = Paesi, non aggregati)."""
    coppie = dati[["paese", "indicatore"]].drop_duplicates()
    mancanti = [(p, i) for p, i in zip(coppie["paese"], coppie["indicatore"]) if (p, i) not in ultimo]
    if solo_paesi:
        mancanti = [(p, i) for p, i in mancanti if re.fullmatch(r"[A-Z]{3}", p)]
    return sorted(mancanti)


# ---------------------------------------------------------------------
# Lettura e scrittura degli snapshot
# ---------------------------------------------------------------------

def _csv_testo(intestazione: list[str], righe) -> str:
    uscita = io.StringIO()
    scrittore = csv.writer(uscita, lineterminator="\n")
    scrittore.writerow(intestazione)
    scrittore.writerows(righe)
    return uscita.getvalue()


def testo_dati_csv(dati: pd.DataFrame) -> str:
    """Il contenuto di dati.csv: ordinato per (paese, indicatore, anno), un valore per riga, nessun doppione."""
    ordinati = dati.drop_duplicates(["paese", "indicatore", "anno"], keep="last").sort_values(["paese", "indicatore", "anno"], kind="stable")
    return _csv_testo(COLONNE_DATI, ((p, i, int(a), formatta_valore(v))
                                     for p, i, a, v in zip(ordinati["paese"], ordinati["indicatore"], ordinati["anno"], ordinati["valore"])))


def testo_ultimo_csv(ultimo: dict[tuple[str, str], int], fiscale: set[tuple[str, str]] | None = None) -> str:
    fiscale = fiscale or set()
    return _csv_testo(COLONNE_ULTIMO, ((p, i, a, 1 if (p, i) in fiscale else "") for (p, i), a in sorted(ultimo.items())))


def testo_meta(meta: dict) -> str:
    return json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def testo_paesi_csv(paesi: pd.DataFrame) -> str:
    ordinati = paesi.drop_duplicates("paese").sort_values("paese", kind="stable")
    return _csv_testo(COLONNE_PAESI, zip(ordinati["paese"], ordinati["nome"], ordinati["regione"], ordinati["tipo"]))


def scrivi_snapshot(cartella: Path, dati: pd.DataFrame, meta: dict, ultimo: dict[tuple[str, str], int] | None = None,
                    paesi: pd.DataFrame | None = None, fiscale: set[tuple[str, str]] | None = None) -> None:
    """Scrive i file dello snapshot (a capo sempre "\\n", anche su Windows)."""
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "dati.csv").write_text(testo_dati_csv(dati), encoding="utf-8", newline="\n")
    if ultimo is not None:
        (cartella / "ultimo_effettivo.csv").write_text(testo_ultimo_csv(ultimo, fiscale), encoding="utf-8", newline="\n")
    if paesi is not None:
        (cartella / "paesi.csv").write_text(testo_paesi_csv(paesi), encoding="utf-8", newline="\n")
    (cartella / "meta.json").write_text(testo_meta(meta), encoding="utf-8", newline="\n")


def leggi_snapshot(radice: Path, fonte: str) -> Snapshot | None:
    """Legge lo snapshot di una fonte dalla sua cartella nel progetto; None se non esiste ancora (la build funziona lo stesso)."""
    return leggi_cartella(radice / CARTELLE[fonte], fonte)


def leggi_cartella(cartella: Path, fonte: str) -> Snapshot | None:
    """Legge uno snapshot da una cartella qualsiasi (per i confronti); None se manca dati.csv."""
    if not (cartella / "dati.csv").exists():
        return None
    dati = pd.read_csv(cartella / "dati.csv", dtype={"paese": str, "indicatore": str, "anno": int, "valore": float})
    ultimo: dict[tuple[str, str], int] = {}
    fiscale: set[tuple[str, str]] = set()
    file_ultimo = cartella / "ultimo_effettivo.csv"
    if file_ultimo.exists():
        tabella = pd.read_csv(file_ultimo, dtype={"paese": str, "indicatore": str, "anno": int})
        ultimo = {(p, i): int(a) for p, i, a in zip(tabella["paese"], tabella["indicatore"], tabella["anno"])}
        if "anno_fiscale" in tabella:
            fiscale = {(p, i) for p, i, f in zip(tabella["paese"], tabella["indicatore"], tabella["anno_fiscale"]) if f == 1}
    meta = json.loads((cartella / "meta.json").read_text(encoding="utf-8")) if (cartella / "meta.json").exists() else {}
    paesi = (pd.read_csv(cartella / "paesi.csv", dtype=str, keep_default_na=False)
             if (cartella / "paesi.csv").exists() else None)
    return Snapshot(fonte=fonte, dati=dati, ultimo_effettivo=ultimo, meta=meta, paesi=paesi, fiscale=fiscale)


# ---------------------------------------------------------------------
# Controllo di freschezza degli snapshot
# ---------------------------------------------------------------------

@dataclass
class StatoSnapshot:
    """Stato di freschezza di una parte dello snapshot (WEO, WDI o WGI)."""

    id: str
    nome: str
    frequenza: str                       # "semestrale" o "annuale"
    data: date | None                    # pubblicazione (WEO) o aggiornamento della fonte (Banca Mondiale)
    giorni: int | None                   # giorni trascorsi da `data`
    soglia: int
    edizione: str | None = None          # es. "April 2026"
    n_paesi: int = 0
    n_indicatori: int = 0

    @property
    def presente(self) -> bool:
        return self.data is not None

    @property
    def in_ritardo(self) -> bool:
        return self.giorni is not None and self.giorni > self.soglia


def stato_freschezza(id_: str, nome: str, frequenza: str, data: date | None, oggi: date, **extra) -> StatoSnapshot:
    """Giorni dalla pubblicazione e confronto con la soglia della frequenza (210 giorni a semestri, 456 per l'annuale)."""
    return StatoSnapshot(id=id_, nome=nome, frequenza=frequenza, data=data,
                         giorni=None if data is None else max((oggi - data).days, 0),
                         soglia=SOGLIA_ANNUALI_GIORNI[frequenza], **extra)


def _data(testo) -> date | None:
    try:
        return date.fromisoformat(str(testo)[:10])
    except (TypeError, ValueError):
        return None


def stati_snapshot(snapshot_imf: Snapshot | None, snapshot_bm: Snapshot | None, oggi: date) -> list[StatoSnapshot]:
    """Stato dei tre snapshot: WEO (data di pubblicazione), WDI e WGI (data di aggiornamento della Banca Mondiale)."""
    stati = []
    for snapshot, parti in ((snapshot_imf, [(FONTE_IMF, "IMF World Economic Outlook", "pubblicato")]),
                            (snapshot_bm, [("wdi", "World Bank WDI", "wdi_aggiornato"), ("wgi", "World Bank WGI", "wgi_aggiornato")])):
        for id_, nome, chiave in parti:
            frequenza = FREQUENZA_FONTE[FONTE_IMF if id_ == FONTE_IMF else FONTE_BM]
            if snapshot is None:
                stati.append(stato_freschezza(id_, nome, frequenza, None, oggi))
                continue
            dati = snapshot.dati[snapshot.dati["paese"].isin(snapshot.codici_paesi())]
            if id_ in ("wdi", "wgi"):
                dati = dati[dati["indicatore"].str.startswith("GOV_WGI_") == (id_ == "wgi")]
            stati.append(stato_freschezza(id_, nome, frequenza, _data(snapshot.meta.get(chiave)), oggi,
                                          edizione=snapshot.meta.get("edizione"), n_paesi=dati["paese"].nunique(),
                                          n_indicatori=dati["indicatore"].nunique()))
    return stati


def edizione_weo(pubblicazione: date) -> str:
    """Nome dell'edizione dalla data di pubblicazione: aprile (uscita tra gennaio e giugno) o ottobre."""
    return f"{'April' if pubblicazione.month <= 6 else 'October'} {pubblicazione.year}"


def meta_weo(pubblicazione: str, codici: list[str], equivalenze: dict[str, str]) -> dict:
    """Il contenuto di meta.json (uguale per script e importatore: si confrontano con lo stesso formato)."""
    return {
        "fonte": "International Monetary Fund, World Economic Outlook (WEO)",
        "edizione": edizione_weo(date.fromisoformat(pubblicazione)),
        "pubblicato": pubblicazione,
        "indicatori": sorted(codici),
        "ultimo_effettivo": "LATEST_ACTUAL_ANNUAL_DATA (FY2024/25 = 2024)"
                            + ("; if missing, copied from " + ", ".join(f"{a} <- {b}" for a, b in sorted(equivalenze.items())) if equivalenze else ""),
    }


def copertura(snapshot: Snapshot, catalogo: list[Indicatore]) -> list[dict]:
    """Per ogni indicatore del catalogo presente nello snapshot: Paesi coperti, anni, ultimo anno effettivo (per la pagina Series status)."""
    righe = []
    for indicatore in indicatori_di(catalogo, snapshot.fonte):
        dati = snapshot.dati[snapshot.dati["indicatore"] == indicatore.codice]
        if dati.empty:
            righe.append({"indicatore": indicatore, "n_paesi": 0, "dal": None, "al": None, "effettivo_da": None, "effettivo_a": None})
            continue
        paesi = set(dati["paese"]) & snapshot.codici_paesi()
        effettivi = [a for (p, i), a in snapshot.ultimo_effettivo.items() if i == indicatore.codice and p in paesi]
        righe.append({"indicatore": indicatore, "n_paesi": len(paesi), "dal": int(dati["anno"].min()), "al": int(dati["anno"].max()),
                      "effettivo_da": min(effettivi) if effettivi else None, "effettivo_a": max(effettivi) if effettivi else None})
    return righe


# ---------------------------------------------------------------------
# Confronto tra due snapshot (importatore contro API; riepilogo delle pull request)
# ---------------------------------------------------------------------

@dataclass
class Differenze:
    """Confronto di due tabelle di dati (paese, indicatore, anno, valore)."""

    uguali: int = 0
    aggiunte: int = 0                    # righe presenti solo nella seconda
    rimosse: int = 0                     # righe presenti solo nella prima
    cambiate: int = 0                    # stessa chiave, valore diverso (oltre la tolleranza)
    per_indicatore: dict[str, int] = field(default_factory=dict)   # indicatore -> righe diverse (aggiunte + rimosse + cambiate)
    esempi: list[tuple] = field(default_factory=list)              # (stato, paese, indicatore, anno, prima, dopo)

    @property
    def identici(self) -> bool:
        return not (self.aggiunte or self.rimosse or self.cambiate)


def differenze(prima: pd.DataFrame, dopo: pd.DataFrame, tolleranza: float = 0.0, max_esempi: int = 10) -> Differenze:
    """Confronta due tabelle di dati. `tolleranza` = differenza massima tra due valori per considerarli uguali."""
    chiavi = ["paese", "indicatore", "anno"]
    unite = prima.merge(dopo, on=chiavi, how="outer", suffixes=("_prima", "_dopo"), indicator=True)
    risultato = Differenze()
    solo_prima = unite["_merge"] == "left_only"
    solo_dopo = unite["_merge"] == "right_only"
    entrambe = unite["_merge"] == "both"
    cambiato = entrambe & ((unite["valore_prima"] - unite["valore_dopo"]).abs() > tolleranza)
    risultato.uguali = int((entrambe & ~cambiato).sum())
    risultato.aggiunte, risultato.rimosse, risultato.cambiate = int(solo_dopo.sum()), int(solo_prima.sum()), int(cambiato.sum())
    diverse = unite[solo_prima | solo_dopo | cambiato].copy()
    risultato.per_indicatore = {i: int(n) for i, n in diverse["indicatore"].value_counts().sort_index().items()}
    for stato, maschera in (("changed", cambiato), ("added", solo_dopo), ("removed", solo_prima)):
        for riga in unite[maschera].head(max_esempi).itertuples():
            if len(risultato.esempi) < max_esempi:
                risultato.esempi.append((stato, riga.paese, riga.indicatore, int(riga.anno),
                                         None if pd.isna(riga.valore_prima) else riga.valore_prima,
                                         None if pd.isna(riga.valore_dopo) else riga.valore_dopo))
    return risultato


def differenze_ultimo(prima: dict[tuple[str, str], int], dopo: dict[tuple[str, str], int],
                      fiscale_prima: set | None = None, fiscale_dopo: set | None = None) -> list[tuple]:
    """Coppie (paese, indicatore) con ultimo anno effettivo (o segno "anno fiscale") diverso: [(paese, indicatore, prima, dopo)], ordinate."""
    fp, fd = fiscale_prima or set(), fiscale_dopo or set()
    return sorted((p, i, prima.get((p, i)), dopo.get((p, i))) for p, i in set(prima) | set(dopo)
                  if prima.get((p, i)) != dopo.get((p, i)) or ((p, i) in fp) != ((p, i) in fd))
