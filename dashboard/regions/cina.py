"""Pagina Cina: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
from .modello import Sezione

LPR_1A = "WS_CBPOL/D.CN"
CPI = "WS_LONG_CPI/M.CN.771"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("politica-monetaria", "Monetary policy",
                "China has no single policy rate like the Fed or the ECB: the reference for credit is "
                "the Loan Prime Rate (LPR), published every month by the People's Bank of China "
                "based on quotes from banks.",
                grafici=[
                    storico("cn-lpr", "1-year Loan Prime Rate", [LPR_1A], periodo_iniziale="Max", largo=True,
                            note=["china-lpr"]),
                ]),
        Sezione("inflazione", "Inflation", "Change in consumer prices compared with a year earlier.",
                grafici=[
                    storico("cn-inflazione", "China CPI (% y/y)", [CPI], riferimento=(0, ""),
                            periodo_iniziale="10Y", largo=True,
                            note=["zero-line-china"]),
                ]),
    ]
