"""Pagina Corea del Sud: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
from .modello import Sezione

CPI = "WS_LONG_CPI/M.KR.771"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("inflazione", "Inflation", "Change in consumer prices compared with a year earlier.",
                grafici=[
                    storico("kr-inflazione", "South Korea CPI (% y/y)", [CPI], riferimento=(2, ""),
                            periodo_iniziale="10Y", largo=True,
                            note=["target-bok"]),
                ]),
    ]
