# Dashboard macro

## Obiettivo
Dashboard macroeconomica **statica**, rigenerata ogni giorno e pubblicata su **GitHub Pages**, in inglese.
L'utente è uno studente di finanza, principiante in programmazione: spiegare le scelte
in modo semplice e proporre un piano prima di modifiche importanti.

## Il sito (dopo la ristrutturazione del 01/10/2026, vedi [docs/ristrutturazione.md](docs/ristrutturazione.md))
Una pagina HTML per ogni indirizzo (`site/<id>/index.html`, link sempre relativi):
- **Overview** (`/`): 14 numeri chiave con mini-grafico (blocco `panoramica:` di `config.yaml`), "What changed this week", schede verso le altre pagine, stato dei dati.
- **Markets** (`markets/`, hub): `rates` (tassi di policy, curve, rendimenti, pendenza e inversioni, inflazione, tassi reali), `credit` (spread societari e sovrani),
  `equities` (tabella di performance a gruppi con "Last", confronto borse locale/USD, VIX), `fx`, `commodities`. In ogni pagina i Paesi si confrontano nello stesso grafico.
- **Economies** (`economies/`, hub): `usa` (per ora solo la disoccupazione), `italy`, `euro-area`, `uk`, `compare` (pagine vuote "coming soon", livello A); **`economies/country.html?c=ISO3`** = una pagina sola per ~218 Paesi (livello B, dati annuali FMI e Banca Mondiale, vedi sotto); le schede Japan, China, South Korea dell'hub portano lì.
  **Prossimo lavoro: riempire le pagine di Economies** (si fa una pagina per volta, con le stesse regole di Markets).
- **Method & sources** (`method/`, `method/series/`): fonti, controllo di freschezza, fonti di riserva, serie calcolate, "What changed this week", limiti noti (registro delle note),
  tabella di tutte le serie.
- **Tema chiaro/scuro**: segue il sistema; l'interruttore ◐ (Auto/Light/Dark) imposta `data-theme` su `<html>` e la scelta si ricorda solo nel `localStorage` del visitatore (`static/app.js`, `render.css_colori`, `static/style.css`).
- I vecchi indirizzi (`usa/`, `eurozona/`, `commodities/`...) restano come pagine che rimandano ai nuovi (`pagine.REINDIRIZZAMENTI`).

## Regole del progetto
- **Testi del sito in INGLESE**: numeri `1,234.5` (punto decimale), date `30 Sep 2026`, scadenze `10Y`, unità `bp`/`pp`, periodi `1Y 5Y 10Y Max`.
  **Commenti e nomi interni del codice restano in italiano.** Nel config `nome` e `unita` sono in inglese (`"% y/y"`).
- **Righe "How to read it" (`come_leggerlo`)**: ogni grafico ne ha una (la build avvisa se manca). Linguaggio semplice, una o due frasi,
  comprensibili a chi non è del settore; prudenti e fattuali: descrivono relazioni storiche ("historically", "has tended to"), mai previsioni o certezze,
  e citano le eccezioni importanti quando servono (es. oro e tassi reali dopo il 2022). Gli esempi concreti si **verificano sui dati** prima di scriverli
  (es. l'inversione 2022-24 senza recessione NBER; l'inflazione giapponese sopra il 2% solo fino a fine 2025). **Quando si scrive o si cambia una pagina si mostra
  all'utente una tabella con tutte le righe della pagina, da rivedere prima del merge.**
- **Note tecniche**: i testi lunghi stanno in `contenuti/note.yaml` (un id per nota); un grafico le richiama con `note=["id", ...]`. Sotto il grafico compaiono solo la fonte
  con il link e i titoli delle note; i testi sono in Method > Known limits. Link alle fonti: `dashboard/fonti_url.py`.
- **Pagine**: definite nel blocco `pagine:` di `config.yaml` (stato `attiva`, `in-arrivo`, `dopo`; `numeri_chiave`) e costruite da funzioni registrate in
  `dashboard/mercati/__init__.py` o `dashboard/economie/__init__.py` (`costruisci(serie, config) -> list[Sezione]`). Una serie (o indice) ha **una sola definizione** in `config.yaml`;
  i grafici la riusano per id. Gli id dei grafici non devono coincidere con gli id HTML delle sezioni (`<slug>-<sezione>`): l'elemento duplicato non si disegna.
- Ambiente: Windows + PowerShell, **Python 3.14**, ambiente virtuale `.venv`.
- Prima di aggiungere una libreria, verificare che esista un wheel per Python 3.14 su Windows
  (`pip install --dry-run --only-binary=:all: <pacchetto>`) e aggiornare `requirements.txt` con la versione fissata.
- **Smart App Control di Windows è attivo** su questo PC e blocca alcuni file compilati appena pubblicati
  (es. pandas 3.0.6 → "Un criterio di controllo dell'applicazione ha bloccato il file"). Soluzione adottata:
  usare una versione leggermente precedente (pandas 3.0.5). Non modificare le impostazioni di sicurezza.
  yfinance 1.7.0 e le sue librerie compilate (curl_cffi 0.16.3, cffi, lxml, protobuf) funzionano: provate il 30/09/2026.
  Per verificare una libreria nuova senza toccare `.venv`: installarla in un ambiente virtuale temporaneo e importarla.
- La chiave API sta in `.env` (`FRED_API_KEY=...`), mai nel codice, nei log o sul sito. `.env` e `.venv` sono in `.gitignore`.
- Un errore su una serie **non deve mai** bloccare la generazione del sito: la serie diventa "non disponibile"
  e compare un avviso. `build.py` esce con codice 1 solo se non si scarica nessuna serie.
- **Serie calcolate solo con componenti dalla stessa fonte.** Una serie `fonte: calcolata` (differenza o rapporto)
  si calcola solo se tutte le componenti vengono dalla stessa fonte principale. Se anche una sola componente è
  passata alla riserva, la serie calcolata diventa "non disponibile" con un avviso che spiega il motivo: non si
  mescolano mai spot e future, fonti diverse o unità diverse (es. Brent spot FRED − WTI future Yahoo).
  Vale per tutte le serie calcolate (spread Brent-WTI, rapporto rame/oro, spread BTP-Bund, pendenze, borse in USD...). Codice: `data._calcola`.
- Una riserva può avere un'unità diversa dalla principale (`riserva: {..., unita: ..., nota: ...}`): la serie assume
  l'unità della riserva e l'avviso lo dice. Per questo non mettere nello stesso grafico serie che potrebbero finire
  in unità diverse (es. grano e mais sono in due grafici separati).
- **Controllo di freschezza** su tutte le serie: se l'ultimo dato supera la soglia (10 giorni giornaliere, 21 settimanali,
  75 mensili, 120 trimestrali, contati dalla fine del periodo) il sito mostra un avviso nelle pagine che usano la serie (e, in breve, nell'Overview).
  Serve a scoprire le serie "congelate" che non danno errore (vedi il caso HICP sotto).
  Una serie può avere `soglia_giorni: N` (sostituisce quella standard) solo con il motivo scritto nel config
  (oggi: tasso BoK dal BIS, 45 giorni, perché il BIS pubblica la Corea con ~1 mese di ritardo).
- **Grafici**: un solo asse y per grafico (niente doppio asse); **colori fissi per Paese** (blocco `colori:` di `config.yaml`, campo `paese`/`colore` di ogni serie; le variabili
  CSS `--c-<chiave>` le scrive ogni pagina da lì). I colori hanno contrasto ≥ 3:1 con lo sfondo in entrambi i temi e si distinguono a coppie anche con il daltonismo:
  `python tools/valida_palette.py --pairs all` va rilanciato se se ne cambia uno. Più serie dello stesso colore nello stesso grafico si distinguono dallo stile
  della linea (piena, tratteggiata, puntinata...). Bande grigie = recessioni: NBER (serie `USREC`) o CEPR (date a mano in `config.yaml` → `recessioni:`) **solo nei grafici di una sola economia**;
  nessuna banda nei confronti tra Paesi, nei cambi e in Asia. Per confrontare due serie con unità diverse si usa `charts.due_pannelli`
  (due pannelli con lo stesso asse del tempo; quello in basso si può invertire; `app.js` gestisce `layout.meta.assi_invertiti`).
- **Grafici "base 100"** (`charts.linee_base100`): il JavaScript ribasa a 100 all'inizio del periodo scelto, ma non prima della prima data in cui esistono tutte le serie (`base100()` in `static/app.js`).
  **Grafici con due varianti** (`Grafico.varianti`, interruttore "Local currency / In USD"): la figura contiene le linee di entrambe, ognuna con `meta.variante`; `app.js` mostra solo quelle della variante scelta
  e ribasa considerando solo le linee visibili. In `linee_base100` il 3° elemento facoltativo di ogni voce è `{linea, variante, benchmark}` (la stessa `linea` = stessa identità e stesso stile; benchmark = linea spessa tratteggiata nel colore "mondo").
  Le borse in USD sono serie `calcolata` (indice / cambio "valuta per dollaro", tutto Yahoo): se un cambio passa alla riserva FRED la serie in USD è "non disponibile" con avviso.
- **Azioni**: sempre prezzi di chiusura senza dividendi (`auto_adjust=False` in `yahoo.py`), spiegato nelle note. `Sezione.tabella_performance` / `gruppi_performance` + `etichetta_performance` = tabella con Last / 1W / 1M / YTD / 1Y.
  Le schede "Key numbers" mostrano la variazione da inizio anno per le serie con `categoria: borsa` (o se la pagina ha `ytd: true`).
- Sotto i grafici con future continui Yahoo c'è il link alla nota sui cambi di scadenza (compare solo se i dati sono davvero di Yahoo, non della riserva).
- Prima di aggiungere una serie, verificarne sulla fonte **storico e ultimo dato** (non solo che esista).
- **Dati senza fonte gratuita aggiornata = righe eliminate, non serie "non disponibili"**: non si mettono in config (altrimenti l'avviso resterebbe acceso per sempre)
  e si scrive una nota nel registro (`not-included-*` in `contenuti/note.yaml`, gruppo "Country coverage").
- **"What changed this week"** (`dashboard/movimenti.py`, funzioni pure con test): movimento a 7 giorni diviso per la deviazione standard dei movimenti a 7 giorni dei 3 anni precedenti;
  soglia **2×** (a 1,5× circa il 13% delle serie la supera per caso in una settimana normale: la lista sarebbe sempre piena), massimo 5 righe, una serie per gruppo (`gruppo_movimenti`).
  Entrano solo serie con `movimenti: true` (giornaliere o settimanali; mai tassi di policy né serie mensili). "×normal" non è una probabilità. La motivazione è scritta in Method.
- **Dati annuali per Paese (FMI WEO e Banca Mondiale, step 10a)**: non sono `serie` (sarebbero ~2.000 voci): stanno in un **catalogo `indicatori:`** di `config.yaml` e in **snapshot CSV nel repository**
  (`dati/weo/`, `dati/bm/`; formato in `dashboard/annuali.py`: `dati.csv` = paese, indicatore, anno, valore, ordinato e arrotondato a 3 decimali per eccesso a metà (interi da 1 milione in su), nella scala dell'FMI (miliardi, milioni) come il file del WEO, così il diff mostra solo i valori cambiati;
  `ultimo_effettivo.csv` = ultimo anno con dato reale per Paese e indicatore, dopo è stima/proiezione, più `anno_fiscale` (1 se l'FMI scrive "FY2024/25": 200 coppie, 33 Paesi); `meta.json` = date di pubblicazione/aggiornamento della fonte, mai la data di oggi). La build giornaliera legge solo gli snapshot.
  **FMI: a mano** (`python tools/aggiorna_weo.py` a ogni WEO, metà aprile e metà ottobre; riserva: `python tools/importa_weo.py FILE` con il CSV scaricato da data.imf.org, verificato: dà lo stesso snapshot dell'API byte per byte): i termini d'uso chiedono richieste avviate da una persona.
  **Banca Mondiale: automatica** (`.github/workflows/aggiorna-dati-bm.yml`, mensile: esegue test e controlli e apre una pull request solo se i dati cambiano, con l'esito nella descrizione; il merge lo fa l'utente) o a mano (`python tools/aggiorna_bm.py`).
  Freschezza a semestri (WEO: 210 giorni dalla pubblicazione) e annuale (Banca Mondiale: 456 giorni); se l'ultimo commit ha più di 45 giorni il job `controlla-attivita` del workflow giornaliero apre **una sola issue** su GitHub (`tools/controlla_attivita.py`; si chiude da sola al commit successivo; NON c'è alcun avviso sul sito pubblico): GitHub spegne i workflow programmati dopo 60 giorni senza attività.
  La Banca Mondiale va chiamata senza `page=1` e con controllo di `sourceid` (con `page=1` risponde a volte con un'altra sorgente). Disoccupazione e occupazione WB sono stime modellate ILO; WGI: solo il punteggio 0-100 (`GOV_WGI_CC.SC`, con `_LB`/`_UB`), nessun rango.
- **Pagina del Paese** (`economies/country.html`, step 10b): struttura e righe "How to read it" in `contenuti/paese.yaml` (sezioni, grafici, forma, serie del catalogo); disegno in `static/paese.js` (Plotly; selettore con ricerca, indirizzo `?c=ITA` aggiornato con `pushState`, codice non valido = messaggio con il selettore); dati in `site/economies/dati/<ISO3>.json` (un file per Paese, ~3 KB compressi) e `ultimi-valori.json` (per la mappa dell'Overview, step 14), scritti da `dashboard/paesi.py` a ogni build.
  Regole: il Paese ha dati FMI per PIL, crescita, PIL pro capite, prezzi, finanza pubblica, conto corrente (anni dopo l'ultimo anno **effettivo** = stime/proiezioni, tratteggiati; l'anno effettivo sta accanto al valore); la Banca Mondiale solo per lavoro, popolazione, WGI e, **solo per i Paesi senza FMI**, PIL e crescita (mai le due fonti nello stesso grafico). Anni fiscali (`anno_fiscale` nello snapshot): nota sotto i grafici. Nessun interruttore di fonte.
  **Righe "How to read it" della pagina del Paese**: esempi solo di episodi chiusi da almeno due anni (oggi: Italia 2020-21 e 2022, Grecia 2024); **mai valori correnti né classifiche**, perché il WEO di ottobre li cambierebbe (un test lo controlla: nessun anno dal 2025 in poi, nessuna classifica).
- **Scala logaritmica dell'inflazione** (pagina del Paese, `scala_log: true` in `contenuti/paese.yaml`): scala simmetrica log10(1+|y|) col segno, automatica se nella finestra visibile (10Y/25Y/Max, proiezioni comprese) c'è almeno un anno sopra il 100%; si ricalcola a ogni cambio di periodo; i pulsanti Linear/Log e la nota "Logarithmic scale above 1%..." mostrano sempre la scala davvero usata; la scelta manuale resta finché non si cambia Paese; i tooltip hanno sempre i valori veri. Debito della Liberia e saldo della Guinea Equatoriale (outlier del solo periodo Max) restano lineari per scelta.
- **Nomi dei Paesi** (pagina del Paese): **nomi brevi e comuni in inglese** ("Egypt", "South Korea", "Russia", non "Egypt, Arab Rep." né "Russian Federation"); **per Taiwan, Kosovo e Cisgiordania e Gaza il nome della fonte**, senza interpretazioni nostre (Taiwan: "Taiwan Province of China", nome dell'FMI; Kosovo e West Bank and Gaza: nome della Banca Mondiale). Ogni nome cambiato sta in `config.yaml` (`nomi_paesi:` o il blocco `paesi:`) con accanto **il nome originale della fonte** (`nome_fonte`): un test controlla che sia ancora quello della Banca Mondiale e che nessun nome mostrato abbia virgole o "Rep."/"SAR". La ricerca trova un Paese anche dal nome originale. Un Paese nuovo nei dati con un nome lungo fa fallire quel test: va aggiunto a `nomi_paesi`.
- **Link "→ Economy" e riquadro Markets** (blocco `paesi:` di `config.yaml`, regola in `dashboard/paesi.py`): il link di un Paese porta alla sua pagina di livello A **solo se è `completa: true`** (campo del blocco `pagine`, non solo `attiva`), altrimenti a `economies/country.html?c=ISO3`; l'area euro non ha link finché `economies/euro-area` non è completa; mai link a codici che non sono nei dati né a pagine `in-arrivo`. Il "Full page →" della pagina del Paese segue la stessa regola. Quando una pagina di livello A è finita (step 11-13) si imposta `completa: true` e i link cambiano da soli. `tools/controlla_link.py` verifica anche i `?c=`.
- **Prima di dichiarare finito un lavoro** (e prima di ogni merge): `python -m unittest discover -s tests -t .` (con `PROVE_CON_RETE=1` anche gli episodi storici), `python build.py`,
  `python tools/inventario.py controlla` e `sito` (nessun grafico o serie perso o doppio, ognuno nella pagina promessa da `docs/mappa-grafici.yaml`), `python tools/controlla_link.py` (link interni).
  I test girano anche nel workflow GitHub prima della build: se falliscono non si pubblica.
- **Flusso di lavoro con l'utente**: un ramo per lavoro; a fine lavoro riepilogo e **attesa dell'ok dell'utente prima del merge su `main`** (il merge e il push pubblicano il sito).
  Dopo ogni modifica richiesta dall'utente si **verifica che sia applicata** (nel file e nella pagina generata) prima di unire. Nessun commit o push fuori da questo flusso senza richiesta esplicita.

## Struttura
```
config.yaml              colori fissi, pagine (hub, Markets, Economies), menu, panoramica (numeri chiave dell'Overview), recessioni CEPR,
                         elenco delle serie (id, fonte, nome, paese, categoria, unita, trasformazione; facoltativi: colore, riserva, componenti,
                         operazione, fattore, decimali, soglia_giorni, movimenti, gruppo_movimenti, etichetta_breve)
build.py                 comando unico: scarica → calcola → genera site/
contenuti/note.yaml      registro delle note tecniche (testi in inglese, raggruppati; ancore method/#note-<id>)
contenuti/paese.yaml     contenuto della pagina del Paese: sezioni, grafici, righe "How to read it", schede, tabella IMF outlook
dashboard/
  sources/               un modulo per fonte; ognuno espone scarica(id) -> pandas.Series (imf.py, imf_file.py e worldbank.py sono diversi: dati annuali, non in FONTI)
    __init__.py          registro FONTI {"fred", "ecb", "yahoo", "bis", "mof", "statjp"}
    fred.py              API ufficiale FRED (retry, errori senza chiave nel messaggio)
    ecb.py               API ECB Data Portal, senza chiave; id = "DATASET/CHIAVE" (es. FM/D.U2.EUR.4F.KR.DFR.LEV)
    yahoo.py             Yahoo Finance via yfinance (non ufficiale), id = ticker (es. CL=F); riusabile per borse e cambi
    bis.py               API BIS (stats.bis.org), senza chiave; id = "DATASET/CHIAVE" (es. WS_CBPOL/D.JP tassi di policy, WS_LONG_CPI/M.JP.771 inflazione a/a)
    mof_giappone.py      CSV del Ministero delle Finanze giapponese (JGB giornalieri); id = JGB_2Y, JGB_10Y, JGB_30Y
    statjp.py            Statistics Bureau of Japan via DBnomics (CPI); id = "CPIm/001" (totale), "CPIm/733" (senza freschi) o "CPIm/740" (senza freschi né energia)
    errori.py            ErroreFonte
  data.py                classe Serie, lettura config, download con riserva, serie calcolate (A − B o A / B, stessa fonte),
                         trasformazioni (livello / yoy), variazioni 1W/1M/1Y (+ YTD), controllo di freschezza
  charts.py              grafici riutilizzabili: linee_storiche (recessioni, inversioni, linea di riferimento, unità sull'asse), linee_base100,
                         due_pannelli, curva_rendimenti, periodi_recessione (da USREC), periodi_da_trimestri (da elenco CEPR)
  modello.py             dataclass Sezione (tabella_performance, gruppi_performance) e Grafico (note, come_leggerlo, varianti, alto)
  mercati/               una pagina per file (rates, credit, equities, fx, commodities) + registro PAGINE in __init__.py
  economie/              le pagine di Economies (per ora usa.py) + registro PAGINE
  movimenti.py           "What changed this week" (calcolo puro, testato)
  sparkline.py           mini-grafici SVG delle schede dell'Overview
  fonti_url.py           link alle pagine delle serie presso le fonti (FRED, BCE, BIS, DBnomics, Yahoo, MoF)
  annuali.py             dati annuali per Paese: catalogo `indicatori`, snapshot (lettura/scrittura), freschezza a semestri, confronto di snapshot
  paesi.py               pagina del Paese e link Markets <-> Economies: elenco dei Paesi, dati per Paese, regola della destinazione dei link
  attivita.py            data dell'ultimo commit e soglia dei 45 giorni (la usa tools/controlla_attivita.py, che apre la issue)
  metodo.py              contenuto vivo della pagina Method (fonti, soglie, riserve, serie calcolate, gruppi dei movimenti, note raggruppate)
  pagine.py              percorsi relativi, menu a due righe, REINDIRIZZAMENTI dei vecchi indirizzi
  render.py              prepara i dati per i template e scrive site/ (pagine, hub, Overview, Method, Series status, reindirizzamenti)
templates/               base, panoramica (Overview), pagina, paese (pagina del Paese), hub, metodo, serie, reindirizzamento, _componenti (macro)
static/style.css         stile, tema chiaro/scuro, layout per telefono
static/paese.js          pagina del Paese (selettore, grafici annuali, tabella IMF outlook)
static/app.js            disegno Plotly (solo quando un grafico sta per entrare nello schermo), pulsanti 1Y/5Y/10Y/Max, varianti, colori fissi dal tema
tests/                   test_movimenti.py (unittest, solo libreria standard)
tools/                   inventario.py (nulla perso/doppio), controlla_link.py, valida_palette.py,
                         aggiorna_weo.py / importa_weo.py / aggiorna_bm.py (snapshot annuali), riepilogo_snapshot.py e descrizione_pr.py (testo della pull request dei dati), controlla_attivita.py (issue dei 45 giorni)
dati/                    snapshot CSV dei dati annuali (weo/, bm/), versionati: si aggiornano solo con gli strumenti sopra
docs/                    ristrutturazione.md (piano e registro), mappa-grafici.yaml, inventario-baseline.json
site/                    OUTPUT generato (non versionato: lo ricrea la GitHub Action)
.github/workflows/aggiorna-dashboard.yml   test + build giornaliera + pubblicazione su Pages
.github/workflows/aggiorna-dati-bm.yml      mensile: snapshot Banca Mondiale, controlli e pull request se i dati cambiano
```

### Azioni occidentali e benchmark (verificate il 01/10/2026)
- Yahoo, indici giornalieri: `^GSPC` (dal 1927), `^NDX` (1985), `^RUT` (1987), `^SPXEW` S&P 500 Equal Weight (dal 12/2006; `^SP500EW` è lo stesso indice),
  `^STOXX50E` (dal 2007), `^GDAXIP` DAX K di prezzo (dal 03/2013), `^FCHI` (1990), `FTSEMIB.MI` (1997). Riserva FRED solo per `^GSPC` (`SP500`, dal 10/2016) e `^NDX` (`NASDAQ100`);
  `RU2000PR` non esiste. Per l'equal-weight non servono gli ETF `RSP`/`SPY` (dal 2003): il rapporto degli indici (`SP500_EW_SU_CW`, ×100) è quasi identico.
- **DAX**: `^GDAXI` è l'indice "performance" (dividendi reinvestiti, 323 contro ~146 degli altri in base 100 dal 2008): fuorviante nel confronto.
  Si usa `^GDAXIP` (Yahoo "DAX K", Kursindex = indice di prezzo, dal 05/03/2013, verificato: il rapporto `^GDAXI`/`^GDAXIP` cresce del ~3% annuo, cioè i dividendi).
  Costo: il "Max" del grafico a base 100 dell'Eurozona parte dal 2013 (prima dal 2008). `^GDAXP` e simili non esistono.
- **Banche europee**: `^SX7E` (Euro Stoxx Banks) e `^SX7P` non esistono su Yahoo. Si usa l'ETF `EXV1.DE` (iShares STOXX Europe 600 Banks, in €, dal 01/2008,
  Xetra: l'ultimo dato è spesso del giorno prima), che include banche non dell'area euro (UK, Svizzera). `BNK.PA` parte solo dal 2024.
- **MSCI ACWI**: `^ACWI` non esiste; si usa l'ETF `ACWI` (dal 03/2008, in $). L'ETF distribuisce dividendi, che nel prezzo non adjusted compaiono come piccoli cali.
- Cambi per la conversione in USD (Yahoo, "valuta per dollaro"): `EUR=X`, `JPY=X`, `CNY=X`, `KRW=X`, `HKD=X` (dal 2001; riserva FRED `DEXHKUS`; HKD agganciato al dollaro).
  `EURUSD=X` è l'inverso di `EUR=X`; si è scelto `EUR=X` per usare sempre il rapporto indice / cambio. FRED non offre una riserva con lo stesso verso per l'euro.

## Come si aggiunge…
- **una serie**: un blocco in `config.yaml` (con `paese`, e `colore` se serve); se deve apparire in un grafico, aggiungerla nella pagina in `dashboard/mercati/<pagina>.py`
  (o `dashboard/economie/`); se deve entrare in "What changed this week": `movimenti: true` + `gruppo_movimenti`.
  Riserva automatica: `riserva: {fonte: fred, id: ..., trasformazione: ...}` (usata solo se la principale fallisce,
  segnalata con un avviso). Spread calcolato: `fonte: calcolata` + `componenti: [A, B]` → A − B nelle date comuni;
  `operazione: rapporto` → A / B, `fattore: 1000` moltiplica il risultato.
- **una fonte** (es. BIS): `dashboard/sources/bis.py` con `scarica(id)`, registrarla in `sources/__init__.py`
  e in `NOMI_FONTI` di `data.py` (nome mostrato sul sito).
- **una pagina**: una voce nel blocco `pagine:` di `config.yaml` (e nel `menu:`), un file `dashboard/mercati/<id>.py` o `dashboard/economie/<id>.py` con
  `costruisci(serie, config) -> list[Sezione]`, registrato nel `PAGINE` del suo `__init__.py`; `stato: attiva`. Poi le righe `come_leggerlo` e la tabella da far rivedere all'utente.

## Comandi
```powershell
.\.venv\Scripts\Activate.ps1           # attiva l'ambiente virtuale
pip install -r requirements.txt       # installa le librerie
python build.py                        # genera site/
python -m unittest discover -s tests -t .   # test (dati inventati; PROVE_CON_RETE=1 per gli episodi storici)
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

### Commodities (verificate il 30/09/2026)
- Yahoo, future continui giornalieri: `CL=F` WTI e `NG=F` Henry Hub (dal 2000), `BZ=F` Brent (dal 2007), `TTF=F` gas
  europeo in €/MWh (dal 2017), `GC=F` oro, `SI=F` argento, `HG=F` rame in $/libbra (dal 2000), `ALI=F` alluminio COMEX
  (dal 2014, volume quasi zero ma prezzo aggiornato e coerente con l'FMI), `ZW=F` grano e `ZC=F` mais in cent/bushel (dal 2000).
- Yahoo: `yahoo.py` scarta l'ultima candela se la seduta non è finita (fine seduta dai metadati Yahoo; per i future, che dichiarano 23:59,
  si usa 17:00 ora di New York). La build gira alle **23:30 UTC** lun-sab, dopo la chiusura dei future USA (21-22 UTC), del TTF e delle borse asiatiche;
  i dati BCE sono già usciti, FRED può avere il giorno D con un giorno di ritardo rispetto a Yahoo (normale).
- Riserve FRED: spot giornalieri `DCOILWTICO`, `DCOILBRENTEU`, `DHHNGSP` (stessa unità, ma spot ≠ future: a settembre 2026
  il Brent spot era circa 11 $ sopra il future); medie mensili FMI `PNGASEUUSDM` ($/MMBtu), `PCOPPUSDM`, `PALUMUSDM`,
  `PWHEAMTUSDM`, `PMAIZMTUSDM` ($/tonnellata), dal 1992, circa 2 mesi di ritardo.
- **Oro e argento: nessuna riserva gratuita.** FRED non pubblica più l'LBMA; `PGOLDUSDM`/`PSILVUSDM` non esistono;
  gli indici NASDAQ `NASDAQQGLDI`/`NASDAQQSLVO` non seguono il prezzo (1 anno: −16% contro +8% del future). Se Yahoo fallisce
  spesso su GitHub, valutare il Pink Sheet mensile della Banca Mondiale (file Excel, servirebbe una fonte nuova).
- WTI: il 20/04/2020 il future ha chiuso a −37 $: `yahoo.py` non scarta i valori negativi.
- I cambi di scadenza si vedono nei dati (es. il Brent di novembre scade l'ultimo giorno lavorativo di settembre).

### Asia e confronti tra Paesi (verificate il 01/10/2026)
- **BIS** `WS_CBPOL` (tassi di policy, giornalieri; USA/EA/JP/CN a fine settembre, **Corea ferma a fine agosto**): CN è l'**LPR a 1 anno**
  (dal 20/08/2019; prima tasso ufficiale sui prestiti), US il punto medio dell'obiettivo Fed, XM il tasso sui depositi BCE.
  `WS_LONG_CPI/M.<PAESE>.771` = inflazione annua mensile (JP e KR fino a luglio, CN/US/XM fino ad agosto). L'unità 628 sono gli indici.
- **Giappone**: JGB giornalieri dal Ministero delle Finanze (`jgbcme_all.csv` + `jgbcme.csv` del mese; 2A dal 1974, 10A dal 1986, 30A dal 1999). Riserva FRED solo per il 10A
  (`IRLTLT01JPM156N`, mensile). CPI: DBnomics `STATJP/CPIm/001` (totale), `/733` e `/740` (core, core-core): indici dal 1970, ultimo agosto, variazione annua con `yoy`. Il grafico del Giappone usa tutto Statistics Bureau; il BIS (`WS_LONG_CPI/M.JP.771`, un mese indietro) resta solo nel confronto dell'inflazione tra Paesi, per una fonte uniforme.
  FRED/OCSE per CPI Giappone e Cina sono **fermi** (2021 e 2025): non usarli.
- **Corea**: rendimento 10A solo mensile (FRED `IRLTLT01KRM156N`). Il 3A giornaliero esiste solo su ECOS (Bank of Korea),
  che richiede la registrazione con numero di telefono coreano: non usata. La chiave `sample` di ECOS restituisce al massimo 10 righe.
- **Cina**: non inclusi rendimento 10A, LPR 5A e PPI (nessuna fonte gratuita aggiornata: NBS su DBnomics è ferma a 02/2026, FRED/OCSE al 2022-2023).
  **CSI 300**: su Yahoo `000300.SS` restituisce una sola candela, quindi si usa l'ETF `510300.SS` (dal 2012, prezzo in yuan) con nota sul sito.
- Yahoo: `^N225`, `^HSI`, `^KS11`, `^GSPC`, `^STOXX50E`, `FTSEMIB.MI`, `JPY=X`, `CNY=X`, `KRW=X` (cambi "valuta per dollaro", riserve FRED `DEXJPUS`, `DEXCHUS`, `DEXKOUS`).
- Nel confronto delle valute (FX) i cambi yen/yuan/won sono capovolti (1/x) per essere letti nello stesso verso dell'euro (EUR/USD BCE).
