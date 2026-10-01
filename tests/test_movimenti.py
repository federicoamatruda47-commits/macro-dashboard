"""Test del calcolo di "What changed this week" (dashboard/movimenti.py).

Si lanciano dalla cartella del progetto, con l'ambiente virtuale attivo, senza installare nulla (solo unittest):
    python -m unittest discover -s tests -t . -v

I test normali usano dati inventati (casuali ma con seme fisso): niente rete, niente chiave API.
Il test "storico" confronta il calcolo con episodi veri (petrolio e VIX nel marzo 2020): parte solo se si imposta
PROVE_CON_RETE=1 e c'è FRED_API_KEY (nel file .env).
"""

import os
import unittest

import numpy as np
import pandas as pd

from dashboard import movimenti
from dashboard.data import Serie


def passeggiata(n_giorni: int = 1100, passo: float = 0.02, partenza: float = 4.0, seme: int = 1,
                fine: str = "2026-09-30") -> pd.Series:
    """Serie giornaliera (giorni lavorativi) inventata: passeggiata casuale con passi N(0, passo)."""
    date = pd.bdate_range(end=fine, periods=n_giorni)
    valori = partenza + np.cumsum(np.random.default_rng(seme).normal(0, passo, n_giorni))
    return pd.Series(valori, index=date)


def con_salto_finale(dati: pd.Series, salto: float) -> pd.Series:
    """Copia della serie in cui l'ultima settimana (ultimi 5 giorni) sale di `salto` in modo graduale."""
    dati = dati.copy()
    dati.iloc[-5:] += np.linspace(salto / 5, salto, 5)
    return dati


def serie_finta(id_serie: str, dati: pd.Series, gruppo: str | None = "g", unita: str = "%", movimenti_attivi: bool = True) -> Serie:
    return Serie(id=id_serie, fonte="fred", nome=id_serie, paese="us", categoria="curva", unita=unita,
                 trasformazione="livello", movimenti=movimenti_attivi, gruppo_movimenti=gruppo, dati=dati)


OGGI = pd.Timestamp("2026-10-01")


class TestCalcola(unittest.TestCase):
    def test_deviazione_standard_ragionevole(self):
        # passi giornalieri da 2 bp: su una settimana (5 giorni lavorativi) la dev. std. attesa è circa 2 × √5 ≈ 4,5 bp
        mossa, dev_std, n = movimenti.calcola(passeggiata(), "bp")
        self.assertAlmostEqual(dev_std, 2 * np.sqrt(5), delta=0.9)
        self.assertGreater(n, 600)

    def test_l_ultima_settimana_non_gonfia_il_proprio_termine_di_paragone(self):
        base = passeggiata()
        _, dev_senza, _ = movimenti.calcola(base, "bp")
        mossa, dev_con, _ = movimenti.calcola(con_salto_finale(base, 1.0), "bp")   # +100 bp in una settimana
        self.assertAlmostEqual(dev_con, dev_senza, delta=0.05 * dev_senza)         # la deviazione standard non cambia
        self.assertGreater(mossa / dev_con, 10)                                    # e il salto risulta enorme

    def test_segno_negativo(self):
        mossa, dev_std, _ = movimenti.calcola(con_salto_finale(passeggiata(), -0.5), "bp")
        self.assertLess(mossa, 0)
        self.assertLess(mossa / dev_std, -5)

    def test_unita_basis_point(self):
        # un salto di 0,30 punti percentuali sono circa 30 bp (più il rumore dei 5 giorni)
        mossa, _, _ = movimenti.calcola(con_salto_finale(passeggiata(), 0.30), "bp")
        self.assertAlmostEqual(mossa, 30, delta=15)

    def test_percentuale(self):
        date = pd.bdate_range(end="2026-09-30", periods=1100)
        rendimenti = np.random.default_rng(3).normal(0, 0.01, len(date))      # ±1% al giorno
        prezzi = pd.Series(100 * np.exp(np.cumsum(rendimenti)), index=date)
        prezzi.iloc[-5:] = prezzi.iloc[-6] * np.linspace(0.98, 0.90, 5)        # −10% in una settimana
        mossa, dev_std, _ = movimenti.calcola(prezzi, "%")
        self.assertAlmostEqual(mossa, -10, delta=0.5)
        self.assertLess(mossa / dev_std, -3)

    def test_poche_osservazioni(self):
        self.assertIsNone(movimenti.calcola(passeggiata(n_giorni=60), "bp"))

    def test_serie_ferma(self):
        date = pd.bdate_range(end="2026-09-30", periods=1100)
        self.assertIsNone(movimenti.calcola(pd.Series(1.25, index=date), "bp"))

    def test_valori_non_positivi_non_rompono_la_percentuale(self):
        dati = passeggiata(partenza=0.5, passo=0.05)          # attraversa lo zero, come il WTI nel 2020
        dati.iloc[100:110] = [-3, -2, -1, 0, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
        risultato = movimenti.calcola(dati, "%")
        if risultato is not None:
            self.assertTrue(np.isfinite(risultato[0]) and np.isfinite(risultato[1]))

    def test_dati_settimanali(self):
        date = pd.date_range(end="2026-09-25", periods=200, freq="7D")        # un dato a settimana
        dati = pd.Series(100 + np.cumsum(np.random.default_rng(5).normal(0, 0.5, 200)), index=date)
        risultato = movimenti.calcola(dati, "%")
        self.assertIsNotNone(risultato)


class TestClassifica(unittest.TestCase):
    def serie_con_punteggio(self, id_serie, salto_in_dev_std, seme, gruppo="g", **extra):
        """Una serie il cui ultimo movimento vale circa `salto_in_dev_std` deviazioni standard."""
        base = passeggiata(seme=seme)
        _, dev_std, _ = movimenti.calcola(base, "bp")
        dati = con_salto_finale(base, salto_in_dev_std * dev_std / 100)
        return serie_finta(id_serie, dati, gruppo=gruppo, **extra)

    def test_sopra_la_soglia_di_2(self):
        serie = {s.id: s for s in [self.serie_con_punteggio("grande", 3.5, 1, "a"), self.serie_con_punteggio("media", 1.5, 2, "b"),
                                   self.serie_con_punteggio("piccola", 0.2, 3, "c")]}
        risultato = movimenti.classifica(serie, OGGI)
        self.assertEqual([m.id for m in risultato.righe], ["grande"])
        self.assertEqual(risultato.n_controllate, 3)
        self.assertEqual(risultato.n_sopra_soglia, 1)
        self.assertEqual(movimenti.SOGLIA, 2.0)

    def test_una_serie_per_gruppo(self):
        serie = {s.id: s for s in [self.serie_con_punteggio("a1", 4.0, 1, "tassi"), self.serie_con_punteggio("a2", 5.0, 2, "tassi"),
                                   self.serie_con_punteggio("b1", 3.0, 3, "borse")]}
        risultato = movimenti.classifica(serie, OGGI)
        self.assertEqual([m.id for m in risultato.righe], ["a2", "b1"])      # del gruppo "tassi" resta solo la più grande
        self.assertEqual(risultato.n_sopra_soglia, 3)                        # ma tutte e tre superavano la soglia

    def test_ordine_per_valore_assoluto_con_segno(self):
        serie = {s.id: s for s in [self.serie_con_punteggio("su", 3.0, 1, "a"), self.serie_con_punteggio("giu", -4.0, 2, "b")]}
        righe = movimenti.classifica(serie, OGGI).righe
        self.assertEqual([m.id for m in righe], ["giu", "su"])
        self.assertLess(righe[0].punteggio, 0)
        self.assertGreater(righe[1].punteggio, 0)

    def test_massimo_cinque_righe(self):
        serie = {s.id: s for s in [self.serie_con_punteggio(f"s{i}", 3.0 + i * 0.1, i + 1, f"g{i}") for i in range(7)]}
        self.assertEqual(len(movimenti.classifica(serie, OGGI).righe), 5)

    def test_settimana_tranquilla(self):
        serie = {s.id: s for s in [self.serie_con_punteggio(f"s{i}", 0.3, i + 1, f"g{i}") for i in range(4)]}
        risultato = movimenti.classifica(serie, OGGI)
        self.assertEqual(risultato.righe, [])
        self.assertEqual(risultato.n_controllate, 4)           # "A quiet week" ma con 4 serie controllate

    def test_serie_senza_gruppo_conta_per_se(self):
        serie = {s.id: s for s in [self.serie_con_punteggio("x", 3.0, 1, None), self.serie_con_punteggio("y", 3.0, 2, None)]}
        self.assertEqual(len(movimenti.classifica(serie, OGGI).righe), 2)

    def test_serie_escluse(self):
        base = con_salto_finale(passeggiata(), 1.0)
        nuova = pd.bdate_range(end="2026-09-30", periods=1100)
        mensile = pd.Series(base.to_numpy(), index=pd.date_range(end="2026-08-01", periods=1100, freq="MS"))
        vecchia = con_salto_finale(passeggiata(fine="2026-06-30"), 1.0)           # ultimo dato di tre mesi prima: "in ritardo"
        serie = {
            "ok": serie_finta("ok", base, "a"),
            "non_attiva": serie_finta("non_attiva", base, "b", movimenti_attivi=False),
            "mensile": serie_finta("mensile", mensile, "c"),
            "in_ritardo": serie_finta("in_ritardo", vecchia, "d"),
            "non_disponibile": Serie(id="nd", fonte="fred", nome="nd", paese="us", categoria="curva", unita="%",
                                     trasformazione="livello", movimenti=True, gruppo_movimenti="e", errore="errore"),
        }
        risultato = movimenti.classifica(serie, OGGI)
        self.assertEqual([m.id for m in risultato.righe], ["ok"])
        self.assertEqual(risultato.n_controllate, 1)

    def test_tipo_in_base_all_unita(self):
        tasso = serie_finta("tasso", con_salto_finale(passeggiata(), 1.0), unita="%")
        prezzo = serie_finta("prezzo", con_salto_finale(passeggiata(partenza=100, passo=0.5), 20), unita="points")
        self.assertEqual(movimenti.movimento_serie(tasso, OGGI).tipo, "bp")
        self.assertEqual(movimenti.movimento_serie(prezzo, OGGI).tipo, "%")


@unittest.skipUnless(os.environ.get("PROVE_CON_RETE") == "1", "serve PROVE_CON_RETE=1, rete e FRED_API_KEY")
class TestStorico(unittest.TestCase):
    """Episodi veri: i movimenti del marzo 2020 devono risultare enormi rispetto alla normalità dei 3 anni precedenti."""

    @classmethod
    def setUpClass(cls):
        from dotenv import load_dotenv
        from dashboard.sources import FONTI
        load_dotenv()
        cls.fred = staticmethod(FONTI["fred"])

    def test_petrolio_marzo_2020(self):
        # settimana al 9 marzo 2020 (guerra dei prezzi tra Arabia Saudita e Russia): WTI circa −34%, oltre 8 volte la norma
        wti = self.fred("DCOILWTICO")["2017-01-01":"2020-03-09"]
        mossa, dev_std, _ = movimenti.calcola(wti, "%")
        self.assertLess(mossa, -25)
        self.assertLess(mossa / dev_std, -5)

    def test_vix_fine_febbraio_2020(self):
        # settimana al 27 febbraio 2020 (l'inizio del crollo Covid): VIX più che raddoppiato, circa 8 volte la norma
        vix = self.fred("VIXCLS")["2017-01-01":"2020-02-27"]
        mossa, dev_std, _ = movimenti.calcola(vix, "%")
        self.assertGreater(mossa, 100)
        self.assertGreater(mossa / dev_std, 5)

    def test_il_vix_dopo_il_balzo_non_e_piu_straordinario(self):
        # un'altra settimana turbolenta (al 13 marzo 2020, VIX +38%) vale meno di 2×: il paragone è con i 3 anni PRIMA
        # e il VIX si muove tanto anche in settimane normali (dev. std. circa 20%): la soglia di 2× è esigente per costruzione
        vix = self.fred("VIXCLS")["2017-01-01":"2020-03-13"]
        mossa, dev_std, _ = movimenti.calcola(vix, "%")
        self.assertLess(abs(mossa / dev_std), 2.0)


if __name__ == "__main__":
    unittest.main()
