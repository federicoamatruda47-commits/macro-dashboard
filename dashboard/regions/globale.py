"""Pagina Confronto globale: gli stessi dati dei Paesi sullo stesso grafico."""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

# Tassi di policy: tutti dal BIS, così hanno la stessa definizione e la stessa fonte
POLICY = [("USA (Fed)", "WS_CBPOL/D.US"), ("Eurozona (BCE)", "WS_CBPOL/D.XM"), ("Giappone (BoJ)", "WS_CBPOL/D.JP"),
          ("Cina (LPR 1A)", "WS_CBPOL/D.CN"), ("Corea del Sud (BoK)", "WS_CBPOL/D.KR")]
# Rendimenti 10 anni (serie già scaricate per le pagine dei singoli Paesi)
DECENNALI = [("USA", "DGS10"), ("Eurozona (AAA)", "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"),
             ("Giappone", "JGB_10Y"), ("Corea del Sud (mensile)", "IRLTLT01KRM156N")]
# Inflazione: tutta dal BIS
INFLAZIONE = [("USA", "WS_LONG_CPI/M.US.771"), ("Eurozona", "WS_LONG_CPI/M.XM.771"),
              ("Giappone", "WS_LONG_CPI/M.JP.771"), ("Cina", "WS_LONG_CPI/M.CN.771"),
              ("Corea del Sud", "WS_LONG_CPI/M.KR.771")]
# Valute: (nome, id, invertita). Il cambio EUR/USD è quotato "dollari per euro", gli altri "valuta per dollaro":
# questi ultimi si invertono, così per ogni linea "sale" = la valuta si rafforza sul dollaro
VALUTE = [("Euro", "EXR/D.USD.EUR.SP00.A", False), ("Yen", "JPY=X", True),
          ("Yuan", "CNY=X", True), ("Won", "KRW=X", True)]
BORSE = [("S&P 500", "^GSPC"), ("Euro Stoxx 50", "^STOXX50E"), ("FTSE MIB", "FTSEMIB.MI"),
         ("Nikkei 225", "^N225"), ("CSI 300 (ETF)", "510300.SS"), ("KOSPI", "^KS11")]


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

    return [
        Sezione("tassi-policy", "Tassi di policy",
                "I tassi con cui le banche centrali guidano il costo del denaro nelle cinque economie.",
                grafici=[
                    storico("gl-policy", "Tassi di policy a confronto", POLICY, periodo_iniziale="Max", largo=True,
                            nota="Tutte le serie vengono dal BIS. Fed: punto medio dell'intervallo obiettivo; "
                                 "BCE: tasso sui depositi; BoJ: tasso overnight obiettivo; BoK: tasso base. "
                                 "ATTENZIONE: per la Cina è il Loan Prime Rate a 1 anno, un tasso sui prestiti "
                                 "bancari, non un tasso overnight come gli altri: tende a stare sopra e non "
                                 "è confrontabile in modo diretto. La Corea ha circa un mese di ritardo."),
                ]),
        Sezione("rendimenti", "Rendimenti a 10 anni",
                "Il costo con cui i governi si finanziano a 10 anni.",
                grafici=[
                    storico("gl-rendimenti", "Rendimenti dei titoli di Stato a 10 anni", DECENNALI,
                            periodo_iniziale="10A", largo=True,
                            nota="USA: Treasury (FRED, giornaliero); Eurozona: curva AAA della BCE come proxy "
                                 "Bund (giornaliero); Giappone: JGB del Ministero delle Finanze (giornaliero); "
                                 "Corea del Sud: media MENSILE OCSE. La Cina non è inclusa: non esiste una "
                                 "fonte gratuita aggiornata."),
                ]),
        Sezione("inflazione", "Inflazione",
                "Variazione annua dei prezzi al consumo, stessa fonte (BIS) per tutti i Paesi.",
                grafici=[
                    storico("gl-inflazione", "Inflazione CPI a confronto (% annua)", INFLAZIONE,
                            riferimento=(2, ""), periodo_iniziale="10A", largo=True,
                            nota="Dati mensili. Linea tratteggiata: 2%, obiettivo di molte banche centrali."),
                ]),
        Sezione("valute", "Valute contro il dollaro",
                "Quanto vale ogni valuta in dollari, normalizzato a 100 all'inizio del periodo scelto "
                "con i pulsanti 1A / 5A / 10A / Max.",
                grafici=[
                    base100("gl-valute", "Valute contro il dollaro (base 100)", VALUTE,
                            periodo_iniziale="5A", largo=True,
                            nota="Sopra 100 = la valuta si è rafforzata rispetto al dollaro dall'inizio del "
                                 "periodo; sotto 100 = si è indebolita. Yen, yuan e won sono quotati come "
                                 "\"valuta per dollaro\" e qui sono capovolti, così tutte le linee si "
                                 "leggono nello stesso verso. Euro: cambio BCE delle 14:15; le altre "
                                 "valute: chiusura Yahoo Finance. Con \"Max\" si parte dalla prima data in cui "
                                 "esistono tutte le valute."),
                ]),
        Sezione("borse", "Borse",
                "Indici azionari nelle valute locali, normalizzati a 100 all'inizio del periodo scelto.",
                grafici=[
                    base100("gl-borse", "Borse a confronto (base 100)", [(n, i, False) for n, i in BORSE],
                            periodo_iniziale="5A", largo=True,
                            nota="Indici di prezzo in valuta locale: la performance non tiene conto dei cambi. "
                                 "Il CSI 300 è rappresentato da un ETF (ticker 510300), non dall'indice, "
                                 "e parte dal 2012: con \"Max\" tutte le linee partono dalla stessa data."),
                ]),
    ]
