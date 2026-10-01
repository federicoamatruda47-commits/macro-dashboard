"""Indirizzi (link) delle pagine delle serie presso le fonti, per i piè di pagina dei grafici e la pagina Series status.

Sono link per le persone (pagine web), non gli indirizzi delle API usate per scaricare i dati.
I formati sono stati controllati a mano il 01/10/2026 (FRED, BCE, BIS, DBnomics).
"""

from urllib.parse import quote

# Sito generale di ogni fonte (pagina "Sources" di Method)
SITI_FONTI = {
    "fred": "https://fred.stlouisfed.org/",
    "ecb": "https://data.ecb.europa.eu/",
    "bis": "https://data.bis.org/",
    "yahoo": "https://finance.yahoo.com/",
    "mof": "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/index.htm",
    "statjp": "https://db.nomics.world/STATJP",
    "imf": "https://data.imf.org/en/datasets/IMF.RES:WEO",
    "wb": "https://data.worldbank.org/",
}


def url_indicatore(fonte: str, codice: str) -> str:
    """Pagina web di un indicatore annuale presso la fonte (WEO: DataMapper; Banca Mondiale: data.worldbank.org, dove i punti dei
    codici WGI diventano trattini bassi). Link per le persone, non l'indirizzo dell'API."""
    if fonte == "imf":
        return f"https://www.imf.org/external/datamapper/{quote(codice)}@WEO"
    return f"https://data.worldbank.org/indicator/{quote(codice.replace('.', '_') if codice.startswith('GOV_WGI_') else codice)}"


# Il portale del BIS organizza le serie per "argomento" (topic): non coincide con il nome del dataset
ARGOMENTI_BIS = {"WS_CBPOL": "CBPOL", "WS_LONG_CPI": "CPI"}


def url_serie(fonte: str, id_serie: str) -> str | None:
    """Pagina web della serie presso la sua fonte (None per le serie calcolate o se non si sa costruirla)."""
    if fonte == "fred":
        return f"https://fred.stlouisfed.org/series/{quote(id_serie)}"
    if fonte == "ecb":
        dataset, _, chiave = id_serie.partition("/")
        return f"https://data.ecb.europa.eu/data/datasets/{dataset}/{dataset}.{chiave}"
    if fonte == "bis":
        dataset, _, chiave = id_serie.partition("/")
        argomento = ARGOMENTI_BIS.get(dataset)
        if argomento is None:
            return SITI_FONTI["bis"]
        return f"https://data.bis.org/topics/{argomento}/BIS,{dataset},1.0/{chiave}"
    if fonte == "yahoo":
        return f"https://finance.yahoo.com/quote/{quote(id_serie, safe='')}"
    if fonte == "statjp":
        return f"https://db.nomics.world/STATJP/{id_serie}"
    if fonte == "mof":
        return SITI_FONTI["mof"]
    return None
