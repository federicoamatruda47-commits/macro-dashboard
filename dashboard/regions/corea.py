"""Pagina Corea del Sud: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi, sezione_non_inclusi
from .modello import Sezione

POLICY = "WS_CBPOL/D.KR"
KTB_10A = "IRLTLT01KRM156N"
CPI = "WS_LONG_CPI/M.KR.771"
CAMBIO = "KRW=X"
KOSPI = "^KS11"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("politica-monetaria", "Politica monetaria",
                "Il tasso base della Bank of Korea (BoK) è il tasso di riferimento per il mercato monetario.",
                grafici=[
                    storico("kr-policy", "Tasso base BoK", [POLICY], periodo_iniziale="Max", largo=True,
                            nota="Fonte BIS, dati giornalieri. Il BIS pubblica la Corea con circa un mese "
                                 "di ritardo: per questa serie l'avviso di dati non aggiornati scatta "
                                 "dopo 45 giorni invece di 10."),
                ]),
        Sezione("titoli-di-stato", "Titoli di Stato",
                "Rendimento dei titoli di Stato coreani a 10 anni.",
                grafici=[
                    storico("kr-ktb", "Titoli di Stato 10 anni (dati MENSILI)", [KTB_10A],
                            periodo_iniziale="Max", largo=True,
                            nota="Dati mensili (media del mese, fonte OCSE tramite FRED), con circa un mese "
                                 "di ritardo: il dato giornaliero non è disponibile gratuitamente."),
                ]),
        Sezione("inflazione", "Inflazione", "Variazione annua dei prezzi al consumo.",
                grafici=[
                    storico("kr-inflazione", "CPI Corea del Sud (% annua)", [CPI], riferimento=(2, ""),
                            periodo_iniziale="10A", largo=True,
                            nota="Fonte BIS, dati mensili. Linea tratteggiata: obiettivo della BoK al 2%."),
                ]),
        Sezione("cambio", "Cambio", grafici=[
            storico("kr-cambio", "USD/KRW (won per 1 dollaro)", [CAMBIO], periodo_iniziale="10A", largo=True,
                    mostra_unita=True,
                    nota="Sale = il won si indebolisce. Se Yahoo non risponde si usa FRED."),
        ]),
        Sezione("borsa", "Borsa", grafici=[
            storico("kr-kospi", "KOSPI", [KOSPI], periodo_iniziale="10A", largo=True,
                    nota="Indice in punti, chiusure giornaliere. Fonte Yahoo Finance (non ufficiale)."),
        ]),
        sezione_non_inclusi("Non incluso: rendimento 3A (dato giornaliero disponibile solo tramite API della "
                            "Bank of Korea con registrazione coreana)."),
    ]
