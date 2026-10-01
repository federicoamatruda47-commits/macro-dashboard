"""Test di dashboard/sources/bis.py: nuovi tentativi quando il BIS risponde 200 ma senza dati (risposte simulate, nessuna rete)."""

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from dashboard.sources import bis
from dashboard.sources.errori import ErroreFonte

CSV_BUONO = "FREQ,REF_AREA,UNIT_MEASURE,TIME_PERIOD,OBS_VALUE\nD,JP,368,2026-09-28,0.5\nD,JP,368,2026-09-29,0.5\n"
SOLO_INTESTAZIONE = "FREQ,REF_AREA,UNIT_MEASURE,TIME_PERIOD,OBS_VALUE\n"


def risposta(testo: str, stato: int = 200):
    return mock.Mock(status_code=stato, text=testo)


def scarica_con(risposte: list):
    """Esegue bis.scarica con le risposte date (senza attese); restituisce (serie o errore, chiamate, testo del log)."""
    log = io.StringIO()
    with mock.patch.object(bis.requests, "get", side_effect=risposte) as get, mock.patch.object(bis.time, "sleep"), redirect_stdout(log):
        try:
            esito = bis.scarica("WS_CBPOL/D.JP")
        except ErroreFonte as errore:
            esito = errore
    return esito, get.call_count, log.getvalue()


class TestRispostaVuota(unittest.TestCase):
    def test_risposta_vuota_poi_buona_riprova_e_scrive_nel_log(self):
        serie, chiamate, log = scarica_con([risposta(""), risposta(CSV_BUONO)])
        self.assertEqual(chiamate, 2)
        self.assertEqual(len(serie), 2)
        self.assertIn("empty response (attempt 1 of 3); trying again", log)
        self.assertIn("WS_CBPOL/D.JP", log)

    def test_solo_intestazione_conta_come_vuota(self):
        serie, chiamate, log = scarica_con([risposta(SOLO_INTESTAZIONE), risposta(" \n"), risposta(CSV_BUONO)])
        self.assertEqual(chiamate, 3)
        self.assertEqual(len(serie), 2)
        self.assertEqual(log.count("empty response"), 2)

    def test_sempre_vuota_errore_dopo_tre_tentativi(self):
        esito, chiamate, log = scarica_con([risposta("")] * 5)
        self.assertEqual(chiamate, bis.TENTATIVI)
        self.assertIsInstance(esito, ErroreFonte)
        self.assertEqual(str(esito), "the BIS returned no data")
        self.assertIn("giving up", log)

    def test_risposta_buona_al_primo_colpo_non_scrive_nulla(self):
        serie, chiamate, log = scarica_con([risposta(CSV_BUONO)])
        self.assertEqual((chiamate, log), (1, ""))

    def test_404_non_si_riprova(self):
        esito, chiamate, _ = scarica_con([risposta("", 404)])
        self.assertEqual(chiamate, 1)
        self.assertIn("not found", str(esito))


if __name__ == "__main__":
    unittest.main()
