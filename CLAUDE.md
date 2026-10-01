# Dashboard macro

## Obiettivo
Dashboard macroeconomica **statica**, rigenerata ogni giorno e pubblicata su **GitHub Pages**.
L'utente è uno studente di finanza, principiante in programmazione: spiegare le scelte
in modo semplice e proporre un piano prima di modifiche importanti.

Roadmap in 3 fasi:
1. **USA** (fatta): politica monetaria, curva Treasury, spread, tassi reali, inflazione, credito, condizioni
2. **Eurozona** (fatta): DFR, curva AAA (proxy Bund), spread sovrani, HICP, HY in euro, EUR/USD. Fonte BCE, riserva FRED
3. **Asia** (fatta): tab Giappone, Cina, Corea del Sud + tab **Confronto globale** (fonti: BIS, Ministero delle Finanze giapponese, Statistics Bureau of Japan via DBnomics, FRED/OCSE, Yahoo)

Sezione **Azioni** (fatta) nelle tab USA ed Eurozona e benchmark ACWI con interruttore valuta locale/USD nel Confronto globale (fonte Yahoo).

Tab tematica **Commodities** (fatta): tabella di performance, energia, metalli preziosi e industriali, agricoli,
grafici commodities vs tassi USA. Fonte Yahoo Finance (future continui), riserva FRED (spot o medie mensili FMI).

## Ristrutturazione in corso
Il sito sta passando da 7 tab in una pagina sola a più pagine (Overview, Markets, Economies, Method & sources), in inglese.
**Piano approvato e stato degli step: [docs/ristrutturazione.md](docs/ristrutturazione.md)** (leggerlo a inizio sessione e aggiornare
la tabella "Stato" a ogni fine step). Un ramo per step (`ristrutturazione/step-N`); a fine step riepilogo e **attesa dell'ok dell'utente
prima del merge**. Prima di dichiarare finito uno step: `python tools/inventario.py controlla` (nessun grafico o serie perso/doppio;
mappa in `docs/mappa-grafici.yaml`). **Righe "How to read it" (`come_leggerlo`, regole dell'utente del 01/10/2026, valgono per tutto lo step 4 e oltre):** linguaggio semplice, una o due frasi,
comprensibili a chi non è del settore; prudenti e fattuali: descrivono relazioni storiche ("historically", "has tended to"), mai previsioni o certezze,
e citano le eccezioni importanti quando servono (es. oro e tassi reali dopo il 2022). **Alla fine di ogni pagina dello step 4 si mostra all'utente una tabella
con tutte le righe "How to read it" di quella pagina, da rivedere prima del merge.** Le pagine stanno in `dashboard/mercati/` e `dashboard/economie/` (registro in `__init__.py`)
e nel blocco `pagine:` di `config.yaml` (non esiste più il blocco `regioni`, né il campo `regione` delle serie).
Quando la ristrutturazione sarà finita, le sezioni "Struttura" e "Regole" qui sotto vanno riscritte.

## Regole del progetto
- **Testi del sito in INGLESE** (decisione del 01/10/2026): numeri `1,234.5` (punto decimale), date `30 Sep 2026`, scadenze `10Y`, unità `bp`/`pp`,
  periodi `1Y 5Y 10Y Max`. **Commenti e nomi interni del codice restano in italiano.** Nel config `nome` e `unita` sono in inglese (`"% y/y"`).
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
  Vale per tutte le serie calcolate (spread Brent-WTI, rapporto rame/oro, spread BTP-Bund, pendenze...). Codice: `data._calcola`.
- Una riserva può avere un'unità diversa dalla principale (`riserva: {..., unita: ..., nota: ...}`): la serie assume
  l'unità della riserva e l'avviso lo dice. Per questo non mettere nello stesso grafico serie che potrebbero finire
  in unità diverse (es. grano e mais sono in due grafici separati).
- **Controllo di freschezza** su tutte le serie: se l'ultimo dato supera la soglia (10 giorni giornaliere, 21 settimanali,
  75 mensili, 120 trimestrali, contati dalla fine del periodo) il sito mostra un avviso in cima. Serve a scoprire
  le serie "congelate" che non danno errore (vedi il caso HICP sotto).
- Grafici: un solo asse y per grafico (niente doppio asse), **colori fissi per Paese** (blocco `colori:` di `config.yaml`, campo `paese`/`colore` di ogni serie; le variabili CSS `--c-<chiave>` le scrive
  ogni pagina da lì; `tools/valida_palette.py --pairs all` verifica i colori anche per il daltonismo: rilanciarlo se se ne cambia uno).
  Più serie dello stesso colore nello stesso grafico si distinguono dallo stile della linea (piena, tratteggiata, puntinata). Ogni grafico
  deve avere `come_leggerlo` (una riga in parole semplici): la build avvisa se manca. Bande grigie = recessioni: NBER (serie `USREC`) per USA e Commodities,
  CEPR (date scritte a mano in `config.yaml` → `recessioni:`) per l'Eurozona.
  Per confrontare due serie con unità diverse si usa `charts.due_pannelli`: due pannelli sovrapposti con lo stesso
  asse del tempo, ognuno col suo asse y (il pannello in basso si può invertire). `app.js` gestisce più assi e gli
  assi invertiti (`layout.meta.assi_invertiti`).
- Sotto i grafici con future continui Yahoo compare la nota sui cambi di scadenza (piccoli salti di prezzo).
- Prima di aggiungere una serie, verificarne sulla fonte **storico e ultimo dato** (non solo che esista).
- **Soglia di freschezza personalizzata**: una serie può avere `soglia_giorni: N` in `config.yaml` (sostituisce quella standard).
  Va usata solo con il motivo scritto nel config (oggi: tasso BoK dal BIS, 45 giorni, perché il BIS pubblica la Corea con ~1 mese di ritardo).
- **Dati senza fonte gratuita aggiornata = righe eliminate, non serie "non disponibili"**: non si mettono in config (altrimenti
  l'avviso resterebbe acceso per sempre) e in fondo alla pagina si scrive una nota (`regions/asia.sezione_non_inclusi`).
- Asia: nessuna banda di recessione (nessuna fonte ufficiale e automatica). Grafici "base 100" (`charts.linee_base100`): il JavaScript
  ribasa a 100 all'inizio del periodo scelto, ma non prima della prima data in cui esistono tutte le serie (`base100()` in `static/app.js`).
- **Azioni**: sempre prezzi di chiusura senza dividendi (`auto_adjust=False` in `yahoo.py`), scritto in nota. Ogni indice ha **una sola
  definizione** in `config.yaml` (regione = tab di appartenenza); i grafici delle altre tab lo riusano per id (es. `^GSPC` è in `usa`
  e il Confronto globale lo legge da lì). Le schede "In sintesi" prendono le serie con `riepilogo: true` della loro regione; per le serie
  con `categoria: borsa` mostrano anche la variazione da inizio anno. `Sezione.tabella_performance` + `etichetta_performance` = tabella con 1S/1M/YTD/1A.
- **Grafici con due varianti** (`Grafico.varianti`, interruttore "Valuta locale / In USD"): la figura contiene le linee di entrambe, ognuna con
  `meta.variante`; `app.js` mostra solo quelle della variante scelta e ribasa a 100 considerando solo le linee visibili. Le linee senza variante
  (S&P 500, ACWI: già in USD) sono sempre visibili. In `charts.linee_base100` il 3° elemento facoltativo di ogni voce è `{slot, variante, benchmark}`
  (benchmark = linea spessa tratteggiata, colore del testo). Le borse in USD sono serie `calcolata` (indice / cambio "valuta per dollaro", tutto Yahoo):
  se un cambio passa alla riserva FRED la serie in USD è "non disponibile" con avviso, come da regola sulle serie calcolate.
- Gli id dei grafici non devono coincidere con gli id delle sezioni (`<regione>-<sezione>`, es. `usa-azioni`): l'elemento duplicato non si disegna.
- Non fare commit o push senza richiesta esplicita dell'utente.

## Struttura
```
config.yaml              regioni/tab, recessioni CEPR, elenco delle serie (id, fonte, nome, regione, categoria, unita,
                         trasformazione, riepilogo; facoltativi: riserva, componenti, operazione, fattore, decimali)
build.py                 comando unico: scarica → calcola → genera site/
dashboard/
  sources/               un modulo per fonte; ognuno espone scarica(id) -> pandas.Series
    __init__.py          registro FONTI {"fred", "ecb", "yahoo", "bis", "mof", "statjp"}
    fred.py              API ufficiale FRED (retry, errori senza chiave nel messaggio)
    ecb.py               API ECB Data Portal, senza chiave; id = "DATASET/CHIAVE" (es. FM/D.U2.EUR.4F.KR.DFR.LEV)
    yahoo.py             Yahoo Finance via yfinance (non ufficiale), id = ticker (es. CL=F); riusabile per borse e cambi
    bis.py               API BIS (stats.bis.org), senza chiave; id = "DATASET/CHIAVE" (es. WS_CBPOL/D.JP tassi di policy, WS_LONG_CPI/M.JP.771 inflazione a/a)
    mof_giappone.py      CSV del Ministero delle Finanze giapponese (JGB giornalieri); id = JGB_2Y, JGB_10Y, JGB_30Y
    statjp.py            Statistics Bureau of Japan via DBnomics (CPI core); id = "CPIm/001" (totale), "CPIm/733" (senza freschi) o "CPIm/740" (senza freschi né energia)
    errori.py            ErroreFonte
  data.py                classe Serie, lettura config, download con riserva, serie calcolate (A − B o A / B, stessa fonte),
                         trasformazioni (livello / yoy), variazioni 1s/1m/1a (+ da inizio anno), controllo di freschezza
  charts.py              grafici riutilizzabili: linee_storiche (recessioni, inversioni, linea di riferimento, unità sull'asse),
                         due_pannelli, curva_rendimenti, periodi_recessione (da USREC), periodi_da_trimestri (da elenco CEPR)
  regions/
    __init__.py          registro REGIONI {"usa", "eurozona", "commodities", "giappone", "cina", "corea", "globale"}
    modello.py           dataclass Sezione (anche tabella_performance) e Grafico (anche alto)
    usa.py               composizione della pagina USA
    eurozona.py          composizione della pagina Eurozona
    commodities.py       composizione della tab Commodities (tematica, non geografica)
    asia.py              attrezzi comuni a Giappone/Cina/Corea (grafici senza recessioni, nota "dati non inclusi")
    giappone.py cina.py corea.py   pagine dei tre Paesi
    globale.py           Confronto globale (policy, 10 anni, inflazione, valute e borse a base 100)
  render.py              prepara i dati per il template e scrive site/
templates/index.html.j2  pagina HTML (Jinja2)
static/style.css         stile, tema chiaro/scuro, layout per telefono
static/app.js            tab, disegno Plotly, pulsanti 1A/5A/10A/Max, colori dal tema
site/                    OUTPUT generato (non versionato: lo ricrea la GitHub Action)
.github/workflows/aggiorna-dashboard.yml   build giornaliera + pubblicazione su Pages
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
- **una serie**: un blocco in `config.yaml`; se deve apparire in un grafico, aggiungerla in `regions/<regione>.py`.
  Riserva automatica: `riserva: {fonte: fred, id: ..., trasformazione: ...}` (usata solo se la principale fallisce,
  segnalata con un avviso). Spread calcolato: `fonte: calcolata` + `componenti: [A, B]` → A − B nelle date comuni;
  `operazione: rapporto` → A / B, `fattore: 1000` moltiplica il risultato.
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

### Asia e Confronto globale (verificate il 01/10/2026)
- **BIS** `WS_CBPOL` (tassi di policy, giornalieri; USA/EA/JP/CN a fine settembre, **Corea ferma a fine agosto**): CN è l'**LPR a 1 anno**
  (dal 20/08/2019; prima tasso ufficiale sui prestiti), US il punto medio dell'obiettivo Fed, XM il tasso sui depositi BCE.
  `WS_LONG_CPI/M.<PAESE>.771` = inflazione annua mensile (JP e KR fino a luglio, CN/US/XM fino ad agosto). L'unità 628 sono gli indici.
- **Giappone**: JGB giornalieri dal Ministero delle Finanze (`jgbcme_all.csv` + `jgbcme.csv` del mese; 2A dal 1974, 10A dal 1986, 30A dal 1999). Riserva FRED solo per il 10A
  (`IRLTLT01JPM156N`, mensile). CPI: DBnomics `STATJP/CPIm/001` (totale), `/733` e `/740` (core, core-core): indici dal 1970, ultimo agosto, variazione annua con `yoy`. Pagina Giappone = tutto Statistics Bureau; il BIS (`WS_LONG_CPI/M.JP.771`, un mese indietro) resta solo nel Confronto globale, per una fonte uniforme tra Paesi.
  FRED/OCSE per CPI Giappone e Cina sono **fermi** (2021 e 2025): non usarli.
- **Corea**: rendimento 10A solo mensile (FRED `IRLTLT01KRM156N`). Il 3A giornaliero esiste solo su ECOS (Bank of Korea),
  che richiede la registrazione con numero di telefono coreano: non usata. La chiave `sample` di ECOS restituisce al massimo 10 righe.
- **Cina**: non inclusi rendimento 10A, LPR 5A e PPI (nessuna fonte gratuita aggiornata: NBS su DBnomics è ferma a 02/2026, FRED/OCSE al 2022-2023).
  **CSI 300**: su Yahoo `000300.SS` restituisce una sola candela, quindi si usa l'ETF `510300.SS` (dal 2012, prezzo in yuan) con nota sul sito.
- Yahoo: `^N225`, `^HSI`, `^KS11`, `^GSPC`, `^STOXX50E`, `FTSEMIB.MI`, `JPY=X`, `CNY=X`, `KRW=X` (cambi "valuta per dollaro", riserve FRED `DEXJPUS`, `DEXCHUS`, `DEXKOUS`).
- Nel Confronto globale i cambi yen/yuan/won sono capovolti (1/x) per essere letti nello stesso verso dell'euro (EUR/USD BCE).
