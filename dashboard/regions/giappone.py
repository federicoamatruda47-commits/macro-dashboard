"""Pagina Giappone: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi
from .modello import Sezione

POLICY = "WS_CBPOL/D.JP"
JGB_2A, JGB_10A, JGB_30A = "JGB_2Y", "JGB_10Y", "JGB_30Y"
CPI = "WS_LONG_CPI/M.JP.771"
CPI_CORE, CPI_CORE_CORE = "CPIm/733", "CPIm/740"
CAMBIO = "JPY=X"
NIKKEI = "^N225"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("politica-monetaria", "Politica monetaria",
                "Tasso obiettivo della Bank of Japan sul mercato overnight (call rate non garantito). "
                "Per decenni è rimasto vicino a zero, e per alcuni anni negativo.",
                grafici=[
                    storico("jp-policy", "Tasso di policy BoJ", [POLICY], periodo_iniziale="Max", largo=True,
                            nota="Fonte BIS, dati giornalieri."),
                ]),
        Sezione("titoli-di-stato", "Titoli di Stato (JGB)",
                "Rendimenti giornalieri dei titoli di Stato giapponesi a 2, 10 e 30 anni, "
                "pubblicati dal Ministero delle Finanze.",
                grafici=[
                    storico("jp-jgb", "Rendimenti JGB a 2, 10 e 30 anni", [JGB_2A, JGB_10A, JGB_30A],
                            periodo_iniziale="10A", largo=True,
                            nota="Il 30 anni parte dal 1999, il 10 anni dal 1986. Se il Ministero non risponde "
                                 "il solo 10 anni ripiega sulla media mensile OCSE (FRED)."),
                ]),
        Sezione("inflazione", "Inflazione",
                "Variazione annua dei prezzi al consumo. Il \"core\" esclude gli alimentari freschi; "
                "il \"core-core\" esclude anche l'energia.",
                grafici=[
                    storico("jp-inflazione", "CPI totale, core e core-core (% annua)",
                            [CPI, CPI_CORE, CPI_CORE_CORE], riferimento=(2, ""), periodo_iniziale="10A",
                            largo=True,
                            nota="Linea tratteggiata: obiettivo della BoJ al 2%. Il CPI totale arriva dal BIS "
                                 "(un mese di ritardo in più); core e core-core dallo Statistics Bureau of "
                                 "Japan (via DBnomics), di cui la variazione annua è calcolata sull'indice."),
                ]),
        Sezione("cambio", "Cambio", grafici=[
            storico("jp-cambio", "USD/JPY (yen per 1 dollaro)", [CAMBIO], periodo_iniziale="10A", largo=True,
                    mostra_unita=True,
                    nota="Sale = lo yen si indebolisce. Se Yahoo non risponde si usa FRED (rilevazione "
                         "giornaliera della Fed, con qualche giorno di ritardo)."),
        ]),
        Sezione("borsa", "Borsa", grafici=[
            storico("jp-nikkei", "Nikkei 225", [NIKKEI], periodo_iniziale="10A", largo=True,
                    nota="Indice in yen, chiusure giornaliere. Fonte Yahoo Finance (non ufficiale)."),
        ]),
    ]
