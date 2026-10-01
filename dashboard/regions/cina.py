"""Pagina Cina: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
from .modello import Sezione

LPR_1A = "WS_CBPOL/D.CN"
CPI = "WS_LONG_CPI/M.CN.771"
CSI300 = "510300.SS"
HANG_SENG = "^HSI"


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
        Sezione("borsa", "Equities",
                "Chinese equities are represented by the CSI 300 (Shanghai and Shenzhen); Hong Kong has a "
                "separate market, measured by the Hang Seng.",
                grafici=[
                    storico("cn-csi300", "CSI 300 (ETF 510300)", [CSI300], periodo_iniziale="10Y",
                            mostra_unita=True,
                            note=["csi300-etf"]),
                    storico("cn-hangseng", "Hang Seng (Hong Kong)", [HANG_SENG], periodo_iniziale="10Y",
                            note=["index-daily-closes"]),
                ]),
    ]
