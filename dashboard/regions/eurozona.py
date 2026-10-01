"""Pagina Eurozona: quali grafici mostrare e in che ordine.

Come usa.py, questo file non scarica nulla: riceve le serie già pronte
(dizionario id -> Serie) e decide come combinarle nei grafici.
I codici BCE sono lunghi: qui sotto li chiamiamo con nomi brevi.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

HICP = "HICP/M.U2.N.000000.4D0.ANR"
HICP_CORE = "HICP/M.U2.N.XEF000.4D0.ANR"



def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    """Restituisce le sezioni della pagina Eurozona."""
    # Le recessioni CEPR non hanno un'API: le date sono scritte in config.yaml
    recessioni = charts.periodi_da_trimestri(config.get("recessioni", {}).get("eurozona", {}).get("periodi"))

    def lista(*ids: str) -> list[Serie]:
        return [trova_serie(serie, i) for i in ids]

    def storico(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Scorciatoia per un grafico a linee nel tempo con le bande di recessione CEPR."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento", "evidenzia_inversioni")
                          if k in opzioni_grafico}
        figura = charts.linee_storiche(lista(*ids), recessioni=recessioni,
                                       etichetta_recessioni="CEPR recession", **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    return [
        Sezione("inflazione", "Inflation", "Change in consumer prices (HICP) compared with a year earlier.",
                grafici=[
                    storico("eur-inflazione", "HICP headline and core (% y/y)", [HICP, HICP_CORE],
                            riferimento=(2, ""), periodo_iniziale="10Y", largo=True,
                            note=["hicp-core", "target-ecb", "bands-cepr"]),
                ]),
    ]
