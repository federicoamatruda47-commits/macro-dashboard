"""Contenuto delle pagine "Sources & method" e "Series status".

Qui stanno i testi fissi sulle fonti e le regole (in inglese, come il sito) e il calcolo delle parti "vive":
soglie di freschezza, fonti di riserva in uso, serie calcolate e note raggruppate.
Le note tecniche stanno in contenuti/note.yaml; render.py le passa già lette.
"""

from .data import FONTE_CALCOLATA, NOMI_FONTI, OPERAZIONI, SOGLIA_RITARDO_GIORNI, Serie
from .fonti_url import SITI_FONTI

# Come mostrare le frequenze (dentro il codice restano in italiano)
FREQUENZE = {"giornaliera": "daily", "settimanale": "weekly", "mensile": "monthly", "trimestrale": "quarterly"}

# Cosa si usa di ogni fonte e che tipo di accesso offre
DESCRIZIONI_FONTI = {
    "fred": ("US rates, inflation, credit spreads, VIX, dollar index, unemployment and recession dates; "
             "fallback series from the OECD and the IMF; the ICE BofA, Moody's, CBOE and NBER series published there.",
             "Official API (free key)."),
    "ecb": ("Euro-area policy rate, AAA yield curve, HICP inflation, EUR/USD and the 10-year yields used for the "
            "Italy, France and Germany spreads.", "Official API (no key)."),
    "bis": ("Policy rates and CPI inflation of the five economies in the cross-country comparisons.",
            "Official API (no key)."),
    "yahoo": ("Equity indices, ETFs, commodity futures and exchange rates.",
              "Unofficial (the yfinance library): it can change or block requests without notice, which is why "
              "many of its series have a fallback."),
    "mof": ("Daily Japanese government bond (JGB) yields.", "Official CSV files (no key)."),
    "statjp": ("Japan CPI by component (headline, core, core-core).",
               "DBnomics, a free aggregator of statistical agencies (no key)."),
    FONTE_CALCOLATA: ("Differences and ratios of other series (spreads, copper/gold, equity indices in USD).",
                      "Calculated here, only from inputs of the same source."),
}

REGOLA_CALCOLATE = (
    "A calculated series (a difference or a ratio of two others) is computed only if all its inputs come from the same "
    "main source. If even one input has switched to its fallback, the calculated series becomes \"unavailable\" with a "
    "warning that explains why: spot and futures prices, different sources or different units are never mixed "
    "(for example Brent spot from FRED minus WTI futures from Yahoo)."
)


def descrivi_fonti(config: dict) -> list[dict]:
    """Tabella delle fonti con il numero di serie che ne usano ogni una come fonte principale."""
    conteggio: dict[str, int] = {}
    for voce in config["serie"]:
        conteggio[voce["fonte"]] = conteggio.get(voce["fonte"], 0) + 1
    righe = []
    for chiave, nome in NOMI_FONTI.items():
        uso, accesso = DESCRIZIONI_FONTI[chiave]
        righe.append({"nome": nome, "uso": uso, "accesso": accesso, "url": SITI_FONTI.get(chiave),
                      "n_serie": conteggio.get(chiave, 0)})
    return righe


def soglie_freschezza(config: dict) -> tuple[list[dict], list[dict]]:
    """(soglie standard per frequenza, serie con una soglia propria e perché)."""
    standard = [{"frequenza": FREQUENZE[f], "giorni": g} for f, g in SOGLIA_RITARDO_GIORNI.items()]
    proprie = [{"nome": v["nome"], "id": v["id"], "giorni": v["soglia_giorni"]}
               for v in config["serie"] if v.get("soglia_giorni")]
    return standard, proprie


def fallback_configurati(config: dict, serie: dict[str, Serie]) -> list[dict]:
    """Tutte le serie con una fonte di riserva: quale è, se è in uso adesso e in cosa differisce."""
    righe = []
    for voce in config["serie"]:
        riserva = voce.get("riserva")
        if not riserva:
            continue
        s = serie[voce["id"]]
        differenze = [riserva["nota"]] if riserva.get("nota") else []
        if riserva.get("unita"):
            differenze.append(f"unit: {riserva['unita']}")
        if riserva.get("trasformazione") == "yoy":
            differenze.append("index converted to a yearly change")
        righe.append({
            "nome": voce["nome"], "principale": f"{NOMI_FONTI.get(voce['fonte'], voce['fonte'])} {voce['id']}",
            "riserva": f"{NOMI_FONTI.get(riserva['fonte'], riserva['fonte'])} {riserva['id']}",
            "differenze": "; ".join(differenze) or "same quantity", "in_uso": bool(s.nota_fonte),
        })
    return righe


def serie_calcolate(config: dict, serie: dict[str, Serie]) -> list[dict]:
    righe = []
    for voce in config["serie"]:
        if voce["fonte"] != FONTE_CALCOLATA:
            continue
        s = serie[voce["id"]]
        a, b = voce["componenti"]
        formula = f"{serie[a].nome} {OPERAZIONI.get(voce.get('operazione', 'differenza'), '−')} {serie[b].nome}"
        if voce.get("fattore", 1) != 1:
            formula += f" × {voce['fattore']:g}"
        righe.append({"nome": voce["nome"], "formula": formula, "ok": s.ok, "errore": s.errore})
    return righe


def raggruppa_note(note: dict, usi_note: dict[str, list[dict]]) -> list[dict]:
    """Le note di contenuti/note.yaml raggruppate come in `gruppi`, con i grafici che le richiamano."""
    gruppi = []
    for id_gruppo, titolo in note["gruppi"].items():
        voci = [{"id": i, "titolo": n["titolo"], "testo": n["testo"], "usi": usi_note.get(i, [])}
                for i, n in note["note"].items() if n["gruppo"] == id_gruppo]
        if voci:
            gruppi.append({"titolo": titolo, "note": voci})
    return gruppi
