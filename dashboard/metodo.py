"""Contenuto delle pagine "Sources & method" e "Series status".

Qui stanno i testi fissi sulle fonti e le regole (in inglese, come il sito) e il calcolo delle parti "vive":
soglie di freschezza, fonti di riserva in uso, serie calcolate e note raggruppate.
Le note tecniche stanno in contenuti/note.yaml; render.py le passa già lette.
"""

from . import annuali, movimenti
from .data import FONTE_CALCOLATA, NOMI_FONTI, OPERAZIONI, SOGLIA_RITARDO_GIORNI, Serie
from .fonti_url import SITI_FONTI

# Come mostrare le frequenze (dentro il codice restano in italiano)
FREQUENZE = {"giornaliera": "daily", "settimanale": "weekly", "mensile": "monthly", "trimestrale": "quarterly",
             "semestrale": "semiannual", "annuale": "annual"}

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
    annuali.FONTE_IMF: ("World Economic Outlook: GDP, growth, inflation, government balance and debt, current account, population "
                        "and the IMF projections, for about 200 countries (annual, 1980 onwards).",
                        "Official API (no key), downloaded by hand twice a year into a snapshot in the repository."),
    annuali.FONTE_BM: ("Unemployment and employment (ILO modelled estimates), long GDP and population histories, and the Worldwide "
                       "Governance Indicators (control of corruption), for about 200 countries (annual).",
                       "Official API (no key), refreshed into a snapshot in the repository."),
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
    """Tabella delle fonti con il numero di serie che ne usano ogni una come fonte principale.

    Per l'FMI e la Banca Mondiale (dati annuali per Paese) il numero è quello degli indicatori del catalogo.
    """
    conteggio: dict[str, int] = {}
    for voce in config["serie"]:
        conteggio[voce["fonte"]] = conteggio.get(voce["fonte"], 0) + 1
    for voce in config.get("indicatori", []):
        conteggio[voce["fonte"]] = conteggio.get(voce["fonte"], 0) + 1
    nomi = {**NOMI_FONTI, **annuali.FONTI_ANNUALI}
    righe = []
    for chiave, nome in nomi.items():
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


def snapshot_annuali(stati: list[annuali.StatoSnapshot]) -> list[dict]:
    """Righe della tabella "Annual data" di Method: edizione, data, giorni trascorsi, soglia e stato di ogni snapshot."""
    righe = []
    for s in stati:
        righe.append({
            "nome": s.nome, "frequenza": FREQUENZE[s.frequenza], "edizione": s.edizione,
            "data": f"{s.data.day} {s.data:%b %Y}" if s.data else None, "giorni": s.giorni, "soglia": s.soglia,
            "presente": s.presente, "in_ritardo": s.in_ritardo, "n_paesi": s.n_paesi, "n_indicatori": s.n_indicatori,
        })
    return righe


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


NOMI_GRUPPI_MOVIMENTI = {
    "us_rates": "US Treasury yields, real yields and curve slopes", "ea_rates": "Euro-area AAA yields and slope",
    "ea_spreads": "Euro-area sovereign spread", "jp_rates": "Japanese government bond yields",
    "us_credit": "US corporate credit spreads", "ea_credit": "Euro high-yield spread",
    "us_equities": "US equity indices", "ea_equities": "Euro-area equity indices and banks", "asia_equities": "Asian equity indices",
    "world_equities": "World equities (ACWI)", "vix": "VIX", "usd": "The dollar (EUR/USD and the broad index)",
    "jpy": "USD/JPY", "cny": "USD/CNY", "krw": "USD/KRW", "oil": "Oil (WTI and Brent)", "gas_us": "US natural gas",
    "gas_eu": "European natural gas", "precious_metals": "Gold and silver", "industrial_metals": "Copper and aluminium",
    "grains": "Wheat and corn",
}


def descrivi_movimenti(config: dict, serie: dict[str, Serie], classifica: movimenti.Classifica) -> dict:
    """I parametri di "What changed this week" (letti da dashboard/movimenti.py), i gruppi e quante serie hanno superato la soglia."""
    gruppi: dict[str, list[str]] = {}
    for voce in config["serie"]:
        if voce.get("movimenti"):
            gruppi.setdefault(voce["gruppo_movimenti"], []).append(serie[voce["id"]].etichetta)
    return {
        "soglia": f"{movimenti.SOGLIA:g}", "massimo": movimenti.MASSIMO, "giorni": movimenti.GIORNI, "anni": movimenti.ANNI_STORICO,
        "minimo": movimenti.MIN_OSSERVAZIONI, "n_serie": sum(len(v) for v in gruppi.values()),
        "n_controllate": classifica.n_controllate, "n_sopra_soglia": classifica.n_sopra_soglia,
        "gruppi": [{"nome": NOMI_GRUPPI_MOVIMENTI.get(g, g), "serie": ", ".join(nomi)} for g, nomi in gruppi.items()],
    }


def raggruppa_note(note: dict, usi_note: dict[str, list[dict]]) -> list[dict]:
    """Le note di contenuti/note.yaml raggruppate come in `gruppi`, con i grafici che le richiamano."""
    gruppi = []
    for id_gruppo, titolo in note["gruppi"].items():
        voci = [{"id": i, "titolo": n["titolo"], "testo": n["testo"], "usi": usi_note.get(i, [])}
                for i, n in note["note"].items() if n["gruppo"] == id_gruppo]
        if voci:
            gruppi.append({"titolo": titolo, "note": voci})
    return gruppi
