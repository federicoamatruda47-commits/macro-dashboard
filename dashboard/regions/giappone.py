"""Pagina Giappone: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
from .modello import Sezione

CPI, CPI_CORE, CPI_CORE_CORE = "CPIm/001", "CPIm/733", "CPIm/740"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("inflazione", "Inflation",
                "Change in consumer prices compared with a year earlier. \"Core\" excludes fresh food; "
                "\"core-core\" also excludes energy.",
                grafici=[
                    storico("jp-inflazione", "Headline, core and core-core CPI (% y/y)",
                            [CPI, CPI_CORE, CPI_CORE_CORE], riferimento=(2, ""), periodo_iniziale="10Y",
                            largo=True,
                            note=["japan-cpi-sources", "target-boj"]),
                ]),
    ]
