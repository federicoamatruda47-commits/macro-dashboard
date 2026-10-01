"""Pagina Confronto globale: gli stessi dati dei Paesi sullo stesso grafico."""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione


# Inflazione: tutta dal BIS
INFLAZIONE = [("US", "WS_LONG_CPI/M.US.771"), ("Euro area", "WS_LONG_CPI/M.XM.771"),
              ("Japan", "WS_LONG_CPI/M.JP.771"), ("China", "WS_LONG_CPI/M.CN.771"),
              ("South Korea", "WS_LONG_CPI/M.KR.771")]


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    def rinominate(elenco) -> list[Serie]:
        return [charts.con_nome(trova_serie(serie, i), nome) for nome, i in elenco]

    def storico(id_grafico, titolo, elenco, **opzioni_grafico) -> Grafico:
        riferimento = opzioni_grafico.pop("riferimento", None)
        figura = charts.linee_storiche(rinominate(elenco), riferimento=riferimento)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura,
                       serie_ids=[i for _, i in elenco], **opzioni_grafico)

    return [
        Sezione("inflazione", "Inflation",
                "Annual change in consumer prices, same source (BIS) for every country.",
                grafici=[
                    storico("gl-inflazione", "CPI inflation compared (% y/y)", INFLAZIONE,
                            riferimento=(2, ""), periodo_iniziale="10Y", largo=True,
                            note=["target-generic"]),
                ]),
    ]
