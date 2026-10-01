"""Costruzione del sito statico: prende serie e grafici e scrive la cartella site/."""

import posixpath
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs_version

from . import annuali, metodo, movimenti
from .data import (FONTE_CALCOLATA, NOMI_FONTI, OPERAZIONI, PERIODI_PERFORMANCE, Serie, tipo_variazione, trova_serie,
                   variazioni)
from .fonti_url import url_indicatore, url_serie
from .pagine import HOME, PAGINA_METODO, PAGINA_SERIE, REINDIRIZZAMENTI, costruisci_menu, percorso, radice
from .economie import PAGINE as PAGINE_ECONOMIE
from .mercati import PAGINE as PAGINE_MERCATI
from .modello import Grafico
from .sparkline import sparkline_svg

FUSO_ORARIO = ZoneInfo("Europe/Rome")
# Costruttore delle sezioni di ogni pagina con contenuti (le pagine "in-arrivo" non ne hanno)
COSTRUTTORI = {**PAGINE_MERCATI, **PAGINE_ECONOMIE}


# Frequenze delle serie come si leggono sul sito (dentro il codice restano in italiano)
FREQUENZE = {"giornaliera": "daily", "settimanale": "weekly", "mensile": "monthly", "trimestrale": "quarterly",
             "semestrale": "semiannual", "annuale": "annual"}


# ---------------------------------------------------------------------
# Formattazione dei numeri e delle date all'inglese (punto decimale, virgola per le migliaia)
# ---------------------------------------------------------------------

def numero(valore: float, decimali: int = 2, segno: bool = False) -> str:
    """Esempio: numero(1234.5, 1) -> '1,234.5'; con segno=True -> '+1,234.5'."""
    testo = f"{valore:+,.{decimali}f}" if segno else f"{valore:,.{decimali}f}"
    return testo.replace("-", "−")  # segno meno tipografico


def valore_con_unita(valore: float, unita: str, decimali: int = 2) -> str:
    return numero(valore, decimali) + ("%" if unita.startswith("%") else "")



def carica_note(radice_progetto: Path) -> dict:
    """Legge contenuti/note.yaml (le note tecniche, con i testi in inglese)."""
    with open(radice_progetto / "contenuti" / "note.yaml", encoding="utf-8") as file:
        return yaml.safe_load(file)


def nome_fonte(s: Serie) -> str:
    """Es. 'BCE', 'Calcolata' oppure 'FRED (riserva)' se la fonte principale non ha risposto."""
    fonte = s.fonte_usata or s.fonte
    base, _, resto = fonte.partition(" ")
    return (NOMI_FONTI.get(base, base.upper()) + (" " + resto if resto else "")).strip()


def testo_variazione(valore: float | None, unita: str) -> str:
    if valore is None:
        return "—"
    tipo = tipo_variazione(unita)
    decimali = 0 if tipo == "bp" else 1
    arrotondato = round(valore, decimali) + 0.0  # "+ 0.0" trasforma −0,0 in 0,0
    # Niente segno se la variazione arrotondata è zero (evita "−0,0")
    testo = numero(arrotondato, decimali, segno=arrotondato != 0)
    return f"{testo} {tipo}" if tipo in ("bp", "pp") else f"{testo}%"


def etichetta_data(s: Serie) -> str:
    """La data di un dato come si legge sulla scheda: 'Aug 2026' per le serie mensili, '30 Sep 2026' per le altre."""
    if s.frequenza == "mensile":
        return f"{s.ultima_data:%b %Y}"
    if s.frequenza == "trimestrale":
        return f"Q{(s.ultima_data.month - 1) // 3 + 1} {s.ultima_data.year}"
    return formatta_data(s.ultima_data)


def formatta_data(data: pd.Timestamp | None) -> str:
    """Es. '30 Sep 2026' (il giorno senza zero iniziale: %-d non esiste su Windows)."""
    return f"{data.day} {data:%b %Y}" if data is not None else "—"


# ---------------------------------------------------------------------
# Preparazione dei dati per il modello HTML
# ---------------------------------------------------------------------

UNITA_SENZA_TESTO = ("%", "% y/y", "points", "index", "indicator")  # unità già chiare dal numero: non si scrivono sulla scheda


def _scheda_riepilogo(s: Serie, oggi: pd.Timestamp, ytd: bool = False) -> dict:
    """Dati di una scheda della sezione riassuntiva (con ytd=True anche la variazione da inizio anno)."""
    scheda = {"nome": s.nome, "id": s.id, "ok": s.ok, "errore": s.errore,
              "unita": "" if s.unita in UNITA_SENZA_TESTO else s.unita}
    # Le borse mostrano sempre anche la variazione da inizio anno (come la tabella delle commodities)
    periodi = PERIODI_PERFORMANCE if ytd or s.categoria == "borsa" else None
    if s.ok:
        scheda.update(
            valore=valore_con_unita(s.ultimo_valore, s.unita, s.decimali),
            data=etichetta_data(s),
            ritardo=s.in_ritardo(oggi),
            variazioni=[{"etichetta": etichetta, "testo": testo_variazione(v, s.unita)}
                        for etichetta, v in variazioni(s, periodi).items()],
        )
    return scheda


def _riga_performance(s: Serie, oggi: pd.Timestamp) -> dict:
    """Una riga della tabella di performance: ultimo prezzo e variazioni colorate."""
    riga = {"nome": s.nome, "id": s.id, "ok": s.ok, "errore": s.errore, "fonte": nome_fonte(s),
            "nota_fonte": s.nota_fonte}
    if s.ok:
        riga.update(
            valore=numero(s.ultimo_valore, s.decimali), unita=s.unita, data=formatta_data(s.ultima_data),
            ritardo=s.in_ritardo(oggi),
            # segno: serve al CSS per colorare in verde (rialzo) o rosso (ribasso)
            variazioni=[{"testo": testo_variazione(v, s.unita),
                         "segno": "" if v is None or round(v, 1) == 0 else ("pos" if v > 0 else "neg")}
                        for v in variazioni(s, PERIODI_PERFORMANCE).values()],
        )
    return riga


def _figura_json(grafico: Grafico) -> str | None:
    if grafico.figura is None:
        return None
    # "</" dentro un <script> chiuderebbe il tag in anticipo: lo rendiamo innocuo
    return grafico.figura.to_json().replace("</", "<\\/")


def _fonte_effettiva(s: Serie) -> tuple[str, str, bool]:
    """(fonte, id presso la fonte, True se è la riserva) dei dati che la serie mostra davvero."""
    if s.nota_fonte and s.riserva:
        return s.riserva["fonte"], s.riserva["id"], True
    return s.fonte, s.id, False


def _fonti_grafico(usate: list[Serie], serie: dict[str, Serie]) -> list[dict]:
    """Le fonti di un grafico per il piè di pagina: una voce per fonte, con il link alla prima serie di quella fonte.

    Le serie calcolate si scompongono nelle loro componenti; la riserva compare come "(fallback)".
    """
    gruppi: dict[str, dict] = {}

    def aggiungi(s: Serie) -> None:
        if not s.ok:
            return
        if s.fonte == FONTE_CALCOLATA:
            for componente in s.componenti:
                aggiungi(trova_serie(serie, componente))
            return
        fonte, id_serie, riserva = _fonte_effettiva(s)
        nome = NOMI_FONTI.get(fonte, fonte.upper()) + (" (fallback)" if riserva else "")
        gruppo = gruppi.setdefault(nome, {"nome": nome, "url": url_serie(fonte, id_serie), "n": 0})
        gruppo["n"] += 1

    for s in usate:
        aggiungi(s)
    return list(gruppi.values())


def _dati_grafico(grafico: Grafico, serie: dict[str, Serie], oggi: pd.Timestamp, note: dict) -> dict:
    usate = [trova_serie(serie, i) for i in grafico.serie_ids]
    ignote = [i for i in grafico.note if i not in note["note"]]
    if ignote:
        print(f"Warning: chart {grafico.id} uses notes missing from contenuti/note.yaml: {', '.join(ignote)}", file=sys.stderr)
    return {
        "id": grafico.id,
        "titolo": grafico.titolo,
        "note": [{"id": i, "titolo": note["note"][i]["titolo"]} for i in grafico.note if i in note["note"]],
        "fonti": _fonti_grafico(usate, serie),
        "come_leggerlo": grafico.come_leggerlo,
        "storico": grafico.storico,
        "periodo_iniziale": grafico.periodo_iniziale,
        "largo": grafico.largo,
        "alto": grafico.alto,
        "varianti": [{"id": i, "etichetta": e} for i, e in grafico.varianti],
        "json": _figura_json(grafico),
        "ultimi_dati": [{"nome": s.nome, "data": formatta_data(s.ultima_data), "ritardo": s.in_ritardo(oggi)}
                        for s in usate if s.ok],
        "mancanti": [{"nome": s.nome, "id": s.id, "errore": s.errore} for s in usate if not s.ok],
    }


def _riga_stato(s: Serie, oggi: pd.Timestamp) -> dict:
    """Una riga della tabella della pagina Series status."""
    fonte = nome_fonte(s)
    url = None if s.fonte == FONTE_CALCOLATA else url_serie(*_fonte_effettiva(s)[:2])
    if s.componenti:
        fonte += ": " + f" {OPERAZIONI.get(s.operazione, '−')} ".join(s.componenti)
        if s.fattore != 1:
            fonte += f" (× {numero(s.fattore, 0)})"
    return {
        "id": s.id, "nome": s.nome, "fonte": fonte, "url": url, "unita": s.unita,
        "frequenza": FREQUENZE.get(s.frequenza, "—"), "dal": formatta_data(s.prima_data), "ultimo": formatta_data(s.ultima_data),
        "valore": (valore_con_unita(s.ultimo_valore, s.unita, s.decimali)
                   if s.ok and s.unita != "indicatore" else "—"),
        "ok": s.ok, "ritardo": s.in_ritardo(oggi), "errore": s.errore, "nota_fonte": s.nota_fonte,
    }


def _voce_ritardo(s: Serie, oggi: pd.Timestamp, nomi_aree: dict[str, str]) -> dict:
    """Una riga dell'avviso 'dati non aggiornati'."""
    return {"id": s.id, "nome": s.nome, "area": nomi_aree.get(s.paese, s.paese),
            "data": formatta_data(s.ultima_data), "frequenza": FREQUENZE.get(s.frequenza),
            "giorni": s.giorni_senza_dati(oggi), "soglia": s.soglia_ritardo}


def _voce_ritardo_annuale(s: annuali.StatoSnapshot) -> dict:
    """Una riga dell'avviso 'dati non aggiornati' per uno snapshot annuale (WEO, WDI, WGI)."""
    return {"id": s.id.upper(), "nome": f"{s.nome} snapshot", "area": "Annual data", "data": f"{s.data.day} {s.data:%b %Y}",
            "frequenza": FREQUENZE[s.frequenza], "giorni": s.giorni, "soglia": s.soglia}


def _righe_indicatori(config: dict, snapshot: dict[str, annuali.Snapshot | None], stati: list[annuali.StatoSnapshot]) -> list[dict]:
    """Una riga per indicatore annuale del catalogo, per la pagina Series status (copertura, anni, ultimo anno effettivo, stato)."""
    stato_per_id = {s.id: s for s in stati}
    righe = []
    for fonte, istantanea in snapshot.items():
        catalogo = annuali.indicatori_di(annuali.carica_catalogo(config), fonte)
        copertura = {c["indicatore"].codice: c for c in annuali.copertura(istantanea, catalogo)} if istantanea else {}
        for ind in catalogo:
            c = copertura.get(ind.codice)
            id_stato = fonte if fonte == annuali.FONTE_IMF else ("wgi" if ind.sorgente_wb == 3 else "wdi")
            stato = stato_per_id[id_stato]
            presente = bool(c and c["n_paesi"])
            if presente and c["effettivo_a"] is not None:
                effettivo = str(c["effettivo_a"]) if c["effettivo_da"] == c["effettivo_a"] else f"{c['effettivo_da']}–{c['effettivo_a']}"
            else:
                effettivo = "—"
            righe.append({
                "nome": ind.nome, "codice": ind.codice, "url": url_indicatore(fonte, ind.codice),
                "fonte": annuali.FONTI_ANNUALI[fonte], "unita": ind.unita, "frequenza": FREQUENZE[annuali.FREQUENZA_FONTE[fonte]],
                "n_paesi": c["n_paesi"] if c else 0, "anni": f"{c['dal']}–{c['al']}" if presente else "—", "effettivo": effettivo,
                "edizione": stato.edizione or (f"{stato.data.day} {stato.data:%b %Y}" if stato.data else "—"),
                "presente": presente, "in_ritardo": stato.in_ritardo, "nota": ind.nota,
            })
    return righe


def css_colori(config: dict) -> str:
    """Le variabili CSS --c-<chiave> dei colori fissi (tema chiaro e scuro), lette da config.yaml.

    Sono scritte dentro ogni pagina: così i colori hanno UNA sola definizione (config.yaml) e li usano
    sia il CSS sia i grafici (app.js li legge dalle variabili).
    """
    colori = config["colori"]

    def valore(chiave: str, tema: str) -> str:
        voce = colori[chiave]
        return colori[voce["alias"]][tema] if "alias" in voce else voce[tema]

    def blocco(tema: str) -> str:
        return " ".join(f"--c-{chiave}: {valore(chiave, tema)};" for chiave in colori)

    scuro = blocco("scuro")
    return (f":root {{ {blocco('chiaro')} }}\n"
            f"@media (prefers-color-scheme: dark) {{ :root:not([data-theme=\"light\"]) {{ {scuro} }} }}\n"
            f":root[data-theme=\"dark\"] {{ {scuro} }}")


def _serie_usate(sezioni, serie: dict[str, Serie]) -> list[Serie]:
    """Le serie che una pagina usa davvero (grafici e tabelle, più le componenti delle serie calcolate).

    Serve a mostrare in ogni pagina solo gli avvisi che la riguardano.
    """
    trovate: dict[str, Serie] = {}

    def aggiungi(id_serie: str) -> None:
        s = trova_serie(serie, id_serie)
        if s.id in trovate:
            return
        trovate[s.id] = s
        for componente in s.componenti or []:
            aggiungi(componente)

    for sezione in sezioni:
        for grafico in sezione.grafici:
            for i in grafico.serie_ids:
                aggiungi(i)
        for i in sezione.serie_tabella():
            aggiungi(i)
    return list(trovate.values())


def _scheda_panoramica(voce: dict, serie: dict[str, Serie], oggi: pd.Timestamp, href_grafici: dict[str, str]) -> dict:
    """Una scheda dell'Overview: come quelle delle pagine, più il mini-grafico a un anno e il link al grafico."""
    s = trova_serie(serie, voce["serie"])
    scheda = _scheda_riepilogo(s, oggi)
    scheda["nome"] = voce["etichetta"]
    scheda["sparkline"] = sparkline_svg(s.dati, s.chiave_colore) if s.ok else ""
    scheda["href"] = href_grafici.get(voce["vai"])
    return scheda


def _righe_movimenti(classifica: movimenti.Classifica, serie: dict[str, Serie], usi_serie: dict[str, list[dict]]) -> dict:
    """Le righe di "What changed this week" pronte per il modello HTML."""
    ultima = max((s.ultima_data for s in serie.values() if s.ok and s.movimenti), default=None)
    righe = []
    for m in classifica.righe:
        usi = usi_serie.get(m.id, [])
        righe.append({
            "etichetta": m.etichetta,
            "movimento": testo_variazione(m.mossa, m.unita),
            "direzione": "up" if m.mossa > 0 else "down",
            "punteggio": f"{abs(m.punteggio):.1f}×",
            "barra": round(min(abs(m.punteggio) / 5, 1) * 100),          # lunghezza della barra: 5× = barra piena
            "data": formatta_data(m.data_ultimo) if ultima is not None and (ultima - m.data_ultimo).days > 3 else None,
            "href": usi[0]["href"] if usi else None,
        })
    return {"righe": righe, "n_controllate": classifica.n_controllate, "n_sopra_soglia": classifica.n_sopra_soglia,
            "soglia": f"{classifica.soglia:g}", "massimo": classifica.massimo,
            "settimana_al": formatta_data(ultima)}


def _con_componenti(ids, serie: dict[str, Serie]) -> set[str]:
    """Gli id dati più, a cascata, le componenti delle serie calcolate."""
    trovati: set[str] = set()
    da_vedere = list(ids)
    while da_vedere:
        i = da_vedere.pop()
        if i not in trovati:
            trovati.add(i)
            da_vedere += trova_serie(serie, i).componenti or []
    return trovati


def prepara_contesto(config: dict, serie: dict[str, Serie], note: dict, radice_progetto: Path | None = None) -> dict:
    """Raccoglie tutto ciò che serve al modello HTML."""
    adesso = datetime.now(FUSO_ORARIO)
    oggi = pd.Timestamp(adesso.date())
    adesso_utc = adesso.astimezone(timezone.utc)

    # Dati annuali per Paese (snapshot nel repository): solo controlli di stato, nessuna pagina li usa ancora
    snapshot = {f: annuali.leggi_snapshot(radice_progetto, f) if radice_progetto else None for f in (annuali.FONTE_IMF, annuali.FONTE_BM)}
    stati_annuali = annuali.stati_snapshot(snapshot[annuali.FONTE_IMF], snapshot[annuali.FONTE_BM], oggi.date())
    ritardo_annuali = [_voce_ritardo_annuale(s) for s in stati_annuali if s.in_ritardo]

    nomi_aree = {chiave: voce["nome"] for chiave, voce in config["colori"].items()}  # es. "us" -> United States
    usi_serie: dict[str, list[dict]] = {}   # id serie -> grafici e tabelle che la usano (per Series status)
    usi_note: dict[str, list[dict]] = {}    # id nota -> grafici che la richiamano (per Known limits)
    href_grafici: dict[str, str] = {}       # id grafico -> indirizzo (per i link dell'Overview)

    def costruisci_voce(voce: dict, costruttore, id_numeri_chiave: list[str], ytd: bool) -> dict:
        """Una pagina del sito con tutto ciò che serve al modello HTML."""
        id_pagina = voce["id"]
        slug = id_pagina.replace("/", "-")  # per gli id HTML delle sezioni (niente "/")
        attiva = voce.get("stato") == "attiva" and costruttore is not None

        sezioni = []
        usate: list[Serie] = []
        if attiva:
            oggetti = costruttore(serie, config)
            usate = _serie_usate(oggetti, serie)
            for sezione in oggetti:
                for g in sezione.grafici:
                    riferimento = {"pagina": voce["nome"], "href": f"{id_pagina}/#chart-{g.id}", "titolo": g.titolo}
                    href_grafici.setdefault(g.id, riferimento["href"])
                    for i in _con_componenti(g.serie_ids, serie):
                        usi_serie.setdefault(i, []).append(riferimento)
                    for i in g.note:
                        usi_note.setdefault(i, []).append(riferimento)
                for i in _con_componenti(sezione.serie_tabella(), serie):
                    usi_serie.setdefault(i, []).append({
                        "pagina": voce["nome"], "href": f"{id_pagina}/#{slug}-{sezione.id}",
                        "titolo": f"{sezione.titolo} (table)"})
                sezioni.append({
                    "id": sezione.id, "titolo": sezione.titolo, "descrizione": sezione.descrizione,
                    "grafici": [_dati_grafico(g, serie, oggi, note) for g in sezione.grafici],
                    "etichetta_performance": sezione.etichetta_performance,
                    "performance": ([_riga_performance(trova_serie(serie, i), oggi) for i in sezione.tabella_performance]
                                    + [{**_riga_performance(trova_serie(serie, i), oggi), "gruppo": titolo}
                                       for titolo, ids in sezione.gruppi_performance for i in ids]),
                })
        schede = [trova_serie(serie, i) for i in id_numeri_chiave]
        return {
            "id": id_pagina, "slug": slug, "href": id_pagina + "/", "nome": voce["nome"],
            "descrizione": voce.get("descrizione", ""),
            "attiva": attiva, "sezioni": sezioni,
            "ancore": [{"id": f"{slug}-{sez['id']}", "titolo": sez["titolo"]} for sez in sezioni],
            "riepilogo": [_scheda_riepilogo(s, oggi, ytd) for s in schede],
            "n_grafici": sum(len(sez["grafici"]) for sez in sezioni),
            "ha_grafici": any(g["json"] for sez in sezioni for g in sez["grafici"]),
            # Solo gli avvisi che riguardano le serie di questa pagina
            "totale_serie": len(usate),
            "errori": [{"id": s.id, "nome": s.nome, "errore": s.errore} for s in usate if not s.ok],
            "in_ritardo": [_voce_ritardo(s, oggi, nomi_aree) for s in usate if s.in_ritardo(oggi)],
            "riserve": [{"id": s.id, "nome": s.nome, "nota": s.nota_fonte} for s in usate if s.nota_fonte],
        }

    # Le pagine "attive" e "in-arrivo" hanno un file; quelle "dopo" sono solo schede nell'hub
    pagine = [costruisci_voce(p, COSTRUTTORI.get(p["id"]), p.get("numeri_chiave", []), bool(p.get("ytd")))
              for p in config.get("pagine", []) if p.get("tipo") != "hub" and p.get("stato") in ("attiva", "in-arrivo")]
    # Pagina precedente e successiva dentro lo stesso gruppo (nell'ordine di config.yaml)
    voci_pagine = {p["id"]: p for p in config.get("pagine", [])}
    for i, pagina in enumerate(pagine):
        gruppo = voci_pagine[pagina["id"]].get("gruppo")
        fratelli = [q for q in pagine if voci_pagine[q["id"]].get("gruppo") == gruppo]
        posizione = fratelli.index(pagina)
        for chiave, indice in (("precedente", posizione - 1), ("successivo", posizione + 1)):
            if 0 <= indice < len(fratelli):
                vicina = fratelli[indice]
                pagina[chiave] = {"nome": vicina["nome"], "href": posixpath.relpath(vicina["id"], pagina["id"]) + "/"}

    stato = []
    for s in serie.values():
        riga = _riga_stato(s, oggi)
        riga["area"] = nomi_aree.get(s.paese, s.paese)
        riga["usi"] = usi_serie.get(s.id, [])
        stato.append(riga)
    standard, proprie = metodo.soglie_freschezza(config)
    classifica_movimenti = movimenti.classifica(serie, oggi)

    # Overview: numeri chiave, movimenti della settimana, schede verso le altre pagine
    esplora = [{"gruppo": "Markets", "nome": p["nome"], "descrizione": p.get("descrizione", ""), "href": p["id"] + "/"}
               for p in config.get("pagine", []) if p.get("gruppo") == "markets" and p.get("stato") == "attiva"]
    esplora += [{"gruppo": "More", "nome": "Economies", "href": "economies/",
                 "descrizione": "One page per economy. The US labour market is in; the others are coming."},
                {"gruppo": "More", "nome": "Sources & method", "href": "method/",
                 "descrizione": "Where the data comes from, how freshness is checked and the known limits."}]

    return {
        "stato": stato,
        "panoramica": [{"titolo": g["titolo"], "schede": [_scheda_panoramica(v, serie, oggi, href_grafici) for v in g["schede"]]}
                       for g in config.get("panoramica", [])],
        "movimenti": _righe_movimenti(classifica_movimenti, serie, usi_serie),
        "esplora": esplora,
        "metodo": {
            "fonti": metodo.descrivi_fonti(config), "soglie": standard, "soglie_proprie": proprie,
            "fallback": metodo.fallback_configurati(config, serie), "calcolate": metodo.serie_calcolate(config, serie),
            "regola_calcolate": metodo.REGOLA_CALCOLATE, "gruppi_note": metodo.raggruppa_note(note, usi_note),
            "movimenti": metodo.descrivi_movimenti(config, serie, classifica_movimenti),
            "annuali": metodo.snapshot_annuali(stati_annuali),
        },
        "indicatori_annuali": _righe_indicatori(config, snapshot, stati_annuali),
        "aggiornato": f"{adesso_utc.day} {adesso_utc:%b %Y}, {adesso_utc:%H:%M} UTC",
        "pagine": pagine,
        "errori": [{"id": s.id, "nome": s.nome, "errore": s.errore} for s in serie.values() if not s.ok],
        "in_ritardo": [_voce_ritardo(s, oggi, nomi_aree) for s in serie.values() if s.in_ritardo(oggi)] + ritardo_annuali,
        "riserve": [{"id": s.id, "nome": s.nome, "nota": s.nota_fonte} for s in serie.values() if s.nota_fonte],
        "totale_serie": len(serie),
        "css_colori": css_colori(config),
        "plotly_versione": get_plotlyjs_version(),
        "versione": adesso.strftime("%Y%m%d%H%M"),
    }


# ---------------------------------------------------------------------
# Scrittura dei file
# ---------------------------------------------------------------------

def scrivi_reindirizzamento(cartella_site: Path, vecchio: str, nuovo: str, ambiente: Environment) -> None:
    """Scrive una pagina minima nel vecchio indirizzo che porta al nuovo (i link già condivisi continuano a funzionare)."""
    html = ambiente.get_template("reindirizzamento.html.j2").render(
        destinazione=radice(vecchio) + percorso(nuovo), nome=nuovo)
    file = cartella_site / percorso(vecchio) / "index.html"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(html, encoding="utf-8")


def genera_sito(config: dict, serie: dict[str, Serie], radice_progetto: Path) -> Path:
    """Scrive site/index.html (home) e site/<id pagina>/index.html per ogni pagina, più CSS e JavaScript.

    Restituisce il percorso della home.
    """
    cartella_site = radice_progetto / "site"
    cartella_site.mkdir(exist_ok=True)

    ambiente = Environment(loader=FileSystemLoader(radice_progetto / "templates"),
                           autoescape=select_autoescape(["html", "j2"]),
                           trim_blocks=True, lstrip_blocks=True)
    contesto = prepara_contesto(config, serie, carica_note(radice_progetto), radice_progetto)
    # Regola del sito: ogni grafico ha una riga "How to read it" (si scrive pagina per pagina durante la ristrutturazione)
    senza = [g["id"] for r in contesto["pagine"] for s in r["sezioni"] for g in s["grafici"] if not g["come_leggerlo"]]
    if senza:
        print(f"Warning: {len(senza)} charts have no 'come_leggerlo' line (How to read it), e.g. {', '.join(senza[:4])}...")
    comune = {chiave: contesto[chiave]
              for chiave in ("aggiornato", "plotly_versione", "versione", "css_colori")}

    def scrivi(id_pagina: str, modello: str, **dati) -> Path:
        menu, sottomenu = costruisci_menu(config, id_pagina)
        html = ambiente.get_template(modello).render(
            **comune, **dati, id_pagina=id_pagina, radice=radice(id_pagina), menu=menu, sottomenu=sottomenu)
        file = cartella_site / percorso(id_pagina) / "index.html"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(html, encoding="utf-8")
        return file

    avvisi = {k: contesto[k] for k in ("errori", "in_ritardo", "riserve", "totale_serie")}
    for pagina_dati in contesto["pagine"]:
        scrivi(pagina_dati["id"], "pagina.html.j2", r=pagina_dati)
    for hub in [p for p in config.get("pagine", []) if p.get("tipo") == "hub"]:
        etichette = {"in-arrivo": "coming soon", "dopo": "later"}   # le pagine "attive" non hanno etichetta
        figlie = [{"nome": p["nome"], "descrizione": p.get("descrizione", ""), "etichetta": etichette.get(p.get("stato")),
                   "href": None if p.get("stato") == "dopo" else p["id"].rsplit("/", 1)[-1] + "/"}
                  for p in config["pagine"] if p.get("gruppo") == hub["id"]]
        scrivi(hub["id"], "hub.html.j2", pagina=hub, figlie=figlie, **avvisi)
    for vecchio, nuovo in REINDIRIZZAMENTI.items():
        scrivi_reindirizzamento(cartella_site, vecchio, nuovo, ambiente)
    scrivi(PAGINA_METODO, "metodo.html.j2", m=contesto["metodo"], **avvisi)
    scrivi(PAGINA_SERIE, "serie.html.j2", stato=contesto["stato"], indicatori=contesto["indicatori_annuali"], **avvisi)
    pagina = scrivi(HOME, "panoramica.html.j2", **{k: contesto[k] for k in ("panoramica", "movimenti", "esplora")}, **avvisi)

    # CSS e JavaScript
    for file in (radice_progetto / "static").iterdir():
        shutil.copy2(file, cartella_site / file.name)
    # Dice a GitHub Pages di pubblicare i file così come sono (senza Jekyll)
    (cartella_site / ".nojekyll").touch()
    return pagina
