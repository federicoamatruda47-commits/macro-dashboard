"""Pagina Cina: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi, sezione_non_inclusi
from .modello import Sezione

LPR_1A = "WS_CBPOL/D.CN"
CPI = "WS_LONG_CPI/M.CN.771"
CAMBIO = "CNY=X"
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
                            nota="Source: BIS, daily data. From 20 Aug 2019 it is the 1-year LPR; before that the BIS "
                                 "uses the official 1-year lending rate."),
                ]),
        Sezione("inflazione", "Inflation", "Change in consumer prices compared with a year earlier.",
                grafici=[
                    storico("cn-inflazione", "China CPI (% y/y)", [CPI], riferimento=(0, ""),
                            periodo_iniziale="10Y", largo=True,
                            nota="Source: BIS, monthly data. Dashed line: zero (below = deflation)."),
                ]),
        Sezione("cambio", "Exchange rate", grafici=[
            storico("cn-cambio", "USD/CNY (yuan per 1 dollar)", [CAMBIO], periodo_iniziale="10Y", largo=True,
                    mostra_unita=True,
                    nota="Onshore rate. Up = the yuan weakens. If Yahoo does not respond FRED is used."),
        ]),
        Sezione("borsa", "Equities",
                "Chinese equities are represented by the CSI 300 (Shanghai and Shenzhen); Hong Kong has a "
                "separate market, measured by the Hang Seng.",
                grafici=[
                    storico("cn-csi300", "CSI 300 (ETF 510300)", [CSI300], periodo_iniziale="10Y",
                            mostra_unita=True,
                            nota="Note: this is not the index but an ETF that tracks it (ticker 510300 on the "
                                 "Shanghai exchange, price in yuan), because Yahoo does not provide the history of the "
                                 "CSI 300 index. The price follows the index but is not equal to its level; "
                                 "data start in 2012."),
                    storico("cn-hangseng", "Hang Seng (Hong Kong)", [HANG_SENG], periodo_iniziale="10Y",
                            nota="Index in points, daily closes. Source: Yahoo Finance (unofficial)."),
                ]),
        sezione_non_inclusi("Not included for lack of free, up-to-date sources: 10-year yield, 5-year LPR, PPI."),
    ]
