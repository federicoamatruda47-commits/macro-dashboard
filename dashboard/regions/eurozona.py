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
HY_EURO = "BAMLHE00EHYIOAS"
EURUSD = "EXR/D.USD.EUR.SP00.A"

# Azioni (Yahoo Finance): le definizioni stanno in config.yaml, qui solo gli id
EURO_STOXX_50, DAX, CAC_40, FTSE_MIB, BANCHE = "^STOXX50E", "^GDAXIP", "^FCHI", "FTSEMIB.MI", "EXV1.DE"
AZIONI = [EURO_STOXX_50, DAX, CAC_40, FTSE_MIB, BANCHE]

NOTA_RECESSIONI = "Grey bands: euro-area recessions dated by the CEPR."


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

    def base100(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Confronto a base 100: la ribasatura all'inizio del periodo scelto la fa il JavaScript."""
        figura = charts.linee_base100([(s, False) for s in lista(*ids)])
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
                            largo=True, nota=NOTA_RECESSIONI),
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
                            nota="Red area: inverted curve (spread below zero). " + NOTA_RECESSIONI),
                ]),
        Sezione("spread-sovrani", "Sovereign spreads",
                "How much extra yield investors demand to lend to a country "
                "compared with Germany: it measures perceived risk (debt, politics, "
                "the survival of the euro).",
                grafici=[
                    storico("eur-spread-paesi", "BTP-Bund and OAT-Bund 10-year spreads (MONTHLY data)",
                            ["SPREAD_BTP_BUND", "SPREAD_OAT_BUND"], periodo_iniziale="Max", largo=True,
                            nota="Monthly data: the monthly average of the 10-year yields the ECB uses "
                                 "for its convergence criteria, published with about a month's delay. "
                                 "Daily yields of individual countries are not freely "
                                 "available. " + NOTA_RECESSIONI),
                    storico("eur-spread-tutti", "All euro-area government bonds minus AAA, 10 years (daily)",
                            ["EA_TUTTI_MENO_AAA_10A"], periodo_iniziale="Max", largo=True,
                            nota="10-year yield of the ECB curve for all euro-area government bonds "
                                 "minus that of the AAA curve: a daily indicator "
                                 "of the average risk premium of non-AAA countries (Italy, France, "
                                 "Spain...). Data from 2004. " + NOTA_RECESSIONI),
                ]),
        Sezione("inflazione", "Inflation", "Change in consumer prices (HICP) compared with a year earlier.",
                grafici=[
                    storico("eur-inflazione", "HICP headline and core (% y/y)", [HICP, HICP_CORE],
                            riferimento=(2, ""), periodo_iniziale="10Y", largo=True,
                            nota="Core = excluding energy, food, alcohol and tobacco. "
                                 "Dashed line: the ECB's 2% target. " + NOTA_RECESSIONI),
                ]),
        Sezione("credito", "Credit",
                "Extra yield investors demand on euro corporate bonds compared with government bonds.",
                grafici=[
                    storico("eur-hy", "High Yield OAS in euro (ICE BofA)", [HY_EURO], periodo_iniziale="Max",
                            largo=True,
                            nota="On FRED the series starts in October 2023 (an ICE licensing limit). "
                                 "The euro Investment Grade spread is not included: there is no "
                                 "free source."),
                ]),
        Sezione("azioni", "Equities",
                "The main euro-area equity indices and European banks, in euro.",
                tabella_performance=AZIONI, etichetta_performance="Index",
                grafici=[
                    base100("eur-indici-azionari", "European equity indices and banks (base 100)", AZIONI,
                            periodo_iniziale="5Y", largo=True,
                            nota="Rebased to 100 at the start of the period chosen with the 1Y / 5Y / 10Y / Max buttons; "
                                 "with \"Max\" the chart starts in 2013, when every line exists (the DAX price index on Yahoo starts in March 2013). "
                                 "Closing prices without dividends (not \"adjusted\"), in euro. DAX: the DAX K is used "
                                 "(Kursindex, a price index); the \"official\" DAX index reinvests dividends and would not "
                                 "be comparable with the others. \"European banks\" is the iShares STOXX Europe 600 "
                                 "Banks ETF (Xetra, ticker EXV1): it also includes banks outside the euro area (e.g. the UK, "
                                 "Switzerland) and is NOT the Euro Stoxx Banks, which is not available on Yahoo. The ETF pays out "
                                 "dividends: in the price they show up as small drops."),
                ]),
        Sezione("cambio", "Exchange rate", grafici=[
            storico("eur-eurusd", "EUR/USD (dollars per 1 euro)", [EURUSD], periodo_iniziale="10Y", largo=True,
                    nota="ECB reference rate, taken every working day at 14:15 (Frankfurt time). "
                         "Up = the euro strengthens. " + NOTA_RECESSIONI),
        ]),
    ]
