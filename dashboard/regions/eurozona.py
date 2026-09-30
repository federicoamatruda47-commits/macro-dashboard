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
SCADENZE = [("3M", AAA + "3M"), ("1A", AAA + "1Y"), ("2A", AAA + "2Y"),
            ("5A", AAA + "5Y"), ("10A", AAA + "10Y"), ("30A", AAA + "30Y")]
AAA_2A, AAA_10A = AAA + "2Y", AAA + "10Y"
TUTTI_10A = "YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_10Y"

HICP = "HICP/M.U2.N.000000.4D0.ANR"
HICP_CORE = "HICP/M.U2.N.XEF000.4D0.ANR"
HY_EURO = "BAMLHE00EHYIOAS"
EURUSD = "EXR/D.USD.EUR.SP00.A"

NOTA_RECESSIONI = "Bande grigie: recessioni dell'area euro datate dal CEPR."


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
                                       etichetta_recessioni="Recessione CEPR", **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    figura_curva, _ = charts.curva_rendimenti([(etichetta, trova_serie(serie, i)) for etichetta, i in SCADENZE])
    grafico_curva = Grafico(
        id="eur-curva-oggi", titolo="Curva AAA area euro (proxy Bund): oggi, 1 mese fa, 1 anno fa",
        figura=figura_curva, serie_ids=[i for _, i in SCADENZE], storico=False,
    )

    return [
        Sezione("politica-monetaria", "Politica monetaria",
                "Il tasso sui depositi (DFR) è il tasso che la BCE paga alle banche sulla liquidità "
                "depositata: oggi è il principale strumento con cui la BCE guida i tassi di mercato.",
                grafici=[
                    storico("eur-dfr", "Tasso sui depositi BCE (DFR)", [DFR], periodo_iniziale="Max",
                            largo=True, nota=NOTA_RECESSIONI),
                ]),
        Sezione("curva", "Curva AAA area euro (proxy Bund)",
                "Rendimenti stimati dalla BCE sui titoli di Stato dell'area euro con rating AAA "
                "(Germania, Paesi Bassi e pochi altri). Dati giornalieri dal 2004. I rendimenti "
                "dei soli Bund tedeschi, giornalieri, non sono disponibili gratuitamente: "
                "questa curva ne è una buona approssimazione.",
                grafici=[
                    grafico_curva,
                    storico("eur-rendimenti", "Curva AAA area euro (proxy Bund): 2 e 10 anni",
                            [AAA_2A, AAA_10A], periodo_iniziale="10A"),
                    storico("eur-pendenza", "Pendenza della curva AAA: 10A - 2A", ["EA_AAA_10A_2A"],
                            evidenzia_inversioni=True, periodo_iniziale="Max", largo=True,
                            nota="Area rossa: curva invertita (spread sotto zero). " + NOTA_RECESSIONI),
                ]),
        Sezione("spread-sovrani", "Spread sovrani",
                "Quanto rendimento in più chiedono gli investitori per prestare a un Paese "
                "rispetto alla Germania: misura il rischio percepito (debito, politica, "
                "tenuta dell'euro).",
                grafici=[
                    storico("eur-spread-paesi", "Spread BTP-Bund e OAT-Bund 10 anni (dati MENSILI)",
                            ["SPREAD_BTP_BUND", "SPREAD_OAT_BUND"], periodo_iniziale="Max", largo=True,
                            nota="Dati mensili: media del mese dei rendimenti a 10 anni usati dalla BCE "
                                 "per i criteri di convergenza, pubblicati con circa un mese di ritardo. "
                                 "I rendimenti giornalieri dei singoli Paesi non sono disponibili "
                                 "gratuitamente. " + NOTA_RECESSIONI),
                    storico("eur-spread-tutti", "Tutti i titoli di Stato area euro meno AAA, 10 anni (giornaliero)",
                            ["EA_TUTTI_MENO_AAA_10A"], periodo_iniziale="Max", largo=True,
                            nota="Rendimento a 10 anni della curva BCE di tutti i titoli di Stato "
                                 "dell'area euro meno quello della curva AAA: un indicatore giornaliero "
                                 "del premio di rischio medio dei Paesi non AAA (Italia, Francia, "
                                 "Spagna...). Dati dal 2004. " + NOTA_RECESSIONI),
                ]),
        Sezione("inflazione", "Inflazione", "Variazione dei prezzi al consumo (HICP) rispetto a un anno prima.",
                grafici=[
                    storico("eur-inflazione", "HICP headline e core (% annua)", [HICP, HICP_CORE],
                            riferimento=(2, ""), periodo_iniziale="10A", largo=True,
                            nota="Core = esclusi energia, alimentari, alcol e tabacco. "
                                 "Linea tratteggiata: obiettivo della BCE al 2%. " + NOTA_RECESSIONI),
                ]),
        Sezione("credito", "Credito",
                "Premio di rendimento richiesto sulle obbligazioni societarie in euro rispetto ai titoli di Stato.",
                grafici=[
                    storico("eur-hy", "OAS High Yield in euro (ICE BofA)", [HY_EURO], periodo_iniziale="Max",
                            largo=True,
                            nota="Su FRED la serie parte da ottobre 2023 (limite di licenza ICE). "
                                 "Lo spread Investment Grade in euro non è incluso: non esiste una "
                                 "fonte gratuita."),
                ]),
        Sezione("cambio", "Cambio", grafici=[
            storico("eur-eurusd", "EUR/USD (dollari per 1 euro)", [EURUSD], periodo_iniziale="10A", largo=True,
                    nota="Cambio di riferimento BCE, rilevato ogni giorno lavorativo alle 14:15 (ora di "
                         "Francoforte). Sale = l'euro si rafforza. " + NOTA_RECESSIONI),
        ]),
    ]
