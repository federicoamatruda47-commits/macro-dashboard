"""Rete di sicurezza della ristrutturazione: nessun grafico e nessuna serie deve andare perso.

Uso (dalla cartella del progetto, con l'ambiente virtuale attivo):
    python tools/inventario.py controlla   # confronta il sito attuale con la baseline (da lanciare a ogni step)
    python tools/inventario.py salva       # riscrive la baseline: SOLO allo step 0, sul sito di partenza
    python tools/inventario.py sito        # dopo `python build.py`: controlla le pagine HTML vere in site/ (e ne misura il peso)

Non scarica nulla: costruisce i grafici con un dizionario di serie vuoto (i grafici esistono comunque, con l'avviso
"non disponibile"), quindi gira in pochi secondi e senza chiave API.

Cosa controlla:
  1. nessun id di grafico compare due volte sul sito ("nulla è doppio");
  2. ogni grafico della baseline c'è ancora, oppure docs/mappa-grafici.yaml dice (esito: merged) in quale grafico
     sono finite le sue serie, e quel grafico le contiene davvero ("nulla è perso");
  3. ogni serie di config.yaml c'è ancora (salvo quelle elencate in serie_rimosse);
  4. ogni serie che prima compariva in un grafico o in una tabella di performance compare ancora in almeno uno;
  5. la mappa e la baseline parlano degli stessi grafici.

Dallo step 1 in poi cambia solo `raccogli()`: i grafici si leggono dal registro delle pagine invece che dalle regioni.
"""

import json
import re
import sys
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from dashboard.data import carica_config  # noqa: E402
from dashboard.mercati import PAGINE  # noqa: E402
from dashboard.regions import REGIONI  # noqa: E402

BASELINE = RADICE / "docs" / "inventario-baseline.json"
MAPPA = RADICE / "docs" / "mappa-grafici.yaml"


def raccogli(config: dict) -> dict:
    """Fotografia del sito di adesso: grafici, tabelle di performance, serie di config.yaml e serie usate."""
    grafici, tabelle = [], []
    for id_regione, costruttore in {**REGIONI, **PAGINE}.items():
        for sezione in costruttore({}, config):
            for g in sezione.grafici:
                grafici.append({"id": g.id, "pagina": id_regione, "titolo": g.titolo, "serie_ids": list(g.serie_ids)})
            if sezione.tabella_performance:
                tabelle.append({"pagina": id_regione, "sezione": sezione.id, "serie_ids": list(sezione.tabella_performance)})

    componenti = {s["id"]: s.get("componenti") or [] for s in config["serie"]}

    def con_componenti(ids):
        """Una serie calcolata usa anche le sue componenti (a cascata)."""
        trovate, da_vedere = set(), list(ids)
        while da_vedere:
            i = da_vedere.pop()
            if i not in trovate:
                trovate.add(i)
                da_vedere += componenti.get(i, [])
        return trovate

    usate = set()
    for g in grafici:
        usate |= con_componenti(g["serie_ids"])
    for t in tabelle:
        usate |= con_componenti(t["serie_ids"])
    # USREC non è in nessun grafico come linea: serve a disegnare le bande di recessione NBER
    usate |= {"USREC"} & set(componenti)
    return {"grafici": grafici, "tabelle": tabelle,
            "serie_config": sorted(componenti), "serie_usate": sorted(usate)}


def confronta(baseline: dict, corrente: dict, mappa: dict) -> list[str]:
    """Restituisce l'elenco dei problemi (vuoto = tutto a posto)."""
    problemi = []
    attuali = {}
    for g in corrente["grafici"]:
        if g["id"] in attuali:
            problemi.append(f"Grafico doppio: {g['id']} (pagine {attuali[g['id']]['pagina']} e {g['pagina']})")
        attuali[g["id"]] = g

    voci = mappa.get("grafici", {})
    vecchi = {g["id"]: g for g in baseline["grafici"]}
    for id_vecchio in sorted(set(vecchi) ^ set(voci)):
        problemi.append(f"Mappa e baseline non coincidono su {id_vecchio}: "
                        + ("manca nella mappa" if id_vecchio in vecchi else "non è nella baseline"))

    for id_vecchio, vecchio in vecchi.items():
        if id_vecchio in attuali:
            continue
        voce = voci.get(id_vecchio, {})
        if voce.get("esito") != "merged":
            problemi.append(f"Grafico perso: {id_vecchio} ({vecchio['titolo']}) non c'è più e la mappa non lo dà per assorbito")
            continue
        destinazione = attuali.get(voce.get("in"))
        if destinazione is None:
            problemi.append(f"Grafico perso: {id_vecchio} doveva finire in '{voce.get('in')}', che non esiste")
            continue
        mancanti = sorted(set(vecchio["serie_ids"]) - set(destinazione["serie_ids"]))
        if mancanti:
            problemi.append(f"Serie perse: {id_vecchio} → {destinazione['id']} non contiene {mancanti}")

    rimosse = set(mappa.get("serie_rimosse") or [])
    for i in sorted(set(baseline["serie_config"]) - set(corrente["serie_config"]) - rimosse):
        problemi.append(f"Serie tolta da config.yaml senza essere in serie_rimosse: {i}")
    for i in sorted(set(baseline["serie_usate"]) - set(corrente["serie_usate"]) - rimosse):
        problemi.append(f"Serie che non compare più in nessun grafico o tabella: {i}")
    return problemi


def controlla_sito(baseline: dict, mappa: dict) -> int:
    """Guarda le pagine HTML generate: ogni grafico (anche "non disponibile") ha un <article id="chart-<id>">."""
    trovati: dict[str, list[str]] = {}
    pagine = sorted((RADICE / "site").rglob("index.html"))
    for pagina in pagine:
        html = pagina.read_text(encoding="utf-8")
        nome = pagina.relative_to(RADICE / "site").parent.as_posix().lstrip(".")
        print(f"  {nome or '(home)':<14} {pagina.stat().st_size / 1e6:6.2f} MB  "
              f"{len(re.findall(r'<article class=\"scheda-grafico', html)):3d} grafici")
        for id_grafico in re.findall(r'<article class="scheda-grafico[^"]*" id="chart-([^"]+)"', html):
            trovati.setdefault(id_grafico, []).append(nome)
    problemi = []
    for id_grafico, dove in sorted(trovati.items()):
        if len(dove) > 1:
            problemi.append(f"Grafico doppio nel sito: {id_grafico} in {dove}")
    attesi = {g["id"] for g in baseline["grafici"]}
    for id_grafico in sorted(attesi - set(trovati)):
        if mappa["grafici"][id_grafico].get("esito") != "merged":
            problemi.append(f"Grafico mancante nel sito: {id_grafico}")
    for id_grafico in sorted(set(trovati) - attesi - set(mappa.get("nuovi", {}))):
        problemi.append(f"Grafico nel sito che né la baseline né la mappa conoscono: {id_grafico}")
    totale = sum(len(v) for v in trovati.values())
    print(f"Grafici nel sito: {totale} ({len(pagine)} pagine); baseline: {len(attesi)}")
    for p in problemi:
        print("✗", p)
    print("OK: il sito contiene tutti i grafici." if not problemi else f"{len(problemi)} problema/i.")
    return 1 if problemi else 0


def main() -> int:
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    if comando not in ("salva", "controlla", "sito"):
        print(__doc__)
        return 2
    config = carica_config(RADICE / "config.yaml")
    corrente = raccogli(config)

    if comando == "salva":
        sito = RADICE / "site" / "index.html"
        corrente["html_byte_vecchio_sito"] = sito.stat().st_size if sito.exists() else None
        BASELINE.write_text(json.dumps(corrente, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Baseline salvata: {len(corrente['grafici'])} grafici, {len(corrente['tabelle'])} tabelle di performance, "
              f"{len(corrente['serie_config'])} serie in config ({len(corrente['serie_usate'])} usate) → {BASELINE.name}")
        return 0

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    mappa = yaml.safe_load(MAPPA.read_text(encoding="utf-8"))
    if comando == "sito":
        return controlla_sito(baseline, mappa)
    problemi = confronta(baseline, corrente, mappa)
    print(f"Grafici: {len(corrente['grafici'])} oggi, {len(baseline['grafici'])} nella baseline · "
          f"serie in config: {len(corrente['serie_config'])}/{len(baseline['serie_config'])}")
    for p in problemi:
        print("✗", p)
    print("OK: nulla è perso e nulla è doppio." if not problemi else f"{len(problemi)} problema/i.")
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
