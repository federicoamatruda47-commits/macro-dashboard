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
    return mock.Mock(status_code=stato, text=testo, content=testo.encode("utf-8"))


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

    def test_risposta_buona_al_primo_colpo_scrive_solo_il_peso(self):
        serie, chiamate, log = scarica_con([risposta(CSV_BUONO)])
        self.assertEqual(chiamate, 1)
        self.assertNotIn("empty response", log)
        self.assertEqual(len(log.strip().splitlines()), 1)                           # una riga: id, KB e numero di valori

    def test_la_richiesta_chiede_dataonly(self):
        log = io.StringIO()
        with mock.patch.object(bis.requests, "get", return_value=risposta(CSV_BUONO)) as get, redirect_stdout(log):
            bis.scarica("WS_CBPOL/D.JP")
        self.assertEqual(get.call_args.kwargs["params"], {"format": "csv", "detail": "dataonly"})
        self.assertIn("WS_CBPOL/D.JP", log.getvalue())
        self.assertIn("2 values", log.getvalue())                      # il peso e il numero di valori finiscono nel log

    def test_risposta_dataonly_senza_colonne_di_testo(self):
        csv = "FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE\nD,JP,2026-09-28,1.25\nD,JP,2026-09-29,1.25\n"      # forma di detail=dataonly (senza UNIT_MEASURE)
        serie, chiamate, _ = scarica_con([risposta(csv)])
        self.assertEqual((chiamate, len(serie), float(serie.iloc[-1])), (1, 2, 1.25))

    def test_pause_tra_i_tentativi_10_e_30_secondi(self):
        with mock.patch.object(bis.requests, "get", side_effect=[risposta("")] * 3), mock.patch.object(bis.time, "sleep") as sonno, redirect_stdout(io.StringIO()):
            with self.assertRaises(ErroreFonte):
                bis.scarica("WS_CBPOL/D.JP")
        self.assertEqual([c.args[0] for c in sonno.call_args_list], [10, 30])

    def test_404_non_si_riprova(self):
        esito, chiamate, _ = scarica_con([risposta("", 404)])
        self.assertEqual(chiamate, 1)
        self.assertIn("not found", str(esito))


if __name__ == "__main__":
    unittest.main()
