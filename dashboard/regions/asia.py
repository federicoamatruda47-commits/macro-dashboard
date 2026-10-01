"""Strumenti comuni alle pagine di Giappone, Cina e Corea del Sud.

Le tre pagine non hanno bande di recessione: per questi Paesi non esiste una fonte ufficiale
e automatica (nessun equivalente di NBER o CEPR), quindi non se ne disegnano.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico


def attrezzi(serie: dict[str, Serie]):
    """Restituisce (lista, storico): due scorciatoie per costruire i grafici di una pagina."""

    def lista(*ids: str) -> list[Serie]:
        return [trova_serie(serie, i) for i in ids]

    def storico(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Grafico a linee nel tempo, senza bande di recessione."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento", "mostra_unita")
                          if k in opzioni_grafico}
        figura = charts.linee_storiche(lista(*ids), **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    return lista, storico

