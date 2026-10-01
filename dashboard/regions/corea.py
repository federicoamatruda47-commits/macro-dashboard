"""Pagina Corea del Sud: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi, sezione_non_inclusi
from .modello import Sezione

POLICY = "WS_CBPOL/D.KR"
KTB_10A = "IRLTLT01KRM156N"
CPI = "WS_LONG_CPI/M.KR.771"
CAMBIO = "KRW=X"
KOSPI = "^KS11"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("politica-monetaria", "Monetary policy",
                "The Bank of Korea (BoK) base rate is the reference rate for the money market.",
                grafici=[
                    storico("kr-policy", "BoK base rate", [POLICY], periodo_iniziale="Max", largo=True,
                            nota="Source: BIS, daily data. The BIS publishes Korea with about a month "
                                 "of delay: for this series the stale-data warning triggers "
                                 "after 45 days instead of 10."),
                ]),
        Sezione("titoli-di-stato", "Government bonds",
                "Yield on Korean government bonds at 10 years.",
                grafici=[
                    storico("kr-ktb", "10-year government bonds (MONTHLY data)", [KTB_10A],
                            periodo_iniziale="Max", largo=True,
                            nota="Monthly data (monthly average, source OECD via FRED), with about a month "
                                 "of delay: daily data is not freely available."),
                ]),
        Sezione("inflazione", "Inflation", "Change in consumer prices compared with a year earlier.",
                grafici=[
                    storico("kr-inflazione", "South Korea CPI (% y/y)", [CPI], riferimento=(2, ""),
                            periodo_iniziale="10Y", largo=True,
                            nota="Source: BIS, monthly data. Dashed line: the BoK's 2% target."),
                ]),
        Sezione("cambio", "Exchange rate", grafici=[
            storico("kr-cambio", "USD/KRW (won per 1 dollar)", [CAMBIO], periodo_iniziale="10Y", largo=True,
                    mostra_unita=True,
                    nota="Up = the won weakens. If Yahoo does not respond FRED is used."),
        ]),
        Sezione("borsa", "Equities", grafici=[
            storico("kr-kospi", "KOSPI", [KOSPI], periodo_iniziale="10Y", largo=True,
                    nota="Index in points, daily closes. Source: Yahoo Finance (unofficial)."),
        ]),
        sezione_non_inclusi("Not included: 3-year yield (the daily data is only available through the Bank of "
                            "Korea API, which requires a Korean registration)."),
    ]
