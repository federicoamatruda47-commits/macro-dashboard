"""Prova (temporanea, step 10a): le API dell'FMI e della Banca Mondiale rispondono da GitHub Actions?

Solo libreria standard. Per ogni indirizzo prova due "User-Agent" (quello predefinito di Python e uno da browser)
e stampa codice, tempo, byte e righe. Non scrive nulla nel progetto. Si usa dal workflow `prova-api.yml`
e si può lanciare anche a mano: python tools/prova_api_actions.py
"""
import csv
import io
import json
import sys
import time
import urllib.error
import urllib.request

UA_PYTHON = None  # lascia il predefinito di urllib ("Python-urllib/3.x")
UA_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

IMF = "https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO"
WB = "https://api.worldbank.org/v2"

# (nome, indirizzo, header Accept, tipo di controllo)
PROVE = [
    ("FMI SDMX  NGDP_RPCH tutti i paesi (CSV)", f"{IMF}/*.NGDP_RPCH.A", "application/vnd.sdmx.data+csv", "csv"),
    ("FMI SDMX  PPPPC tutti i paesi (CSV)", f"{IMF}/*.PPPPC.A", "application/vnd.sdmx.data+csv", "csv"),
    ("FMI SDMX  Italia JSON", f"{IMF}/ITA.NGDP_RPCH.A?lastNObservations=3", "application/json", "json"),
    ("FMI DataMapper (vecchia API)", "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/ITA", "application/json", "json"),
    ("WB WDI  PIL reale crescita, tutti i paesi", f"{WB}/country/all/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page=20000", None, "wb"),
    ("WB WGI  GOV_WGI_CC.SC (source 3)", f"{WB}/country/all/indicator/GOV_WGI_CC.SC?format=json&per_page=20000&source=3", None, "wb"),
    ("WB elenco paesi", f"{WB}/country?format=json&per_page=400", None, "wb"),
]


def chiama(url, accept, ua):
    intestazioni = {}
    if ua:
        intestazioni["User-Agent"] = ua
    if accept:
        intestazioni["Accept"] = accept
    richiesta = urllib.request.Request(url, headers=intestazioni)
    inizio = time.time()
    try:
        with urllib.request.urlopen(richiesta, timeout=120) as r:
            corpo = r.read()
            return r.status, time.time() - inizio, corpo, ""
    except urllib.error.HTTPError as e:
        return e.code, time.time() - inizio, e.read(), str(e)
    except Exception as e:  # rete, timeout, ecc.
        return 0, time.time() - inizio, b"", f"{type(e).__name__}: {e}"


def righe(tipo, corpo):
    try:
        if tipo == "csv":
            return f"{len(list(csv.DictReader(io.StringIO(corpo.decode('utf-8')))))} righe CSV"
        d = json.loads(corpo)
        if tipo == "wb":
            return f"{len(d[1])} voci JSON (pagine: {d[0].get('pages')}, aggiornato {d[0].get('lastupdated')})"
        return "JSON valido"
    except Exception as e:
        return f"contenuto non leggibile ({type(e).__name__}): {corpo[:80]!r}"


def main():
    esito = []
    for nome, url, accept, tipo in PROVE:
        for etichetta, ua in (("UA python", UA_PYTHON), ("UA browser", UA_BROWSER)):
            codice, secondi, corpo, errore = chiama(url, accept, ua)
            ok = codice == 200
            dettaglio = righe(tipo, corpo) if ok else (errore or corpo[:80].decode("utf-8", "replace").replace("\n", " "))
            riga = f"{'OK ' if ok else 'KO '} {nome} [{etichetta}] -> HTTP {codice}, {secondi:.1f} s, {len(corpo):,} byte, {dettaglio}"
            print(riga, flush=True)
            esito.append((ok, riga))
    print()
    print(f"Riuscite {sum(1 for ok, _ in esito if ok)} prove su {len(esito)}.")
    return 0  # l'esito si legge nel log: il workflow non deve fallire se un'API risponde 403


if __name__ == "__main__":
    sys.exit(main())
