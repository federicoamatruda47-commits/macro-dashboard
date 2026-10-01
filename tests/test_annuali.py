"""Test dei dati annuali per Paese (dashboard/annuali.py, sources/imf.py, sources/worldbank.py, sources/imf_file.py, attivita.py).

Si lanciano come gli altri test, senza rete e senza chiave: dati inventati e risposte finte delle API.
    python -m unittest discover -s tests -t . -v
"""

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import pandas as pd
import yaml

from dashboard import annuali, attivita
from dashboard.sources import imf, imf_file, worldbank
from dashboard.sources.errori import ErroreFonte

RADICE = Path(__file__).resolve().parent.parent


def dati_finti() -> pd.DataFrame:
    return pd.DataFrame([
        ("ITA", "NGDP_RPCH", 2024, 0.783024), ("ITA", "NGDP_RPCH", 2025, 0.539615), ("ITA", "NGDP_RPCH", 2026, 0.520816),
        ("DEU", "NGDP_RPCH", 2025, -0.1), ("DEU", "NGDP_RPCH", 2024, -0.5),
        ("ITA", "PPPPC", 2025, 55000.0004), ("G001", "NGDP_RPCH", 2025, 3.2),
    ], columns=["paese", "indicatore", "anno", "valore"])


class TestFormati(unittest.TestCase):
    def test_valore_a_tre_decimali_senza_zeri_inutili(self):
        self.assertEqual(annuali.formatta_valore(0.738834), "0.739")
        self.assertEqual(annuali.formatta_valore(2.5), "2.5")
        self.assertEqual(annuali.formatta_valore(3.0), "3")
        self.assertEqual(annuali.formatta_valore(61000000.0), "61000000")
        self.assertEqual(annuali.formatta_valore(-0.0002), "0")        # niente "-0"
        self.assertEqual(annuali.formatta_valore(-8.868156), "-8.868")
        self.assertEqual(annuali.formatta_valore(1282.9475), "1282.948")             # a metà: per eccesso, come il file dell'FMI (round() darebbe 1282.947)
        self.assertEqual(annuali.formatta_valore(1.9275), "1.928")
        self.assertEqual(annuali.formatta_valore(-4.6765), "-4.677")
        self.assertEqual(annuali.formatta_valore(1e6 + 0.5), "1000001")
        self.assertEqual(annuali.formatta_valore(21231427856677.898), "21231427856678")   # valori enormi: interi, niente rumore binario

    def test_leggere_e_riscrivere_non_cambia_il_testo(self):
        import random
        casuale = random.Random(7)
        valori = [casuale.uniform(-100, 100) for _ in range(500)] + [casuale.uniform(1e5, 3e13) for _ in range(500)] + [0.0005, 0.0015, 2.0005, 1e6 - 0.0004]
        for v in valori:
            testo = annuali.formatta_valore(v)
            self.assertEqual(annuali.formatta_valore(float(testo)), testo, v)

    def test_ultimo_anno_effettivo(self):
        self.assertEqual(annuali.anno_effettivo("2025"), 2025)
        self.assertEqual(annuali.anno_effettivo("FY2024/25"), 2024)    # anno fiscale = anno di inizio
        self.assertEqual(annuali.anno_effettivo(" FY2023/24 "), 2023)
        self.assertEqual(annuali.anno_effettivo(2025), 2025)
        for vuoto in ("", None, float("nan"), "n/a", "2025Q4"):
            self.assertIsNone(annuali.anno_effettivo(vuoto))

    def test_edizione_dal_mese_di_pubblicazione(self):
        self.assertEqual(annuali.edizione_weo(date(2026, 4, 14)), "April 2026")
        self.assertEqual(annuali.edizione_weo(date(2026, 10, 15)), "October 2026")


class TestUltimoEffettivo(unittest.TestCase):
    def test_equivalente_solo_dove_ci_sono_i_dati_e_mai_sovrascrivendo(self):
        dati = dati_finti()
        ultimo = {("ITA", "NGDPD"): 2025, ("DEU", "NGDPD"): 2024, ("ITA", "PPPPC"): 2023}
        dati = pd.concat([dati, pd.DataFrame([("DEU", "PPPPC", 2024, 1.0), ("FRA", "PPPPC", 2024, 1.0)],
                                              columns=dati.columns)])
        completo = annuali.completa_ultimo_effettivo(ultimo, dati, {"PPPPC": "NGDPD"})
        self.assertEqual(completo[("ITA", "PPPPC")], 2023)             # già presente: resta
        self.assertEqual(completo[("DEU", "PPPPC")], 2024)             # copiato da NGDPD
        self.assertNotIn(("FRA", "PPPPC"), completo)                   # nessun NGDPD per FRA: resta ignoto
        self.assertNotIn(("DEU", "NGDP_RPCH"), completo)

    def test_coppie_senza_ultimo_anno_ignorano_gli_aggregati(self):
        dati = dati_finti()
        mancanti = annuali.senza_ultimo_effettivo(dati, {("ITA", "NGDP_RPCH"): 2025})
        self.assertIn(("DEU", "NGDP_RPCH"), mancanti)
        self.assertIn(("ITA", "PPPPC"), mancanti)
        self.assertNotIn(("G001", "NGDP_RPCH"), mancanti)              # aggregato


class TestSnapshot(unittest.TestCase):
    def test_csv_ordinato_senza_doppioni_e_con_a_capo_unix(self):
        mescolati = dati_finti().sample(frac=1, random_state=3)
        testo = annuali.testo_dati_csv(pd.concat([mescolati, mescolati.head(2)]))     # con doppioni
        righe = testo.split("\n")
        self.assertEqual(righe[0], "paese,indicatore,anno,valore")
        self.assertEqual(righe[1], "DEU,NGDP_RPCH,2024,-0.5")
        self.assertEqual(righe[2], "DEU,NGDP_RPCH,2025,-0.1")
        self.assertEqual(righe[3], "G001,NGDP_RPCH,2025,3.2")
        self.assertIn("ITA,PPPPC,2025,55000", righe)
        self.assertEqual(len(righe), 1 + 7 + 1)                         # intestazione + 7 dati + riga vuota finale
        self.assertNotIn("\r", testo)
        # Lo stesso contenuto in qualunque ordine dà lo stesso testo: i diff mostrano solo i valori cambiati
        self.assertEqual(testo, annuali.testo_dati_csv(dati_finti()))

    def test_scrittura_e_lettura(self):
        with tempfile.TemporaryDirectory() as cartella:
            radice = Path(cartella)
            ultimo = {("ITA", "NGDP_RPCH"): 2025}
            annuali.scrivi_snapshot(radice / annuali.CARTELLE["imf"], dati_finti(), {"pubblicato": "2026-04-14", "edizione": "April 2026"}, ultimo)
            for nome in ("dati.csv", "ultimo_effettivo.csv", "meta.json"):
                self.assertNotIn(b"\r", (radice / annuali.CARTELLE["imf"] / nome).read_bytes())
            letto = annuali.leggi_snapshot(radice, "imf")
            self.assertEqual(len(letto.dati), 7)
            self.assertEqual(letto.meta["edizione"], "April 2026")
            self.assertAlmostEqual(letto.serie("ITA", "NGDP_RPCH").loc[2025], 0.54)
            self.assertIs(letto.e_stima("ITA", "NGDP_RPCH", 2026), True)
            self.assertIs(letto.e_stima("ITA", "NGDP_RPCH", 2025), False)
            self.assertIsNone(letto.e_stima("DEU", "NGDP_RPCH", 2025))   # ultimo anno effettivo ignoto
            self.assertIsNone(annuali.leggi_snapshot(radice, "wb"))      # snapshot assente: nessun errore

    def test_i_veri_paesi_escludono_gli_aggregati(self):
        paesi = pd.DataFrame([("ITA", "Italy", "Europe", "country"), ("WLD", "World", "", "aggregate")],
                             columns=annuali.COLONNE_PAESI)
        dati = pd.DataFrame([("ITA", "SP.POP.TOTL", 2025, 59.0), ("WLD", "SP.POP.TOTL", 2025, 8000.0)], columns=annuali.COLONNE_DATI)
        self.assertEqual(annuali.Snapshot("wb", dati, {}, paesi=paesi).codici_paesi(), {"ITA"})
        self.assertEqual(annuali.Snapshot("imf", dati_finti(), {}).codici_paesi(), {"ITA", "DEU"})   # G001 è un aggregato FMI


class TestFreschezza(unittest.TestCase):
    def test_weo_di_aprile_a_semestri(self):
        pubblicato = date(2026, 4, 14)
        self.assertFalse(annuali.stato_freschezza("imf", "WEO", "semestrale", pubblicato, date(2026, 11, 9)).in_ritardo)    # 209 giorni
        self.assertFalse(annuali.stato_freschezza("imf", "WEO", "semestrale", pubblicato, date(2026, 11, 10)).in_ritardo)   # 210: ancora ok
        self.assertTrue(annuali.stato_freschezza("imf", "WEO", "semestrale", pubblicato, date(2026, 11, 11)).in_ritardo)    # 211

    def test_il_weo_di_ottobre_a_meta_mese_non_da_un_falso_allarme(self):
        vecchio = annuali.stato_freschezza("imf", "WEO", "semestrale", date(2026, 4, 14), date(2026, 10, 16))
        self.assertEqual(vecchio.giorni, 185)
        self.assertFalse(vecchio.in_ritardo)                                   # il WEO nuovo esce a metà ottobre: non si deve avvisare a ottobre
        nuovo = annuali.stato_freschezza("imf", "WEO", "semestrale", date(2026, 10, 14), date(2026, 10, 16))
        self.assertEqual(nuovo.giorni, 2)
        # Se non lo si aggiorna, l'avviso scatta a maggio dell'anno dopo (210 giorni dopo metà ottobre)
        self.assertTrue(annuali.stato_freschezza("imf", "WEO", "semestrale", date(2026, 10, 14), date(2027, 5, 13)).in_ritardo)
        self.assertFalse(annuali.stato_freschezza("imf", "WEO", "semestrale", date(2026, 10, 14), date(2027, 5, 12)).in_ritardo)

    def test_banca_mondiale_a_quindici_mesi(self):
        self.assertFalse(annuali.stato_freschezza("wdi", "WDI", "annuale", date(2026, 7, 13), date(2027, 10, 12)).in_ritardo)
        self.assertTrue(annuali.stato_freschezza("wdi", "WDI", "annuale", date(2026, 7, 13), date(2027, 10, 13)).in_ritardo)

    def test_snapshot_assenti_non_sono_in_ritardo(self):
        stati = annuali.stati_snapshot(None, None, date(2026, 10, 1))
        self.assertEqual([s.id for s in stati], ["imf", "wdi", "wgi"])
        self.assertTrue(all(not s.presente and not s.in_ritardo for s in stati))

    def test_stati_dai_metadati(self):
        imf_snap = annuali.Snapshot("imf", dati_finti(), {}, meta={"pubblicato": "2026-04-14", "edizione": "April 2026"})
        paesi = pd.DataFrame([("ITA", "Italy", "Europe", "country")], columns=annuali.COLONNE_PAESI)
        bm_dati = pd.DataFrame([("ITA", "SP.POP.TOTL", 2025, 59.0), ("ITA", "GOV_WGI_CC.SC", 2025, 60.0)], columns=annuali.COLONNE_DATI)
        bm_snap = annuali.Snapshot("wb", bm_dati, {}, meta={"wdi_aggiornato": "2026-07-13", "wgi_aggiornato": "2025-01-01"}, paesi=paesi)
        stati = {s.id: s for s in annuali.stati_snapshot(imf_snap, bm_snap, date(2026, 10, 1))}
        self.assertEqual(stati["imf"].giorni, 170)
        self.assertEqual(stati["imf"].edizione, "April 2026")
        self.assertEqual((stati["wdi"].n_indicatori, stati["wgi"].n_indicatori), (1, 1))
        self.assertFalse(stati["wdi"].in_ritardo)
        self.assertTrue(stati["wgi"].in_ritardo)                                # aggiornato più di 15 mesi fa


class TestCatalogo(unittest.TestCase):
    def voce(self, **modifiche):
        base = {"id": "a", "nome": "A", "unita": "%", "fonte": "imf", "codice": "NGDP_RPCH", "sezione": "output"}
        return {**base, **modifiche}

    def test_catalogo_vero_di_config_yaml(self):
        config = yaml.safe_load((RADICE / "config.yaml").read_text(encoding="utf-8"))
        catalogo = annuali.carica_catalogo(config)
        codici_imf = {i.codice for i in annuali.indicatori_di(catalogo, "imf")}
        self.assertTrue({"NGDPD", "NGDP_RPCH", "PPPPC", "PCPIPCH", "GGXCNL_NGDP", "GGXWDG_NGDP", "BCA_NGDPD"} <= codici_imf)
        self.assertFalse({"NGDPDPC", "LP"} & codici_imf)                      # tolti: la pagina del Paese non li usa
        wgi = [i for i in annuali.indicatori_di(catalogo, "wb") if i.sorgente_wb == 3]
        self.assertEqual({i.codice for i in wgi}, {"GOV_WGI_CC.SC", "GOV_WGI_CC.SC_LB", "GOV_WGI_CC.SC_UB"})   # solo punteggio e intervallo, nessun rango
        self.assertFalse([i for i in catalogo if "RNK" in i.codice or "PER" in i.codice.split(".")])
        for i in annuali.indicatori_di(catalogo, "wb"):
            if i.codice in ("SL.UEM.TOTL.ZS", "SL.EMP.TOTL.SP.ZS"):
                self.assertIn("ILO modelled estimate", i.nome)

    def test_errori_di_configurazione(self):
        with self.assertRaises(ValueError):
            annuali.carica_catalogo({"indicatori": [{"id": "a", "nome": "A"}]})                           # campi mancanti
        with self.assertRaises(ValueError):
            annuali.carica_catalogo({"indicatori": [self.voce(fonte="ocse")]})                            # fonte sconosciuta
        with self.assertRaises(ValueError):
            annuali.carica_catalogo({"indicatori": [self.voce(), self.voce()]})                            # id doppio
        with self.assertRaises(ValueError):
            annuali.carica_catalogo({"indicatori": [self.voce(ultimo_effettivo_da="NGDPD")]})              # riferimento non nel catalogo
        with self.assertRaises(ValueError):
            annuali.carica_catalogo({"indicatori": [self.voce(fonte="wb", sorgente_wb=9)]})
        self.assertEqual(annuali.carica_catalogo({}), [])


class TestConfronto(unittest.TestCase):
    def test_uguali_cambiati_aggiunti_rimossi(self):
        prima = dati_finti()
        dopo = prima.copy()
        dopo.loc[(dopo["paese"] == "ITA") & (dopo["anno"] == 2025) & (dopo["indicatore"] == "NGDP_RPCH"), "valore"] = 0.9
        dopo = dopo[~((dopo["paese"] == "DEU") & (dopo["anno"] == 2024))]
        dopo = pd.concat([dopo, pd.DataFrame([("FRA", "NGDP_RPCH", 2025, 1.1)], columns=dopo.columns)])
        d = annuali.differenze(prima, dopo)
        self.assertEqual((d.cambiate, d.aggiunte, d.rimosse, d.uguali), (1, 1, 1, 5))
        self.assertEqual(d.per_indicatore, {"NGDP_RPCH": 3})
        self.assertFalse(d.identici)
        self.assertTrue(annuali.differenze(prima, prima.copy()).identici)

    def test_tolleranza_per_gli_arrotondamenti(self):
        a = pd.DataFrame([("ITA", "X", 2025, 0.7384)], columns=annuali.COLONNE_DATI)
        b = pd.DataFrame([("ITA", "X", 2025, 0.738)], columns=annuali.COLONNE_DATI)
        self.assertFalse(annuali.differenze(a, b).identici)
        self.assertTrue(annuali.differenze(a, b, tolleranza=0.0006).identici)

    def test_ultimo_anno_diverso(self):
        self.assertEqual(annuali.differenze_ultimo({("ITA", "A"): 2025, ("DEU", "A"): 2024}, {("ITA", "A"): 2025, ("DEU", "A"): 2025, ("FRA", "A"): 2025}),
                         [("DEU", "A", 2024, 2025), ("FRA", "A", None, 2025)])


FILE_WEO = (
    "WEO Country Code\tISO\tWEO Subject Code\tCountry\tSubject Descriptor\tSubject Notes\tUnits\tScale\tCountry/Series-specific Notes\t"
    "2023\t2024\t2025\t2026\tEstimates Start After\n"
    '136\tITA\tNGDP_RPCH\tItaly\tGross domestic product, constant prices\tnote\tPercent change\t\t\t0.923\t0.783\t0.54\t0.521\t2025\n'
    '136\tITA\tNGDPD\tItaly\tGross domestic product, current prices\tnote\tU.S. dollars\tBillions\t\t"2,380.129"\t"2,372.5"\t"2,500.2"\tn/a\t2024\n'
    '534\tIND\tNGDP_RPCH\tIndia\tGross domestic product, constant prices\tnote\tPercent change\t\t\t8.2\t6.5\t--\t\t2024\n'
    '111\tUSA\tOTHER\tUnited States\tNon in catalogo\tnote\tx\t\t\t1\t2\t3\t4\t2025\n'
    "\n"
    "International Monetary Fund, World Economic Outlook Database, April 2026\n"
)


class TestImportatoreFile(unittest.TestCase):
    def test_lettura_del_file_weo(self):
        dati, ultimo, fiscale, pubblicazione = imf_file.leggi_file_weo(FILE_WEO, {"NGDP_RPCH", "NGDPD"})
        self.assertIsNone(pubblicazione)               # il formato vecchio non riporta la data
        self.assertEqual(sorted(dati["indicatore"].unique()), ["NGDPD", "NGDP_RPCH"])        # OTHER escluso
        self.assertEqual(sorted(dati["paese"].unique()), ["IND", "ITA"])                      # niente righe di nota
        valore = lambda p, i, a: float(dati[(dati.paese == p) & (dati.indicatore == i) & (dati.anno == a)]["valore"].iloc[0])  # noqa: E731
        self.assertEqual(valore("ITA", "NGDPD", 2023), 2380.129)                              # virgola delle migliaia
        self.assertEqual(len(dati[(dati.paese == "ITA") & (dati.indicatore == "NGDPD")]), 3)  # "n/a" saltato
        self.assertEqual(len(dati[dati.paese == "IND"]), 2)                                   # "--" e vuoto saltati
        self.assertEqual(ultimo, {("ITA", "NGDP_RPCH"): 2025, ("ITA", "NGDPD"): 2024, ("IND", "NGDP_RPCH"): 2024})

    def test_codifiche_diverse(self):
        for codifica in ("utf-16", "utf-8-sig", "cp1252"):
            testo = FILE_WEO.replace("Italy", "Italy ü") if codifica != "cp1252" else FILE_WEO.replace("Italy", "Italy é")
            dati, _, _, _ = imf_file.leggi_file_weo(testo.encode(codifica), {"NGDP_RPCH"})
            self.assertEqual(len(dati), 6, codifica)

    def test_file_non_valido(self):
        with self.assertRaises(ErroreFonte):
            imf_file.leggi_file_weo("a\tb\n1\t2\n", {"NGDP_RPCH"})
        with self.assertRaises(ErroreFonte):
            imf_file.leggi_file_weo(FILE_WEO, {"INESISTENTE"})

    def test_file_e_api_danno_lo_stesso_snapshot(self):
        """Dati identici (arrotondati a 3 decimali) scritti nel formato del file e riletti dall'importatore: stesso testo di dati.csv."""
        dati = dati_finti().query("indicatore == 'NGDP_RPCH' and paese != 'G001'")
        righe = ["WEO Country Code\tISO\tWEO Subject Code\tCountry\tSubject Descriptor\tSubject Notes\tUnits\tScale\tCountry/Series-specific Notes\t"
                 "2024\t2025\t2026\tEstimates Start After"]
        for paese, gruppo in dati.groupby("paese"):
            celle = [annuali.formatta_valore(gruppo.set_index("anno")["valore"].get(a, float("nan"))) if a in set(gruppo["anno"]) else "n/a" for a in (2024, 2025, 2026)]
            righe.append(f"1\t{paese}\tNGDP_RPCH\t{paese}\td\tn\tPercent change\t\t\t" + "\t".join(celle) + "\t2025")
        letti, ultimo, _, _ = imf_file.leggi_file_weo("\n".join(righe) + "\n", {"NGDP_RPCH"})
        self.assertEqual(annuali.testo_dati_csv(letti), annuali.testo_dati_csv(dati))
        self.assertTrue(annuali.differenze(dati, letti, tolleranza=0.0006).identici)
        self.assertEqual(ultimo, {("ITA", "NGDP_RPCH"): 2025, ("DEU", "NGDP_RPCH"): 2025})


def risposta(stato=200, testo="", json_=None):
    r = mock.Mock()
    r.status_code = stato
    r.content = testo.encode("utf-8")
    r.json = mock.Mock(side_effect=(lambda: json_) if json_ is not None else ValueError)
    return r


CSV_FMI = ("STRUCTURE[;],STRUCTURE_ID,ACTION,COUNTRY,INDICATOR,FREQUENCY,TIME_PERIOD,OBS_VALUE,LATEST_ACTUAL_ANNUAL_DATA,SCALE\n"
           "dataflow,IMF.RES:WEO(9.0.0),R,ITA,NGDP_RPCH,A,2024,0.783024,2025,0\n"
           "dataflow,IMF.RES:WEO(9.0.0),R,ITA,NGDP_RPCH,A,2025,0.539615,2025,0\n"
           "dataflow,IMF.RES:WEO(9.0.0),R,IND,NGDP_RPCH,A,2024,6.5,FY2024/25,0\n"
           "dataflow,IMF.RES:WEO(9.0.0),R,IND,NGDP_RPCH,A,2025,,FY2024/25,0\n"
           "dataflow,IMF.RES:WEO(9.0.0),R,G001,NGDP_RPCH,A,2025,3.2,,0\n")


class TestApiFmi(unittest.TestCase):
    def test_lettura_della_risposta_e_ultimo_anno_effettivo(self):
        with mock.patch.object(imf.requests, "get", return_value=risposta(testo=CSV_FMI)) as chiamata:
            tabella = imf.scarica_indicatore("NGDP_RPCH")
        self.assertEqual(chiamata.call_args.args[0], imf.URL_DATI + "*.NGDP_RPCH.A")
        self.assertEqual(chiamata.call_args.kwargs["params"]["attributes"], "LATEST_ACTUAL_ANNUAL_DATA,SCALE")     # poche colonne, non le ~60 predefinite
        self.assertEqual(len(tabella), 4)                                                                      # il valore vuoto è scartato
        effettivi = tabella.drop_duplicates("paese").set_index("paese")["ultimo_effettivo"].map(annuali.anno_effettivo)
        self.assertEqual(effettivi["ITA"], 2025)
        self.assertEqual(effettivi["IND"], 2024)                                                               # FY2024/25
        self.assertTrue(pd.isna(effettivi["G001"]))                                                            # aggregato senza ultimo anno

    def test_i_valori_sono_nella_scala_dell_fmi(self):
        """L'API dà l'unità grezza e l'esponente SCALE (9 = miliardi, 6 = milioni): lo snapshot usa la scala del file dell'FMI."""
        csv_scala = ("COUNTRY,INDICATOR,FREQUENCY,TIME_PERIOD,OBS_VALUE,LATEST_ACTUAL_ANNUAL_DATA,SCALE\n"
                     "ITA,NGDPD,A,2025,2550110691000,2024,9\n"
                     "ABW,NGDPD,A,2025,4000000000,2024,9\n")
        with mock.patch.object(imf.requests, "get", return_value=risposta(testo=csv_scala)):
            tabella = imf.scarica_indicatore("NGDPD")
        self.assertAlmostEqual(tabella.set_index("paese").loc["ITA", "valore"], 2550.110691)
        self.assertEqual(annuali.formatta_valore(tabella.set_index("paese").loc["ITA", "valore"]), "2550.111")
        csv_milioni = csv_scala.replace("NGDPD", "LP").replace("2550110691000,2024,9", "58934357,2024,6").replace("4000000000,2024,9", "81163,2024,6")
        with mock.patch.object(imf.requests, "get", return_value=risposta(testo=csv_milioni)):
            tabella = imf.scarica_indicatore("LP")
        self.assertEqual(annuali.formatta_valore(tabella.set_index("paese").loc["ABW", "valore"]), "0.081")    # 81.163 persone = 0,081 milioni, come nel file

    def test_errori_diventano_errore_fonte(self):
        with mock.patch.object(imf.requests, "get", return_value=risposta(stato=404)), self.assertRaises(ErroreFonte):
            imf.scarica_indicatore("NGDP_RPCH")
        with mock.patch.object(imf.requests, "get", return_value=risposta(testo=CSV_FMI.replace("NGDP_RPCH", "ALTRO"))), self.assertRaises(ErroreFonte):
            imf.scarica_indicatore("NGDP_RPCH")
        with mock.patch.object(imf.requests, "get", side_effect=imf.requests.ConnectionError()), mock.patch.object(imf.time, "sleep"), \
                self.assertRaises(ErroreFonte):
            imf.scarica_indicatore("NGDP_RPCH")

    def test_data_di_pubblicazione(self):
        csv_pub = "COUNTRY,INDICATOR,FREQUENCY,TIME_PERIOD,OBS_VALUE,PUBLICATION_DATE\nITA,NGDP_RPCH,A,2024,0.7,2026-04-14T13:00:00Z\n"
        with mock.patch.object(imf.requests, "get", return_value=risposta(testo=csv_pub)):
            self.assertEqual(imf.data_pubblicazione(), "2026-04-14")


def voce_wb(iso3, anno, valore):
    return {"countryiso3code": iso3, "date": str(anno), "value": valore, "country": {"id": iso3}}


class TestApiBancaMondiale(unittest.TestCase):
    def test_lettura_senza_page_alla_prima_richiesta_e_aggregati_senza_codice_scartati(self):
        meta = {"pages": 1, "sourceid": "2", "lastupdated": "2026-07-13"}
        voci = [voce_wb("ITA", 2025, 59.0), voce_wb("ITA", 2024, None), voce_wb("", 2025, 100.0), voce_wb("WLD", 2025, 8000.0)]
        with mock.patch.object(worldbank.requests, "get", return_value=risposta(json_=[meta, voci])) as chiamata:
            dati, aggiornato = worldbank.scarica_indicatore("SP.POP.TOTL", 2)
        self.assertNotIn("page", chiamata.call_args.kwargs["params"])      # con page=1 esplicito la Banca Mondiale può cambiare sorgente
        self.assertEqual(chiamata.call_args.kwargs["params"]["source"], 2)
        self.assertEqual(aggiornato, "2026-07-13")
        self.assertEqual(sorted(dati["paese"]), ["ITA", "WLD"])            # valore nullo e codice vuoto scartati

    def test_sorgente_sbagliata_e_errore(self):
        meta = {"pages": 1, "sourceid": "25", "lastupdated": "2025-07-01"}
        with mock.patch.object(worldbank.requests, "get", return_value=risposta(json_=[meta, [voce_wb("ITA", 2025, 1.0)]])), self.assertRaises(ErroreFonte):
            worldbank.scarica_indicatore("SP.POP.TOTL", 2)

    def test_piu_pagine(self):
        pagina1 = [{"pages": 2, "sourceid": "3", "lastupdated": "2026-09-25"}, [voce_wb("ITA", 2024, 60.0)]]
        pagina2 = [{"pages": 2, "sourceid": "3", "lastupdated": "2026-09-25"}, [voce_wb("ITA", 2025, 61.0)]]
        with mock.patch.object(worldbank.requests, "get", side_effect=[risposta(json_=pagina1), risposta(json_=pagina2)]) as chiamata:
            dati, _ = worldbank.scarica_indicatore("GOV_WGI_CC.SC", 3)
        self.assertEqual(len(dati), 2)
        self.assertEqual(chiamata.call_args_list[1].kwargs["params"]["page"], 2)

    def test_codice_sbagliato_e_risposte_non_valide(self):
        with mock.patch.object(worldbank.requests, "get", return_value=risposta(json_=[{"message": [{"id": "120"}]}])), self.assertRaises(ErroreFonte):
            worldbank.scarica_indicatore("NON.ESISTE")
        with mock.patch.object(worldbank.requests, "get", return_value=risposta(testo="<html>")), self.assertRaises(ErroreFonte):
            worldbank.scarica_indicatore("SP.POP.TOTL")
        with mock.patch.object(worldbank.requests, "get", return_value=risposta(stato=500)), mock.patch.object(worldbank.time, "sleep"), \
                self.assertRaises(ErroreFonte):
            worldbank.scarica_indicatore("SP.POP.TOTL")

    def test_elenco_paesi(self):
        voci = [{"id": "ITA", "name": "Italy", "region": {"value": "Europe & Central Asia"}},
                {"id": "WLD", "name": "World", "region": {"value": "Aggregates"}}]
        with mock.patch.object(worldbank.requests, "get", return_value=risposta(json_=[{"pages": 1}, voci])):
            paesi = worldbank.scarica_paesi()
        self.assertEqual(dict(zip(paesi["paese"], paesi["tipo"])), {"ITA": "country", "WLD": "aggregate"})


class TestAttivita(unittest.TestCase):
    def test_avviso_oltre_45_giorni(self):
        self.assertFalse(attivita.valuta(date(2026, 8, 17), date(2026, 10, 1)).in_ritardo)   # 45 giorni
        self.assertTrue(attivita.valuta(date(2026, 8, 16), date(2026, 10, 1)).in_ritardo)    # 46
        self.assertEqual(attivita.valuta(date(2026, 10, 1), date(2026, 10, 1)).giorni, 0)
        self.assertIsNone(attivita.valuta(None, date(2026, 10, 1)))                           # git assente: nessun avviso

    def test_cartella_senza_git(self):
        with tempfile.TemporaryDirectory() as cartella:
            self.assertIsNone(attivita.data_ultimo_commit(Path(cartella)))


class TestSnapshotNelRepository(unittest.TestCase):
    """Controlli di coerenza sugli snapshot veri in dati/ (si saltano se non ci sono)."""

    def test_formato_e_ordine(self):
        catalogo = annuali.carica_catalogo(yaml.safe_load((RADICE / "config.yaml").read_text(encoding="utf-8")))
        for fonte in ("imf", "wb"):
            snapshot = annuali.leggi_snapshot(RADICE, fonte)
            if snapshot is None:
                self.skipTest(f"nessuno snapshot {fonte}")
            testo = (RADICE / annuali.CARTELLE[fonte] / "dati.csv").read_text(encoding="utf-8")
            self.assertEqual(testo, annuali.testo_dati_csv(snapshot.dati), f"{fonte}: dati.csv non è nel formato canonico (ordine o decimali)")
            self.assertFalse(snapshot.dati.duplicated(["paese", "indicatore", "anno"]).any())
            self.assertEqual({i.codice for i in annuali.indicatori_di(catalogo, fonte)}, set(snapshot.dati["indicatore"]),
                             f"{fonte}: gli indicatori dello snapshot non coincidono con il catalogo")
            self.assertIn(snapshot.fonte, ("imf", "wb"))
        imf_snap = annuali.leggi_snapshot(RADICE, "imf")
        if imf_snap is not None:
            self.assertTrue(set(imf_snap.ultimo_effettivo) <= set(zip(imf_snap.dati["paese"], imf_snap.dati["indicatore"])))


if __name__ == "__main__":
    unittest.main()


class TestDescrizionePr(unittest.TestCase):
    """Il testo della pull request mensile dei dati: esito dei controlli scritto nella descrizione."""

    @staticmethod
    def modulo():
        import importlib.util
        spec = importlib.util.spec_from_file_location("descrizione_pr", RADICE / "tools" / "descrizione_pr.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_tutto_superato(self):
        m = self.modulo()
        esiti = m.leggi_esiti("test|superato\nbuild|superato\n")
        self.assertEqual(m.titolo(esiti, "2026-10"), "World Bank data snapshot 2026-10")
        testo = m.descrizione(esiti, "- Valori cambiati: 3")
        self.assertIn("✅ passed", testo)
        self.assertNotIn("FAILED", testo)
        self.assertIn("Valori cambiati: 3", testo)
        self.assertIn("do not start other workflows", testo)

    def test_un_controllo_fallito_titolo_e_avviso(self):
        m = self.modulo()
        esiti = m.leggi_esiti("test|superato\nlink|FALLITO\n")
        self.assertTrue(m.titolo(esiti, "2026-10").startswith("[checks failed]"))
        testo = m.descrizione(esiti, "")
        self.assertIn("**FAILED**", testo)
        self.assertIn("draft", testo)


class TestControllaAttivita(unittest.TestCase):
    """tools/controlla_attivita.py: una sola issue, mai duplicata; si chiude quando torna un commit (con `gh` finto)."""

    @staticmethod
    def modulo():
        import importlib.util
        spec = importlib.util.spec_from_file_location("controlla_attivita", RADICE / "tools" / "controlla_attivita.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def lancia(self, m, giorni, aperte):
        """Esegue main() con `gh` e la data dell'ultimo commit finti: ritorna le chiamate a `gh` che modificano qualcosa."""
        chiamate = []

        def finto_gh(*argomenti):
            if argomenti[:2] == ("issue", "list"):
                return __import__("json").dumps([{"number": n, "title": t} for n, t in aperte])
            chiamate.append(argomenti)
            return "https://github.com/x/y/issues/9"

        oggi = date(2026, 10, 1)
        stato = attivita.valuta(date.fromordinal(oggi.toordinal() - giorni), oggi, 45)
        with mock.patch.object(m, "gh", side_effect=finto_gh), mock.patch.object(m.attivita, "valuta", return_value=stato), \
                mock.patch.object(m.attivita, "data_ultimo_commit", return_value=stato.ultimo_commit), mock.patch("sys.argv", ["x"]):
            m.main()
        return chiamate

    def test_apre_una_sola_issue_oltre_45_giorni(self):
        m = self.modulo()
        chiamate = self.lancia(m, 46, [])
        self.assertEqual([c[:2] for c in chiamate], [("issue", "create")])
        self.assertEqual(chiamate[0][3], m.TITOLO)
        self.assertIn("46 giorni fa", chiamate[0][5])

    def test_non_ne_apre_una_seconda(self):
        m = self.modulo()
        self.assertEqual(self.lancia(m, 50, [(3, m.TITOLO), (7, "Un'altra issue")]), [])

    def test_sotto_soglia_non_apre_nulla(self):
        m = self.modulo()
        self.assertEqual(self.lancia(m, 45, []), [])
        self.assertEqual(self.lancia(m, 3, [(4, "Un'altra issue")]), [])

    def test_chiude_la_issue_quando_torna_un_commit(self):
        m = self.modulo()
        chiamate = self.lancia(m, 2, [(5, m.TITOLO)])
        self.assertEqual([c[:3] for c in chiamate], [("issue", "close", "5")])

    def test_issue_aperta_riconosce_il_titolo_esatto(self):
        m = self.modulo()
        elenco = '[{"number": 8, "title": "Nessun commit da più di 45 giorni"}, {"number": 6, "title": "%s"}, {"number": 9, "title": "%s"}]' % (m.TITOLO, m.TITOLO)
        with mock.patch.object(m, "gh", return_value=elenco):
            self.assertEqual(m.issue_aperta(m.TITOLO), 6)          # la più vecchia, se per sbaglio ce ne sono due
            self.assertIsNone(m.issue_aperta("[PROVA] " + m.TITOLO))


CSV_PORTALE = (
    '"DATASET","SERIES_CODE","OBS_MEASURE","COUNTRY","INDICATOR","FREQUENCY","SCALE","UNIT","PUBLICATION_DATE","LATEST_ACTUAL_ANNUAL_DATA","2023","2024","2025"\n'
    '"IMF.RES:WEO(9.0.0)","ITA.NGDPD.A","OBS_VALUE","Italy","GDP","Annual","Billions","US dollar","2026-04-14T13:00:00Z","2025","2380.129","2372.5","2550.111"\n'
    '"IMF.RES:WEO(9.0.0)","IND.NGDP_RPCH.A","OBS_VALUE","India","GDP","Annual","Units","Percent","2026-04-14T13:00:00Z","FY2024/25","8.2","6.5","6.4"\n'
    '"IMF.RES:WEO(9.0.0)","KOS.NGDP_RPCH.A","OBS_VALUE","Kosovo","GDP","Annual","Units","Percent","2026-04-14T13:00:00Z","2024","4.1","","3.9"\n'
    '"IMF.RES:WEO(9.0.0)","ITA.PPPPC.A","OBS_VALUE","Italy","GDP","Annual","Units","","2026-04-14T13:00:00Z","","60000","62000","63537.964"\n'
    '"IMF.RES:WEO(9.0.0)","G001.NGDPD.A","OBS_VALUE","World","GDP","Annual","Billions","US dollar","2026-04-14T13:00:00Z","2025","100","101","102"\n'
)


class TestFormatoPortaleEAnnoFiscale(unittest.TestCase):
    def test_csv_del_portale(self):
        dati, ultimo, fiscale, pubblicazione = imf_file.leggi_file_weo(CSV_PORTALE.encode("utf-8-sig"), {"NGDPD", "NGDP_RPCH", "PPPPC"})
        self.assertEqual(pubblicazione, "2026-04-14")                     # la data del WEO, non quella dello scaricamento
        self.assertEqual(sorted(dati["paese"].unique()), ["IND", "ITA", "KOS"])        # niente aggregati (G001)
        self.assertEqual(ultimo[("IND", "NGDP_RPCH")], 2024)
        self.assertEqual(fiscale, {("IND", "NGDP_RPCH")})
        self.assertNotIn(("ITA", "PPPPC"), ultimo)                        # come nel file vero: PPPPC senza ultimo anno effettivo
        self.assertEqual(len(dati[dati.paese == "KOS"]), 2)               # il valore vuoto è saltato

    def test_alias_dei_codici_e_completamento_dell_anno_fiscale(self):
        dati, ultimo, fiscale, _ = imf_file.leggi_file_weo(CSV_PORTALE, {"NGDPD", "NGDP_RPCH", "PPPPC"})
        dati, ultimo, fiscale = annuali.applica_alias(dati), annuali.alias_chiavi(ultimo), annuali.alias_chiavi(fiscale)
        self.assertEqual(sorted(dati["paese"].unique()), ["IND", "ITA", "XKX"])        # KOS -> XKX
        self.assertIn(("XKX", "NGDP_RPCH"), ultimo)
        originale = dict(ultimo)
        ultimo = annuali.completa_ultimo_effettivo(ultimo, dati, {"PPPPC": "NGDPD"})
        self.assertEqual(ultimo[("ITA", "PPPPC")], 2025)                  # anno copiato da NGDPD
        # Un indicatore senza attributo eredita anche il segno "anno fiscale" dell'indicatore di riferimento
        fiscale_con_ref = annuali.completa_fiscale(fiscale | {("ITA", "NGDPD")}, originale, dati, {"PPPPC": "NGDPD"})
        self.assertIn(("ITA", "PPPPC"), fiscale_con_ref)
        self.assertNotIn(("ITA", "PPPPC"), annuali.completa_fiscale(fiscale, originale, dati, {"PPPPC": "NGDPD"}))

    def test_il_flag_anno_fiscale_si_scrive_e_si_rilegge(self):
        with tempfile.TemporaryDirectory() as cartella:
            radice = Path(cartella)
            ultimo = {("IND", "NGDP_RPCH"): 2024, ("ITA", "NGDP_RPCH"): 2025}
            annuali.scrivi_snapshot(radice / annuali.CARTELLE["imf"], dati_finti(), {"pubblicato": "2026-04-14"}, ultimo, fiscale={("IND", "NGDP_RPCH")})
            testo = (radice / annuali.CARTELLE["imf"] / "ultimo_effettivo.csv").read_text(encoding="utf-8")
            self.assertEqual(testo, "paese,indicatore,anno,anno_fiscale\nIND,NGDP_RPCH,2024,1\nITA,NGDP_RPCH,2025,\n")
            letto = annuali.leggi_snapshot(radice, "imf")
            self.assertEqual(letto.fiscale, {("IND", "NGDP_RPCH")})
            self.assertEqual(letto.ultimo_effettivo[("ITA", "NGDP_RPCH")], 2025)

    def test_differenze_contano_anche_il_segno_fiscale(self):
        a = {("IND", "A"): 2024}
        self.assertEqual(annuali.differenze_ultimo(a, a, set(), {("IND", "A")}), [("IND", "A", 2024, 2024)])
        self.assertEqual(annuali.differenze_ultimo(a, a, {("IND", "A")}, {("IND", "A")}), [])

    def test_e_anno_fiscale(self):
        self.assertTrue(annuali.e_anno_fiscale("FY2024/25"))
        self.assertFalse(annuali.e_anno_fiscale("2025"))
        self.assertFalse(annuali.e_anno_fiscale(""))
        self.assertFalse(annuali.e_anno_fiscale(None))
