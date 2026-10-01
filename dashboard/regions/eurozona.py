"""Pagina Eurozona: quali grafici mostrare e in che ordine.

Come usa.py, questo file non scarica nulla: riceve le serie già pronte
(dizionario id -> Serie) e decide come combinarle nei grafici.
I codici BCE sono lunghi: qui sotto li chiamiamo con nomi brevi.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

DFR = "FM/D.U2.EUR.4F.KR.DFR.LEV"

# Curva AAA dell'area euro (BCE): usata come approssimazione dei Bund tedeschi
AAA = "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_"
SCADENZE = [("3M", AAA + "3M"), ("1Y", AAA + "1Y"), ("2Y", AAA + "2Y"),
            ("5Y", AAA + "5Y"), ("10Y", AAA + "10Y"), ("30Y", AAA + "30Y")]
AAA_2A, AAA_10A = AAA + "2Y", AAA + "10Y"
TUTTI_10A = "YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_10Y"

HICP = "HICP/M.U2.N.000000.4D0.ANR"
HICP_CORE = "HICP/M.U2.N.XEF000.4D0.ANR"



def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    """Restituisce le sezioni della pagina Eurozona."""
    # Le recessioni CEPR non hanno un'API: le date sono scritte in config.yaml
    recessioni = charts.periodi_da_trimestri(config.get("recessioni", {}).get("eurozona", {}).get("periodi"))

    def lista(*ids: str) -> list[Serie]:
        return [trova_serie(serie, i) for i in ids]

    def storico(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Scorciatoia per un grafico a linee nel tempo con le bande di recessione CEPR."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento", "evidenzia_inversioni")
                          if k in opzioni_grafico}
        figura = charts.linee_storiche(lista(*ids), recessioni=recessioni,
                                       etichetta_recessioni="CEPR recession", **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    figura_curva, _ = charts.curva_rendimenti([(etichetta, trova_serie(serie, i)) for etichetta, i in SCADENZE])
    grafico_curva = Grafico(
        id="eur-curva-oggi", titolo="Euro-area AAA curve (Bund proxy): today, 1 month ago, 1 year ago",
        figura=figura_curva, serie_ids=[i for _, i in SCADENZE], storico=False,
    )

    return [
        Sezione("politica-monetaria", "Monetary policy",
                "The deposit facility rate (DFR) is the rate the ECB pays banks on the liquidity "
                "they deposit: today it is the main tool the ECB uses to steer market rates.",
                grafici=[
                    storico("eur-dfr", "ECB deposit facility rate (DFR)", [DFR], periodo_iniziale="Max",
                            largo=True, note=["bands-cepr"]),
                ]),
        Sezione("curva", "AAA curve of the euro area (Bund proxy)",
                "Yields estimated by the ECB on euro-area government bonds rated AAA "
                "(Germany, the Netherlands and a few others). Daily data from 2004. Daily yields "
                "on German Bunds alone are not freely available: "
                "this curve is a good approximation.",
                grafici=[
                    grafico_curva,
                    storico("eur-rendimenti", "AAA curve of the euro area (Bund proxy): 2 and 10 years",
                            [AAA_2A, AAA_10A], periodo_iniziale="10Y"),
                    storico("eur-pendenza", "Slope of the AAA curve: 10Y - 2Y", ["EA_AAA_10A_2A"],
                            evidenzia_inversioni=True, periodo_iniziale="Max", largo=True,
                            note=["curve-inversion", "bands-cepr"]),
                ]),
        Sezione("inflazione", "Inflation", "Change in consumer prices (HICP) compared with a year earlier.",
                grafici=[
                    storico("eur-inflazione", "HICP headline and core (% y/y)", [HICP, HICP_CORE],
                            riferimento=(2, ""), periodo_iniziale="10Y", largo=True,
                            note=["hicp-core", "target-ecb", "bands-cepr"]),
                ]),
    ]
