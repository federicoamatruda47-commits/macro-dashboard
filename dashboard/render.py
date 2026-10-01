"""Costruzione del sito statico: prende serie e grafici e scrive la cartella site/."""

import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs_version

from .data import NOMI_FONTI, OPERAZIONI, PERIODI_PERFORMANCE, Serie, tipo_variazione, trova_serie, variazioni
from .regions import REGIONI, Grafico

FUSO_ORARIO = ZoneInfo("Europe/Rome")


# ---------------------------------------------------------------------
# Formattazione dei numeri "all'italiana" (virgola decimale)
# ---------------------------------------------------------------------

def numero(valore: float, decimali: int = 2, segno: bool = False) -> str:
    """Esempio: numero(1234.5, 1) -> '1.234,5'; con segno=True -> '+1.234,5'."""
    testo = f"{valore:+,.{decimali}f}" if segno else f"{valore:,.{decimali}f}"
    testo = testo.replace(",", "§").replace(".", ",").replace("§", ".")
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
    decimali = 0 if tipo == "pb" else 1
    arrotondato = round(valore, decimali) + 0.0  # "+ 0.0" trasforma −0,0 in 0,0
    # Niente segno se la variazione arrotondata è zero (evita "−0,0")
    testo = numero(arrotondato, decimali, segno=arrotondato != 0)
    return f"{testo} {tipo}" if tipo in ("pb", "pp") else f"{testo}%"


def data_it(data: pd.Timestamp | None) -> str:
    return f"{data:%d/%m/%Y}" if data is not None else "—"


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
            data=data_it(s.ultima_data),
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
            valore=numero(s.ultimo_valore, s.decimali), unita=s.unita, data=data_it(s.ultima_data),
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
        "storico": grafico.storico,
        "periodo_iniziale": grafico.periodo_iniziale,
        "largo": grafico.largo,
        "alto": grafico.alto,
        "varianti": [{"id": i, "etichetta": e} for i, e in grafico.varianti],
        "json": _figura_json(grafico),
        "ultimi_dati": [{"nome": s.nome, "data": data_it(s.ultima_data), "ritardo": s.in_ritardo(oggi)}
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
        "frequenza": s.frequenza or "—", "dal": data_it(s.prima_data), "ultimo": data_it(s.ultima_data),
        "valore": (valore_con_unita(s.ultimo_valore, s.unita, s.decimali)
                   if s.ok and s.unita != "indicatore" else "—"),
        "ok": s.ok, "ritardo": s.in_ritardo(oggi), "errore": s.errore, "nota_fonte": s.nota_fonte,
    }


def _voce_ritardo(s: Serie, oggi: pd.Timestamp, nomi_regioni: dict[str, str]) -> dict:
    """Una riga dell'avviso 'dati non aggiornati'."""
    return {"id": s.id, "nome": s.nome, "regione": nomi_regioni.get(s.regione, s.regione),
            "data": data_it(s.ultima_data), "frequenza": s.frequenza,
            "giorni": s.giorni_senza_dati(oggi), "soglia": s.soglia_ritardo}


def prepara_contesto(config: dict, serie: dict[str, Serie]) -> dict:
    """Raccoglie tutto ciò che serve al modello HTML."""
    adesso = datetime.now(FUSO_ORARIO)
    oggi = pd.Timestamp(adesso.date())

    regioni = []
    for regione in config["regioni"]:
        serie_regione = [s for s in serie.values() if s.regione == regione["id"]]
        costruttore = REGIONI.get(regione["id"])
        attiva = regione.get("attiva", False) and costruttore is not None

        sezioni = []
        if attiva:
            for sezione in costruttore(serie, config):
                sezioni.append({
                    "id": sezione.id, "titolo": sezione.titolo, "descrizione": sezione.descrizione,
                    "grafici": [_dati_grafico(g, serie, oggi) for g in sezione.grafici],
                    "etichetta_performance": sezione.etichetta_performance,
                    "performance": [_riga_performance(trova_serie(serie, i), oggi)
                                    for i in sezione.tabella_performance],
                })

        regioni.append({
            "id": regione["id"], "nome": regione["nome"], "attiva": attiva, "sezioni": sezioni,
            "riepilogo": [_scheda_riepilogo(s, oggi) for s in serie_regione if s.riepilogo],
            "stato": [_riga_stato(s, oggi) for s in serie_regione],
        })

    nomi_regioni = {r["id"]: r["nome"] for r in config["regioni"]}
    return {
        "aggiornato": adesso.strftime("%d/%m/%Y alle %H:%M") + " (ora italiana)",
        "regioni": regioni,
        "errori": [{"id": s.id, "nome": s.nome, "errore": s.errore} for s in serie.values() if not s.ok],
        "in_ritardo": [_voce_ritardo(s, oggi, nomi_regioni) for s in serie.values() if s.in_ritardo(oggi)],
        "riserve": [{"id": s.id, "nome": s.nome, "nota": s.nota_fonte} for s in serie.values() if s.nota_fonte],
        "totale_serie": len(serie),
        "plotly_versione": get_plotlyjs_version(),
        "versione": adesso.strftime("%Y%m%d%H%M"),
    }


# ---------------------------------------------------------------------
# Scrittura dei file
# ---------------------------------------------------------------------

def genera_sito(config: dict, serie: dict[str, Serie], radice: Path) -> Path:
    """Scrive site/index.html e copia i file statici. Restituisce il percorso della pagina."""
    cartella_site = radice / "site"
    cartella_site.mkdir(exist_ok=True)

    ambiente = Environment(loader=FileSystemLoader(radice / "templates"),
                           autoescape=select_autoescape(["html", "j2"]),
                           trim_blocks=True, lstrip_blocks=True)
    html = ambiente.get_template("index.html.j2").render(**prepara_contesto(config, serie))

    pagina = cartella_site / "index.html"
    pagina.write_text(html, encoding="utf-8")

    # CSS e JavaScript
    for file in (radice / "static").iterdir():
        shutil.copy2(file, cartella_site / file.name)
    # Dice a GitHub Pages di pubblicare i file così come sono (senza Jekyll)
    (cartella_site / ".nojekyll").touch()
    return pagina
