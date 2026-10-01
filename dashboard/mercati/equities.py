"""Pagina Equities (azioni): indici azionari a confronto e volatilità.

Come le altre pagine di mercato: riceve le serie già pronte (dizionario id -> Serie) e decide come combinarle nei
grafici. Le definizioni degli indici stanno una volta sola in config.yaml; le note tecniche in contenuti/note.yaml.
Sempre prezzi di chiusura senza dividendi (non "adjusted"). Niente bande di recessione sui confronti tra Paesi.
"""

from .. import charts
from ..data import Serie, trova_serie
from ..regions.modello import Grafico, Sezione

# Indici americani
SP500, NASDAQ100, RUSSELL2000, SP500_EW = "^GSPC", "^NDX", "^RUT", "^SPXEW"
RAPPORTO_EW = "SP500_EW_SU_CW"
# Indici dell'area euro e banche europee (ETF)
EURO_STOXX_50, DAX, CAC_40, FTSE_MIB, BANCHE = "^STOXX50E", "^GDAXIP", "^FCHI", "FTSEMIB.MI", "EXV1.DE"
# Asia (il CSI 300 è rappresentato da un ETF) e indice mondiale (anch'esso un ETF)
NIKKEI, CSI300, KOSPI, HANG_SENG = "^N225", "510300.SS", "^KS11", "^HSI"
ACWI = "ACWI"
VIX = "VIXCLS"

# Tabella di performance, a gruppi: (titolo del gruppo, id delle serie)
GRUPPI_TABELLA = [
    ("United States", [SP500, NASDAQ100, RUSSELL2000, SP500_EW]),
    ("Euro area", [EURO_STOXX_50, DAX, CAC_40, FTSE_MIB, BANCHE]),
    ("Asia", [NIKKEI, CSI300, KOSPI, HANG_SENG]),
    ("World", [ACWI]),
]

# Confronto globale: (nome, indice in valuta locale, stesso indice convertito in USD). L'S&P 500 è già in dollari.
# Le versioni in USD sono serie calcolate (indice / cambio "valuta per dollaro") e vengono dalla stessa fonte, Yahoo.
BORSE = [("S&P 500", SP500, None), ("Euro Stoxx 50", EURO_STOXX_50, "^STOXX50E_USD"),
         ("FTSE MIB", FTSE_MIB, "FTSEMIB.MI_USD"), ("Nikkei 225", NIKKEI, "^N225_USD"),
         ("CSI 300 (ETF)", CSI300, "510300.SS_USD"), ("KOSPI", KOSPI, "^KS11_USD"),
         ("Hang Seng", HANG_SENG, "^HSI_USD")]
BENCHMARK = ("MSCI ACWI (ETF)", ACWI)  # indice mondiale, già in dollari: stessa linea in entrambe le versioni


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    recessioni = charts.periodi_recessione(serie.get("USREC"))

    def lista(*ids: str) -> list[Serie]:
        return [trova_serie(serie, i) for i in ids]

    def base100(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Confronto a base 100: la ribasatura all'inizio del periodo scelto la fa il JavaScript."""
        figura = charts.linee_base100([(s, False) for s in lista(*ids)])
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    def confronto_borse() -> Grafico:
        """Borse a base 100 con interruttore valuta locale / USD: le linee delle due versioni stanno nella
        stessa figura e il JavaScript mostra solo quelle della versione scelta."""
        voci = []
        for linea, (nome, locale, usd) in enumerate(BORSE, start=1):
            voci.append((charts.con_nome(trova_serie(serie, locale), nome), False,
                         {"linea": linea, **({"variante": "locale"} if usd else {})}))
            if usd:
                voci.append((charts.con_nome(trova_serie(serie, usd), nome), False,
                             {"linea": linea, "variante": "usd"}))
        nome_bm, id_bm = BENCHMARK
        voci.append((charts.con_nome(trova_serie(serie, id_bm), nome_bm), False, {"linea": 99, "benchmark": True}))
        # Nell'avviso "non disponibile" compaiono le versioni in USD solo se mancano (es. cambio non scaricato)
        ids = [i for _, i, _ in BORSE] + [id_bm]
        ids += [u for _, _, u in BORSE if u and not trova_serie(serie, u).ok]
        return Grafico(
            id="gl-borse", titolo="Equity indices compared (base 100)", figura=charts.linee_base100(voci),
            serie_ids=ids, periodo_iniziale="5Y", largo=True,
            varianti=[("locale", "Local currency"), ("usd", "In USD")],
            note=["rebase-base100", "price-no-dividends", "usd-conversion", "acwi-etf", "csi300-etf",
                  "hang-seng-hkd", "index-daily-closes"],
            come_leggerlo="Each line starts at 100 when the chosen period begins, so markets with very different index levels can be compared. "
                          "\"Local currency\" ignores exchange rates, while \"In USD\" converts each index into dollars and so includes currency moves. "
                          "Prices exclude dividends, so markets with high dividend yields look weaker than their total return.")

    return [
        Sezione("performance", "Performance",
                "The latest level of each index (column \"Last\") and its change over 1 week, 1 month, year to date and 1 year. "
                "Indices are in points of their own currency; for the two ETFs (China, European banks) and MSCI ACWI the "
                "level is the fund's price. Green = up, red = down.",
                gruppi_performance=GRUPPI_TABELLA, etichetta_performance="Index"),
        Sezione("confronto", "Equity indices compared",
                "Stock markets from five economies on the same chart, in local currency or converted to US dollars.",
                grafici=[confronto_borse()]),
        Sezione("dettaglio", "Regional detail",
                "A closer look at the US and euro-area markets, and at how broad the US rally is.",
                grafici=[
                    base100("usa-indici-azionari", "US equity indices (base 100)", [SP500, NASDAQ100, RUSSELL2000],
                            periodo_iniziale="5Y", largo=True,
                            note=["rebase-base100", "price-no-dividends", "us-index-definitions"],
                            come_leggerlo="Three views of the US stock market: the S&P 500 (large companies), the Nasdaq 100 (many technology companies) "
                                          "and the Russell 2000 (small companies). The gaps between the lines show which parts of the market have done better or worse over the period."),
                    base100("eur-indici-azionari", "European equity indices and banks (base 100)",
                            [EURO_STOXX_50, DAX, CAC_40, FTSE_MIB, BANCHE], periodo_iniziale="5Y", largo=True,
                            note=["rebase-base100", "price-no-dividends", "dax-price-index", "ea-banks-etf"],
                            come_leggerlo="The main euro-area stock indices and a fund of European banks, all in euro. Banks have historically tended to be more sensitive "
                                          "to the economic cycle and to changes in interest rates than the broad indices."),
                    Grafico(id="usa-concentrazione", titolo="Concentration: S&P 500 Equal Weight / S&P 500",
                            figura=charts.linee_storiche(lista(RAPPORTO_EW), recessioni=recessioni),
                            serie_ids=[RAPPORTO_EW], periodo_iniziale="Max", largo=True,
                            note=["equal-weight-ratio", "bands-nber"],
                            come_leggerlo="When the line falls, a few very large companies are driving the S&P 500 more than the average stock; "
                                          "when it rises, the gains are spreading to more companies. It describes how broad a rally is, not where prices will go next."),
                ]),
        Sezione("volatilita", "Volatility",
                "How nervous the US stock market is, as measured by option prices.",
                grafici=[
                    Grafico(id="usa-vix", titolo="VIX (expected volatility of the S&P 500)",
                            figura=charts.linee_storiche(lista(VIX), recessioni=recessioni),
                            serie_ids=[VIX], periodo_iniziale="5Y", note=["vix-definition", "bands-nber"],
                            come_leggerlo="The VIX measures how much stock-market volatility investors expect over the next month, based on S&P 500 option prices. "
                                          "It has historically jumped when markets fall sharply, such as in 2008 and in March 2020, and stayed low in calm periods."),
                ]),
    ]
