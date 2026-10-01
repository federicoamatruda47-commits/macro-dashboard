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
# Valute: (nome, id, invertita). Il cambio EUR/USD è quotato "dollari per euro", gli altri "valuta per dollaro":
# questi ultimi si invertono, così per ogni linea "sale" = la valuta si rafforza sul dollaro
VALUTE = [("Euro", "EXR/D.USD.EUR.SP00.A", False), ("Yen", "JPY=X", True),
          ("Yuan", "CNY=X", True), ("Won", "KRW=X", True)]
# Borse: (nome, indice in valuta locale, stesso indice convertito in USD). L'S&P 500 è già in dollari.
# Gli indici sono definiti una volta sola in config.yaml; le versioni in USD sono serie calcolate
# (indice / cambio "valuta per dollaro") e vengono dalla stessa fonte, Yahoo.
BORSE = [("S&P 500", "^GSPC", None), ("Euro Stoxx 50", "^STOXX50E", "^STOXX50E_USD"),
         ("FTSE MIB", "FTSEMIB.MI", "FTSEMIB.MI_USD"), ("Nikkei 225", "^N225", "^N225_USD"),
         ("CSI 300 (ETF)", "510300.SS", "510300.SS_USD"), ("KOSPI", "^KS11", "^KS11_USD"),
         ("Hang Seng", "^HSI", "^HSI_USD")]
BENCHMARK = ("MSCI ACWI (ETF)", "ACWI")  # indice mondiale, già in dollari: stessa linea in entrambe le versioni


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    def rinominate(elenco) -> list[Serie]:
        return [charts.con_nome(trova_serie(serie, i), nome) for nome, i in elenco]

    def storico(id_grafico, titolo, elenco, **opzioni_grafico) -> Grafico:
        riferimento = opzioni_grafico.pop("riferimento", None)
        figura = charts.linee_storiche(rinominate(elenco), riferimento=riferimento)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura,
                       serie_ids=[i for _, i in elenco], **opzioni_grafico)

    def base100(id_grafico, titolo, elenco, **opzioni_grafico) -> Grafico:
        """Confronto a base 100: la ribasatura all'inizio del periodo scelto la fa il JavaScript."""
        voci = [(charts.con_nome(trova_serie(serie, i), nome), invertita) for nome, i, invertita in elenco]
        return Grafico(id=id_grafico, titolo=titolo, figura=charts.linee_base100(voci),
                       serie_ids=[i for _, i, _ in elenco], **opzioni_grafico)

    def borse() -> Grafico:
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
            nota="With \"Local currency\" performance ignores exchange rates (the S&P 500 and MSCI ACWI are already in "
                 "dollars); with \"In USD\" each index is divided by the Yahoo Finance exchange rate of the same day, "
                 "so it includes the currency effect. Dashed: MSCI ACWI, the world benchmark index "
                 "(represented by the iShares ACWI ETF, in dollars). All prices are closes without dividends "
                 "(not \"adjusted\"), for consistency between indices and ETFs: the ACWI ETF pays out dividends, which show up "
                 "in the price as small drops. The CSI 300 is represented by an ETF (ticker 510300), not "
                 "by the index, and starts in 2012: with \"Max\" every line starts on the same date. Hang Seng: "
                 "the Hong Kong dollar is pegged to the US dollar, so the conversion matters little. "
                 "Markets and exchange rates do not close at the same time: small one-day differences.")

    return [
        Sezione("tassi-policy", "Policy rates",
                "The rates central banks use to steer the cost of money in the five economies.",
                grafici=[
                    storico("gl-policy", "Policy rates compared", POLICY, periodo_iniziale="Max", largo=True,
                            nota="All series come from the BIS. Fed: midpoint of the target range; "
                                 "ECB: deposit facility rate; BoJ: target overnight rate; BoK: base rate. "
                                 "WARNING: for China it is the 1-year Loan Prime Rate, a bank lending "
                                 "rate, not an overnight rate like the others: it tends to sit higher and is not "
                                 "directly comparable. Korea is about a month behind."),
                ]),
        Sezione("rendimenti", "10-year yields",
                "The cost at which governments borrow for 10 years.",
                grafici=[
                    storico("gl-rendimenti", "10-year government bond yields", DECENNALI,
                            periodo_iniziale="10Y", largo=True,
                            nota="US: Treasuries (FRED, daily); euro area: the ECB AAA curve as a Bund "
                                 "proxy (daily); Japan: JGBs from the Ministry of Finance (daily); "
                                 "South Korea: OECD MONTHLY average. China is not included: there is no free, "
                                 "up-to-date source."),
                ]),
        Sezione("inflazione", "Inflation",
                "Annual change in consumer prices, same source (BIS) for every country.",
                grafici=[
                    storico("gl-inflazione", "CPI inflation compared (% y/y)", INFLAZIONE,
                            riferimento=(2, ""), periodo_iniziale="10Y", largo=True,
                            nota="Monthly data. Dashed line: 2%, the target of many central banks."),
                ]),
        Sezione("valute", "Currencies against the dollar",
                "How much each currency is worth in dollars, rebased to 100 at the start of the period chosen "
                "with the 1Y / 5Y / 10Y / Max buttons.",
                grafici=[
                    base100("gl-valute", "Currencies against the dollar (base 100)", VALUTE,
                            periodo_iniziale="5Y", largo=True,
                            nota="Above 100 = the currency has strengthened against the dollar since the start of the "
                                 "period; below 100 = it has weakened. The yen, yuan and won are quoted as "
                                 "\"currency per dollar\" and are flipped here, so every line reads "
                                 "the same way. Euro: ECB rate at 14:15; the other "
                                 "currencies: Yahoo Finance close. With \"Max\" the chart starts on the first date when "
                                 "all the currencies exist."),
                ]),
        Sezione("borse", "Equities",
                "Equity indices, in local currency or converted to dollars, rebased to 100 at the start "
                "of the chosen period.",
                grafici=[borse()]),
    ]
