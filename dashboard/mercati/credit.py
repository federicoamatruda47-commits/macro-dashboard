"""Pagina Credit: spread delle obbligazioni societarie e spread sovrani (il "prezzo del rischio" nei mercati obbligazionari).

Come le altre pagine di mercato: riceve le serie già pronte (dizionario id -> Serie) e decide come combinarle
nei grafici. Le note tecniche stanno in contenuti/note.yaml: qui si indicano solo gli id.
Bande di recessione solo sui grafici di una sola economia (NBER per gli USA, CEPR per l'area euro): il confronto
USA-area euro non ne ha.
"""

from .. import charts
from ..data import Serie, trova_serie
from ..regions.modello import Grafico, Sezione

HY_USA, HY_EURO = "BAMLH0A0HYM2", "BAMLHE00EHYIOAS"
IG_USA, BAA = "BAMLC0A0CM", "BAA10Y"
BTP_BUND, OAT_BUND = "SPREAD_BTP_BUND", "SPREAD_OAT_BUND"
TUTTI_MENO_AAA = "EA_TUTTI_MENO_AAA_10A"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    nber = charts.periodi_recessione(serie.get("USREC"))
    cepr = charts.periodi_da_trimestri(config.get("recessioni", {}).get("eurozona", {}).get("periodi"))

    def storico(id_grafico, titolo, ids, recessioni, etichetta, **opzioni_grafico) -> Grafico:
        """Grafico a linee nel tempo di una sola economia, con le sue bande di recessione."""
        figura = charts.linee_storiche([trova_serie(serie, i) for i in ids], recessioni=recessioni,
                                       etichetta_recessioni=etichetta)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    # Confronto USA - area euro: stessa fonte (ICE BofA via FRED), nessuna banda di recessione
    confronto_hy = Grafico(
        id="mk-credit-hy", titolo="High-yield spread: US vs euro area",
        figura=charts.linee_storiche([charts.con_nome(trova_serie(serie, HY_USA), "US high yield"),
                                      charts.con_nome(trova_serie(serie, HY_EURO), "Euro-area high yield")]),
        serie_ids=[HY_USA, HY_EURO], periodo_iniziale="Max", largo=True,
        note=["ice-oas-history", "ea-ig-not-available"],
        come_leggerlo="A credit spread is the extra yield investors ask to hold riskier company bonds instead of government bonds: "
                      "the higher it is, the more risk investors see. Spreads have historically widened in recessions and market stress; "
                      "this chart only covers the years since October 2023.")

    return [
        Sezione("high-yield", "High yield: US vs euro area",
                "The extra yield (the spread) investors demand on lower-rated corporate bonds over government bonds, "
                "in the US and in the euro area, from the same provider (ICE BofA).",
                grafici=[confronto_hy]),
        Sezione("usa-dettaglio", "US credit in detail",
                "Investment-grade and high-yield spreads, and a series that goes back to 1986 for comparing past crises.",
                grafici=[
                    storico("usa-oas", "Investment Grade and High Yield OAS (ICE BofA)", [IG_USA, HY_USA], nber,
                            "NBER recession", periodo_iniziale="Max", note=["ice-oas-history", "bands-nber"],
                            come_leggerlo="Investment-grade bonds are issued by financially stronger companies than high-yield ones, so their spread is smaller. "
                                          "The two have historically tended to widen together when markets are under stress, with high yield moving more; "
                                          "these series only start in October 2023."),
                    storico("usa-baa", "Baa (Moody's) spread vs 10Y Treasury", [BAA], nber, "NBER recession",
                            periodo_iniziale="Max", note=["baa-history", "bands-nber"],
                            come_leggerlo="The extra yield on medium-quality (Baa-rated) US corporate bonds over 10-year Treasuries, available since 1986. "
                                          "It has historically widened sharply around recessions and financial crises, such as in 2008 and 2020."),
                ]),
        Sezione("spread-sovrani", "Sovereign spreads",
                "How much extra yield investors demand to lend to a country compared with Germany: "
                "it measures perceived risk (public debt, politics, the stability of the euro area).",
                grafici=[
                    storico("eur-spread-paesi", "BTP-Bund and OAT-Bund 10-year spreads (MONTHLY data)",
                            [BTP_BUND, OAT_BUND], cepr, "CEPR recession", periodo_iniziale="Max", largo=True,
                            note=["monthly-sovereign-yields", "bands-cepr"],
                            come_leggerlo="The extra yield Italy and France pay over Germany on 10-year bonds, a common gauge of how risky investors consider each country's debt. "
                                          "It rose sharply during the euro-area debt crisis of 2011-2012 and has widened again at times of stress, "
                                          "as for Italy in 2018 and France in 2024. Monthly averages smooth out short spikes; "
                                          "the daily chart below shows them better."),
                    storico("eur-spread-tutti", "All euro-area government bonds minus AAA, 10 years (daily)",
                            [TUTTI_MENO_AAA], cepr, "CEPR recession", periodo_iniziale="Max", largo=True,
                            note=["ea-all-minus-aaa", "bands-cepr"],
                            come_leggerlo="The average extra yield that all euro-area governments pay over the AAA group (mainly Germany), shown daily. "
                                          "It has tended to rise when investors worry about the weaker euro-area countries."),
                ]),
    ]
