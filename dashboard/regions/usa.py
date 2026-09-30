"""Pagina Stati Uniti: quali grafici mostrare e in che ordine.

Questo file non scarica nulla: riceve le serie già pronte (dizionario id -> Serie)
e decide come combinarle nei grafici.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

# Scadenze della curva: (etichetta sull'asse, id della serie)
SCADENZE = [("3M", "DGS3MO"), ("2A", "DGS2"), ("5A", "DGS5"), ("10A", "DGS10"), ("30A", "DGS30")]


def costruisci(serie: dict[str, Serie]) -> list[Sezione]:
    """Restituisce le sezioni della pagina USA."""
    recessioni = charts.periodi_recessione(serie.get("USREC"))

    def lista(*ids: str) -> list[Serie]:
        return [trova_serie(serie, i) for i in ids]

    def storico(id_grafico, titolo, ids, **opzioni_grafico) -> Grafico:
        """Scorciatoia per un grafico a linee nel tempo con le bande di recessione."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento", "evidenzia_inversioni")
                          if k in opzioni_grafico}
        figura = charts.linee_storiche(lista(*ids), recessioni=recessioni, **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids), **opzioni_grafico)

    # La curva "oggi vs 1 mese vs 1 anno" ha una forma diversa dagli altri grafici
    figura_curva, _ = charts.curva_rendimenti([(etichetta, trova_serie(serie, i)) for etichetta, i in SCADENZE])
    grafico_curva = Grafico(
        id="usa-curva-oggi", titolo="Curva dei Treasury: oggi, 1 mese fa, 1 anno fa",
        figura=figura_curva, serie_ids=[i for _, i in SCADENZE], storico=False,
    )

    return [
        Sezione("politica-monetaria", "Politica monetaria", grafici=[
            storico("usa-dff", "Fed funds effettivo", ["DFF"], periodo_iniziale="Max", largo=True),
        ]),
        Sezione("curva", "Curva dei Treasury",
                "Rendimenti dei titoli di Stato USA per scadenza. Uno spread 10A-2A o 10A-3M "
                "negativo (curva invertita) ha spesso anticipato le recessioni.",
                grafici=[
                    grafico_curva,
                    storico("usa-rendimenti", "Rendimenti per scadenza nel tempo",
                            [i for _, i in SCADENZE], periodo_iniziale="10A"),
                    storico("usa-spread", "Spread 10A-2A e 10A-3M", ["T10Y2Y", "T10Y3M"],
                            evidenzia_inversioni=True, periodo_iniziale="Max", largo=True,
                            nota="Area rossa: curva invertita (spread sotto zero). "
                                 "Bande grigie: recessioni NBER."),
                ]),
        Sezione("tassi-reali", "Tassi reali e inflazione attesa",
                "Rendimento del Treasury indicizzato all'inflazione (TIPS) e inflazione "
                "attesa dal mercato (breakeven = nominale meno reale). Dati dal 2003.",
                grafici=[
                    storico("usa-reali", "Tasso reale 10A e breakeven 10A", ["DFII10", "T10YIE"],
                            periodo_iniziale="Max", largo=True),
                ]),
        Sezione("inflazione", "Inflazione", "Variazione dei prezzi rispetto a un anno prima.", grafici=[
            storico("usa-inflazione", "CPI headline, CPI core e PCE core (% annua)",
                    ["CPIAUCSL", "CPILFESL", "PCEPILFE"], riferimento=(2, ""),
                    periodo_iniziale="10A", largo=True,
                    nota="Linea tratteggiata: obiettivo della Fed al 2% (misurato sul PCE). "
                         "Bande grigie: recessioni NBER."),
        ]),
        Sezione("credito", "Credito",
                "Premio di rendimento richiesto sulle obbligazioni societarie rispetto ai Treasury.",
                grafici=[
                    storico("usa-baa", "Spread Baa (Moody's) - Treasury 10A", ["BAA10Y"],
                            periodo_iniziale="Max",
                            nota="Serie con storico lungo (dal 1986): utile per confrontare "
                                 "le crisi passate."),
                    storico("usa-oas", "OAS Investment Grade e High Yield (ICE BofA)",
                            ["BAMLC0A0CM", "BAMLH0A0HYM2"], periodo_iniziale="Max",
                            nota="Gli OAS ICE BofA su FRED partono da ottobre 2023: per motivi di "
                                 "licenza FRED pubblica solo gli ultimi anni. Per lo storico lungo "
                                 "guarda lo spread Baa - Treasury 10A."),
                ]),
        Sezione("condizioni", "Condizioni finanziarie e lavoro", grafici=[
            storico("usa-vix", "VIX (volatilità attesa S&P 500)", ["VIXCLS"], periodo_iniziale="5A"),
            storico("usa-dollaro", "Dollaro broad (indice nominale, gen 2006 = 100)", ["DTWEXBGS"],
                    periodo_iniziale="Max"),
            storico("usa-disoccupazione", "Tasso di disoccupazione", ["UNRATE"], periodo_iniziale="Max",
                    largo=True),
        ]),
    ]
