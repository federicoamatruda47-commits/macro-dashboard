"""Mattoni con cui ogni regione descrive la propria pagina."""

from dataclasses import dataclass, field

import plotly.graph_objects as go


@dataclass
class Grafico:
    """Un riquadro della pagina: titolo, figura Plotly e informazioni di contorno."""

    id: str                       # identificativo unico nella pagina (es. "usa-spread")
    titolo: str
    figura: go.Figure | None      # None = nessuna serie disponibile -> riquadro di avviso
    serie_ids: list[str]          # serie usate: servono per date e avvisi sotto il grafico
    nota: str | None = None       # nota tecnica sotto il grafico (dallo step 3 si sposta nella pagina Method)
    come_leggerlo: str | None = None  # una riga in parole semplici su come si legge il grafico (obbligatoria: la build avvisa se manca)
    storico: bool = True          # True = asse temporale con pulsanti 1A / 5A / 10A / Max
    periodo_iniziale: str = "10Y" # periodo mostrato all'apertura: "1Y", "5Y", "10Y" o "Max"
    largo: bool = False           # True = occupa tutta la larghezza su schermi grandi
    alto: bool = False            # True = riquadro più alto (grafici a due pannelli)
    # Interruttore tra due versioni dello stesso grafico (es. borse in valuta locale / in USD):
    # coppie (id della variante, etichetta del pulsante). La prima è quella mostrata all'apertura.
    # Le linee della figura con meta "variante" uguale a un id si vedono solo con quella variante scelta.
    varianti: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Sezione:
    """Gruppo di grafici con un titolo (es. "Curva dei Treasury")."""

    id: str
    titolo: str
    descrizione: str = ""
    grafici: list[Grafico] = field(default_factory=list)
    # Id delle serie da mostrare in una tabella di performance (variazioni 1S, 1M,
    # da inizio anno, 1Y colorate verde/rosso) sopra i grafici della sezione
    tabella_performance: list[str] = field(default_factory=list)
    etichetta_performance: str = "Commodity"  # intestazione della prima colonna di quella tabella
