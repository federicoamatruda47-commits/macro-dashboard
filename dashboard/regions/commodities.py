"""Pagina Commodities: materie prime (energia, metalli, agricoli) e loro legame con i tassi USA.

Non è una regione geografica, ma segue la stessa struttura di usa.py ed eurozona.py:
riceve le serie già pronte (dizionario id -> Serie) e decide come combinarle nei grafici.
Le bande grigie sono le recessioni USA (NBER): i prezzi sono in dollari e i mercati
di riferimento (NYMEX, COMEX, CBOT) sono americani.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

WTI, BRENT, GAS_USA, GAS_EU = "CL=F", "BZ=F", "NG=F", "TTF=F"
ORO, ARGENTO = "GC=F", "SI=F"
RAME, ALLUMINIO = "HG=F", "ALI=F"
GRANO, MAIS = "ZW=F", "ZC=F"
TUTTE = [WTI, BRENT, GAS_USA, GAS_EU, ORO, ARGENTO, RAME, ALLUMINIO, GRANO, MAIS]

NOTA_RECESSIONI = "Bande grigie: recessioni USA (NBER)."
# Aggiunta sotto i grafici che usano davvero dati Yahoo (non se è in uso la riserva FRED)
NOTA_SCADENZE = ("Future continuo Yahoo Finance: si segue sempre il contratto con la scadenza più "
                 "vicina e, quando scade, si passa al successivo. In quei giorni possono comparire "
                 "piccoli salti di prezzo che non sono veri movimenti di mercato.")


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    """Restituisce le sezioni della pagina Commodities."""
    recessioni = charts.periodi_recessione(serie.get("USREC"))

    def da_yahoo(id_serie: str) -> bool:
        """True se i dati mostrati vengono da Yahoo (per le serie calcolate: da una componente)."""
        s = trova_serie(serie, id_serie)
        if s.componenti:
            return s.ok and any(da_yahoo(c) for c in s.componenti)
        return s.fonte_usata == "yahoo"

    def nota_completa(ids, testo: str = "") -> str:
        parti = [testo] if testo else []
        if any(da_yahoo(i) for i in ids):
            parti.append(NOTA_SCADENZE)
        parti.append(NOTA_RECESSIONI)
        return " ".join(parti)

    def prezzo(id_grafico, titolo, ids, nota: str = "", **opzioni_grafico) -> Grafico:
        """Grafico a linee dei prezzi, con l'unità sull'asse e le bande NBER."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento",) if k in opzioni_grafico}
        figura = charts.linee_storiche([trova_serie(serie, i) for i in ids], recessioni=recessioni,
                                       mostra_unita=True, **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids),
                       nota=nota_completa(ids, nota), **opzioni_grafico)

    def confronto(id_grafico, titolo, sopra, sotto, nota: str, inverti: bool = False) -> Grafico:
        """Due pannelli con lo stesso asse del tempo: commodity sopra, tasso USA sotto."""
        figura = charts.due_pannelli(trova_serie(serie, sopra), trova_serie(serie, sotto),
                                     recessioni=recessioni, inverti_sotto=inverti)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=[sopra, sotto],
                       nota=nota_completa([sopra], nota), periodo_iniziale="Max", largo=True, alto=True)

    return [
        Sezione("performance", "Performance",
                "Variazione percentuale del prezzo rispetto a 1 settimana, 1 mese, fine dell'anno "
                "scorso e 1 anno prima. Verde = rialzo, rosso = ribasso.",
                tabella_performance=TUTTE),
        Sezione("energia", "Energia",
                "Petrolio e gas naturale: il WTI è il riferimento americano, il Brent quello "
                "internazionale; Henry Hub è il gas USA, TTF (Paesi Bassi) il gas europeo.",
                grafici=[
                    prezzo("com-petrolio", "Petrolio WTI e Brent", [WTI, BRENT], largo=True,
                           nota="Il 20/04/2020 il future WTI ha chiuso sotto zero (−37 $): "
                                "a scadenza nessuno aveva spazio per stoccare il petrolio."),
                    prezzo("com-gas-usa", "Gas naturale Henry Hub (USA)", [GAS_USA]),
                    prezzo("com-gas-eu", "Gas naturale TTF (Europa)", [GAS_EU], periodo_iniziale="Max",
                           nota="Su Yahoo dati dal 2017."),
                ]),
        Sezione("metalli-preziosi", "Metalli preziosi",
                "Oro e argento: beni rifugio e riserva di valore. Nessuna fonte di riserva gratuita: "
                "se Yahoo non risponde i grafici restano vuoti.",
                grafici=[
                    prezzo("com-oro", "Oro", [ORO]),
                    prezzo("com-argento", "Argento", [ARGENTO]),
                ]),
        Sezione("metalli-industriali", "Metalli industriali",
                "Rame e alluminio sono usati in edilizia, elettricità e manifattura: i loro prezzi "
                "seguono il ciclo economico globale (soprattutto la domanda cinese).",
                grafici=[
                    prezzo("com-rame", "Rame", [RAME]),
                    prezzo("com-alluminio", "Alluminio (COMEX)", [ALLUMINIO], periodo_iniziale="Max",
                           nota="Future COMEX poco scambiato (il riferimento mondiale è il London Metal "
                                "Exchange, non gratuito): il prezzo è coerente con quello LME ma può "
                                "muoversi a scatti. Su Yahoo dati dal 2014."),
                ]),
        Sezione("agricoli", "Agricoli", "Future del Chicago Board of Trade, in centesimi di dollaro per bushel "
                "(circa 27 kg di grano o 25 kg di mais).",
                grafici=[
                    prezzo("com-grano", "Grano", [GRANO]),
                    prezzo("com-mais", "Mais", [MAIS]),
                ]),
        Sezione("analisi", "Commodities e tassi",
                "Grafici a due pannelli con lo stesso asse del tempo: la commodity in alto, il tasso "
                "USA in basso, ognuno con la sua scala (niente doppio asse). Il periodo mostrato è "
                "quello in cui esistono entrambe le serie: i dati su TIPS e breakeven partono dal 2003.",
                grafici=[
                    confronto("com-oro-reale", "Oro vs tasso reale USA 10 anni (TIPS)", ORO, "DFII10",
                              "L'oro non paga interessi: quando il rendimento reale sale, tenerlo "
                              "\"costa\" di più e il prezzo tende a scendere. Per questo l'asse del tasso "
                              "reale è INVERTITO (i valori alti stanno in basso): se il legame tiene, le "
                              "due linee salgono e scendono insieme. Dal 2022 il legame si è indebolito "
                              "per gli acquisti di oro delle banche centrali.",
                              inverti=True),
                    confronto("com-rame-oro", "Rapporto rame/oro vs Treasury 10 anni",
                              "RAPPORTO_RAME_ORO", "DGS10",
                              "Rame (metallo ciclico) diviso oro (bene rifugio), moltiplicato per 1000: "
                              "sale quando il mercato si aspetta più crescita e tende a muoversi insieme "
                              "ai rendimenti a 10 anni. Calcolato solo se entrambi i prezzi vengono da Yahoo."),
                    confronto("com-petrolio-breakeven", "Petrolio WTI vs inflazione attesa 10 anni (breakeven)",
                              WTI, "T10YIE",
                              "Il prezzo dell'energia pesa molto sull'inflazione attesa dal mercato "
                              "(breakeven = rendimento nominale meno rendimento reale): le due serie "
                              "tendono a muoversi insieme."),
                    prezzo("com-brent-wti", "Spread Brent − WTI", ["SPREAD_BRENT_WTI"], largo=True,
                           periodo_iniziale="Max", riferimento=(0, ""),
                           nota="Differenza tra i due future sul petrolio. Calcolato solo se entrambi i "
                                "prezzi vengono da Yahoo: le riserve FRED sono prezzi spot e non si "
                                "mescolano con i future. Il Brent è un contratto ICE che scade prima del "
                                "WTI: nei giorni di scadenza lo spread può saltare."),
                ]),
    ]
