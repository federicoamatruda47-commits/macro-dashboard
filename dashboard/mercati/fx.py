"""Pagina FX (valute): le principali valute contro il dollaro e l'indice del dollaro.

Come le altre pagine di mercato: riceve le serie già pronte (dizionario id -> Serie) e decide come
combinarle nei grafici. Le note tecniche stanno in contenuti/note.yaml: qui si indicano solo gli id.
Niente bande di recessione sui cambi (sono rapporti tra due economie), tranne l'indice del dollaro, che è
l'indice del dollaro USA e usa le recessioni NBER.
"""

from .. import charts
from ..data import Serie, trova_serie
from ..regions.modello import Grafico, Sezione

EURUSD = "EXR/D.USD.EUR.SP00.A"     # BCE, quotato "dollari per euro"
USDJPY, USDCNY, USDKRW = "JPY=X", "CNY=X", "KRW=X"  # Yahoo, quotati "valuta per dollaro"
DOLLARO_BROAD = "DTWEXBGS"

# Valute: (nome, id, invertita). L'euro è quotato "dollari per euro", le altre "valuta per dollaro":
# queste ultime si invertono, così per ogni linea "sale" = la valuta si rafforza sul dollaro
VALUTE = [("Euro", EURUSD, False), ("Yen", USDJPY, True), ("Yuan", USDCNY, True), ("Won", USDKRW, True)]


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    recessioni = charts.periodi_recessione(serie.get("USREC"))

    def livello(id_grafico, titolo, id_serie, note: list[str], come_leggerlo: str, **opzioni) -> Grafico:
        """Un tasso di cambio nel tempo, senza bande di recessione."""
        figura = charts.linee_storiche([trova_serie(serie, id_serie)], mostra_unita=True)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=[id_serie], note=note,
                       come_leggerlo=come_leggerlo, periodo_iniziale="10Y", **opzioni)

    voci = [(charts.con_nome(trova_serie(serie, i), nome), invertita) for nome, i, invertita in VALUTE]
    confronto = Grafico(
        id="gl-valute", titolo="Currencies against the dollar (base 100)", figura=charts.linee_base100(voci),
        serie_ids=[i for _, i, _ in VALUTE], periodo_iniziale="5Y", largo=True,
        note=["rebase-base100", "currencies-base100"],
        come_leggerlo="Each line starts at 100 when the chosen period begins: above 100 the currency has gained against the US dollar, "
                      "below 100 it has lost. Currencies have historically been influenced by interest-rate differences, trade and investors' appetite for risk.")

    dollaro = Grafico(
        id="usa-dollaro", titolo="Broad dollar index (Jan 2006 = 100)",
        figura=charts.linee_storiche([trova_serie(serie, DOLLARO_BROAD)], recessioni=recessioni),
        serie_ids=[DOLLARO_BROAD], periodo_iniziale="Max", largo=True, note=["broad-dollar-index", "bands-nber"],
        come_leggerlo="An index of the dollar against the currencies of the United States' main trading partners: when it rises, the dollar is getting stronger. "
                      "It has historically tended to strengthen in periods of global stress, but not in every one.")

    return [
        Sezione("confronto", "Currencies compared",
                "How the euro, yen, yuan and won have moved against the US dollar over the same period, "
                "rebased to 100 at the start of the period chosen with the 1Y / 5Y / 10Y / Max buttons.",
                grafici=[confronto]),
        Sezione("livelli", "Exchange rates in levels",
                "The actual exchange rates, each in the way it is usually quoted: for EUR/USD, up means a stronger euro; "
                "for the others, up means a stronger dollar.",
                grafici=[
                    livello("eur-eurusd", "EUR/USD (dollars per 1 euro)", EURUSD, ["eurusd-ecb"],
                            "How many US dollars one euro buys: when the line rises, the euro is getting stronger against the dollar. "
                            "Differences between ECB and Fed interest rates have historically been one of the factors behind its moves, but not the only one."),
                    livello("jp-cambio", "USD/JPY (yen per 1 dollar)", USDJPY, ["usdjpy"],
                            "How many yen one US dollar buys: when the line rises, the yen is getting weaker. The yen has tended to weaken when Japanese "
                            "interest rates are much lower than US ones, but it has sometimes strengthened sharply in periods of market stress."),
                    livello("cn-cambio", "USD/CNY (yuan per 1 dollar)", USDCNY, ["usdcny"],
                            "How many Chinese yuan one US dollar buys: when the line rises, the yuan is getting weaker. The yuan is managed more tightly "
                            "than the other currencies here, so its moves have historically been smaller and more gradual."),
                    livello("kr-cambio", "USD/KRW (won per 1 dollar)", USDKRW, ["usdkrw"],
                            "How many Korean won one US dollar buys: when the line rises, the won is getting weaker. The won has historically tended "
                            "to weaken in periods of global financial stress, such as in 2008."),
                ]),
        Sezione("dollaro", "The broad dollar",
                "The dollar against a basket of the currencies of its main trading partners, instead of one currency at a time.",
                grafici=[dollaro]),
    ]
