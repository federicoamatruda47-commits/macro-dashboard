"""Pagina Corea del Sud: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
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
                            note=["korea-bis-delay"]),
                ]),
        Sezione("titoli-di-stato", "Government bonds",
                "Yield on Korean government bonds at 10 years.",
                grafici=[
                    storico("kr-ktb", "10-year government bonds (MONTHLY data)", [KTB_10A],
                            periodo_iniziale="Max", largo=True,
                            note=["korea-ktb-monthly"]),
                ]),
        Sezione("inflazione", "Inflation", "Change in consumer prices compared with a year earlier.",
                grafici=[
                    storico("kr-inflazione", "South Korea CPI (% y/y)", [CPI], riferimento=(2, ""),
                            periodo_iniziale="10Y", largo=True,
                            note=["target-bok"]),
                ]),
        Sezione("cambio", "Exchange rate", grafici=[
            storico("kr-cambio", "USD/KRW (won per 1 dollar)", [CAMBIO], periodo_iniziale="10Y", largo=True,
                    mostra_unita=True,
                    note=["usdkrw"]),
        ]),
        Sezione("borsa", "Equities", grafici=[
            storico("kr-kospi", "KOSPI", [KOSPI], periodo_iniziale="10Y", largo=True,
                            note=["index-daily-closes"]),
        ]),
    ]
