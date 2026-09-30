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

CAMPI_OBBLIGATORI = ["id", "fonte", "nome", "regione", "categoria", "unita", "trasformazione"]
TRASFORMAZIONI = ["livello", "yoy"]

# Dopo quanti giorni senza nuovi dati una serie si considera "in ritardo"
SOGLIA_RITARDO_GIORNI = {"giornaliera": 10, "settimanale": 21, "mensile": 70, "trimestrale": 190}


@dataclass
class Serie:
    """Una serie della configurazione, con i suoi dati o il suo errore."""

    id: str
    fonte: str
    nome: str
    regione: str
    categoria: str
    unita: str
    trasformazione: str
    riepilogo: bool = False
    dati: pd.Series | None = None  # dati già trasformati (es. in variazione annua)
    errore: str | None = None

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

    def in_ritardo(self, oggi: pd.Timestamp) -> bool:
        """True se l'ultimo dato è più vecchio del normale per questa frequenza."""
        if not self.ok or self.frequenza is None:
            return False
        return (oggi - self.ultima_data).days > SOGLIA_RITARDO_GIORNI[self.frequenza]


def trova_serie(serie: dict[str, "Serie"], id_serie: str) -> "Serie":
    """Restituisce la serie richiesta; se non è in config.yaml, un segnaposto con errore.

    Così un grafico che usa una serie tolta dalla configurazione mostra un avviso
    invece di bloccare tutto lo script.
    """
    if id_serie in serie:
        return serie[id_serie]
    return Serie(id=id_serie, fonte="?", nome=id_serie, regione="?", categoria="?", unita="",
                 trasformazione="livello", errore="serie non presente in config.yaml")


# ---------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------

def carica_config(percorso: Path) -> dict:
    """Legge config.yaml e controlla che ogni serie abbia i campi necessari."""
    with open(percorso, encoding="utf-8") as file:
        config = yaml.safe_load(file)

    id_regioni = {regione["id"] for regione in config.get("regioni", [])}
    for voce in config.get("serie", []):
        mancanti = [campo for campo in CAMPI_OBBLIGATORI if campo not in voce]
        if mancanti:
            raise ValueError(f"Serie {voce.get('id', '?')}: mancano i campi {mancanti} in config.yaml")
        if voce["trasformazione"] not in TRASFORMAZIONI:
            raise ValueError(f"Serie {voce['id']}: trasformazione '{voce['trasformazione']}' non valida "
                             f"(usa una tra {TRASFORMAZIONI})")
        if voce["regione"] not in id_regioni:
            raise ValueError(f"Serie {voce['id']}: regione '{voce['regione']}' non definita in 'regioni'")
    return config


# ---------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------

def scarica_tutte(config: dict) -> dict[str, Serie]:
    """Scarica tutte le serie della configurazione. Non si ferma mai per un errore."""
    risultati: dict[str, Serie] = {}
    for voce in config["serie"]:
        serie = Serie(**{campo: voce[campo] for campo in CAMPI_OBBLIGATORI},
                      riepilogo=bool(voce.get("riepilogo", False)))
        funzione_download = FONTI.get(serie.fonte)

        try:
            if funzione_download is None:
                raise ErroreFonte(f"fonte '{serie.fonte}' non supportata")
            grezza = funzione_download(serie.id)
            serie.dati = trasforma(grezza, serie.trasformazione)
            print(f"  OK      {serie.id:<14} {len(serie.dati):>6} dati, ultimo {serie.ultima_data:%d/%m/%Y}")
        except ErroreFonte as errore:
            serie.errore = str(errore)
            print(f"  ERRORE  {serie.id:<14} {serie.errore}")
        except Exception as errore:  # errore imprevisto: lo registriamo e andiamo avanti
            serie.errore = f"errore imprevisto ({type(errore).__name__})"
            print(f"  ERRORE  {serie.id:<14} {serie.errore}: {errore}")

        risultati[serie.id] = serie
    return risultati


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
    "1 sett.": pd.DateOffset(weeks=1),
    "1 mese": pd.DateOffset(months=1),
    "1 anno": pd.DateOffset(years=1),
}


def tipo_variazione(unita: str) -> str:
    """Come esprimere una variazione in base all'unità della serie.

    - tassi in %            -> differenza in punti base (1 pb = 0,01%)
    - variazioni annue      -> differenza in punti percentuali
    - indici, punti, ecc.   -> variazione percentuale
    """
    if unita == "%":
        return "pb"
    if unita == "% a/a":
        return "pp"
    return "%"


def variazioni(serie: Serie) -> dict[str, float | None]:
    """Calcola la variazione a 1 settimana, 1 mese e 1 anno rispetto all'ultimo dato."""
    risultato: dict[str, float | None] = {}
    tipo = tipo_variazione(serie.unita)

    for etichetta, periodo in PERIODI_VARIAZIONE.items():
        if not serie.ok:
            risultato[etichetta] = None
            continue
        # Per i dati mensili la variazione settimanale non ha senso
        if etichetta == "1 sett." and serie.frequenza in ("mensile", "trimestrale"):
            risultato[etichetta] = None
            continue
        data_riferimento = serie.ultima_data - periodo
        if data_riferimento < serie.prima_data:
            risultato[etichetta] = None
            continue

        precedente = float(serie.dati.asof(data_riferimento))
        attuale = serie.ultimo_valore
        if tipo == "pb":
            risultato[etichetta] = (attuale - precedente) * 100
        elif tipo == "pp":
            risultato[etichetta] = attuale - precedente
        else:
            risultato[etichetta] = (attuale / precedente - 1) * 100 if precedente else None
    return risultato
