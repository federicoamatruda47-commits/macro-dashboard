"""Pagina Stati Uniti: quali grafici mostrare e in che ordine.

Questo file non scarica nulla: riceve le serie già pronte (dizionario id -> Serie)
e decide come combinarle nei grafici. I testi mostrati sul sito sono in inglese.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

# Scadenze della curva: (etichetta sull'asse, id della serie)
SCADENZE = [("3M", "DGS3MO"), ("2Y", "DGS2"), ("5Y", "DGS5"), ("10Y", "DGS10"), ("30Y", "DGS30")]

# Azioni (Yahoo Finance): le definizioni delle serie stanno in config.yaml, qui solo gli id
SP500, NASDAQ100, RUSSELL2000, SP500_EW = "^GSPC", "^NDX", "^RUT", "^SPXEW"
AZIONI = [SP500, NASDAQ100, RUSSELL2000, SP500_EW]
RAPPORTO_EW = "SP500_EW_SU_CW"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    """Restituisce le sezioni della pagina USA (config non serve: le recessioni arrivano da USREC)."""
    recessioni = charts.periodi_recessione(serie.get("USREC"))

    def lista(*ids: str) -> list[Serie]:
        return [trova_serie(serie, i) for i in ids]

    def storico(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Scorciatoia per un grafico a linee nel tempo con le bande di recessione."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento", "evidenzia_inversioni")
                          if k in opzioni_grafico}
        figura = charts.linee_storiche(lista(*ids), recessioni=recessioni, **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    def base100(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Confronto a base 100: la ribasatura all'inizio del periodo scelto la fa il JavaScript."""
        figura = charts.linee_base100([(s, False) for s in lista(*ids)])
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    # La curva "oggi vs 1 mese vs 1 anno" ha una forma diversa dagli altri grafici
    figura_curva, _ = charts.curva_rendimenti([(etichetta, trova_serie(serie, i)) for etichetta, i in SCADENZE])
    grafico_curva = Grafico(
        id="usa-curva-oggi", titolo="Treasury curve: today, 1 month ago, 1 year ago",
        figura=figura_curva, serie_ids=[i for _, i in SCADENZE], storico=False,
    )

    return [
        Sezione("politica-monetaria", "Monetary policy", grafici=[
            storico("usa-dff", "Effective Fed funds rate", ["DFF"], periodo_iniziale="Max", largo=True),
        ]),
        Sezione("curva", "Treasury curve",
                "Yields on US government bonds by maturity. A negative 10Y-2Y or 10Y-3M spread "
                "(an inverted curve) has often preceded recessions.",
                grafici=[
                    grafico_curva,
                    storico("usa-rendimenti", "Yields by maturity over time",
                            [i for _, i in SCADENZE], periodo_iniziale="10Y"),
                    storico("usa-spread", "10Y-2Y and 10Y-3M spreads", ["T10Y2Y", "T10Y3M"],
                            evidenzia_inversioni=True, periodo_iniziale="Max", largo=True,
                            nota="Red area: inverted curve (spread below zero). "
                                 "Grey bands: NBER recessions."),
                ]),
        Sezione("tassi-reali", "Real rates and expected inflation",
                "Yield on the inflation-indexed Treasury (TIPS) and the inflation expected by the market "
                "(breakeven = nominal minus real). Data from 2003.",
                grafici=[
                    storico("usa-reali", "10Y real yield and 10Y breakeven", ["DFII10", "T10YIE"],
                            periodo_iniziale="Max", largo=True),
                ]),
        Sezione("inflazione", "Inflation", "Change in prices compared with a year earlier.", grafici=[
            storico("usa-inflazione", "Headline CPI, core CPI and core PCE (% y/y)",
                    ["CPIAUCSL", "CPILFESL", "PCEPILFE"], riferimento=(2, ""),
                    periodo_iniziale="10Y", largo=True,
                    nota="Dashed line: the Fed's 2% target (measured on PCE). "
                         "Grey bands: NBER recessions."),
        ]),
        Sezione("credito", "Credit",
                "Extra yield investors demand on corporate bonds compared with Treasuries.",
                grafici=[
                    storico("usa-baa", "Baa (Moody's) spread vs 10Y Treasury", ["BAA10Y"],
                            periodo_iniziale="Max",
                            nota="A long-history series (from 1986): useful to compare past crises."),
                    storico("usa-oas", "Investment Grade and High Yield OAS (ICE BofA)",
                            ["BAMLC0A0CM", "BAMLH0A0HYM2"], periodo_iniziale="Max",
                            nota="ICE BofA OAS series on FRED only start in October 2023: for licensing reasons "
                                 "FRED publishes only the last few years. For the long history "
                                 "see the Baa vs 10Y Treasury spread."),
                ]),
        Sezione("azioni", "Equities",
                "The main US equity indices: price changes and, below, how much of the S&P 500's rise "
                "depends on a few very large stocks.",
                tabella_performance=AZIONI, etichetta_performance="Index",
                grafici=[
                    base100("usa-indici-azionari", "US equity indices (base 100)", [SP500, NASDAQ100, RUSSELL2000],
                            periodo_iniziale="5Y", largo=True,
                            nota="Rebased to 100 at the start of the period chosen with the 1Y / 5Y / 10Y / Max buttons. "
                                 "Closing prices of the indices without dividends (not \"adjusted\"). "
                                 "S&P 500: 500 large companies; Nasdaq 100: the 100 largest non-financial companies "
                                 "on the Nasdaq (a lot of technology); Russell 2000: small companies."),
                    storico("usa-concentrazione", "Concentration: S&P 500 Equal Weight / S&P 500", [RAPPORTO_EW],
                            periodo_iniziale="Max", largo=True,
                            nota="Ratio (×100) between the S&P 500 with every stock at the same weight and "
                                 "the S&P 500 weighted by market capitalisation. When it falls, the market is concentrating on a few "
                                 "giants: the \"average\" stock does worse than the index. When it rises, the rally broadens. "
                                 "What matters is the direction, not the level (it depends on the indices' start date, "
                                 "Dec 2006). Price indices, without dividends. Grey bands: NBER recessions."),
                ]),
        Sezione("condizioni", "Financial conditions and labour", grafici=[
            storico("usa-vix", "VIX (expected volatility of the S&P 500)", ["VIXCLS"], periodo_iniziale="5Y"),
            storico("usa-dollaro", "Broad dollar (nominal index, Jan 2006 = 100)", ["DTWEXBGS"],
                    periodo_iniziale="Max"),
            storico("usa-disoccupazione", "Unemployment rate", ["UNRATE"], periodo_iniziale="Max",
                    largo=True),
        ]),
    ]
