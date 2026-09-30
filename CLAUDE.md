# Dashboard macro

## Obiettivo
Dashboard macroeconomica **statica**, rigenerata ogni giorno e pubblicata su **GitHub Pages**.
L'utente è uno studente di finanza, principiante in programmazione: spiegare le scelte
in modo semplice e proporre un piano prima di modifiche importanti.

Roadmap in 3 fasi:
1. **USA** (fatta): politica monetaria, curva Treasury, spread, tassi reali, inflazione, credito, condizioni
2. **Eurozona** (fonte prevista: BCE)
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
- Grafici: un solo asse y per grafico (niente doppio asse), palette a ordine fisso (`--s1`…`--s8` in `static/style.css`,
  uguale a `PALETTE` in `dashboard/charts.py`), bande grigie = recessioni NBER (serie `USREC`).
- Non fare commit o push senza richiesta esplicita dell'utente.

## Struttura
```
config.yaml              elenco delle serie (id, fonte, nome, regione, categoria, unita, trasformazione, riepilogo) e delle regioni/tab
build.py                 comando unico: scarica → calcola → genera site/
dashboard/
  sources/               un modulo per fonte; ognuno espone scarica(id) -> pandas.Series
    __init__.py          registro FONTI {"fred": fred.scarica, ...}
    fred.py              API ufficiale FRED (retry, errori senza chiave nel messaggio)
    errori.py            ErroreFonte
  data.py                classe Serie, lettura config, download, trasformazioni (livello / yoy), variazioni 1s/1m/1a
  charts.py              grafici riutilizzabili: linee_storiche (recessioni, inversioni, linea di riferimento), curva_rendimenti
  regions/
    __init__.py          registro REGIONI {"usa": usa.costruisci, ...}
    modello.py           dataclass Sezione e Grafico
    usa.py               composizione della pagina USA
  render.py              prepara i dati per il template e scrive site/
templates/index.html.j2  pagina HTML (Jinja2)
static/style.css         stile, tema chiaro/scuro, layout per telefono
static/app.js            tab, disegno Plotly, pulsanti 1A/5A/10A/Max, colori dal tema
site/                    OUTPUT generato (non versionato: lo ricrea la GitHub Action)
.github/workflows/aggiorna-dashboard.yml   build giornaliera + pubblicazione su Pages
```

## Come si aggiunge…
- **una serie**: un blocco in `config.yaml`; se deve apparire in un grafico, aggiungerla in `regions/<regione>.py`.
- **una fonte** (es. BCE): `dashboard/sources/ecb.py` con `scarica(id)`, registrarla in `sources/__init__.py`.
- **una regione**: `dashboard/regions/<id>.py` con `costruisci(serie) -> list[Sezione]`, registrarla in
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
