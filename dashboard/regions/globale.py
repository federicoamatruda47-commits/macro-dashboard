"""Pagina Confronto globale: gli stessi dati dei Paesi sullo stesso grafico."""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

# Tassi di policy: tutti dal BIS, così hanno la stessa definizione e la stessa fonte
POLICY = [("US (Fed)", "WS_CBPOL/D.US"), ("Euro area (ECB)", "WS_CBPOL/D.XM"), ("Japan (BoJ)", "WS_CBPOL/D.JP"),
          ("China (1Y LPR)", "WS_CBPOL/D.CN"), ("South Korea (BoK)", "WS_CBPOL/D.KR")]
# Rendimenti 10 anni (serie già scaricate per le pagine dei singoli Paesi)
DECENNALI = [("US", "DGS10"), ("Euro area (AAA)", "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"),
             ("Japan", "JGB_10Y"), ("South Korea (monthly)", "IRLTLT01KRM156N")]
# Inflazione: tutta dal BIS
INFLAZIONE = [("US", "WS_LONG_CPI/M.US.771"), ("Euro area", "WS_LONG_CPI/M.XM.771"),
              ("Japan", "WS_LONG_CPI/M.JP.771"), ("China", "WS_LONG_CPI/M.CN.771"),
              ("South Korea", "WS_LONG_CPI/M.KR.771")]


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    def rinominate(elenco) -> list[Serie]:
        return [charts.con_nome(trova_serie(serie, i), nome) for nome, i in elenco]

    def storico(id_grafico, titolo, elenco, **opzioni_grafico) -> Grafico:
        riferimento = opzioni_grafico.pop("riferimento", None)
        figura = charts.linee_storiche(rinominate(elenco), riferimento=riferimento)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura,
                       serie_ids=[i for _, i in elenco], **opzioni_grafico)

    return [
        Sezione("tassi-policy", "Policy rates",
                "The rates central banks use to steer the cost of money in the five economies.",
                grafici=[
                    storico("gl-policy", "Policy rates compared", POLICY, periodo_iniziale="Max", largo=True,
                            note=["policy-rates-compared"]),
                ]),
        Sezione("rendimenti", "10-year yields",
                "The cost at which governments borrow for 10 years.",
                grafici=[
                    storico("gl-rendimenti", "10-year government bond yields", DECENNALI,
                            periodo_iniziale="10Y", largo=True,
                            note=["yields-compared"]),
                ]),
        Sezione("inflazione", "Inflation",
                "Annual change in consumer prices, same source (BIS) for every country.",
                grafici=[
                    storico("gl-inflazione", "CPI inflation compared (% y/y)", INFLAZIONE,
                            riferimento=(2, ""), periodo_iniziale="10Y", largo=True,
                            note=["target-generic"]),
                ]),
    ]
