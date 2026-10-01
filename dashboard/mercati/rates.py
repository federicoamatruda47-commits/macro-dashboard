"""Pagina Rates & curves: tassi di policy, curve dei rendimenti, rendimenti a 10 anni, pendenza e inversioni,
inflazione e tassi reali (l'inflazione sta qui perché è ciò contro cui si misurano i tassi).

Come le altre pagine di mercato: riceve le serie già pronte (dizionario id -> Serie) e decide come combinarle
nei grafici. Le note tecniche stanno in contenuti/note.yaml: qui si indicano solo gli id.
Bande di recessione solo sui grafici di una sola economia (NBER per gli USA, CEPR per l'area euro); i confronti
tra Paesi non ne hanno. Le economie hanno la loro vista nella sezione Economies (step 5, docs/ristrutturazione.md).
"""

from .. import charts
from ..data import Serie, trova_serie
from ..regions.modello import Grafico, Sezione

# Tassi di policy confrontati: tutti dal BIS, così hanno la stessa definizione e la stessa fonte
POLICY = [("US (Fed)", "WS_CBPOL/D.US"), ("Euro area (ECB)", "WS_CBPOL/D.XM"), ("Japan (BoJ)", "WS_CBPOL/D.JP"),
          ("China (1Y LPR)", "WS_CBPOL/D.CN"), ("South Korea (BoK)", "WS_CBPOL/D.KR")]
# Fonti primarie dei due tassi principali
FED_FUNDS, DFR = "DFF", "FM/D.U2.EUR.4F.KR.DFR.LEV"

# Curva USA: (etichetta sull'asse, id)
SCADENZE_USA = [("3M", "DGS3MO"), ("2Y", "DGS2"), ("5Y", "DGS5"), ("10Y", "DGS10"), ("30Y", "DGS30")]
# Curva AAA dell'area euro (BCE): usata come approssimazione dei Bund tedeschi
AAA = "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_"
SCADENZE_EA = [("3M", AAA + "3M"), ("1Y", AAA + "1Y"), ("2Y", AAA + "2Y"),
               ("5Y", AAA + "5Y"), ("10Y", AAA + "10Y"), ("30Y", AAA + "30Y")]
AAA_2A, AAA_10A = AAA + "2Y", AAA + "10Y"

# Rendimenti a 10 anni confrontati (serie già scaricate per le altre pagine)
DECENNALI = [("US", "DGS10"), ("Euro area (AAA)", AAA_10A), ("Japan", "JGB_10Y"),
             ("South Korea (monthly)", "IRLTLT01KRM156N")]
JGB = ["JGB_2Y", "JGB_10Y", "JGB_30Y"]

PENDENZA_USA, PENDENZA_EA = "T10Y2Y", "EA_AAA_10A_2A"
SPREAD_USA_3M = "T10Y3M"

# Inflazione confrontata: tutta dal BIS, stessa fonte e stessa definizione per ogni Paese
INFLAZIONE = [("US", "WS_LONG_CPI/M.US.771"), ("Euro area", "WS_LONG_CPI/M.XM.771"),
              ("Japan", "WS_LONG_CPI/M.JP.771"), ("China", "WS_LONG_CPI/M.CN.771"),
              ("South Korea", "WS_LONG_CPI/M.KR.771")]
# Dettagli per Paese
CPI_USA = ["CPIAUCSL", "CPILFESL", "PCEPILFE"]
HICP, HICP_CORE = "HICP/M.U2.N.000000.4D0.ANR", "HICP/M.U2.N.XEF000.4D0.ANR"
CPI_GIAPPONE = ["CPIm/001", "CPIm/733", "CPIm/740"]
TASSI_REALI_USA = ["DFII10", "T10YIE"]


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    nber = charts.periodi_recessione(serie.get("USREC"))
    cepr = charts.periodi_da_trimestri(config.get("recessioni", {}).get("eurozona", {}).get("periodi"))

    def rinominate(elenco) -> list[Serie]:
        return [charts.con_nome(trova_serie(serie, i), nome) for nome, i in elenco]

    def confronto(id_grafico, titolo, elenco, note: list[str], come_leggerlo: str, **opzioni) -> Grafico:
        """Confronto tra Paesi: serie rinominate, nessuna banda di recessione."""
        inversioni = opzioni.pop("evidenzia_inversioni", False)
        riferimento = opzioni.pop("riferimento", None)
        figura = charts.linee_storiche(rinominate(elenco), evidenzia_inversioni=inversioni, riferimento=riferimento)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=[i for _, i in elenco],
                       note=note, come_leggerlo=come_leggerlo, **opzioni)

    def paese(id_grafico, titolo, ids, recessioni, etichetta, note: list[str], come_leggerlo: str, **opzioni) -> Grafico:
        """Grafico di una sola economia, con le sue bande di recessione."""
        inversioni = opzioni.pop("evidenzia_inversioni", False)
        riferimento = opzioni.pop("riferimento", None)
        figura = charts.linee_storiche([trova_serie(serie, i) for i in ids], recessioni=recessioni,
                                       etichetta_recessioni=etichetta, evidenzia_inversioni=inversioni,
                                       riferimento=riferimento)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids),
                       note=note, come_leggerlo=come_leggerlo, **opzioni)

    def curva(id_grafico, titolo, scadenze, note: list[str], come_leggerlo: str) -> Grafico:
        figura, _ = charts.curva_rendimenti([(etichetta, trova_serie(serie, i)) for etichetta, i in scadenze])
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=[i for _, i in scadenze],
                       storico=False, note=note, come_leggerlo=come_leggerlo)

    return [
        Sezione("tassi-policy", "Policy rates",
                "The interest rates central banks set to steer the cost of money, compared across five economies and, "
                "for the Fed and the ECB, from the primary sources.",
                grafici=[
                    confronto("gl-policy", "Policy rates compared", POLICY,
                              ["policy-rates-compared", "china-lpr", "korea-bis-delay"],
                              "A policy rate is the interest rate a central bank sets to steer borrowing costs: raising it is meant to cool the economy "
                              "and cutting it to support it. China's line is a bank lending rate (the LPR), not an overnight rate like the others, so it is not directly comparable.",
                              periodo_iniziale="Max", largo=True),
                    confronto("mk-rates-fed-ecb", "Fed funds effective rate and ECB deposit rate",
                              [("US: effective Fed funds rate", FED_FUNDS), ("Euro area: ECB deposit facility rate", DFR)],
                              ["fed-ecb-rates"],
                              "Each line is the rate that guides short-term borrowing costs in its area: the effective Fed funds rate in the US "
                              "and the deposit facility rate in the euro area. They change in steps after central-bank meetings.",
                              periodo_iniziale="Max", largo=True),
                ]),
        Sezione("curve", "Government yield curves",
                "The interest rate each government pays to borrow for different lengths of time, today compared with "
                "one month and one year ago.",
                grafici=[
                    curva("usa-curva-oggi", "Treasury curve: today, 1 month ago, 1 year ago", SCADENZE_USA,
                          ["curve-snapshot"],
                          "A yield curve shows the interest rate a government pays to borrow for different lengths of time. It usually slopes upwards, "
                          "because longer loans pay more; the dashed and dotted lines show how the curve has shifted over the past month and year."),
                    curva("eur-curva-oggi", "Euro-area AAA curve (Bund proxy): today, 1 month ago, 1 year ago", SCADENZE_EA,
                          ["aaa-bund-proxy", "curve-snapshot"],
                          "The same picture for the euro area, using yields on AAA-rated government bonds (mainly Germany) as a stand-in for German Bunds. "
                          "Comparing the three lines shows how much borrowing costs have moved at each maturity over the past month and year."),
                ]),
        Sezione("rendimenti-10a", "10-year yields compared",
                "The cost at which governments borrow for ten years, a common benchmark for long-term interest rates.",
                grafici=[
                    confronto("gl-rendimenti", "10-year government bond yields", DECENNALI,
                              ["yields-compared", "korea-ktb-monthly"],
                              "The yield on a 10-year government bond is what a government pays to borrow for ten years. Yields have historically tended to rise "
                              "with expected inflation and policy rates; South Korea's line is a monthly average, so it is smoother.",
                              periodo_iniziale="10Y", largo=True),
                ]),
        Sezione("pendenza", "Curve slope and inversions",
                "The slope of the curve is the long-term yield minus the short-term yield. When it turns negative the curve is inverted.",
                grafici=[
                    confronto("mk-rates-slope", "Curve slope 10Y-2Y: US vs euro area",
                              [("US 10Y-2Y", PENDENZA_USA), ("Euro-area AAA 10Y-2Y", PENDENZA_EA)],
                              ["curve-inversion", "aaa-bund-proxy"],
                              "The slope is the 10-year yield minus the 2-year yield. When it falls below zero (red area) the curve is inverted: short-term rates are "
                              "higher than long-term ones, which in the US has often come before recessions, though with long and variable delays. "
                              "The long inversion of 2022-2024 has not been followed by a recession so far, a reminder that the signal can fail.",
                              periodo_iniziale="Max", largo=True, evidenzia_inversioni=True),
                    paese("usa-spread", "10Y-2Y and 10Y-3M spreads", [PENDENZA_USA, SPREAD_USA_3M], nber, "NBER recession",
                          ["curve-inversion", "bands-nber"],
                          "Two versions of the US slope: 10-year minus 2-year, and 10-year minus 3-month. Both have historically turned negative before many US recessions "
                          "(grey bands), but the delay has varied and the signal is not a forecast. The long inversions that began in 2022 "
                          "(10Y-2Y until 2024, 10Y-3M until 2025) have not been followed by a recession so far, a reminder that the signal can fail.",
                          periodo_iniziale="Max", largo=True, evidenzia_inversioni=True),
                ]),
        Sezione("inflazione", "Inflation and real rates",
                "Interest rates only mean something against inflation: how fast consumer prices are rising in five economies, "
                "and what US bonds pay above inflation.",
                grafici=[
                    confronto("gl-inflazione", "CPI inflation compared (% y/y)", INFLAZIONE, ["target-generic"],
                              "Inflation is the yearly change in consumer prices; many central banks aim for about 2%. Central banks have historically tended to raise "
                              "interest rates when inflation runs well above their target and to cut them when it stays too low.",
                              periodo_iniziale="10Y", largo=True, riferimento=(2, "")),
                    paese("usa-reali", "10Y real yield and 10Y breakeven (US)", TASSI_REALI_USA, nber, "NBER recession",
                          ["usa-tips-breakeven", "bands-nber"],
                          "A real yield is what an inflation-protected Treasury (TIPS) pays above inflation. Breakeven inflation is the ordinary yield minus the real yield, "
                          "and shows the inflation rate the bond market is pricing in; both come from market prices, so they move every day and are not forecasts.",
                          periodo_iniziale="Max", largo=True),
                ]),
        Sezione("dettaglio", "Yields by country",
                "A closer look at the yields of the US, the euro area and Japan, by maturity.",
                grafici=[
                    paese("usa-rendimenti", "US yields by maturity over time", [i for _, i in SCADENZE_USA], nber, "NBER recession",
                          ["bands-nber"],
                          "US yields from 3 months to 30 years. Short maturities have historically followed the Fed's policy rate closely, "
                          "while long ones also reflect expectations about growth and inflation.",
                          periodo_iniziale="10Y"),
                    paese("eur-rendimenti", "Euro-area AAA curve (Bund proxy): 2 and 10 years", [AAA_2A, AAA_10A], cepr, "CEPR recession",
                          ["aaa-bund-proxy", "bands-cepr"],
                          "Euro-area AAA yields at 2 and 10 years. The 2-year follows expected ECB rates more closely than the 10-year, "
                          "so the gap between them changes as those expectations change.",
                          periodo_iniziale="10Y"),
                    confronto("jp-jgb", "JGB yields at 2, 10 and 30 years", [(s.nome, s.id) for s in
                                                                            [trova_serie(serie, i) for i in JGB]],
                              ["jgb-history"],
                              "Japanese government bond yields at 2, 10 and 30 years. They stayed unusually low for decades "
                              "while the Bank of Japan held its policy rate near zero or below and, from 2016 to 2024, capped the 10-year yield.",
                              periodo_iniziale="10Y", largo=True),
                ]),
        Sezione("inflazione-paesi", "Inflation by country",
                "The official inflation measures of the US, the euro area and Japan, with their \"core\" versions that leave out the most volatile prices.",
                grafici=[
                    paese("usa-inflazione", "Headline CPI, core CPI and core PCE (% y/y)", CPI_USA, nber, "NBER recession",
                          ["target-fed", "bands-nber"],
                          "Headline CPI covers every item in the basket; core CPI and core PCE leave out food and energy, which swing a lot, to show the underlying trend. "
                          "The Fed's 2% target is defined on the PCE index, and it watches core PCE closely.",
                          periodo_iniziale="10Y", largo=True, riferimento=(2, "")),
                    paese("eur-inflazione", "HICP headline and core (% y/y)", [HICP, HICP_CORE], cepr, "CEPR recession",
                          ["hicp-core", "target-ecb", "bands-cepr"],
                          "HICP is the euro area's official measure of consumer-price inflation; \"core\" leaves out energy, food, alcohol and tobacco to show the underlying trend. "
                          "The ECB aims for 2% over the medium term.",
                          periodo_iniziale="10Y", largo=True, riferimento=(2, "")),
                    confronto("jp-inflazione", "Headline, core and core-core CPI (% y/y)", [(trova_serie(serie, i).nome, i) for i in CPI_GIAPPONE],
                              ["japan-cpi-sources", "target-boj"],
                              "Japan's CPI in three versions: total, \"core\" (without fresh food) and \"core-core\" (also without energy). "
                              "Japanese inflation stayed close to zero or negative for many years, which is why the BoJ's 2% target was a long-running aim. "
                              "Headline inflation then stayed above 2% from April 2022 to the end of 2025, and in 2024 the BoJ ended negative interest rates "
                              "and began raising its policy rate; in 2026 inflation has mostly been below 2% again.",
                              periodo_iniziale="10Y", largo=True, riferimento=(2, "")),
                ]),
    ]
