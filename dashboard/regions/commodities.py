"""Pagina Commodities: materie prime (energia, metalli, agricoli) e loro legame con i tassi USA.

Non è una regione geografica, ma segue la stessa struttura di usa.py ed eurozona.py:
riceve le serie già pronte (dizionario id -> Serie) e decide come combinarle nei grafici.
Le bande grigie sono le recessioni USA (NBER): i prezzi sono in dollari e i mercati
di riferimento (NYMEX, COMEX, CBOT) sono americani.
Le note tecniche stanno in contenuti/note.yaml: qui si indicano solo gli id.
"""

from .. import charts
from ..data import Serie, trova_serie
from .modello import Grafico, Sezione

WTI, BRENT, GAS_USA, GAS_EU = "CL=F", "BZ=F", "NG=F", "TTF=F"
ORO, ARGENTO = "GC=F", "SI=F"
RAME, ALLUMINIO = "HG=F", "ALI=F"
GRANO, MAIS = "ZW=F", "ZC=F"
TUTTE = [WTI, BRENT, GAS_USA, GAS_EU, ORO, ARGENTO, RAME, ALLUMINIO, GRANO, MAIS]


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    """Restituisce le sezioni della pagina Commodities."""
    recessioni = charts.periodi_recessione(serie.get("USREC"))

    def da_yahoo(id_serie: str) -> bool:
        """True se i dati mostrati vengono da Yahoo (per le serie calcolate: da una componente)."""
        s = trova_serie(serie, id_serie)
        if s.componenti:
            return s.ok and any(da_yahoo(c) for c in s.componenti)
        return s.fonte_usata == "yahoo"

    def note_complete(ids, specifiche: list[str]) -> list[str]:
        """Note del grafico: le sue, più quella sui future continui (solo se i dati sono davvero di Yahoo,
        non della riserva FRED) e quella sulle bande NBER."""
        return specifiche + (["continuous-futures"] if any(da_yahoo(i) for i in ids) else []) + ["bands-nber"]

    def prezzo(id_grafico, titolo, ids, note: list[str] | None = None, **opzioni_grafico) -> Grafico:
        """Grafico a linee dei prezzi, con l'unità sull'asse e le bande NBER."""
        opzioni_figura = {k: opzioni_grafico.pop(k) for k in ("riferimento",) if k in opzioni_grafico}
        figura = charts.linee_storiche([trova_serie(serie, i) for i in ids], recessioni=recessioni,
                                       mostra_unita=True, **opzioni_figura)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=list(ids),
                       note=note_complete(ids, note or []), **opzioni_grafico)

    def confronto(id_grafico, titolo, sopra, sotto, note: list[str], inverti: bool = False) -> Grafico:
        """Due pannelli con lo stesso asse del tempo: commodity sopra, tasso USA sotto."""
        figura = charts.due_pannelli(trova_serie(serie, sopra), trova_serie(serie, sotto),
                                     recessioni=recessioni, inverti_sotto=inverti)
        return Grafico(id=id_grafico, titolo=titolo, figura=figura, serie_ids=[sopra, sotto],
                       note=note_complete([sopra], note), periodo_iniziale="Max", largo=True, alto=True)

    return [
        Sezione("performance", "Performance",
                "Percentage change in price versus 1 week, 1 month, the end of last year "
                "and 1 year earlier. Green = up, red = down.",
                tabella_performance=TUTTE, etichetta_performance="Commodity"),
        Sezione("energia", "Energy",
                "Oil and natural gas: WTI is the US benchmark, Brent the international one; "
                "Henry Hub is US gas, TTF (Netherlands) is European gas.",
                grafici=[
                    prezzo("com-petrolio", "WTI and Brent crude oil", [WTI, BRENT], largo=True,
                           note=["wti-negative-2020"]),
                    prezzo("com-gas-usa", "Henry Hub natural gas (US)", [GAS_USA]),
                    prezzo("com-gas-eu", "TTF natural gas (Europe)", [GAS_EU], periodo_iniziale="Max",
                           note=["ttf-history"]),
                ]),
        Sezione("metalli-preziosi", "Precious metals",
                "Gold and silver: safe-haven assets and stores of value. There is no free fallback "
                "source: if Yahoo does not respond the charts stay empty.",
                grafici=[
                    prezzo("com-oro", "Gold", [ORO]),
                    prezzo("com-argento", "Silver", [ARGENTO]),
                ]),
        Sezione("metalli-industriali", "Industrial metals",
                "Copper and aluminium are used in construction, electrical equipment and manufacturing: their prices "
                "follow the global economic cycle (above all Chinese demand).",
                grafici=[
                    prezzo("com-rame", "Copper", [RAME]),
                    prezzo("com-alluminio", "Aluminium (COMEX)", [ALLUMINIO], periodo_iniziale="Max",
                           note=["aluminium-comex"]),
                ]),
        Sezione("agricoli", "Agricultural", "Chicago Board of Trade futures, in US cents per bushel "
                "(about 27 kg of wheat or 25 kg of corn).",
                grafici=[
                    prezzo("com-grano", "Wheat", [GRANO]),
                    prezzo("com-mais", "Corn", [MAIS]),
                ]),
        Sezione("analisi", "Commodities and rates",
                "Two-panel charts with the same time axis: the commodity on top, the US "
                "rate below, each with its own scale (no dual axis). The period shown is "
                "the one in which both series exist: TIPS and breakeven data start in 2003.",
                grafici=[
                    confronto("com-oro-reale", "Gold vs 10-year US real yield (TIPS)", ORO, "DFII10",
                              ["gold-real-yield"], inverti=True),
                    confronto("com-rame-oro", "Copper/gold ratio vs 10-year Treasury",
                              "RAPPORTO_RAME_ORO", "DGS10", ["copper-gold-ratio"]),
                    confronto("com-petrolio-breakeven", "WTI crude oil vs 10-year expected inflation (breakeven)",
                              WTI, "T10YIE", ["oil-breakeven"]),
                    prezzo("com-brent-wti", "Brent − WTI spread", ["SPREAD_BRENT_WTI"], largo=True,
                           periodo_iniziale="Max", riferimento=(0, ""), note=["brent-wti-spread"]),
                ]),
    ]
