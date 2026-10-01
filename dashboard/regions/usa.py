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
        Sezione("lavoro", "Labour", grafici=[
            storico("usa-disoccupazione", "Unemployment rate", ["UNRATE"], periodo_iniziale="Max",
                    largo=True),
        ]),
    ]
