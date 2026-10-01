"""Pagina Stati Uniti: quali grafici mostrare e in che ordine.

Questo file non scarica nulla: riceve le serie già pronte (dizionario id -> Serie)
e decide come combinarle nei grafici. I testi mostrati sul sito sono in inglese.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    """Restituisce le sezioni della pagina USA (config non serve: le recessioni arrivano da USREC)."""
    recessioni = charts.periodi_recessione(serie.get("USREC"))

    def lista(*ids: str) -> list[Serie]:
        return [trova_serie(serie, i) for i in ids]

    def storico(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Scorciatoia per un grafico a linee nel tempo con le bande di recessione."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento", "evidenzia_inversioni")
                          if k in opzioni_grafico}
        figura = charts.linee_storiche(lista(*ids), recessioni=recessioni, **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    return [
        Sezione("tassi-reali", "Real rates and expected inflation",
                "Yield on the inflation-indexed Treasury (TIPS) and the inflation expected by the market "
                "(breakeven = nominal minus real). Data from 2003.",
                grafici=[
                    storico("usa-reali", "10Y real yield and 10Y breakeven", ["DFII10", "T10YIE"],
                            periodo_iniziale="Max", largo=True, note=["usa-tips-breakeven"]),
                ]),
        Sezione("inflazione", "Inflation", "Change in prices compared with a year earlier.", grafici=[
            storico("usa-inflazione", "Headline CPI, core CPI and core PCE (% y/y)",
                    ["CPIAUCSL", "CPILFESL", "PCEPILFE"], riferimento=(2, ""),
                    periodo_iniziale="10Y", largo=True,
                    note=["target-fed", "bands-nber"]),
        ]),
        Sezione("lavoro", "Labour", grafici=[
            storico("usa-disoccupazione", "Unemployment rate", ["UNRATE"], periodo_iniziale="Max",
                    largo=True),
        ]),
    ]
