"""Pagina Cina: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
from .modello import Sezione

CPI = "WS_LONG_CPI/M.CN.771"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("inflazione", "Inflation", "Change in consumer prices compared with a year earlier.",
                grafici=[
                    storico("cn-inflazione", "China CPI (% y/y)", [CPI], riferimento=(0, ""),
                            periodo_iniziale="10Y", largo=True,
                            note=["zero-line-china"]),
                ]),
    ]
