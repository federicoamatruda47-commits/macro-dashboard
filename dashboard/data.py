"""Lettura della configurazione, download delle serie e calcoli di base.

Idea chiave: ogni serie diventa un oggetto `Serie` che contiene i dati
(se il download è riuscito) OPPURE il messaggio d'errore. Così un errore
su una serie non blocca le altre e il sito si genera comunque.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from .sources import FONTI, ErroreFonte

CAMPI_OBBLIGATORI = ["id", "fonte", "nome", "regione", "paese", "categoria", "unita", "trasformazione"]
TRASFORMAZIONI = ["livello", "yoy"]
FONTE_CALCOLATA = "calcolata"  # serie ottenuta da altre serie (componenti: [A, B] -> A − B oppure A / B)
OPERAZIONI = {"differenza": "−", "rapporto": "/"}  # operazioni possibili per le serie calcolate
# Come mostrare il nome della fonte sul sito
NOMI_FONTI = {"fred": "FRED", "ecb": "ECB", "yahoo": "Yahoo Finance", "bis": "BIS",
              "mof": "Japan Ministry of Finance",
              "statjp": "Statistics Bureau of Japan (via DBnomics)", FONTE_CALCOLATA: "Calculated"}

# Controllo di freschezza: dopo quanti giorni senza nuovi dati una serie è "in ritardo".
# Per mensili e trimestrali i giorni si contano dalla FINE del periodo
# (il dato di agosto "vale" fino al 31 agosto, anche se è datato 1° agosto).
SOGLIA_RITARDO_GIORNI = {"giornaliera": 10, "settimanale": 21, "mensile": 75, "trimestrale": 120}
DURATA_PERIODO = {"mensile": pd.DateOffset(months=1), "trimestrale": pd.DateOffset(months=3)}


@dataclass
class Serie:
    """Una serie della configurazione, con i suoi dati o il suo errore."""

    id: str
    fonte: str
    nome: str
    regione: str
    paese: str                           # a chi appartiene (us, ea, it, de, fr, jp, cn, kr, uk) o "global"
    categoria: str
    unita: str
    trasformazione: str
    riepilogo: bool = False
    decimali: int = 2                    # cifre decimali mostrate sul sito (es. 4 per EUR/USD)
    riserva: dict | None = None          # fonte alternativa se la principale non risponde
    componenti: list[str] | None = None  # solo per fonte "calcolata": [A, B]
    operazione: str = "differenza"       # solo per fonte "calcolata": A − B ("differenza") o A / B ("rapporto")
    fattore: float = 1.0                 # solo per fonte "calcolata": il risultato viene moltiplicato per questo
    soglia_giorni: int | None = None     # soglia di freschezza propria di questa serie (al posto di quella standard)
    colore: str | None = None            # chiave del blocco "colori" di config.yaml se diversa dal paese
    dati: pd.Series | None = None  # dati già trasformati (es. in variazione annua)
    errore: str | None = None
    fonte_usata: str | None = None       # es. "fred (riserva)" se si è dovuto usare la riserva
    nota_fonte: str | None = None        # perché si è usata la riserva

    @property
    def chiave_colore(self) -> str:
        """Chiave del colore fisso della serie nel blocco "colori" di config.yaml."""
        return self.colore or self.paese

    @property
    def ok(self) -> bool:
        return self.dati is not None and not self.dati.empty

    @property
    def ultima_data(self) -> pd.Timestamp | None:
        return self.dati.index[-1] if self.ok else None

    @property
    def prima_data(self) -> pd.Timestamp | None:
        return self.dati.index[0] if self.ok else None

    @property
    def ultimo_valore(self) -> float | None:
        return float(self.dati.iloc[-1]) if self.ok else None

    @property
    def frequenza(self) -> str | None:
        """Stima la frequenza guardando la distanza tipica tra due date."""
        if not self.ok or len(self.dati) < 3:
            return None
        giorni = self.dati.index.to_series().diff().dt.days.median()
        if giorni <= 4:
            return "giornaliera"
        if giorni <= 10:
            return "settimanale"
        if giorni <= 40:
            return "mensile"
        return "trimestrale"

    @property
    def soglia_ritardo(self) -> int | None:
        if self.soglia_giorni is not None:
            return self.soglia_giorni
        return SOGLIA_RITARDO_GIORNI.get(self.frequenza) if self.frequenza else None

    def giorni_senza_dati(self, oggi: pd.Timestamp) -> int | None:
        """Giorni trascorsi dalla fine del periodo dell'ultimo dato."""
        if not self.ok:
            return None
        fine_periodo = self.ultima_data
        if self.frequenza in DURATA_PERIODO:
            fine_periodo = fine_periodo + DURATA_PERIODO[self.frequenza] - pd.Timedelta(days=1)
        return max((oggi - fine_periodo).days, 0)

    def in_ritardo(self, oggi: pd.Timestamp) -> bool:
        """True se l'ultimo dato è più vecchio del normale per questa frequenza.

        Serve a scoprire le serie "congelate": la fonte risponde senza errori
        ma non aggiunge più dati (es. un dataset dismesso e sostituito da un altro).
        """
        if not self.ok or self.soglia_ritardo is None:
            return False
        return self.giorni_senza_dati(oggi) > self.soglia_ritardo


def trova_serie(serie: dict[str, "Serie"], id_serie: str) -> "Serie":
    """Restituisce la serie richiesta; se non è in config.yaml, un segnaposto con errore.

    Così un grafico che usa una serie tolta dalla configurazione mostra un avviso
    invece di bloccare tutto lo script.
    """
    if id_serie in serie:
        return serie[id_serie]
    return Serie(id=id_serie, fonte="?", nome=id_serie, regione="?", paese="global", categoria="?", unita="",
                 trasformazione="livello", errore="series not found in config.yaml")


# ---------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------

def carica_config(percorso: Path) -> dict:
    """Legge config.yaml e controlla che ogni serie abbia i campi necessari."""
    with open(percorso, encoding="utf-8") as file:
        config = yaml.safe_load(file)

    id_regioni = {regione["id"] for regione in config.get("regioni", [])}
    colori = config.get("colori", {})
    for chiave, colore in colori.items():
        if "alias" in colore:
            if colore["alias"] not in colori or "alias" in colori[colore["alias"]]:
                raise ValueError(f"Colore '{chiave}': l'alias '{colore['alias']}' deve essere un colore definito (non un alias)")
        elif not ("chiaro" in colore and "scuro" in colore):
            raise ValueError(f"Colore '{chiave}': servono 'chiaro' e 'scuro' (oppure 'alias')")
    id_serie = [voce.get("id") for voce in config.get("serie", [])]
    doppi = sorted({i for i in id_serie if id_serie.count(i) > 1})
    if doppi:
        raise ValueError(f"Serie ripetute in config.yaml: {doppi}")

    for voce in config.get("serie", []):
        mancanti = [campo for campo in CAMPI_OBBLIGATORI if campo not in voce]
        if mancanti:
            raise ValueError(f"Serie {voce.get('id', '?')}: mancano i campi {mancanti} in config.yaml")
        if voce["fonte"] == FONTE_CALCOLATA:
            componenti = voce.get("componenti")
            if not (isinstance(componenti, list) and len(componenti) == 2):
                raise ValueError(f"Serie {voce['id']}: una serie calcolata richiede 'componenti: [A, B]'")
            sconosciute = [c for c in componenti if c not in id_serie]
            if sconosciute:
                raise ValueError(f"Serie {voce['id']}: componenti non presenti in config.yaml: {sconosciute}")
            if voce.get("operazione", "differenza") not in OPERAZIONI:
                raise ValueError(f"Serie {voce['id']}: 'operazione' deve essere una tra {list(OPERAZIONI)}")
            if not isinstance(voce.get("fattore", 1), (int, float)):
                raise ValueError(f"Serie {voce['id']}: 'fattore' deve essere un numero")
        soglia = voce.get("soglia_giorni")
        if soglia is not None and not (isinstance(soglia, int) and soglia > 0):
            raise ValueError(f"Serie {voce['id']}: 'soglia_giorni' deve essere un numero intero positivo")
        riserva = voce.get("riserva")
        if riserva is not None:
            if not (isinstance(riserva, dict) and "fonte" in riserva and "id" in riserva):
                raise ValueError(f"Serie {voce['id']}: 'riserva' deve avere almeno 'fonte' e 'id'")
            if riserva.get("trasformazione", voce["trasformazione"]) not in TRASFORMAZIONI:
                raise ValueError(f"Serie {voce['id']}: trasformazione della riserva non valida")
        if voce["trasformazione"] not in TRASFORMAZIONI:
            raise ValueError(f"Serie {voce['id']}: trasformazione '{voce['trasformazione']}' non valida "
                             f"(usa una tra {TRASFORMAZIONI})")
        if voce.get("colore", voce["paese"]) not in colori:
            raise ValueError(f"Serie {voce['id']}: il colore '{voce.get('colore', voce['paese'])}' non è definito in 'colori' "
                             "(per un Paese senza colore proprio usa 'colore: <chiave>')")
        if voce["regione"] not in id_regioni:
            raise ValueError(f"Serie {voce['id']}: regione '{voce['regione']}' non definita in 'regioni'")
    return config


# ---------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------

def _nuova_serie(voce: dict) -> Serie:
    return Serie(**{campo: voce[campo] for campo in CAMPI_OBBLIGATORI},
                 riepilogo=bool(voce.get("riepilogo", False)),
                 decimali=int(voce.get("decimali", 2)),
                 riserva=voce.get("riserva"),
                 componenti=voce.get("componenti"),
                 operazione=voce.get("operazione", "differenza"),
                 fattore=float(voce.get("fattore", 1)),
                 soglia_giorni=voce.get("soglia_giorni"),
                 colore=voce.get("colore"))


def _scarica_da(fonte: str, id_fonte: str, trasformazione: str) -> pd.Series:
    funzione_download = FONTI.get(fonte)
    if funzione_download is None:
        raise ErroreFonte(f"source '{fonte}' not supported")
    return trasforma(funzione_download(id_fonte), trasformazione)


def _descrivi_errore(errore: Exception) -> str:
    if isinstance(errore, ErroreFonte):
        return str(errore)
    return f"unexpected error ({type(errore).__name__})"


def _scarica_una(serie: Serie) -> None:
    """Scarica una serie dalla fonte principale; se fallisce, prova la riserva (se c'è)."""
    try:
        serie.dati = _scarica_da(serie.fonte, serie.id, serie.trasformazione)
        serie.fonte_usata = serie.fonte
        return
    except Exception as errore:  # anche un errore imprevisto non deve fermare le altre serie
        serie.errore = _descrivi_errore(errore)

    if not serie.riserva:
        return
    riserva = serie.riserva
    try:
        serie.dati = _scarica_da(riserva["fonte"], riserva["id"],
                                 riserva.get("trasformazione", serie.trasformazione))
    except Exception as errore:
        serie.errore += f"; the fallback source does not respond either ({_descrivi_errore(errore)})"
        return
    principale = NOMI_FONTI.get(serie.fonte, serie.fonte.upper())
    alternativa = NOMI_FONTI.get(riserva["fonte"], riserva["fonte"].upper())
    serie.nota_fonte = (f"{principale} unavailable ({serie.errore}): "
                        f"using the fallback {alternativa} {riserva['id']}")
    # La riserva può essere un dato diverso (es. prezzo spot invece del future) o in un'altra unità
    if riserva.get("unita") and riserva["unita"] != serie.unita:
        serie.nota_fonte += f", in {riserva['unita']} instead of {serie.unita}"
        serie.unita = riserva["unita"]
    if riserva.get("nota"):
        serie.nota_fonte += f" ({riserva['nota']})"
    serie.fonte_usata = f"{riserva['fonte']} (fallback)"
    serie.errore = None


def _calcola(serie: Serie, risultati: dict[str, Serie]) -> None:
    """Serie calcolata: A − B oppure A / B, solo nelle date in comune.

    Regola: si calcola SOLO se tutte le componenti vengono dalla stessa fonte principale.
    Se anche una sola è passata alla riserva, il risultato mescolerebbe dati diversi
    (es. Brent spot FRED − WTI future Yahoo, o unità diverse): la serie diventa
    "non disponibile" con un messaggio che spiega il motivo.
    """
    componenti = [risultati[c] for c in serie.componenti]
    mancanti = [c.id for c in componenti if not c.ok]
    if mancanti:
        serie.errore = "missing input data: " + ", ".join(mancanti)
        return
    da_riserva = [c for c in componenti if c.nota_fonte]
    if da_riserva:
        elenco = ", ".join(f"{c.nome} ({c.id})" for c in da_riserva)
        serie.errore = (f"not calculated: {elenco} {'comes' if len(da_riserva) == 1 else 'come'} "
                        "from the fallback source, and different sources are never mixed "
                        "(e.g. spot and futures prices, or different units)")
        return
    fonti = {c.fonte_usata for c in componenti}
    if len(fonti) > 1:
        serie.errore = "not calculated: the inputs come from different sources (" + ", ".join(sorted(fonti)) + ")"
        return

    a, b = componenti
    tabella = pd.concat([a.dati, b.dati], axis=1, join="inner").dropna()
    if tabella.empty:
        serie.errore = "the two input series have no dates in common"
        return
    if serie.operazione == "rapporto":
        tabella = tabella[tabella.iloc[:, 1] != 0]  # niente divisioni per zero
        risultato = tabella.iloc[:, 0] / tabella.iloc[:, 1]
    else:
        risultato = tabella.iloc[:, 0] - tabella.iloc[:, 1]
    serie.dati = trasforma((risultato * serie.fattore).rename(serie.id), serie.trasformazione)
    serie.fonte_usata = FONTE_CALCOLATA


def scarica_tutte(config: dict) -> dict[str, Serie]:
    """Scarica tutte le serie della configurazione. Non si ferma mai per un errore.

    Prima le serie da scaricare, poi quelle calcolate (che usano le prime).
    """
    risultati: dict[str, Serie] = {}
    voci = config["serie"]
    da_scaricare = [v for v in voci if v["fonte"] != FONTE_CALCOLATA]
    calcolate = [v for v in voci if v["fonte"] == FONTE_CALCOLATA]

    for voce in da_scaricare + calcolate:
        serie = _nuova_serie(voce)
        if serie.fonte == FONTE_CALCOLATA:
            _calcola(serie, risultati)
        else:
            _scarica_una(serie)

        if serie.ok:
            riserva = "  [FALLBACK]" if serie.nota_fonte else ""
            print(f"  OK      {serie.id:<36} {len(serie.dati):>6} dati, "
                  f"ultimo {serie.ultima_data:%d/%m/%Y}{riserva}")
        else:
            print(f"  ERRORE  {serie.id:<36} {serie.errore}")
        risultati[serie.id] = serie

    # Stesso ordine di config.yaml (conta per schede riassuntive e tabelle)
    return {voce["id"]: risultati[voce["id"]] for voce in voci}


# ---------------------------------------------------------------------
# Trasformazioni e variazioni
# ---------------------------------------------------------------------

def trasforma(serie: pd.Series, trasformazione: str) -> pd.Series:
    """Applica la trasformazione richiesta in config.yaml."""
    if trasformazione == "livello":
        return serie
    if trasformazione == "yoy":
        return variazione_annua(serie)
    raise ValueError(f"trasformazione sconosciuta: {trasformazione}")


def variazione_annua(serie: pd.Series) -> pd.Series:
    """Variazione % rispetto al dato di un anno prima (funziona con ogni frequenza).

    Esempio: CPI di agosto 2026 confrontato con CPI di agosto 2025.
    """
    date_anno_prima = serie.index - pd.DateOffset(years=1)
    # asof = "l'ultimo valore disponibile a quella data" (NaN se prima dell'inizio)
    valori_anno_prima = serie.asof(date_anno_prima).to_numpy()
    risultato = (serie.to_numpy() / valori_anno_prima - 1) * 100
    return pd.Series(risultato, index=serie.index, name=serie.name).dropna()


# Periodi usati nella scheda riassuntiva
PERIODI_VARIAZIONE = {
    "1W": pd.DateOffset(weeks=1),
    "1M": pd.DateOffset(months=1),
    "1Y": pd.DateOffset(years=1),
}
# Periodi della tabella di performance (commodities): in più "da inizio anno"
DA_INIZIO_ANNO = "YTD"
PERIODI_PERFORMANCE = {
    "1W": pd.DateOffset(weeks=1),
    "1M": pd.DateOffset(months=1),
    DA_INIZIO_ANNO: DA_INIZIO_ANNO,  # confronto con l'ultimo dato dell'anno precedente
    "1Y": pd.DateOffset(years=1),
}


def tipo_variazione(unita: str) -> str:
    """Come esprimere una variazione in base all'unità della serie.

    - tassi in %            -> differenza in punti base (1 bp = 0,01%)
    - variazioni annue      -> differenza in punti percentuali
    - indici, punti, ecc.   -> variazione percentuale
    """
    if unita == "%":
        return "bp"
    if unita == "% y/y":
        return "pp"
    return "%"


def variazioni(serie: Serie, periodi: dict | None = None) -> dict[str, float | None]:
    """Calcola la variazione rispetto all'ultimo dato (predefinito: 1 settimana, 1 mese, 1 anno).

    `periodi` può essere PERIODI_PERFORMANCE per avere anche la variazione da inizio anno.
    """
    risultato: dict[str, float | None] = {}
    tipo = tipo_variazione(serie.unita)

    for etichetta, periodo in (periodi or PERIODI_VARIAZIONE).items():
        if not serie.ok:
            risultato[etichetta] = None
            continue
        # Per i dati mensili la variazione settimanale non ha senso
        if etichetta == "1W" and serie.frequenza in ("mensile", "trimestrale"):
            risultato[etichetta] = None
            continue
        if periodo == DA_INIZIO_ANNO:
            # Es. ultimo dato 30/09/2026 -> confronto con l'ultimo dato fino al 31/12/2025
            data_riferimento = pd.Timestamp(year=serie.ultima_data.year - 1, month=12, day=31)
        else:
            data_riferimento = serie.ultima_data - periodo
        if data_riferimento < serie.prima_data:
            risultato[etichetta] = None
            continue

        precedente = float(serie.dati.asof(data_riferimento))
        attuale = serie.ultimo_valore
        if tipo == "bp":
            risultato[etichetta] = (attuale - precedente) * 100
        elif tipo == "pp":
            risultato[etichetta] = attuale - precedente
        else:
            risultato[etichetta] = (attuale / precedente - 1) * 100 if precedente else None
    return risultato
