"""Test della pagina del Paese e dei collegamenti Markets <-> Economies (dashboard/paesi.py).

    python -m unittest discover -s tests -t . -v
Dati inventati più alcuni controlli sugli snapshot veri in dati/ (si saltano se non ci sono).
"""

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import yaml

from dashboard import annuali, paesi

RADICE = Path(__file__).resolve().parent.parent


def config_finta(completa_usa: bool = False, stato_italia: str = "in-arrivo") -> dict:
    return {
        "colori": {"us": {}, "it": {}, "jp": {}, "ea": {}, "global": {}, "kr": {}},
        "pagine": [{"id": "economies", "tipo": "hub"},
                   {"id": "economies/usa", "stato": "attiva", "completa": completa_usa},
                   {"id": "economies/italy", "stato": stato_italia, "completa": True},
                   {"id": "economies/euro-area", "stato": "in-arrivo"},
                   {"id": "markets/rates", "stato": "attiva"}, {"id": "markets/equities", "stato": "attiva"}],
        "serie": [{"id": "DFF"}, {"id": "^N225"}, {"id": "^GSPC"}],
        "paesi": {
            "us": {"iso3": "USA", "nome": "United States", "pagina": "economies/usa", "mercati": ["DFF", "^GSPC"], "vai": ["markets/rates"]},
            "it": {"iso3": "ITA", "nome": "Italy", "pagina": "economies/italy"},
            "ea": {"nome": "Euro area", "pagina": "economies/euro-area"},
            "jp": {"iso3": "JPN", "nome": "Japan", "mercati": ["^N225"], "vai": ["markets/equities"]},
            "kr": {"iso3": "KOR", "nome": "South Korea"},
        },
        "paesi_aggiuntivi": {"TWN": {"nome": "Taiwan Province of China", "regione": "East Asia & Pacific"}},
    }


CODICI = {"USA", "ITA", "JPN", "KOR"}


class TestConfigPaesi(unittest.TestCase):
    def test_config_valida(self):
        self.assertEqual(set(paesi.carica_paesi(config_finta())), {"us", "it", "ea", "jp", "kr"})

    def test_riferimenti_sbagliati(self):
        for modifica in ({"paesi": {"zz": {"iso3": "ZZZ", "nome": "Z"}}},                                   # chiave senza colore
                         {"paesi": {"us": {"iso3": "us", "nome": "x"}}},                                     # iso3 non valido
                         {"paesi": {"us": {"iso3": "USA", "nome": "x", "pagina": "economies/nessuna"}}},    # pagina inesistente
                         {"paesi": {"us": {"iso3": "USA", "nome": "x", "mercati": ["NON_ESISTE"]}}},        # serie inesistente
                         {"paesi": {"us": {"iso3": "USA", "nome": "x", "vai": ["markets/nessuna"]}}},       # pagina Markets inesistente
                         {"paesi": {"us": {"iso3": "USA"}}}):                                                # manca il nome
            with self.assertRaises(ValueError):
                paesi.carica_paesi({**config_finta(), **modifica})

    def test_config_vera(self):
        config = yaml.safe_load((RADICE / "config.yaml").read_text(encoding="utf-8"))
        carica = paesi.carica_paesi(config)
        self.assertEqual(carica["jp"].iso3, "JPN")
        self.assertIsNone(carica["ea"].iso3)
        for chiave in ("economies/usa", "economies/italy", "economies/euro-area", "economies/uk"):
            voce = next(p for p in config["pagine"] if p["id"] == chiave)
            self.assertFalse(voce["completa"], chiave)               # nessuna pagina di livello A è ancora completa


class TestDestinazione(unittest.TestCase):
    def test_pagina_a_solo_se_completa(self):
        # USA: pagina attiva ma NON completa -> la pagina del Paese
        self.assertEqual(paesi.destinazione("us", config_finta(), "markets/rates", CODICI), "../../economies/country.html?c=USA")
        # USA completa -> la pagina di livello A
        self.assertEqual(paesi.destinazione("us", config_finta(completa_usa=True), "markets/rates", CODICI), "../../economies/usa/")

    def test_pagina_in_arrivo_non_conta_anche_se_segnata_completa(self):
        self.assertEqual(paesi.destinazione("it", config_finta(stato_italia="in-arrivo"), "markets/equities", CODICI),
                         "../../economies/country.html?c=ITA")
        self.assertEqual(paesi.destinazione("it", config_finta(stato_italia="attiva"), "markets/equities", CODICI), "../../economies/italy/")

    def test_area_euro_senza_link_finche_non_e_completa(self):
        self.assertIsNone(paesi.destinazione("ea", config_finta(), "markets/rates", CODICI))
        config = config_finta()
        config["pagine"][3].update(stato="attiva", completa=True)
        self.assertEqual(paesi.destinazione("ea", config, "markets/rates", CODICI), "../../economies/euro-area/")

    def test_mai_link_morti(self):
        self.assertIsNone(paesi.destinazione("kr", config_finta(), "markets/rates", {"USA"}))          # KOR non è nei dati
        self.assertIsNone(paesi.destinazione("global", config_finta(), "markets/rates", CODICI))       # non è un Paese
        self.assertIsNone(paesi.destinazione("energia", config_finta(), "markets/rates", CODICI))

    def test_percorsi_relativi_da_pagine_diverse(self):
        self.assertEqual(paesi.destinazione("jp", config_finta(), "economies", CODICI), "country.html?c=JPN")             # dall'hub
        self.assertEqual(paesi.destinazione("jp", config_finta(), "markets", CODICI), "../economies/country.html?c=JPN")   # da una pagina di primo livello

    def test_full_page_solo_verso_pagine_complete(self):
        self.assertIsNone(paesi.pagina_completa_del_paese("USA", config_finta()))
        self.assertEqual(paesi.pagina_completa_del_paese("USA", config_finta(completa_usa=True)), "usa/")
        self.assertIsNone(paesi.pagina_completa_del_paese("JPN", config_finta()))

    def test_link_di_un_grafico_senza_doppioni(self):
        link = paesi.link_economia_per_serie(["jp", "jp", "global", "us", "ea", "jp"], config_finta(), "markets/rates", CODICI)
        self.assertEqual([l["nome"] for l in link], ["Japan", "United States"])           # global e area euro senza destinazione
        self.assertTrue(all(l["href"].startswith("../../economies/") for l in link))


def snapshot_finti():
    dati_imf = pd.DataFrame([
        ("ITA", "NGDP_RPCH", 2024, 0.783024), ("ITA", "NGDP_RPCH", 2025, 0.539615), ("ITA", "NGDP_RPCH", 2026, 0.5),
        ("ITA", "NGDPD", 2025, 2550.111), ("IND", "NGDP_RPCH", 2024, 6.5), ("IND", "NGDP_RPCH", 2025, 6.4), ("TWN", "NGDP_RPCH", 2025, 3.0),
        ("XKX", "NGDP_RPCH", 2025, 4.0),
    ], columns=annuali.COLONNE_DATI)
    imf = annuali.Snapshot("imf", dati_imf, {("ITA", "NGDP_RPCH"): 2025, ("ITA", "NGDPD"): 2025, ("IND", "NGDP_RPCH"): 2024, ("TWN", "NGDP_RPCH"): 2025},
                           fiscale={("IND", "NGDP_RPCH")})
    elenco = pd.DataFrame([("ITA", "Italy", "Europe & Central Asia ", "country"), ("IND", "India", "South Asia", "country"),
                           ("CUB", "Cuba", "Latin America & Caribbean", "country"), ("XKX", "Kosovo", "Europe & Central Asia", "country"),
                           ("WLD", "World", "", "aggregate")], columns=annuali.COLONNE_PAESI)
    dati_bm = pd.DataFrame([
        ("ITA", "SL.UEM.TOTL.ZS", 2025, 6.391), ("ITA", "SP.POP.TOTL", 2025, 58915656), ("ITA", "NY.GDP.MKTP.CD", 2025, 2.5e12),
        ("CUB", "SP.POP.TOTL", 2024, 11000000), ("CUB", "NY.GDP.MKTP.CD", 2023, 1.1e11), ("CUB", "NY.GDP.MKTP.CD", 2024, 1.2e11),
        ("CUB", "NY.GDP.MKTP.KD.ZG", 2024, 1.5), ("ITA", "GOV_WGI_CC.SC", 1996, 60.0), ("ITA", "GOV_WGI_CC.SC", 1998, 61.0),
        ("ITA", "GOV_WGI_CC.SC", 2002, 62.5), ("WLD", "SP.POP.TOTL", 2025, 8.0e9),
    ], columns=annuali.COLONNE_DATI)
    bm = annuali.Snapshot("wb", dati_bm, {}, paesi=elenco)
    return imf, bm


def catalogo_vero():
    return annuali.carica_catalogo(yaml.safe_load((RADICE / "config.yaml").read_text(encoding="utf-8")))


class TestElencoEDati(unittest.TestCase):
    def test_elenco_unisce_le_fonti_e_usa_i_nomi_giusti(self):
        imf, bm = snapshot_finti()
        elenco = paesi.elenco_paesi(imf, bm, config_finta())
        per_codice = {p["c"]: p for p in elenco}
        self.assertEqual(set(per_codice), {"ITA", "IND", "TWN", "XKX", "CUB"})                 # nessun aggregato (WLD)
        self.assertEqual(per_codice["TWN"]["nome"], "Taiwan Province of China")                # nome dato dall'FMI, dal blocco paesi_aggiuntivi
        self.assertEqual(per_codice["TWN"]["regione"], "East Asia & Pacific")
        self.assertEqual((per_codice["TWN"]["fmi"], per_codice["TWN"]["bm"]), (True, False))
        self.assertEqual((per_codice["CUB"]["fmi"], per_codice["CUB"]["bm"]), (False, True))
        self.assertEqual(per_codice["ITA"]["regione"], "Europe & Central Asia")                # spazio finale tolto
        self.assertEqual([p["nome"] for p in elenco], sorted((p["nome"] for p in elenco), key=str.casefold))   # ordine alfabetico

    def test_dati_di_un_paese_con_fmi(self):
        imf, bm = snapshot_finti()
        d = paesi.dati_paese("ITA", imf, bm, catalogo_vero())
        self.assertEqual(d["fonte"], "imf")
        self.assertEqual(d["serie"]["gdp_growth"], {"y": 2024, "v": [0.783024, 0.539615, 0.5]})
        self.assertEqual(d["effettivo"]["gdp_growth"], 2025)
        self.assertEqual(d["ultimo"]["gdp_growth"], [2025, 0.539615])                          # ultimo anno EFFETTIVO, non la proiezione 2026
        self.assertEqual(d["finale"]["gdp_growth"], 2026)
        self.assertEqual(d["ultimo"]["population"], [2025, 58.9157])                           # persone -> milioni, 6 cifre significative
        wgi = d["serie"]["corruption_score"]
        self.assertEqual((wgi["y"], len(wgi["v"])), (1996, 7))                                 # 1996..2002 con i buchi come null
        self.assertEqual([wgi["v"][i] for i in (0, 2, 6)], [60.0, 61.0, 62.5])
        self.assertIsNone(wgi["v"][1])
        self.assertNotIn("gdp_nominal_wb", d["serie"])                                         # la Banca Mondiale non sostituisce l'FMI se c'è l'FMI
        self.assertEqual(d["serie"]["gdp_nominal"]["v"], [2550.11])                            # miliardi FMI

    def test_anno_fiscale(self):
        imf, bm = snapshot_finti()
        d = paesi.dati_paese("IND", imf, bm, catalogo_vero())
        self.assertEqual(d["fiscale"], ["gdp_growth"])
        self.assertEqual(paesi.dati_paese("ITA", imf, bm, catalogo_vero())["fiscale"], [])

    def test_paese_senza_fmi_usa_la_banca_mondiale_e_non_mescola(self):
        imf, bm = snapshot_finti()
        d = paesi.dati_paese("CUB", imf, bm, catalogo_vero())
        self.assertEqual(d["fonte"], "wb")
        self.assertEqual(d["serie"]["gdp_nominal"], {"y": 2023, "v": [110.0, 120.0]})          # dollari -> miliardi, sotto la stessa chiave del WEO
        self.assertEqual(d["ultimo"]["gdp_growth"], [2024, 1.5])
        self.assertEqual(d["effettivo"]["gdp_nominal"], 2024)                                 # Banca Mondiale: tutto effettivo, nessuna proiezione
        self.assertEqual(d["fiscale"], [])
        self.assertNotIn("government_debt", d["serie"])

    def test_paese_solo_fmi_senza_dati_banca_mondiale(self):
        imf, bm = snapshot_finti()
        d = paesi.dati_paese("TWN", imf, bm, catalogo_vero())
        self.assertEqual(set(d["serie"]), {"gdp_growth"})

    def test_paese_sconosciuto(self):
        imf, bm = snapshot_finti()
        self.assertIsNone(paesi.dati_paese("ZZZ", imf, bm, catalogo_vero()))

    def test_ultimi_valori_per_la_mappa(self):
        imf, bm = snapshot_finti()
        dati = {c: paesi.dati_paese(c, imf, bm, catalogo_vero()) for c in ("ITA", "CUB", "IND")}
        uv = paesi.ultimi_valori(dati)
        self.assertEqual(uv["gdp_growth"]["ITA"], [0.539615, 2025])
        self.assertEqual(uv["gdp_growth"]["CUB"], [1.5, 2024])
        self.assertEqual(uv["unemployment_ilo"]["ITA"], [6.391, 2025])
        self.assertNotIn("CUB", uv["unemployment_ilo"])
        self.assertEqual(set(uv), set(paesi.INDICATORI_MAPPA))

    def test_scrittura_dei_file_e_pulizia(self):
        imf, bm = snapshot_finti()
        with tempfile.TemporaryDirectory() as cartella:
            site = Path(cartella)
            (site / paesi.CARTELLA_DATI).mkdir(parents=True)
            (site / paesi.CARTELLA_DATI / "VECCHIO.json").write_text("{}")
            elenco = paesi.elenco_paesi(imf, bm, config_finta())
            scritti = paesi.scrivi_dati(site, imf, bm, catalogo_vero(), elenco)
            nomi = sorted(p.name for p in (site / paesi.CARTELLA_DATI).glob("*.json"))
            self.assertEqual(nomi, ["CUB.json", "IND.json", "ITA.json", "TWN.json", "XKX.json", "ultimi-valori.json"])   # VECCHIO.json rimosso
            letto = json.loads((site / paesi.CARTELLA_DATI / "ITA.json").read_text(encoding="utf-8"))
            self.assertEqual(letto["c"], "ITA")
            self.assertEqual(set(scritti), {"CUB", "IND", "ITA", "TWN", "XKX"})
            self.assertNotIn(b"\r", (site / paesi.CARTELLA_DATI / "ITA.json").read_bytes())


class TestSnapshotVeri(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.imf = annuali.leggi_snapshot(RADICE, "imf")
        cls.bm = annuali.leggi_snapshot(RADICE, "wb")
        if cls.imf is None or cls.bm is None:
            raise unittest.SkipTest("snapshot non presenti")
        cls.config = yaml.safe_load((RADICE / "config.yaml").read_text(encoding="utf-8"))
        cls.catalogo = annuali.carica_catalogo(cls.config)

    def test_218_paesi_senza_doppioni_di_codice(self):
        elenco = paesi.elenco_paesi(self.imf, self.bm, self.config)
        codici = [p["c"] for p in elenco]
        self.assertEqual(len(codici), len(set(codici)))
        self.assertEqual(len(codici), 218)
        self.assertNotIn("KOS", codici)                    # alias: Kosovo è XKX
        self.assertNotIn("WBG", codici)
        self.assertTrue({"XKX", "PSE", "TWN", "CUB", "ITA"} <= set(codici))
        self.assertEqual(next(p for p in elenco if p["c"] == "TWN")["nome"], "Taiwan Province of China")
        self.assertEqual(next(p for p in elenco if p["c"] == "KOR")["nome"], "South Korea")
        self.assertEqual(next(p for p in elenco if p["c"] == "PRK")["nome"], "North Korea")          # nome più semplice di "Korea, Dem. People's Rep."
        self.assertEqual(next(p for p in elenco if p["c"] == "EGY")["nome"], "Egypt")

    def test_casi_speciali(self):
        c = lambda iso: paesi.dati_paese(iso, self.imf, self.bm, self.catalogo)  # noqa: E731
        ind = c("IND")
        self.assertIn("gdp_growth", ind["fiscale"])
        self.assertIn("government_debt", ind["fiscale"])
        self.assertEqual(c("ITA")["fiscale"], [])
        siria = c("SYR")
        self.assertEqual(siria["finale"]["gdp_growth"], 2010)                   # nessuna proiezione: i dati FMI si fermano al 2010
        self.assertEqual(siria["effettivo"]["gdp_growth"], 2010)
        self.assertEqual(c("CUB")["fonte"], "wb")
        self.assertEqual(c("ITA")["fonte"], "imf")
        self.assertEqual(c("ITA")["ultimo"]["gdp_growth"][0], 2025)
        self.assertGreater(c("ITA")["finale"]["gdp_growth"], c("ITA")["effettivo"]["gdp_growth"])      # l'Italia ha proiezioni
        mao = c("MAC")
        self.assertGreater(mao["finale"]["gdp_growth"], mao["effettivo"]["gdp_growth"])                 # Macao ha proiezioni...
        self.assertEqual(mao["finale"]["government_primary_balance"], 2022)                              # ...tranne il saldo primario
        self.assertNotIn("unemployment_ilo", c("TWN")["serie"])                                          # Taiwan: solo FMI

    def test_tutti_i_paesi_hanno_dati_e_file_piccoli(self):
        elenco = paesi.elenco_paesi(self.imf, self.bm, self.config)
        dimensioni = []
        for p in elenco:
            d = paesi.dati_paese(p["c"], self.imf, self.bm, self.catalogo)
            self.assertIsNotNone(d, p["c"])
            dimensioni.append(len(json.dumps(d, separators=(",", ":"))))
        self.assertLess(max(dimensioni), 12_000)           # circa 3-4 KB compressi per Paese

    def test_ultimo_anno_effettivo_mai_oltre_l_ultimo_dato(self):
        d = paesi.dati_paese("LKA", self.imf, self.bm, self.catalogo)
        for chiave, (anno, _) in d["ultimo"].items():
            self.assertLessEqual(anno, d["finale"][chiave])


if __name__ == "__main__":
    unittest.main()


class TestContenutoPagina(unittest.TestCase):
    def setUp(self):
        self.catalogo = catalogo_vero()
        self.note = yaml.safe_load((RADICE / "contenuti" / "note.yaml").read_text(encoding="utf-8"))

    def test_contenuto_vero(self):
        c = paesi.carica_contenuto(RADICE / "contenuti" / "paese.yaml", self.catalogo, self.note)
        usati = {i for s in c["sezioni"] for g in s["grafici"] for i in g["serie"] + g.get("tooltip_extra", [])}
        usati |= set(c["outlook"]["indicatori"]) | {k["id"] for k in c["numeri_chiave"]}
        # Ogni indicatore del catalogo è usato dalla pagina (o è la sua alternativa della Banca Mondiale per i Paesi senza FMI)
        non_usati = {i.id for i in self.catalogo} - usati - set(paesi.SOSTITUTI_BM.values()) - {"corruption_score_low", "corruption_score_high"}
        self.assertEqual(non_usati, set())
        self.assertEqual(len(c["numeri_chiave"]), 7)
        for s in c["sezioni"]:
            for g in s["grafici"]:
                self.assertTrue(g["come_leggerlo"].strip(), g["id"])

    def test_righe_senza_valori_correnti(self):
        """Le righe "How to read it" non citano classifiche né valori di anni recenti: il WEO di ottobre li cambierebbe."""
        c = paesi.carica_contenuto(RADICE / "contenuti" / "paese.yaml", self.catalogo, self.note)
        testi = [g["come_leggerlo"] for s in c["sezioni"] for g in s["grafici"]] + [c["outlook"]["come_leggerlo"]]
        import re
        from datetime import date
        limite = date.today().year - 1       # anni chiusi da almeno due anni: nessun anno dall'anno scorso in poi (nel 2026: niente 2025 né dopo)
        for testo in testi:
            anni = [int(a) for a in re.findall(r"\b(19\d\d|20\d\d)\b", testo)]
            self.assertTrue(all(a < limite for a in anni), f"anno recente (>= {limite}) in: {testo}")
            self.assertNotRegex(testo.lower(), r"\b(th|nd|rd|st) of \d+|ranks?\b|ranking of", testo)
        anni_citati = sorted({a for t in testi for a in re.findall(r"\b(19\d\d|20\d\d)\b", t)})
        self.assertEqual(anni_citati, ["2020", "2021", "2022", "2024"])                      # Italia 2020-21, Italia 2022, Grecia 2024

    def test_errori_di_contenuto(self):
        with tempfile.TemporaryDirectory() as cartella:
            base = yaml.safe_load((RADICE / "contenuti" / "paese.yaml").read_text(encoding="utf-8"))

            def prova(modifica):
                copia = json.loads(json.dumps(base))
                modifica(copia)
                file = Path(cartella) / "p.yaml"
                file.write_text(yaml.safe_dump(copia, allow_unicode=True), encoding="utf-8")
                with self.assertRaises(ValueError):
                    paesi.carica_contenuto(file, self.catalogo, self.note)

            prova(lambda c: c["sezioni"][0]["grafici"][0].update(serie=["non_esiste"]))
            prova(lambda c: c["sezioni"][0]["grafici"][0].update(forma="torta"))
            prova(lambda c: c["sezioni"][0]["grafici"][0].update(come_leggerlo=""))
            prova(lambda c: c["sezioni"][0]["grafici"][0].update(note=["nota-inesistente"]))
            prova(lambda c: c["sezioni"][0]["grafici"].append(dict(c["sezioni"][0]["grafici"][0])))            # id ripetuto
            prova(lambda c: c.update(numeri_chiave=[{"id": "non_esiste", "nome": "x"}]))


class TestNomiDeiPaesi(unittest.TestCase):
    """Regola dei nomi (CLAUDE.md): nomi brevi in inglese; il nome originale della fonte resta in config accanto a quello mostrato."""

    @classmethod
    def setUpClass(cls):
        cls.bm = annuali.leggi_snapshot(RADICE, "wb")
        cls.imf = annuali.leggi_snapshot(RADICE, "imf")
        if cls.bm is None or cls.imf is None:
            raise unittest.SkipTest("snapshot non presente")
        cls.config = yaml.safe_load((RADICE / "config.yaml").read_text(encoding="utf-8"))
        cls.nomi_wb = dict(zip(cls.bm.paesi["paese"], cls.bm.paesi["nome"]))

    def test_il_nome_originale_e_sempre_quello_della_fonte(self):
        for codice, voce in self.config["nomi_paesi"].items():
            self.assertEqual(voce["nome_fonte"], self.nomi_wb[codice], f"{codice}: il nome originale in config non è più quello della Banca Mondiale")
            self.assertNotEqual(voce["nome"], voce["nome_fonte"], f"{codice}: se il nome non cambia non serve la voce")
        for chiave, voce in self.config["paesi"].items():
            if voce.get("nome_fonte"):
                self.assertEqual(voce["nome_fonte"], self.nomi_wb[voce["iso3"]], chiave)

    def test_nomi_brevi_senza_virgole(self):
        for p in paesi.elenco_paesi(self.imf, self.bm, self.config):
            if p["c"] in ("TWN", "XKX", "PSE"):
                continue                       # nome della fonte, senza interpretazioni
            self.assertNotIn(",", p["nome"], f"{p['c']}: nome da accorciare o da mettere in nomi_paesi: {p['nome']!r}")
            self.assertNotRegex(p["nome"], r"\bRep\.|\bFed\.|\bIslamic\b|\bSAR\b", p["c"])

    def test_nome_della_fonte_per_taiwan_kosovo_e_cisgiordania(self):
        per_codice = {p["c"]: p for p in paesi.elenco_paesi(self.imf, self.bm, self.config)}
        self.assertEqual(per_codice["TWN"]["nome"], "Taiwan Province of China")
        for codice in ("TWN", "XKX", "PSE"):
            self.assertEqual(per_codice[codice]["nome"], per_codice[codice]["nome_fonte"])
        self.assertEqual(per_codice["XKX"]["nome"], self.nomi_wb["XKX"])
        self.assertEqual(per_codice["KOR"]["nome_fonte"], "Korea, Rep.")
        self.assertEqual(per_codice["KOR"]["nome"], "South Korea")


def elenco_finto() -> list[dict]:
    return [
        {"c": "ITA", "nome": "Italy", "nome_fonte": "Italy", "alias": [], "regione": "Europe & Central Asia", "fmi": True, "bm": True},
        {"c": "JPN", "nome": "Japan", "nome_fonte": "Japan", "alias": [], "regione": "East Asia & Pacific", "fmi": True, "bm": True},
        {"c": "KOR", "nome": "South Korea", "nome_fonte": "Korea, Rep.", "alias": [], "regione": "East Asia & Pacific", "fmi": True, "bm": True},
        {"c": "TUR", "nome": "Turkiye", "nome_fonte": "Turkiye", "alias": ["Turkey", "Türkiye"], "regione": "Europe & Central Asia", "fmi": True, "bm": True},
        {"c": "USA", "nome": "United States", "nome_fonte": "United States", "alias": ["US"], "regione": "North America", "fmi": True, "bm": True},
        {"c": "CUW", "nome": "Curacao", "nome_fonte": "Curacao", "alias": ["Curaçao"], "regione": "Latin America & Caribbean", "fmi": False, "bm": True},
    ]


ULTIMI_FINTI = {"gdp_growth": {"ITA": [0.54, 2025], "USA": [2.117, 2025], "JPN": [-0.04, 2024], "CUW": [5.027, 2024]},
                "inflation_average": {"ITA": [1.6, 2025], "USA": [2.7, 2025], "TUR": [34.949, 2025]}}


def riquadri_finti(config: dict | None = None, codici: set[str] | None = None) -> dict:
    config = config or config_finta()
    config["hub_economies"] = {"in_evidenza": ["us", "ea", "it", "jp"], "pagine_in_evidenza": ["economies/compare"],
                               "regioni": ["North America", "Latin America & Caribbean", "Europe & Central Asia", "East Asia & Pacific"]}
    config["pagine"].append({"id": "economies/compare", "nome": "Compare", "stato": "in-arrivo"})
    return paesi.riquadri_paesi(elenco_finto(), ULTIMI_FINTI, config, "economies", codici if codici is not None else {p["c"] for p in elenco_finto()})


class TestRiquadriPaesi(unittest.TestCase):
    def test_ogni_paese_compare_una_volta_nelle_regioni_in_ordine_geografico(self):
        r = riquadri_finti()
        self.assertEqual([g["nome"] for g in r["regioni"]], ["North America", "Latin America & Caribbean", "Europe & Central Asia", "East Asia & Pacific"])
        codici = [t["c"] for g in r["regioni"] for t in g["paesi"]]
        self.assertEqual(sorted(codici), sorted(p["c"] for p in elenco_finto()))
        self.assertEqual(r["n_paesi"], 6)
        asia = next(g for g in r["regioni"] if g["nome"] == "East Asia & Pacific")
        self.assertEqual([t["nome"] for t in asia["paesi"]], ["Japan", "South Korea"])           # alfabetico dentro la regione

    def test_regione_non_elencata_in_fondo(self):
        config = config_finta()
        r = paesi.riquadri_paesi(elenco_finto(), ULTIMI_FINTI, {**config, "hub_economies": {"regioni": ["North America"]}}, "economies", {"USA"})
        self.assertEqual(r["regioni"][0]["nome"], "North America")
        self.assertEqual(len(r["regioni"]), 4)

    def test_valori_con_anno_e_trattino_quando_manca_il_dato(self):
        r = riquadri_finti()
        per_codice = {t["c"]: t for g in r["regioni"] for t in g["paesi"]}
        self.assertEqual(per_codice["ITA"]["crescita"], {"testo": "0.5%", "anno": 2025})
        self.assertEqual(per_codice["USA"]["inflazione"], {"testo": "2.7%", "anno": 2025})
        self.assertEqual(per_codice["TUR"]["inflazione"], {"testo": "34.9%", "anno": 2025})
        self.assertIsNone(per_codice["TUR"]["crescita"])                                          # mai un valore inventato
        self.assertEqual(per_codice["JPN"]["crescita"]["testo"], "0.0%")                          # niente "-0.0%"

    def test_link_pagina_di_livello_a_solo_se_completa(self):
        incompleta = {t["c"]: t["href"] for t in riquadri_finti(config_finta(completa_usa=False))["in_evidenza"] if t["c"]}
        self.assertEqual(incompleta["USA"], "country.html?c=USA")
        self.assertEqual(incompleta["ITA"], "country.html?c=ITA")          # pagina italiana in-arrivo: mai un link alla pagina vuota
        regioni = riquadri_finti(config_finta(completa_usa=True))["regioni"]
        usa = next(t for g in regioni for t in g["paesi"] if t["c"] == "USA")
        self.assertEqual(usa["href"], "usa/")                               # stessa regola nelle regioni e in "Featured"
        self.assertEqual(next(t for g in regioni for t in g["paesi"] if t["c"] == "KOR")["href"], "country.html?c=KOR")
        completa = {t["c"]: t["href"] for t in riquadri_finti(config_finta(completa_usa=True))["in_evidenza"] if t["c"]}
        self.assertEqual(completa["USA"], "usa/")

    def test_paese_senza_dati_non_e_un_link(self):
        r = riquadri_finti(codici={"USA"})
        per_codice = {t["c"]: t for g in r["regioni"] for t in g["paesi"]}
        self.assertEqual(per_codice["USA"]["href"], "country.html?c=USA")
        self.assertIsNone(per_codice["ITA"]["href"])

    def test_in_evidenza_nell_ordine_del_config_con_schede_coming_soon(self):
        r = riquadri_finti()
        self.assertEqual([t["nome"] for t in r["in_evidenza"]], ["United States", "Euro area", "Italy", "Japan", "Compare"])
        euro, confronto = r["in_evidenza"][1], r["in_evidenza"][4]
        for scheda in (euro, confronto):
            self.assertIsNone(scheda["href"])
            self.assertEqual(scheda["etichetta"], "coming soon")
            self.assertTrue(scheda["senza_numeri"])

    def test_chiave_dell_in_evidenza_sconosciuta_da_errore(self):
        config = config_finta()
        config["hub_economies"] = {"in_evidenza": ["xx"]}
        with self.assertRaises(ValueError):
            paesi.riquadri_paesi(elenco_finto(), ULTIMI_FINTI, config, "economies", set())


class TestRicercaSenzaAccentiENomiAlternativi(unittest.TestCase):
    def test_normalizzazione(self):
        self.assertEqual(paesi.chiave_ricerca("Curaçao"), "curacao")
        self.assertEqual(paesi.chiave_ricerca("  São Tomé "), "sao tome")
        self.assertEqual(paesi.chiave_ricerca("Türkiye"), "turkiye")

    def test_chiavi_senza_duplicati(self):
        tur = next(p for p in elenco_finto() if p["c"] == "TUR")
        self.assertEqual(paesi.chiavi_paese(tur), "tur|turkiye|turkey")

    def test_ricerca_per_nome_originale_e_per_alias(self):
        per_codice = {p["c"]: paesi.chiavi_paese(p) for p in elenco_finto()}
        for testo, codice in [("Korea, Rep.", "KOR"), ("turkey", "TUR"), ("Türkiye", "TUR"), ("Curaçao", "CUW"), ("curacao", "CUW"), ("us", "USA"), ("jpn", "JPN")]:
            self.assertIn(paesi.chiave_ricerca(testo), per_codice[codice], testo)


class TestNomiAlternativiVeri(unittest.TestCase):
    """Ogni nome alternativo di config.yaml trova il suo Paese (la ricerca fa `chiavi.includes(testo normalizzato)`, come in static/elenco-paesi.js)."""

    @classmethod
    def setUpClass(cls):
        bm = annuali.leggi_snapshot(RADICE, "wb")
        imf = annuali.leggi_snapshot(RADICE, "imf")
        if bm is None or imf is None:
            raise unittest.SkipTest("snapshot non presente")
        cls.config = yaml.safe_load((RADICE / "config.yaml").read_text(encoding="utf-8"))
        cls.elenco = paesi.elenco_paesi(imf, bm, cls.config)
        cls.chiavi = {p["c"]: paesi.chiavi_paese(p) for p in cls.elenco}

    def test_i_nomi_richiesti_dall_utente(self):
        for testo, codice in [("Turkey", "TUR"), ("Türkiye", "TUR"), ("Ivory Coast", "CIV"), ("Czech Republic", "CZE"), ("Burma", "MMR"), ("Holland", "NLD"),
                              ("Curaçao", "CUW"), ("Curacao", "CUW"), ("Korea, Rep.", "KOR")]:
            trovati = [c for c, chiavi in self.chiavi.items() if paesi.chiave_ricerca(testo) in chiavi]
            self.assertIn(codice, trovati, testo)

    def test_ogni_alias_del_config_trova_il_suo_paese(self):
        for codice, nomi in self.config["nomi_alternativi"].items():
            self.assertIn(codice, self.chiavi, f"{codice}: Paese non presente nei dati")
            for nome in nomi:
                trovati = [c for c, chiavi in self.chiavi.items() if paesi.chiave_ricerca(nome) in chiavi]
                self.assertIn(codice, trovati, f"{nome!r} non trova {codice}")

    def test_ogni_regione_dei_dati_e_nell_ordine_del_config(self):
        elencate = set(self.config["hub_economies"]["regioni"])
        usate = {p["regione"] for p in self.elenco}
        self.assertEqual(usate - elencate, set(), "regione nuova nei dati: aggiungerla a hub_economies.regioni")
        self.assertEqual(elencate - usate, set(), "regione in config che non ha Paesi")

    def test_riquadri_veri_senza_doppioni(self):
        codici = {p["c"] for p in self.elenco}
        r = paesi.riquadri_paesi(self.elenco, {}, self.config, "economies", codici)
        elencati = [t["c"] for g in r["regioni"] for t in g["paesi"]]
        self.assertEqual(len(elencati), len(set(elencati)))
        self.assertEqual(set(elencati), codici)
        self.assertEqual([t["nome"] for t in r["in_evidenza"]], ["United States", "Euro area", "Italy", "United Kingdom", "China", "Japan", "Compare"])


class TestStessoComponente(unittest.TestCase):
    def test_hub_e_pagina_del_paese_usano_lo_stesso_macro(self):
        for modello in ("hub.html.j2", "paese.html.j2"):
            testo = (RADICE / "templates" / modello).read_text(encoding="utf-8")
            self.assertIn("ricerca_paesi(riquadri)", testo, modello)
            self.assertIn("elenco-paesi.js", testo, modello)
        self.assertIn("ElencoPaesi.cerca", (RADICE / "static" / "paese.js").read_text(encoding="utf-8"))   # il selettore a tendina usa la stessa ricerca
