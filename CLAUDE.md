# Dashboard macro

## Obiettivo
Dashboard macroeconomica **statica**, rigenerata ogni giorno e pubblicata su **GitHub Pages**.
L'utente è uno studente di finanza, principiante in programmazione: spiegare le scelte
in modo semplice e proporre un piano prima di modifiche importanti.

Roadmap in 3 fasi:
1. **USA** (fatta): politica monetaria, curva Treasury, spread, tassi reali, inflazione, credito, condizioni
2. **Eurozona** (fatta): DFR, curva AAA (proxy Bund), spread sovrani, HICP, HY in euro, EUR/USD. Fonte BCE, riserva FRED
3. **Asia** (Giappone, Cina, Corea) + sezione **Confronto globale** (fonti previste: BIS, yfinance)

## Regole del progetto
- **Commenti e testi del sito in italiano.** Numeri in formato italiano (virgola decimale).
- Ambiente: Windows + PowerShell, **Python 3.14**, ambiente virtuale `.venv`.
- Prima di aggiungere una libreria, verificare che esista un wheel per Python 3.14 su Windows
  (`pip install --dry-run --only-binary=:all: <pacchetto>`) e aggiornare `requirements.txt` con la versione fissata.
- **Smart App Control di Windows è attivo** su questo PC e blocca alcuni file compilati appena pubblicati
  (es. pandas 3.0.6 → "Un criterio di controllo dell'applicazione ha bloccato il file"). Soluzione adottata:
  usare una versione leggermente precedente (pandas 3.0.5). Non modificare le impostazioni di sicurezza.
- La chiave API sta in `.env` (`FRED_API_KEY=...`), mai nel codice, nei log o sul sito. `.env` e `.venv` sono in `.gitignore`.
- Un errore su una serie **non deve mai** bloccare la generazione del sito: la serie diventa "non disponibile"
  e compare un avviso. `build.py` esce con codice 1 solo se non si scarica nessuna serie.
- **Controllo di freschezza** su tutte le serie: se l'ultimo dato supera la soglia (10 giorni giornaliere, 21 settimanali,
  75 mensili, 120 trimestrali, contati dalla fine del periodo) il sito mostra un avviso in cima. Serve a scoprire
  le serie "congelate" che non danno errore (vedi il caso HICP sotto).
- Grafici: un solo asse y per grafico (niente doppio asse), palette a ordine fisso (`--s1`…`--s8` in `static/style.css`,
  uguale a `PALETTE` in `dashboard/charts.py`). Bande grigie = recessioni: NBER (serie `USREC`) per gli USA,
  CEPR (date scritte a mano in `config.yaml` → `recessioni:`) per l'Eurozona.
- Prima di aggiungere una serie, verificarne sulla fonte **storico e ultimo dato** (non solo che esista).
- Non fare commit o push senza richiesta esplicita dell'utente.

## Struttura
```
config.yaml              regioni/tab, recessioni CEPR, elenco delle serie (id, fonte, nome, regione, categoria, unita,
                         trasformazione, riepilogo; facoltativi: riserva, componenti, decimali)
build.py                 comando unico: scarica → calcola → genera site/
dashboard/
  sources/               un modulo per fonte; ognuno espone scarica(id) -> pandas.Series
    __init__.py          registro FONTI {"fred": fred.scarica, "ecb": ecb.scarica}
    fred.py              API ufficiale FRED (retry, errori senza chiave nel messaggio)
    ecb.py               API ECB Data Portal, senza chiave; id = "DATASET/CHIAVE" (es. FM/D.U2.EUR.4F.KR.DFR.LEV)
    errori.py            ErroreFonte
  data.py                classe Serie, lettura config, download con riserva, serie calcolate (A − B),
                         trasformazioni (livello / yoy), variazioni 1s/1m/1a, controllo di freschezza
  charts.py              grafici riutilizzabili: linee_storiche (recessioni, inversioni, linea di riferimento), curva_rendimenti,
                         periodi_recessione (da USREC), periodi_da_trimestri (da elenco CEPR)
  regions/
    __init__.py          registro REGIONI {"usa": usa.costruisci, "eurozona": eurozona.costruisci}
    modello.py           dataclass Sezione e Grafico
    usa.py               composizione della pagina USA
    eurozona.py          composizione della pagina Eurozona
  render.py              prepara i dati per il template e scrive site/
templates/index.html.j2  pagina HTML (Jinja2)
static/style.css         stile, tema chiaro/scuro, layout per telefono
static/app.js            tab, disegno Plotly, pulsanti 1A/5A/10A/Max, colori dal tema
site/                    OUTPUT generato (non versionato: lo ricrea la GitHub Action)
.github/workflows/aggiorna-dashboard.yml   build giornaliera + pubblicazione su Pages
```

## Come si aggiunge…
- **una serie**: un blocco in `config.yaml`; se deve apparire in un grafico, aggiungerla in `regions/<regione>.py`.
  Riserva automatica: `riserva: {fonte: fred, id: ..., trasformazione: ...}` (usata solo se la principale fallisce,
  segnalata con un avviso). Spread calcolato: `fonte: calcolata` + `componenti: [A, B]` → A − B nelle date comuni.
- **una fonte** (es. BIS): `dashboard/sources/bis.py` con `scarica(id)`, registrarla in `sources/__init__.py`
  e in `NOMI_FONTI` di `data.py` (nome mostrato sul sito).
- **una regione**: `dashboard/regions/<id>.py` con `costruisci(serie, config) -> list[Sezione]`, registrarla in
  `regions/__init__.py`, mettere `attiva: true` in `config.yaml`.

## Comandi
```powershell
.\.venv\Scripts\Activate.ps1           # attiva l'ambiente virtuale
pip install -r requirements.txt       # installa le librerie
python build.py                        # genera site/index.html
python -m http.server 8000 --directory site   # anteprima su http://localhost:8000
```

## Note sui dati (verificate a settembre 2026)
- OAS ICE BofA (`BAMLC0A0CM`, `BAMLH0A0HYM2`) su FRED partono da **ottobre 2023** (licenza): per lo storico lungo si usa `BAA10Y` (dal 1986).
- `DFII10`, `T10YIE` dal 2003; `DTWEXBGS` dal 2006 ed esce settimanalmente con qualche giorno di ritardo.
- Per alleggerire la pagina, i dati giornalieri più vecchi di 5 anni sono ridotti a un punto a settimana (`charts.alleggerisci`).
- "Ultimo dato" = data dell'ultima osservazione della serie; una serie è "in ritardo" se supera le soglie di `SOGLIA_RITARDO_GIORNI` in `data.py`.

### Eurozona (verificate il 30/09/2026)
- **HICP: il vecchio dataset BCE `ICP` è fermo a dicembre 2025** (tutte le serie, tutti i Paesi) e risponde senza errori.
  Dal 2026 l'HICP è nel nuovo dataset **`HICP`**, con codice fornitore **`4D0`** al posto di `4`:
  headline `HICP/M.U2.N.000000.4D0.ANR`, core `HICP/M.U2.N.XEF000.4D0.ANR` (entrambe dal 1991, variazione annua già calcolata).
  Il codice `4F0` nello stesso dataset indica indicatori stimati dalla BCE (es. supercore), non la stima flash.
- Rendimenti 2A/10A: curva **AAA** BCE (`YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_*`), giornaliera dal 09/2004, usata come
  proxy Bund. La curva di tutti i titoli di Stato area euro è `G_N_C` al posto di `G_N_A` (stesso storico).
- **Rendimenti giornalieri dei singoli Paesi (Bund, BTP, OAT): non gratuiti.** Si usano le medie mensili dei criteri
  di convergenza `IRS/M.<PAESE>.L.L40.CI.0000.EUR.N.Z` (DE dal 1990, IT dal 1991, FR dal 1986; circa un mese di ritardo).
  Riserva FRED: `IRLTLT01<PAESE>M156N` (OECD, mensile). Nel dataset `FM` la BCE ha solo benchmark dell'area euro, mensili.
- Spread IG in euro: nessuna fonte gratuita. HY in euro: solo `BAMLHE00EHYIOAS` su FRED, dal 10/2023 (licenza ICE).
- Recessioni: nessuna API. L'indicatore OECD su FRED (`EUROREC`) è fermo al 08/2022; il sito CEPR blocca
  le richieste automatiche (403). Date CEPR in `config.yaml`, da aggiornare a mano.
- Riserve FRED per l'HICP: `CP0000EZCCM086NEST` e `00XEFDEZCCM086NEST` (indici a composizione variabile → `trasformazione: yoy`).
