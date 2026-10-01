"""Pagina Cina: quali grafici mostrare e in che ordine."""

from ..data import Serie
from .asia import attrezzi, sezione_non_inclusi
from .modello import Sezione

LPR_1A = "WS_CBPOL/D.CN"
CPI = "WS_LONG_CPI/M.CN.771"
CAMBIO = "CNY=X"
CSI300 = "510300.SS"
HANG_SENG = "^HSI"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    _, storico = attrezzi(serie)

    return [
        Sezione("politica-monetaria", "Politica monetaria",
                "La Cina non ha un unico tasso di policy come Fed o BCE: il riferimento per il credito è "
                "il Loan Prime Rate (LPR), pubblicato ogni mese dalla People's Bank of China "
                "sulla base delle quotazioni delle banche.",
                grafici=[
                    storico("cn-lpr", "Loan Prime Rate a 1 anno", [LPR_1A], periodo_iniziale="Max", largo=True,
                            nota="Fonte BIS, dati giornalieri. Dal 20/08/2019 è l'LPR a 1 anno; prima il BIS "
                                 "usa il tasso ufficiale sui prestiti a 1 anno."),
                ]),
        Sezione("inflazione", "Inflazione", "Variazione annua dei prezzi al consumo.",
                grafici=[
                    storico("cn-inflazione", "CPI Cina (% annua)", [CPI], riferimento=(0, ""),
                            periodo_iniziale="10A", largo=True,
                            nota="Fonte BIS, dati mensili. Linea tratteggiata: zero (sotto = deflazione)."),
                ]),
        Sezione("cambio", "Cambio", grafici=[
            storico("cn-cambio", "USD/CNY (yuan per 1 dollaro)", [CAMBIO], periodo_iniziale="10A", largo=True,
                    mostra_unita=True,
                    nota="Cambio onshore. Sale = lo yuan si indebolisce. Se Yahoo non risponde si usa FRED."),
        ]),
        Sezione("borsa", "Borsa",
                "La borsa cinese è rappresentata dal CSI 300 (Shanghai e Shenzhen); Hong Kong ha un mercato "
                "separato, misurato dall'Hang Seng.",
                grafici=[
                    storico("cn-csi300", "CSI 300 (ETF 510300)", [CSI300], periodo_iniziale="10A",
                            mostra_unita=True,
                            nota="Attenzione: non è l'indice ma un ETF che lo replica (ticker 510300 sulla borsa di "
                                 "Shanghai, prezzo in yuan), perché Yahoo non fornisce lo storico dell'indice "
                                 "CSI 300. Il prezzo segue l'indice ma non coincide con il suo livello; "
                                 "i dati partono dal 2012."),
                    storico("cn-hangseng", "Hang Seng (Hong Kong)", [HANG_SENG], periodo_iniziale="10A",
                            nota="Indice in punti, chiusure giornaliere. Fonte Yahoo Finance (non ufficiale)."),
                ]),
        sezione_non_inclusi("Non inclusi per mancanza di fonti gratuite aggiornate: rendimento 10A, LPR 5A, PPI."),
    ]
