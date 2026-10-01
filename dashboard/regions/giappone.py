"""Pagina Giappone: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
from .modello import Sezione

POLICY = "WS_CBPOL/D.JP"
JGB_2A, JGB_10A, JGB_30A = "JGB_2Y", "JGB_10Y", "JGB_30Y"
CPI, CPI_CORE, CPI_CORE_CORE = "CPIm/001", "CPIm/733", "CPIm/740"
NIKKEI = "^N225"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("politica-monetaria", "Monetary policy",
                "The Bank of Japan's target for the overnight market (uncollateralised call rate). "
                "For decades it stayed close to zero, and for some years it was negative.",
                grafici=[
                    storico("jp-policy", "BoJ policy rate", [POLICY], periodo_iniziale="Max", largo=True),
                ]),
        Sezione("titoli-di-stato", "Government bonds (JGB)",
                "Daily yields on Japanese government bonds at 2, 10 and 30 years, "
                "published by the Ministry of Finance.",
                grafici=[
                    storico("jp-jgb", "JGB yields at 2, 10 and 30 years", [JGB_2A, JGB_10A, JGB_30A],
                            periodo_iniziale="10Y", largo=True,
                            note=["jgb-history"]),
                ]),
        Sezione("inflazione", "Inflation",
                "Change in consumer prices compared with a year earlier. \"Core\" excludes fresh food; "
                "\"core-core\" also excludes energy.",
                grafici=[
                    storico("jp-inflazione", "Headline, core and core-core CPI (% y/y)",
                            [CPI, CPI_CORE, CPI_CORE_CORE], riferimento=(2, ""), periodo_iniziale="10Y",
                            largo=True,
                            note=["japan-cpi-sources", "target-boj"]),
                ]),
        Sezione("borsa", "Equities", grafici=[
            storico("jp-nikkei", "Nikkei 225", [NIKKEI], periodo_iniziale="10Y", largo=True,
                            note=["index-daily-closes"]),
        ]),
    ]
