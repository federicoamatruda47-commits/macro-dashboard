"""Costruzione del sito statico: prende serie e grafici e scrive la cartella site/."""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs_version

from .data import NOMI_FONTI, OPERAZIONI, PERIODI_PERFORMANCE, Serie, tipo_variazione, trova_serie, variazioni
from .pagine import HOME, costruisci_menu, percorso, radice
from .regions import REGIONI, Grafico

FUSO_ORARIO = ZoneInfo("Europe/Rome")


# Frequenze delle serie come si leggono sul sito (dentro il codice restano in italiano)
FREQUENZE = {"giornaliera": "daily", "settimanale": "weekly", "mensile": "monthly", "trimestrale": "quarterly"}


# ---------------------------------------------------------------------
# Formattazione dei numeri e delle date all'inglese (punto decimale, virgola per le migliaia)
# ---------------------------------------------------------------------

def numero(valore: float, decimali: int = 2, segno: bool = False) -> str:
    """Esempio: numero(1234.5, 1) -> '1,234.5'; con segno=True -> '+1,234.5'."""
    testo = f"{valore:+,.{decimali}f}" if segno else f"{valore:,.{decimali}f}"
    return testo.replace("-", "−")  # segno meno tipografico


def valore_con_unita(valore: float, unita: str, decimali: int = 2) -> str:
    return numero(valore, decimali) + ("%" if unita.startswith("%") else "")



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


def formatta_data(data: pd.Timestamp | None) -> str:
    """Es. '30 Sep 2026' (il giorno senza zero iniziale: %-d non esiste su Windows)."""
    return f"{data.day} {data:%b %Y}" if data is not None else "—"


# ---------------------------------------------------------------------
# Preparazione dei dati per il modello HTML
# ---------------------------------------------------------------------

def _scheda_riepilogo(s: Serie, oggi: pd.Timestamp) -> dict:
    """Dati di una scheda della sezione riassuntiva."""
    scheda = {"nome": s.nome, "id": s.id, "ok": s.ok, "errore": s.errore}
    # Le borse mostrano anche la variazione da inizio anno (come la tabella delle commodities)
    periodi = PERIODI_PERFORMANCE if s.categoria == "borsa" else None
    if s.ok:
        scheda.update(
            valore=valore_con_unita(s.ultimo_valore, s.unita, s.decimali),
            data=formatta_data(s.ultima_data),
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


def _dati_grafico(grafico: Grafico, serie: dict[str, Serie], oggi: pd.Timestamp) -> dict:
    usate = [trova_serie(serie, i) for i in grafico.serie_ids]
    return {
        "id": grafico.id,
        "titolo": grafico.titolo,
        "nota": grafico.nota,
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
    """Una riga della tabella 'Stato delle serie' in fondo alla pagina."""
    fonte = nome_fonte(s)
    if s.componenti:
        fonte += ": " + f" {OPERAZIONI.get(s.operazione, '−')} ".join(s.componenti)
        if s.fattore != 1:
            fonte += f" (× {numero(s.fattore, 0)})"
    return {
        "id": s.id, "nome": s.nome, "fonte": fonte, "unita": s.unita,
        "frequenza": FREQUENZE.get(s.frequenza, "—"), "dal": formatta_data(s.prima_data), "ultimo": formatta_data(s.ultima_data),
        "valore": (valore_con_unita(s.ultimo_valore, s.unita, s.decimali)
                   if s.ok and s.unita != "indicatore" else "—"),
        "ok": s.ok, "ritardo": s.in_ritardo(oggi), "errore": s.errore, "nota_fonte": s.nota_fonte,
    }


def _voce_ritardo(s: Serie, oggi: pd.Timestamp, nomi_regioni: dict[str, str]) -> dict:
    """Una riga dell'avviso 'dati non aggiornati'."""
    return {"id": s.id, "nome": s.nome, "regione": nomi_regioni.get(s.regione, s.regione),
            "data": formatta_data(s.ultima_data), "frequenza": FREQUENZE.get(s.frequenza),
            "giorni": s.giorni_senza_dati(oggi), "soglia": s.soglia_ritardo}


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

    return f":root {{ {blocco('chiaro')} }}\n@media (prefers-color-scheme: dark) {{ :root {{ {blocco('scuro')} }} }}"


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
        for i in sezione.tabella_performance:
            aggiungi(i)
    return list(trovate.values())


def prepara_contesto(config: dict, serie: dict[str, Serie]) -> dict:
    """Raccoglie tutto ciò che serve al modello HTML."""
    adesso = datetime.now(FUSO_ORARIO)
    oggi = pd.Timestamp(adesso.date())
    adesso_utc = adesso.astimezone(timezone.utc)

    nomi_regioni = {r["id"]: r["nome"] for r in config["regioni"]}
    regioni = []
    for regione in config["regioni"]:
        serie_regione = [s for s in serie.values() if s.regione == regione["id"]]
        costruttore = REGIONI.get(regione["id"])
        attiva = regione.get("attiva", False) and costruttore is not None

        sezioni = []
        usate: list[Serie] = []
        if attiva:
            oggetti = costruttore(serie, config)
            usate = _serie_usate(oggetti, serie)
            for sezione in oggetti:
                sezioni.append({
                    "id": sezione.id, "titolo": sezione.titolo, "descrizione": sezione.descrizione,
                    "grafici": [_dati_grafico(g, serie, oggi) for g in sezione.grafici],
                    "etichetta_performance": sezione.etichetta_performance,
                    "performance": [_riga_performance(trova_serie(serie, i), oggi)
                                    for i in sezione.tabella_performance],
                })

        regioni.append({
            "id": regione["id"], "nome": regione["nome"], "descrizione": regione.get("descrizione", ""),
            "attiva": attiva, "sezioni": sezioni,
            "riepilogo": [_scheda_riepilogo(s, oggi) for s in serie_regione if s.riepilogo],
            "stato": [_riga_stato(s, oggi) for s in serie_regione],
            "n_grafici": sum(len(sez["grafici"]) for sez in sezioni),
            "ha_grafici": any(g["json"] for sez in sezioni for g in sez["grafici"]),
            # Solo gli avvisi che riguardano le serie di questa pagina
            "totale_serie": len(usate),
            "errori": [{"id": s.id, "nome": s.nome, "errore": s.errore} for s in usate if not s.ok],
            "in_ritardo": [_voce_ritardo(s, oggi, nomi_regioni) for s in usate if s.in_ritardo(oggi)],
            "riserve": [{"id": s.id, "nome": s.nome, "nota": s.nota_fonte} for s in usate if s.nota_fonte],
        })

    return {
        "aggiornato": f"{adesso_utc.day} {adesso_utc:%b %Y}, {adesso_utc:%H:%M} UTC",
        "regioni": regioni,
        "errori": [{"id": s.id, "nome": s.nome, "errore": s.errore} for s in serie.values() if not s.ok],
        "in_ritardo": [_voce_ritardo(s, oggi, nomi_regioni) for s in serie.values() if s.in_ritardo(oggi)],
        "riserve": [{"id": s.id, "nome": s.nome, "nota": s.nota_fonte} for s in serie.values() if s.nota_fonte],
        "totale_serie": len(serie),
        "css_colori": css_colori(config),
        "plotly_versione": get_plotlyjs_version(),
        "versione": adesso.strftime("%Y%m%d%H%M"),
    }


# ---------------------------------------------------------------------
# Scrittura dei file
# ---------------------------------------------------------------------

def genera_sito(config: dict, serie: dict[str, Serie], radice_progetto: Path) -> Path:
    """Scrive site/index.html (home) e site/<regione>/index.html per ogni pagina, più CSS e JavaScript.

    Restituisce il percorso della home.
    """
    cartella_site = radice_progetto / "site"
    cartella_site.mkdir(exist_ok=True)

    ambiente = Environment(loader=FileSystemLoader(radice_progetto / "templates"),
                           autoescape=select_autoescape(["html", "j2"]),
                           trim_blocks=True, lstrip_blocks=True)
    contesto = prepara_contesto(config, serie)
    # Regola del sito: ogni grafico ha una riga "How to read it" (si scrive pagina per pagina durante la ristrutturazione)
    senza = [g["id"] for r in contesto["regioni"] for s in r["sezioni"] for g in s["grafici"] if not g["come_leggerlo"]]
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

    for regione in contesto["regioni"]:
        scrivi(regione["id"], "pagina.html.j2", r=regione)
    pagina = scrivi(HOME, "home.html.j2", **{k: contesto[k] for k in
                                             ("regioni", "errori", "in_ritardo", "riserve", "totale_serie")})

    # CSS e JavaScript
    for file in (radice_progetto / "static").iterdir():
        shutil.copy2(file, cartella_site / file.name)
    # Dice a GitHub Pages di pubblicare i file così come sono (senza Jekyll)
    (cartella_site / ".nojekyll").touch()
    return pagina
