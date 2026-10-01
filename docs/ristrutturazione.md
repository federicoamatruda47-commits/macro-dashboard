# Ristrutturazione del sito (piano approvato) — COMPLETATA il 01/10/2026

Piano approvato dall'utente il 01/10/2026, con le scelte della sezione 0 e due aggiunte (vedi sotto).
**Questo file è la fonte di verità per ripartire dopo un'interruzione: aggiornare la tabella "Stato" alla fine di ogni step.**

## Stato

| Step | Cosa | Stato |
|---|---|---|
| 0 | Rete di sicurezza: inventario dei 56 grafici e delle serie + controllo automatico "nulla è perso / nulla è doppio" | **fatto e in `main`** |
| 1 | Motore multipagina (base template, menu a 2 righe, link relativi); le 7 tab diventano 7 pagine, stesso contenuto | **fatto e in `main`** |
| 2 | Inglese (testi, numeri, unità, date), campo `paese`, palette fissa per Paese, campo "Come leggerlo" | **fatto e in `main`** |
| 3 | Footer dei grafici (fonte + link + note), registro `contenuti/note.yaml`, pagine Method e Series status | **fatto e in `main`** |
| 4a | Mercati: Commodities | **fatto e in `main`** |
| 4b | Mercati: FX | **fatto e in `main`** |
| 4c | Mercati: Credit | **fatto e in `main`** |
| 4d | Mercati: Equities (con colonna "Last", vedi sotto) | **fatto e in `main`** |
| 4e-1 | Mercati: Rates & curves, parte 1 (tassi di policy, curve, rendimenti a 10 anni, pendenza e inversioni) | **fatto e in `main`** |
| 4e-2 | Mercati: Rates & curves, parte 2 (inflazione e tassi reali) | **fatto e in `main`** (con lo step 4 completo) |
| 5 | Economies (hub + 5 segnaposto + UNRATE in USA); `regioni` → `pagine` nel config; via le vecchie pagine e il Confronto globale | **fatto e in `main`** |
| 6 | Overview (14 numeri chiave con sparkline, "What changed this week", schede, avvisi); diventa `/` | **fatto e in `main`** |
| 7 | Rifinitura: peso pagine, link rotti, README e screenshot, CLAUDE.md, codice morto (opz.: nomi interni in inglese) | **fatto e in `main`** |
| 8 | Interruttore del tema chiaro/scuro (◐) previsto dal wireframe | **fatto e in `main`** |
| 9 | Economies per Paese: **verifica delle fonti** (solo ricerca, nessun codice): [economies-fonti.md](economies-fonti.md) | **fatto e in `main`** |
| 9b | Correzioni al piano (step 10 diviso in 10a/10b, debito italiano nello step 12, snapshot Banca Mondiale), solo documenti | **fatto e in `main`** |
| 10a | Economies, dati: `imf.py`, `worldbank.py`, `aggiorna_weo.py`, importatore del file WEO, snapshot, catalogo indicatori, freschezza a semestri, test (nessuna pagina nuova; solo Method e Series status) | **fatto sul ramo `ristrutturazione/step-10a`, attesa ok** |
| 10b | Economies, pagine: `country.html?c=ISO3`, blocco `paesi:`, link "→ Economy", note, righe "How to read it" | **fatto sul ramo `ristrutturazione/step-10b`, attesa ok** |
| 11 | Economies: Stati Uniti (primo paese del livello A, con il riquadro Markets) | da fare |
| 12 | Economies: Italia e Area euro (con il grafico sulla sostenibilità del debito italiano) | da fare |
| 13 | Economies: Regno Unito, Compare, rifinitura e CLAUDE.md | da fare |
| 14 | Overview: mappa interattiva (clic sul Paese → pagina del Paese) con elenco/ricerca dei Paesi per il telefono | da fare |

Flusso di lavoro: un ramo per step (`ristrutturazione/step-N`); a fine step riepilogo all'utente e **attesa dell'ok prima del merge** su `main`
(il merge pubblica il sito tramite GitHub Actions). Il merge si fa a fine di ogni step (non tutto alla fine), con `git push origin main`. Nessun commit/push fuori da questo flusso senza richiesta.

Strumenti di controllo: `python tools/inventario.py controlla` (deve passare a ogni step), `python tools/inventario.py sito` (dopo `python build.py`: controlla le pagine HTML vere e ne stampa il peso), `python tools/controlla_link.py` (link interni rotti, dopo `build.py`), `python -m unittest discover -s tests -t .` (test di `dashboard/movimenti.py`; con `PROVE_CON_RETE=1` anche gli episodi storici), `python tools/inventario.py salva`
(solo allo step 0, rigenera la baseline), `python tools/valida_palette.py --pairs all` (colori dei Paesi; da rilanciare se se ne cambia uno). Mappa vecchio grafico → nuovo posto: [mappa-grafici.yaml](mappa-grafici.yaml).

## Regole per le righe "How to read it" (richieste dall'utente il 01/10/2026, valgono per tutto lo step 4)

- linguaggio semplice, una o due frasi, comprensibili a chi non è del settore;
- prudenti e fattuali: descrivono relazioni storiche ("historically", "has tended to"), mai previsioni o certezze, e citano le eccezioni importanti quando servono (es. oro e tassi reali dopo il 2022);
- alla fine di ogni pagina si mostra all'utente una tabella con tutte le righe "How to read it" della pagina, da rivedere prima del merge.

## Aggiunte richieste dall'utente

1. Questo piano vive in `docs/ristrutturazione.md`, citato in CLAUDE.md; lo stato si aggiorna dopo ogni step.
2. **Tabella di performance di Equities: colonna "Last"** con l'ultimo livello di ogni indice (in punti, o nel prezzo dell'ETF),
   così non si perde la vista a livelli dei grafici assorbiti (Nikkei, CSI 300, Hang Seng, KOSPI). Nella tabella delle commodities
   la colonna "Ultimo" c'è già: la nuova tabella Equities la mantiene con questo nome inglese ("Last").

## 0. Scelte approvate

| # | Scelta | Motivo |
|---|---|---|
| 1 | **Inglese**: tutti i testi visibili, anche numeri (`1,234.5`), date (`30 Sep 2026`), scadenze (`10Y`), unità (`bp`), pulsanti (`1Y 5Y 10Y Max`). Via il locale italiano di Plotly. | Una sola lingua. |
| 2 | Nomi interni del codice e commenti **restano in italiano** per ora; cambia la regola in CLAUDE.md ("testi del sito in inglese"). Rinomina completa = step opzionale finale. | Nessun rischio inutile. |
| 3 | **L'inflazione sta in "Rates & curves"**, sezione "Inflation & real rates". | Non è una asset class; qui ci sono già breakeven e tassi reali. |
| 4 | **Bande di recessione** solo sui grafici di un singolo Paese (NBER USA, CEPR euro) e su Commodities; i confronti tra Paesi non le hanno. | Una banda USA su un confronto USA-Giappone fuorvia. |
| 5 | **UNRATE** in `Economies / USA` (unico grafico lì). | Nessuna serie persa vince su "pagina vuota". |
| 6 | "Petrolio" nei numeri chiave = **Brent** (`BZ=F`). | Riferimento internazionale. |
| 7 | Spread sovrani (BTP-Bund, OAT-Bund) in **Credit**, sezione "Sovereign spreads". | È rischio di credito sovrano. |

## 1. Mappa del sito

Una pagina HTML per riga; percorsi **relativi** (funzionano anche sotto `/nome-repo/` su GitHub Pages).

```
/                         Overview
/markets/                 hub Markets (5 schede)
  /markets/rates/         Rates & curves
  /markets/credit/        Credit
  /markets/equities/      Equities
  /markets/fx/            FX
  /markets/commodities/   Commodities
/economies/               hub Economies
  /economies/usa/         USA        (solo UNRATE + "more coming")
  /economies/italy/       Italy      (in arrivo)
  /economies/euro-area/   Euro area  (in arrivo)
  /economies/uk/          UK         (in arrivo)
  /economies/compare/     Compare    (in arrivo)
  (Japan, China, South Korea: voci "later")
/method/                  Method & sources
  /method/series/         Series status (tabella live di tutte le serie)
```
Ancore per sezione (`#curve-slope`) e per grafico (`#chart-<id>`).

## 2. Wireframe

### Menu (su ogni pagina, senza JavaScript)
```
Desktop
┌──────────────────────────────────────────────────────────────────┐
│ Macro Dashboard    Overview │ Markets │ Economies │ Method & sources │
├──────────────────────────────────────────────────────────────────┤
│ (2ª riga, solo dentro Markets) Rates & curves · Credit · Equities · FX · Commodities
└──────────────────────────────────────────────────────────────────┘
Telefono (375 px)
┌────────────────────────────┐
│ Macro Dashboard        ◐   │  ◐ = tema chiaro/scuro
│ Overview Markets Economies Method →   │  riga scorrevole, "Method" abbreviato
│ Rates · Credit · Equities · FX · Comm.→ │  2ª riga scorrevole
└────────────────────────────┘
```

### Overview (`/`)
```
Overview
Where rates, inflation and markets stand today — and what moved this week.
Updated 2 Oct 2026, 01:30 UTC · 128 series   [⚠ 2 stale series →] [ⓘ 3 fallback sources →]

KEY NUMBERS                          (1W / 1M / 1Y; le borse anche YTD)
 Policy & inflation   Fed funds · ECB depo · US CPI · EZ HICP                    (4)
 Rates                US 10Y · Euro AAA 10Y (Bund proxy) · BTP-Bund (monthly) · US 10Y-2Y   (4)
 Markets              S&P 500 · Euro Stoxx 50 · EUR/USD · Gold · Brent · VIX     (6)
 Ogni scheda: nome · valore · data del dato · sparkline 1 anno · variazioni. Frecce ▲▼ neutre.

WHAT CHANGED THIS WEEK                      size vs a normal week
 1  Brent oil          +8.2 %    ▮▮▮▮▮▮▮▮▮  3.4× normal   → Commodities
 2  Euro Stoxx 50      −3.1 %    ▮▮▮▮▮▮▮    2.6×          → Equities
 3  US 2Y yield        +14 bp    ▮▮▮▮▮▮     2.2×          → Rates
 4 …  5 …
 "×normal" = this week's move divided by the typical weekly move of the same series over the last 3 years.

EXPLORE
 [Rates & curves] [Credit] [Equities] [FX] [Commodities]
 [Economies: USA · Italy · Euro area · UK — coming soon]   [Method & sources]
```

### Pagina tipo: Rates & curves (`/markets/rates/`)
```
Markets › Rates & curves
H1: Rates & curves
Una riga: Policy rates, government yields and inflation across the US, euro area, Japan, China and Korea.

KEY NUMBERS   4–6 schede
ON THIS PAGE  [Policy rates] [Yield curves] [Yields over time] [Curve slope] [Inflation & real rates]   (chips scorrevoli)
⚠ Data warnings for this page (solo se riguardano serie di QUESTA pagina)

── Policy rates ──
 una riga sulla sezione
 ┌ Policy rates compared ───────────── [1Y][5Y][10Y][Max] ┐
 │  grafico, un colore per Paese
 │  Come leggerlo: …
 │  Source: BIS ↗ · Last data 30 Sep 2026 · Notes ›
 └────────────────────────────────────────────────────────┘
── Yield curves ── (2 grafici affiancati su desktop, impilati su telefono)
── Detail by country ── (grafici a singolo Paese con più serie del confronto)
‹ Previous page: Markets    Next page: Credit ›
```
Struttura uguale per tutte le pagine: titolo, una riga, numeri chiave, ancore, sezioni con grafici, navigazione.
Ogni grafico: titolo, figura, "Come leggerlo" (1 riga), footer (fonte con link, ultimo dato, link alle note).

## 3. Regole comuni

- **Colori fissi per Paese** (palette per daltonici, verificata in chiaro/scuro con il validatore della skill `dataviz` allo step 2):
  USA blu · Euro area arancio · Italia verde · Germania/AAA = colore dell'euro area · Francia verde acqua · UK viola ·
  Giappone rosso-vermiglio · Cina oro scuro · Corea azzurro · Mondo/ACWI grigio scuro tratteggiato.
  Più serie dello stesso Paese nello stesso grafico: stesso colore, stile diverso (pieno, tratteggiato, puntinato).
  Colore fisso anche per ogni commodity. Ogni serie ha un campo `paese`; il colore non dipende più dalla posizione (`slot`, `s1…s8`).
- **"Come leggerlo"**: campo obbligatorio su ogni grafico; la build avvisa se manca.
- **Sotto il grafico** solo fonte con link alla pagina della serie + link "Notes" se serve; "(fallback: FRED)" se è in uso la riserva.
- **Note lunghe** → `contenuti/note.yaml` (un id per nota), mostrate in Method raggruppate; ogni grafico rimanda alla sua.
- I grafici di confronto hanno serie nella stessa unità; se una riserva cambia l'unità, il grafico mostra l'avviso invece di mescolare.

## 4. Dove finisce ogni grafico (56 su 56)

Legenda: **kept** = resta com'è · **merged** = le sue serie entrano in un grafico di confronto · **moved** = spostato 1:1.
Il dettaglio leggibile dalla macchina è in [mappa-grafici.yaml](mappa-grafici.yaml).

### Rates & curves (15 grafici)
| Vecchio | Nuovo |
|---|---|
| `gl-policy` | **Policy rates compared** (kept) |
| `jp-policy`, `cn-lpr`, `kr-policy` | merged in "Policy rates compared" (stesse serie BIS) |
| `usa-dff` + `eur-dfr` | merged in un grafico nuovo "Fed funds effective & ECB deposit rate" |
| `usa-curva-oggi`, `eur-curva-oggi` | Yield curves: kept, affiancati |
| `gl-rendimenti` | **10-year yields compared** (kept) |
| `kr-ktb` | merged in "10-year yields" (stessa serie OECD mensile) |
| `usa-rendimenti`, `eur-rendimenti`, `jp-jgb` | Detail by country (kept) |
| `eur-pendenza` | merged in un grafico nuovo **Curve slope 10Y−2Y: US vs euro area** |
| `usa-spread` (10Y-2Y e 10Y-3M) | Detail by country (kept) |
| `gl-inflazione` | **CPI compared** (kept) |
| `cn-inflazione`, `kr-inflazione` | merged in "CPI compared" (stesse serie BIS) |
| `usa-inflazione`, `eur-inflazione`, `jp-inflazione` | Inflation detail (kept; il Giappone resta Statistics Bureau) |
| `usa-reali` | Inflation & real rates (kept) |

### Credit (5)
| Vecchio | Nuovo |
|---|---|
| `eur-hy` + HY di `usa-oas` | **High yield: US vs euro area** (nuovo confronto, stessa fonte ICE) |
| `usa-oas` (IG + HY) | kept in "US detail" |
| `usa-baa` | kept ("Long history") |
| `eur-spread-paesi`, `eur-spread-tutti` | Sovereign spreads (moved) |

### Equities (6 grafici + 1 tabella)
| Vecchio | Nuovo |
|---|---|
| tabelle performance USA, Eurozona + indici Asia/ACWI | **una tabella** Last / 1W / 1M / YTD / 1Y raggruppata per area (moved e unita) |
| `gl-borse` | **Equity indices compared**, interruttore Local / USD (kept) |
| `jp-nikkei`, `cn-csi300`, `cn-hangseng`, `kr-kospi` | merged in `gl-borse` e nella tabella; il livello in punti resta nella colonna **Last** |
| `usa-indici-azionari`, `eur-indici-azionari`, `usa-concentrazione` | Regional detail (kept) |
| `usa-vix` | Volatility (moved) |

### FX (6)
| Vecchio | Nuovo |
|---|---|
| `gl-valute` | **Currencies vs the dollar, base 100** (kept) |
| `eur-eurusd`, `jp-cambio`, `cn-cambio`, `kr-cambio` | "Exchange rates in levels" (kept: 4 grafici piccoli) |
| `usa-dollaro` | Broad dollar index (moved) |

### Commodities (13 + 1 tabella) e Economies
- Tutti e 13 i `com-*` e la tabella di performance passano **1:1**, con le bande NBER dove ci sono oggi.
- `usa-disoccupazione` → Economies / USA.

Altri elementi: le schede "In sintesi" per regione sono sostituite dai numeri chiave per pagina; le tabelle "Stato delle serie"
vanno in `/method/series/`; le note "dati non inclusi" (Cina, Corea) in Method › Known limits; gli avvisi vanno nell'Overview
(conteggi) e, per le serie di ogni pagina, in quella pagina.

## 5. "What changed this week": metodo

1. Candidate: serie giornaliere/settimanali con `movimenti: true` nel config (~40), esclusi spread calcolati non disponibili e serie "in ritardo".
2. Movimento: variazione sugli ultimi 7 giorni di calendario (bp per i tassi, % per prezzi e indici).
3. Normalità: deviazione standard delle variazioni a 7 giorni degli ultimi 3 anni (esclusa l'ultima settimana); meno di 100 osservazioni = esclusa.
4. Punteggio = |movimento| / deviazione standard, mostrato come "×normal".
5. Al massimo 1 serie per gruppo (`gruppo_movimenti`, es. 2Y e 10Y Treasury sono un solo gruppo).
6. Sotto 1,5× non si mostra; se nessuno supera la soglia: "A quiet week".
7. Le serie mensili non entrano (opzionale dopo: "New releases").

Modulo `dashboard/movimenti.py` con test su dati storici (es. il petrolio nel marzo 2020 deve risultare enorme).

## 6. Method & sources

`/method/`: 1) Sources (da `NOMI_FONTI`); 2) Freshness check (soglie lette dalle costanti di `data.py`, soglia Corea);
3) Fallback sources (spiegazione + elenco live delle serie che usano la riserva); 4) Calculated series (regola "stessa fonte", esempi);
5) Known limits (tutte le vecchie note lunghe, una voce ciascuna con ancora).
`/method/series/`: tabella "Stato delle serie" di oggi in una pagina sola.

## 7. config.yaml e cartelle

**config.yaml**: `regioni:` → `pagine:` (id, percorso, titolo, sottotitolo, genitore, stato, `numeri_chiave`); nuovo `paesi:` (nome, nome breve, colori);
per serie `regione` → `paese`, `riepilogo` sparisce (→ `numeri_chiave` per pagina + blocco `panoramica:`), nuovi facoltativi `etichetta_breve`,
`movimenti`, `gruppo_movimenti`, `url_fonte`; `nome` e `unita` in inglese (`"% a/a"` → `"% y/y"`); `recessioni:` e riserve invariati.

**Cartelle**:
```
dashboard/
  regions/  →  pagine/ { modello.py, comune.py (ex asia.py), mercati/{tassi,credito,azioni,valute,commodities}.py,
                         economie/{usa,...}.py (segnaposto), panoramica.py, metodo.py }
  movimenti.py (nuovo)   fonti_url.py (nuovo)
  render.py   scrive site/<percorso>/index.html per ogni pagina
contenuti/note.yaml (nuovo)
templates/  base.html.j2, panoramica, pagina, hub, metodo, serie + parti (_scheda, _grafico, _tabella)
static/     app.js senza tab; style.css con token colore dei Paesi
tools/      inventario.py (controllo "nulla è perso")
```
Il workflow GitHub non cambia (pubblica già tutta `site/`).

## 8. Rischi per le funzioni esistenti

| Funzione | Rischio | Contromisura |
|---|---|---|
| Freschezza | Gli avvisi usano `regione`; una serie può stare in più pagine | Una sola logica in `data.py`; avviso globale con conteggio unico + avviso per pagina; le serie senza grafico restano controllate |
| Riserve | Nei confronti una riserva con unità diversa romperebbe l'asse unico | Il grafico controlla le unità e mostra "non disponibile" col motivo; elenco riserve live in Method |
| Serie calcolate | Le nuove schede (BTP-Bund, borse in USD) potrebbero mescolare fonti | `data._calcola` non si tocca; schede e "movimenti" mostrano "n.d." come i grafici |
| Base 100 | Il colore oggi segue lo `slot` | Il calcolo "non prima della prima data comune" resta in `app.js`; controllo a vista sui 3 grafici base 100 |
| Interruttore valuta | JS con `meta.variante` | Resta solo in Equities; test: cambio variante → linee giuste, ribasatura corretta, ACWI sempre visibile |
| Asse invertito / due pannelli | `app.js` riscritto in parte | Commodities passa 1:1; confronto a vista di tutti i grafici a due pannelli |
| Formati | `tipo_variazione` e `_suffisso` si basano su stringhe di unità (`"% a/a"`, `startswith("%")`) | Cambio unità e logica nello stesso step |
| Peso | 5,9 MB oggi (un solo `index.html`) | Misura a ogni step; se una pagina supera ~1 MB, dati dei grafici caricati a parte quando entrano a schermo |
| Link | Indirizzi assoluti si rompono sotto `/repo/`; i vecchi `#usa` spariscono | Link relativi; il vecchio `/` diventa Overview |
| Id duplicati | Una serie in più grafici o pagine | Id di grafico unici sul sito, ancora `chart-<id>` |

## 9. Step (dettaglio e verifiche)

0. **Rete di sicurezza**: inventario (56 grafici, 94 serie, dimensione HTML) e controllo automatico. *Verifica*: il controllo passa sul sito attuale.
1. **Motore multipagina**: `render.py` scrive più pagine, base template, menu a 2 righe, link relativi. *Verifica*: 56/56 grafici, menu leggibile a 375 px, link ok.
2. **Inglese e colori**: testi, numeri, unità, `paese`, palette fissa, "Come leggerlo". *Verifica*: nessun testo italiano visibile, stesso Paese = stesso colore, tema scuro ok.
3. **Footer dei grafici e Method**: registro note, fonte+link, pagine Method e Series status. *Verifica*: ogni vecchia nota nel registro, nessuna nota lunga sotto i grafici.
4. **Mercati**, una pagina per volta (4a Commodities, 4b FX, 4c Credit, 4d Equities, 4e Rates & curves). *Verifica*: controllo "nulla è perso / nulla è doppio", confronto a vista nuovi/vecchi.
5. **Economies** + `regioni` → `pagine` + rimozione vecchie pagine e Confronto globale. *Verifica*: nessuna vecchia pagina, 56 grafici mappati.
6. **Overview**. *Verifica*: test del calcolo sui dati storici, schede con serie non disponibile.
7. **Rifinitura**.

## 10. Economies per Paese: piano degli step 9–14 (rivisto il 01/10/2026 dopo le decisioni dell'utente)

Obiettivo: un **modello unico** di pagina per Paese, a due livelli. **A** (USA, Italia, Area euro, Regno Unito): pagine proprie, dati mensili/trimestrali da fonti nazionali o ufficiali.
**B** (tutti gli altri paesi, ~194): **una sola pagina con selettore**, dati annuali FMI WEO + Banca Mondiale. Tabelle e verifiche: [economies-fonti.md](economies-fonti.md). Bozza di e-mail all'FMI: [bozza-email-fmi.md](bozza-email-fmi.md).

### Decisioni dell'utente (01/10/2026)
- **Livello B**: pagina unica `economies/country.html?c=ITA` (codice ISO3 nell'URL): ogni Paese ha un indirizzo diretto, così la mappa e le pagine Markets lo possono aprire. **Livello A**: pagine proprie (`economies/usa/`, ...), anche se i quattro Paesi sono anche nella pagina B (che porta un rimando alla pagina completa).
- **Dati FMI**: snapshot nel repository, aggiornato **a ogni nuovo WEO** (aprile/ottobre; quello di ottobre 2026 esce a metà mese). Pro/contro di API contro file scaricato a mano: in economies-fonti.md (consiglio: script lanciato a mano sul PC dell'utente, con l'importatore del file come riserva). Controllo di freschezza **a semestri**: avviso oltre 210 giorni dalla pubblicazione del WEO; Banca Mondiale oltre 15 mesi.
- **Termini FMI**: bozza di e-mail pronta in `docs/bozza-email-fmi.md`, la invia l'utente; fino alla risposta si procede solo con la citazione visibile.
- **Debito/deficit USA**: amministrazioni pubbliche (FMI) come dato principale; federale (FRED) solo come grafico aggiuntivo, etichettato "Federal government only".
- **Fiducia**: ESI per Italia e area euro; Michigan solo se la licenza lo consente (si legge nello step 11); niente PMI/ISM/GfK (quindi il UK non ha fiducia).
- **Banca Mondiale**: disoccupazione e occupazione sono **stime modellate ILO** (etichetta "ILO modelled estimate" e nota nel registro). **WGI**: il percentile **non esiste più** (WGI 2.0, 2025); si usa il **punteggio 0-100** (`GOV_WGI_CC.SC`) con intervallo al 90%, etichettato "score", non "rank". **Nessun rango** (deciso).
- **UK**: l'API ONS non è cambiata: `HF6X` (debito netto/PIL) e `AA6H` (partite correnti/PIL) esistevano, il 404 era un percorso sbagliato; prezzi delle case dall'**UK HPI di HM Land Registry** (verificato: dal 1995-01 al 2026-07).

### Mappa e collegamenti Markets ↔ Economies (richiesti dall'utente)
Il campo `paese` sulle serie **esiste già** (chiavi `us`, `ea`, `it`, `uk`, `jp`, `cn`, `kr`, `fr`, `de`, `global`, più i gruppi delle materie prime): non serve aggiungerlo, serve un **blocco `paesi:` in `config.yaml`** che per ogni chiave dica il codice ISO3, il nome e la pagina di destinazione (A se `attiva`, altrimenti `country.html?c=<ISO3>`; l'area euro non è un Paese del livello B: solo pagina A).
1. **Step 10b — collegamenti**: blocco `paesi:`; link "→ Economy" sotto ai grafici Markets che hanno un solo Paese (per i grafici di confronto, un elenco di link ai Paesi mostrati, nel piè accanto a Source); regola "mai un link morto" (se la pagina del Paese non c'è, non si mostra). Pagina `country.html?c=` con il selettore e URL condivisibile.
2. **Step 11–13 — riquadro Markets nella pagina del Paese** (A): ogni pagina mette in alto i numeri chiave di mercato di quel Paese (rendimento 10Y, borsa, cambio, politica monetaria) con link alla pagina Markets; per i Paesi del livello B che hanno serie di mercato (Giappone, Cina, Corea, Francia, Germania) lo stesso riquadro compare nella pagina `country.html` (generato dal campo `paese` delle serie).
3. **Step 14 — mappa interattiva nell'Overview**: mappa mondiale (SVG con i confini Natural Earth, di pubblico dominio, semplificati; niente Plotly geo per non appesantire: ~150-250 KB). **Indicatore predefinito: PIL pro capite a PPA**; interruttori: crescita reale, inflazione, disoccupazione, debito/PIL, controllo della corruzione (score 0-100). **Si mostra sempre l'ultimo anno effettivo** (dato reale, mai una proiezione del WEO; `LATEST_ACTUAL_ANNUAL_DATA` per l'FMI, ultimo anno con valore per la Banca Mondiale), e **l'anno compare nel tooltip e nell'elenco di ogni Paese** perché i Paesi hanno anni diversi, **clic sul Paese → pagina del Paese** (A: pagina propria; B: `country.html?c=ISO3`), tooltip con il valore **e l'anno del dato**. **Accanto alla mappa un elenco dei Paesi con ricerca** (campo di testo che filtra per nome, ogni voce porta alla pagina del Paese e mostra lo stesso valore): sul telefono i Paesi piccoli non si possono cliccare sulla mappa, quindi l'elenco è la via principale a 375 px (verifica: tutti i ~194 Paesi raggiungibili da telefono senza usare la mappa). È uno step a parte perché richiede che le pagine Paese esistano e perché pesa sull'Overview (target < 1 MB compressi invariato); se lo step 13 risultasse corto si può unire.

### Step
- **Step 10a: dati** (nessuna pagina nuova; cambiano solo Method e Series status).
  Fonti nuove `dashboard/sources/imf.py` (SDMX `api.imf.org`) e `worldbank.py` (WDI e WGI), con `NOMI_FONTI` e link in `fonti_url.py`. `tools/aggiorna_weo.py` (lanciato a mano dall'utente, scrive `dati/weo/`) **e l'importatore del file WEO** (stesso formato di snapshot, scritto comunque come riserva).
  Snapshot: `dati/weo/` (FMI) e `dati/bm/` (Banca Mondiale), formato comune (paese ISO3, indicatore, anno, valore, `stima` sì/no, data di pubblicazione). La build giornaliera legge solo gli snapshot e non chiama mai l'FMI.
  **Workflow Banca Mondiale** (`tools/aggiorna_bm.py` + workflow mensile che apre una PR solo se i dati cambiano): le PR aperte con `GITHUB_TOKEN` **non fanno partire altri workflow**, quindi il workflow stesso, **prima di aprire la PR, esegue i test e i controlli** (`unittest`, `build.py`, `inventario.py`, `controlla_link.py`) e **scrive l'esito nella descrizione della PR** (superati/falliti, con l'elenco delle differenze nei dati); se i controlli falliscono la PR non si apre (o si apre contrassegnata "checks failed" con il log). **Prima di scrivere `imf.py` e `worldbank.py` si prova l'accesso alle due API da GitHub Actions** (workflow manuale di prova, esito nel registro): decide se l'FMI si può chiamare anche dal workflow o solo a mano.
  Catalogo `indicatori:` e lista dei paesi in `config.yaml` (non ~2.300 voci di serie); frequenze `semestrale` (210 giorni dalla pubblicazione del WEO) e `annuale` (15 mesi) nel controllo di freschezza, con il motivo scritto nel config; reale / stima / proiezione distinti (`LATEST_ACTUAL_ANNUAL_DATA`).
  Method: fonti e freschezza dei nuovi dati; Series status: gli indicatori annuali (per indicatore, non per Paese: 194 paesi non si elencano riga per riga). Test sulle funzioni pure: lettura dello snapshot, freschezza a semestri (WEO di aprile e ottobre a metà mese), importatore del file con un file di prova.
  *Verifica*: snapshot completo (tutti gli indicatori per tutti i paesi, con elenco dei paesi senza dati), importatore e script danno lo stesso snapshot sul WEO di aprile 2026, nessuna pagina cambia (`inventario.py` e `controlla_link.py` invariati), Method e Series status aggiornati.
- **Step 10b: pagine** (dopo l'ok sul 10a).
  Modello di pagina con sezioni fisse (Output & growth, Prices, Labour, Public finances, External, Governance, IMF outlook); pagina `economies/country.html?c=ISO3` (un solo file dati compresso, < 1 MB, JavaScript che legge il parametro `c`, `noscript` con link alla scelta; hub e Overview rimandano ad essa); blocco `paesi:` e link "→ Economy" sotto i grafici Markets; note nel registro (ILO modellato, WGI, stime FMI, "non inclusi"); righe "How to read it" e **tabella da rivedere prima del merge**.
  *Verifica*: tutti i Paesi si aprono dall'URL diretto, peso della pagina, `inventario.py`, `controlla_link.py` (anche i link con `?c=`), nessun link morto da Markets.
- **Step 10c: ridisegno dell'hub Economies** (proposta approvata il 01/10/2026: vedi la sezione "Step 10c" qui sotto; fatto sul ramo, in attesa del merge; si fa prima di riempire le pagine A, così le pagine nuove entrano già nel posto giusto).
- **Step 11: Stati Uniti** (`economies/usa`): PIL, inflazione, lavoro (disoccupazione, occupazione 25-54), debito e deficit PA dal FMI + grafico aggiuntivo federale FRED, partite correnti (NETFI/GDP), popolazione, prezzi delle case (FHFA), Michigan solo se la licenza lo consente, previsioni FMI, riquadro Markets. Riga "How to read it" per grafico e **tabella da rivedere prima del merge**.
- **Step 12: Italia ed Area euro**: Eurostat con `EA21` (nota sul passaggio a 21 paesi), HICP BCE, ESI, prezzi delle case, deficit e debito. **Grafico sulla sostenibilità del debito italiano**: variazione annua del debito/PIL scomposta in **saldo primario + effetto r−g + aggiustamento stock-flussi (residuo)**, tutte le componenti da Eurostat (serie, codici e prova sui dati nella sezione "Sostenibilità del debito italiano" di economies-fonti.md; formula e definizioni da scrivere nella nota del registro e nella riga "How to read it"; test sulla scomposizione: le componenti sommano alla variazione del debito/PIL).
  *Formula nella nota del registro*: **Δd = −saldo primario + (i − g)/(1 + g) · d₋₁ + SFA**, con d = debito/PIL, i = interessi dell'anno / debito di fine anno precedente, g = crescita del PIL nominale; si calcola da valori **in milioni di euro** (debito, saldo, interessi, PIL) e si esprime in % del PIL solo alla fine.
  *SFA grande nel 2022–25: ipotesi da verificare* (non ancora confermate): (a) **crediti d'imposta Superbonus** (deficit registrato per competenza negli anni dei lavori, effetto sul debito per cassa/compensazioni negli anni dopo); (b) variazione della **liquidità del Tesoro** (depositi); (c) **scarti di emissione** (differenza tra valore di emissione e valore nominale dei titoli); (d) **titoli indicizzati** all'inflazione (rivalutazione del capitale). **Prima di scrivere la riga "How to read it" si cerca conferma su fonti ufficiali** (UPB, Banca d'Italia, ISTAT/Eurostat sulle note EDP) e si scrive solo ciò che è confermato. **Avvertenza**: la notifica EDP di ottobre 2026 rivedrà gli ultimi anni: i dati vanno riletti prima del merge e la nota lo dice. Da trovare: partite correnti (Eurostat `bop_c6_q` con le dimensioni giuste / BCE `BP6`; `tipsbp20` ha solo l'Italia annuale).
- **Step 13: Regno Unito, Compare, rifinitura**: ONS (`HF6X`, `AA6H`, `J5IJ`/`DZLS`, `D7G7`, `MGSX`, `LF24`; **deficit = `DZLS` ÷ `YBHA` con numeratore e denominatore sullo stesso periodo**: somma dei 12 mesi (4 trimestri) di `DZLS` divisa per il PIL degli stessi 12 mesi (4 trimestri di `YBHA`), niente PIL di un anno diviso un deficit di un altro; test sulle funzioni pure e nota nel registro), UK HPI, pagina `compare`, schede "later" di Giappone/Cina/Corea sostituite dal livello B, CLAUDE.md e mappa grafici aggiornati.
- **Step 14: mappa interattiva** nell'Overview, con elenco e ricerca dei Paesi (vedi sopra).

Ogni step: un ramo, tabella delle righe "How to read it" da rivedere, test + `build.py` + `inventario.py` + `controlla_link.py`, **attesa dell'ok prima del merge**.

### Step 10c: hub Economies con ricerca e riquadri dei Paesi (proposta, ramo `ristrutturazione/step-10c`)

**Oggi**: l'hub `economies/` ha 9 schede (USA, Italy, Euro area, UK, Compare, Japan, China, South Korea, Country explorer), quasi tutte "coming soon", e la ricerca vive solo in `country.html`
(selettore a tendina in `paese.js` + elenco di link per regione, senza numeri). **Obiettivo**: l'hub diventa l'indice di tutta la sezione: ricerca fissa, "Featured", poi i 218 Paesi per regione con due numeri ciascuno.

**Dati misurati** (build del 01/10/2026): 218 Paesi in 7 regioni della Banca Mondiale (Europe & Central Asia 58, Sub-Saharan Africa 48, Latin America & Caribbean 42, East Asia & Pacific 38,
Middle East/North Africa/Afghanistan/Pakistan 23, South Asia 6, North America 3). `ultimi-valori.json` ha già `gdp_growth` (215 Paesi) e `inflation_average` (197), ciascuno `[valore, anno effettivo]`;
mancano la crescita per VGB, GIB, PRK e l'inflazione per 21 Paesi: il riquadro scrive "—" (mai un valore inventato). Gli anni effettivi della crescita vanno dal 2010 al 2025 (2024 per 104 Paesi, 2025 per 75): **l'anno sta sempre accanto al valore**.

**Un solo componente** (nessuna terza versione): macro Jinja `ricerca_paesi` in `templates/_componenti.html.j2` + `static/elenco-paesi.js`. Il macro scrive **HTML già completo** (barra di ricerca, "Featured" facoltativo, regioni, riquadri-link con i numeri),
quindi non serve scaricare altri file e senza JavaScript restano link normali. Il JavaScript fa solo tre cose: filtra, aggiorna il contatore, nasconde le regioni vuote. La funzione di ricerca (`ElencoPaesi.cerca`: nome, nome originale della fonte, ISO3; normalizza gli accenti) è **la stessa** che oggi sta in `paese.js` e che userà il selettore a tendina di `country.html?c=`: si sposta nel nuovo file e `paese.js` la chiama.
Usi: (1) hub `economies/`; (2) `country.html` **senza** `c` (sostituisce "All countries": il selettore a tendina con Previous/Next resta solo con un Paese aperto, così non ci sono due barre di ricerca); (3) elenco accanto alla mappa (step 14), con la variante `compatta` e un evento `elenco:scelta` per evidenziare il Paese sulla mappa.
Il testo e i numeri dei riquadri sono prodotti da una funzione pura in `dashboard/paesi.py` (`riquadri_paesi`, testata): stessa regola dei link di sempre (`destinazione`: pagina A solo se `completa: true`, altrimenti `country.html?c=ISO3`; l'area euro, senza ISO3, resta una scheda "coming soon" senza link).

**Wireframe desktop** (larghezza ~1100 px; la barra resta in vista sotto il menu durante lo scorrimento):
```
┌ menu a due righe (come ora) ─────────────────────────────────────────────┐
│ Economies                                                                │
│ Annual data for 218 countries… · Updated 01 Oct 2026                     │
├──────────────────────────────────────────────────────────────────────────┤
│ [ 🔍 Search a country or a code (ITA, JPN…)            ✕ ]   218 countries│  ← fissa
├──────────────────────────────────────────────────────────────────────────┤
│ FEATURED                                                                 │
│ ┌United States┐ ┌Euro area┐ ┌Italy────┐ ┌United Kingdom┐ ┌China─┐ ┌Japan┐│
│ │USA          │ │soon     │ │ITA      │ │GBR           │ │CHN   │ │JPN  ││
│ │Growth 2.1%  │ │         │ │Gr. 0.5% │ │Gr. 1.3% 2025 │ │…     │ │…    ││
│ │ 2025        │ │         │ │Infl. …  │ │Infl. …       │ │      │ │     ││
│ └─────────────┘ └─────────┘ └─────────┘ └──────────────┘ └──────┘ └─────┘│
│ ┌Compare (coming soon)┐                                                  │
│ REGIONS:  North America · Latin America · Europe · Middle East · …  (salti)
│ EUROPE & CENTRAL ASIA (58)                                               │
│ ┌Albania───┐ ┌Andorra───┐ ┌Armenia───┐ ┌Austria───┐ ┌Azerbaijan┐ …       │
│ │ALB       │ │AND       │ │ARM       │ │AUT       │ │AZE       │        │
│ │Growth 4.0%│ │Gr. 3.9%  │ │Gr. 7.2%  │ │Gr. 0.6%  │ │Gr. 4.2%  │        │
│ │ (2024)   │ │ (2025)   │ │ (2025)   │ │ (2025)   │ │ (2024)   │        │
│ │Infl. 2.2%│ │…         │ │…         │ │…         │ │…         │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
└──────────────────────────────────────────────────────────────────────────┘
```
Griglia a 5-6 colonne (`auto-fill, minmax(168px, 1fr)`). Riquadro: nome (grassetto, fino a 2 righe), codice ISO3 in piccolo, "Real growth 2.1% · 2025", "Inflation 3.0% · 2025" (inflazione = media annua dei prezzi al consumo, come nella pagina del Paese); "WB only" per i Paesi senza dati FMI (come oggi). Tutto il riquadro è il link (area di tocco ≥ 44 px).

**Wireframe telefono (375 px; gutter 16 px, contenuto 343 px)**:
```
┌───────────────────────────┐
│ ☰ menu (come ora)         │
│ Economies                 │
│ Annual data for 218…      │
├───────────────────────────┤  ← sotto il menu, fissa
│ [🔍 Search a country   ✕ ]│
│ 218 countries             │
├───────────────────────────┤
│ FEATURED                  │
│ ┌United States┐┌Euro area┐│  2 colonne (~165 px)
│ │USA  Gr. 2.1%││soon     ││
│ │     (2025)  ││         ││
│ └─────────────┘└─────────┘│
│ ┌Italy────────┐┌UK───────┐│
│ ┌China────────┐┌Japan────┐│
│ ┌Compare──────┐           │
│ Jump to: North America ·… │  ← catene di salto: vanno a capo, non scorrono
│ EUROPE & CENTRAL ASIA (58)│
│ ┌Albania──────┐┌Andorra──┐│
│ …                         │
└───────────────────────────┘
```
Rischio: menu a due righe + barra di ricerca fissi occupano parte dello schermo basso del telefono. **Regola**: si misura nel browser a 375×667; se menu + barra superano ~150 px, sul telefono resta fissa solo la barra (il menu scorre via). Nessuno scorrimento orizzontale: nomi lunghi vanno a capo (`overflow-wrap: anywhere`), le catene di salto vanno a capo e non scorrono.

**Comportamento della ricerca**: filtra mentre si scrive (nome mostrato, nome originale della fonte — "Korea, Rep." trova South Korea —, ISO3; accenti ignorati); con una ricerca attiva "Featured" e le catene di salto si nascondono (altrimenti USA comparirebbe due volte), le regioni senza risultati spariscono, il contatore dice "12 of 218 countries" (`aria-live`); nessun risultato = "No country matches “xyz”" con il pulsante "Clear"; Esc o ✕ svuotano; Invio apre il primo risultato; l'ordine resta quello per regione e alfabetico. Senza JavaScript: la barra non compare, i riquadri sono link e i numeri sono nell'HTML (`<noscript>` spiega che la ricerca ne ha bisogno).

**Bandiere — raccomandazione: senza.** (1) Le emoji delle bandiere **non si vedono su Windows** (Chrome/Edge mostrano le due lettere del codice): inutilizzabili per un sito pubblico. (2) Le bandiere SVG a licenza libera esistono (per esempio la raccolta *flag-icons*, MIT), ma ne servirebbero 218 file, di peso molto diverso (le bandiere con stemma sono molto più pesanti di quelle a strisce; ordine di grandezza da misurare se le vuoi: da qualche centinaio di KB a oltre 1 MB in totale), oppure 218 richieste in più con `loading="lazy"`. (3) **Regola già nostra**: per Taiwan, Kosovo, Cisgiordania e Gaza, Hong Kong, Macao, Groenlandia ecc. usiamo il nome della fonte "senza interpretazioni nostre"; una bandiera è un'interpretazione in più (quale per la Cisgiordania e Gaza? per Taiwan?) e porterebbe una discussione che non serve a un sito di dati. Il codice ISO3 in piccolo dà già un riconoscimento rapido. Se in seguito le vuoi, si aggiunge in un unico punto (il macro) con un elenco esplicito di eccezioni.

**Peso stimato**: ogni riquadro ~330 byte di HTML → ~70 KB grezzi, ~12-15 KB compressi per l'hub (oggi ~2 KB) e circa +3 KB per `country.html` (che ha già l'elenco: 13 KB); `elenco-paesi.js` ~3 KB; nessun nuovo file di dati né richiesta di rete. Si misura con `gzip` a fine lavoro e si scrive nel registro.

**File toccati**: `dashboard/paesi.py` (`riquadri_paesi`), `dashboard/render.py` (l'hub Economies riceve `riquadri`; `ultimi_valori` passa dalla scrittura dei dati alla build senza rileggere il JSON), `templates/_componenti.html.j2` (macro), `templates/hub.html.j2`, `templates/paese.html.j2` (sostituisce "All countries"), `static/elenco-paesi.js` (nuovo), `static/paese.js` (usa `ElencoPaesi.cerca`, legge i riquadri al posto dell'elenco), `static/style.css`, `config.yaml` (campo `in_evidenza: true` sulle voci del blocco `paesi:` o sulle pagine dell'hub per l'elenco Featured e il loro ordine), `tests/test_paesi.py`, `tools/controlla_link.py` (controlla anche i link dei riquadri), `CLAUDE.md`, `docs/mappa-grafici.yaml` solo se cambia qualche promessa (non dovrebbe).

**Featured**: USA, Euro area, Italy, UK, China, Japan, poi Compare. Per la regola dei link, finché le pagine A non sono `completa: true`, USA/Italy/UK portano a `country.html?c=ISO3` (con i numeri), non alle pagine vuote "coming soon" di oggi; quando una pagina A è finita il link cambia da solo. L'area euro e Compare restano schede "coming soon" senza link. South Korea esce dall'evidenza (resta nella sua regione).
La vecchia scheda "Country explorer" sparisce dall'hub (lo è l'hub); `country.html` senza parametro continua a esistere (vecchi link, mappa).

**Test**: `riquadri_paesi` (regola dei link, "—" quando manca un valore, anno accanto al valore, nome originale della fonte, ordine per regione e alfabetico, nessun Paese perso né doppio: 218), un test che i riquadri dell'hub e di `country.html` vengono dalla stessa funzione, `inventario.py sito` e `controlla_link.py` invariati o estesi.

**Verifica nel browser** (preview, desktop e 375 px, chiaro e scuro): ricerca per nome, per nome della fonte ("Korea, Rep."), per ISO3 ("jpn"), per accenti, nessun risultato, Esc/✕; contatore; clic su un riquadro normale, su un Featured (USA → `country.html?c=USA`) e su una scheda senza link (non cliccabile); barra fissa durante lo scorrimento (altezza misurata); nessuno scorrimento orizzontale a 375 px (`scrollWidth`); cambio del tema con ricerca attiva (colori leggibili, contrasto ≥ 3:1 sul bordo, ≥ 4,5:1 sul testo); `country.html` senza `c` (stesso componente) e con `c=ITA` (selettore a tendina che usa la stessa ricerca); JavaScript disattivato (elenco di link); console senza errori; peso.

**Domande aperte** (con la mia scelta predefinita se non rispondi):
1. Featured: USA, Italy e UK portano a `country.html?c=` finché non sono `completa` (regola esistente), invece che alle pagine A vuote. **Predefinito: sì.**
2. Ordine delle regioni: dalla più "vicina" al resto (North America, Latin America & Caribbean, Europe & Central Asia, Middle East…, Sub-Saharan Africa, South Asia, East Asia & Pacific) o alfabetico? **Predefinito: l'ordine geografico qui sopra.**
3. Bandiere: **predefinito: nessuna**.

**Approvazione e aggiunte dell'utente (01/10/2026)**: risposte 1 sì, 2 ordine geografico, 3 nessuna bandiera. Aggiunte: (1) ricerca senza accenti (Curacao = Curaçao) e **nomi alternativi** in `config.yaml` (`nomi_alternativi:`: Turkey/Türkiye, Ivory Coast, Czech Republic, Burma, Holland...) con un test che li trova tutti; (2) numeri dei riquadri in colore neutro, niente verde/rosso; (3) **la scheda "Euro area coming soon" resta solo fino allo step 12**: se lo step slitta si toglie da `hub_economies.in_evidenza` (promemoria scritto anche nel config). Stessa regola per **"Compare coming soon"**: resta solo fino allo step 13 (pagina `economies/compare`); se lo step slitta si toglie da `hub_economies.pagine_in_evidenza` (promemoria nel config).
Scelte in fase di codice: la variante `compatta` e l'evento `elenco:scelta` per la mappa **non** sono stati scritti (nessun uso oggi): si aggiungono nello step 14; il macro, la ricerca condivisa (`ElencoPaesi.cerca`) e le chiavi di ricerca già ci sono. La regola del telefono si è applicata: testata (129 px) + barra (83 px) = 212 px su 812 (26%), quindi sul telefono resta fissa solo la barra.

### Punti aperti: chiusi dall'utente il 01/10/2026
- **WGI**: solo il punteggio 0-100 con l'intervallo al 90%; **nessun rango** calcolato (e nessuna dicitura "rank").
- **Mappa**: predefinito PIL pro capite a PPA; interruttori crescita reale, inflazione, disoccupazione, debito/PIL, controllo della corruzione; ultimo anno effettivo (non proiezione) con l'anno nel tooltip; elenco/ricerca dei Paesi accanto alla mappa.
- **Se l'FMI rifiuta lo script**: si usa l'**importatore del file WEO** scaricato a mano (non si ripiega sulla sola Banca Mondiale). L'importatore va scritto comunque nello step 10, con lo stesso formato dello snapshot.

## Registro

- 01/10/2026: piano approvato; creato il ramo `ristrutturazione/step-0`.
- 01/10/2026: step 0 completato sul ramo (piano salvato, CLAUDE.md aggiornato, `tools/inventario.py` + baseline: 56 grafici, 3 tabelle, 94 serie; sito di partenza 5.951.736 byte). Attesa ok dell'utente per il merge.
- 01/10/2026: step 0 unito in `main` (e pubblicato con push).
- 01/10/2026: step 1 completato sul ramo `ristrutturazione/step-1`: `dashboard/pagine.py` (percorsi relativi, menu a 2 righe), `render.py` scrive `site/<regione>/index.html` + home provvisoria,
  template `base/pagina/home/_componenti`, avvisi filtrati per le serie di ogni pagina, ancora `#chart-<id>` su ogni grafico, redirect dei vecchi `/#usa`. `config.yaml`: `descrizione` per regione e blocco `menu:` (provvisori fino allo step 5).
  Pesi (MB): usa 1,54 · globale 1,82 · commodities 0,85 · eurozona 0,75 · giappone 0,50 · cina 0,26 · corea 0,21 (prima: 5,95 in un file solo). Controlli: `inventario.py controlla` e `sito` OK (56/56).
- 01/10/2026: step 1 unito in `main`.
- 01/10/2026: step 2 completato sul ramo `ristrutturazione/step-2`. Sito tutto in inglese (testi, nomi serie e unità in `config.yaml`, messaggi d'errore delle fonti, numeri `1,234.5`,
  date `30 Sep 2026`, `bp`/`pp`, `1Y 5Y 10Y Max`, orario di aggiornamento in UTC; via il locale italiano di Plotly). Colori: blocco `colori:` in `config.yaml` + campi `paese`/`colore` su tutte le 94 serie;
  gli 8 colori dei Paesi sono stati cercati con un'ottimizzazione e passano `tools/valida_palette.py --pairs all` in chiaro e scuro (porting Python del validatore della skill dataviz: Node non è installato).
  Dopo la richiesta dell'utente (prima del merge) sono stati rifatti con contrasto ≥ 3:1 con lo sfondo in entrambi i temi (minimo 3,08 chiaro, 3,06 scuro): nessuna linea più spessa necessaria.
  Distanze peggiori (ΔE OKLab×100): daltonismo protan 9,0 / deutan 8,1 chiaro, 8,4 / 8,4 scuro (soglia 8); vista normale 15,5 chiaro, 15,3 scuro (soglia 15); tritan 4,5 / 3,1 (solo informativo, raro).
  Colori: us #2e4aa6/#5d89ff · ea #c27d00/#ca8412 · it #2ea46c/#3bad75 · jp #bf1000/#d5301c · cn #de37a5/#c3118e · kr #8b59f9/#7942e2 · uk #5183c1/#3a6ca8 · fr #1a6937/#2f7a47 (chiaro/scuro).
  L'avviso "manca come_leggerlo" è solo un `print` nel log della build: nelle pagine non compare (verificato).
  Le materie prime usano un colore per gruppo (energia, metalli preziosi, metalli industriali, agricoli: alias di colori dei Paesi che non compaiono mai con loro). Stessa serie colorata uguale in ogni grafico;
  più serie dello stesso colore nello stesso grafico = stile di linea diverso (fino a 6). Campo `come_leggerlo` aggiunto al modello e mostrato sotto i grafici; la build avvisa per i 56 grafici che ancora non ce l'hanno
  (le righe si scrivono pagina per pagina nello step 4). `slot`/`--s1…--s8`/`PALETTE` eliminati.
- 01/10/2026: step 2 unito in `main` (con i colori a contrasto ≥ 3:1).
- 01/10/2026: step 3 completato sul ramo `ristrutturazione/step-3`. Nuove pagine `/method/` ("Sources & method": come funziona, fonti con numero di serie, controllo di freschezza con soglie e serie in ritardo adesso, fonti di riserva
  configurate e in uso, serie calcolate e loro stato, Known limits) e `/method/series/` (tutte le 94 serie con link alla fonte, frequenza, storico, ultimo dato, stato, grafici che le usano). Menu: voce "Method & sources" con seconda riga.
  Registro `contenuti/note.yaml` (49 note raggruppate, ognuna con ancora `method/#note-<id>` e l'elenco dei grafici che la richiamano); i grafici usano `note=["id", ...]` al posto di `nota="..."`.
  Sotto ogni grafico: "How to read it" (quando c'è), `Source: <fonte> ↗ (N series) · Notes: <titoli>`, `Latest data`. Link alla serie costruiti in `dashboard/fonti_url.py` (FRED, BCE, BIS, DBnomics, Yahoo, MoF verificati a mano/con richieste).
  Le tabelle "Stato delle serie" per pagina sono sparite (ora c'è Series status); le sezioni "Data not included" di Cina e Corea sono note nel registro. Verifiche: `controlla`, `sito` (56/56), `controlla_link.py` (435 link interni ok), verifica a frasi che nessuna vecchia nota sia sparita
  (le righe "Source: BIS, daily data" sono sostituite dal piè con la fonte; è stata aggiunta la nota `index-daily-closes`).
- 01/10/2026: step 3 unito in `main`.
- 01/10/2026: step 4a (Commodities) sul ramo `ristrutturazione/step-4a`. Nuovo meccanismo per le pagine nuove: blocco `pagine:` in `config.yaml` (hub `markets` + 5 pagine, solo commodities `attiva`, le altre "coming soon" nell'hub),
  registro `dashboard/mercati/` (costruttore per pagina), pagina hub `/markets/`, pagina `/markets/commodities/` con titolo, una riga, 6 numeri chiave con unità e YTD, chips "On this page", sezioni e 13 grafici ciascuno con "How to read it".
  Il vecchio `/commodities/` resta come pagina che rimanda al nuovo (anche con `#chart-...`). La regione `commodities` resta nel config solo come appartenenza delle serie (`senza_pagina: true`).
  I colori dei gruppi di materie prime sono stati cambiati per non confonderli con il blu degli USA (energia = rosso del Giappone, preziosi = ambra dell'area euro, industriali = viola della Corea, agricoli = verde dell'Italia).
  Nel piano al posto di `dashboard/pagine/` si usa `dashboard/mercati/` (e `dashboard/economie/` allo step 5) perché `dashboard/pagine.py` è già il modulo del menu.
- 01/10/2026: step 4a unito in `main` (righe TTF e Wheat ritoccate come chiesto; un primo merge aveva perso la modifica Wheat per un problema di fine riga e l'ho corretta con un commit successivo su `main`).
- 01/10/2026: step 4b (FX) sul ramo `ristrutturazione/step-4b`: pagina `/markets/fx/` (`dashboard/mercati/fx.py`) con 5 numeri chiave, sezioni "Currencies compared" (`gl-valute`), "Exchange rates in levels" (EUR/USD, USD/JPY, USD/CNY, USD/KRW in griglia 2×2) e "The broad dollar" (`usa-dollaro`), ognuno con "How to read it".
  I 6 grafici sono stati tolti dalle pagine dei Paesi (sezioni "Exchange rate" di Giappone, Cina, Corea, Eurozona; sezione "Currencies" del Confronto globale; `usa-dollaro` da USA). Decisione: i 4 cambi non hanno più le bande CEPR (EUR/USD le aveva): sono rapporti tra due economie;
  l'indice del dollaro mantiene le bande NBER. Nuova nota `broad-dollar-index`. Navigazione "Previous / Next" tra pagine attive dello stesso hub (precedente/successiva: `FX ‹ › Commodities`).
- 01/10/2026: step 4b unito in `main` (riga USD/JPY con l'esempio di agosto 2024, verificata in `main` dopo il merge).
- 01/10/2026: step 4c (Credit) sul ramo `ristrutturazione/step-4c`: pagina `/markets/credit/` (`dashboard/mercati/credit.py`) con 6 numeri chiave e sezioni "High yield: US vs euro area" (nuovo grafico `mk-credit-hy`, assorbe `eur-hy`),
  "US credit in detail" (`usa-oas`, `usa-baa`) e "Sovereign spreads" (`eur-spread-paesi`, `eur-spread-tutti`), tutti con "How to read it". Tolti dalle pagine USA ed Eurozona le sezioni Credit e Sovereign spreads.
  Rinominate cinque serie in `config.yaml` per distinguere USA ed euro (es. "US high-yield spread (OAS)", "Euro high-yield spread (OAS)"). Bande NBER su `usa-oas`/`usa-baa` e CEPR sugli spread sovrani; nessuna banda sul confronto USA-euro.
- 01/10/2026: step 4c unito in `main` (riga BTP-Bund / OAT-Bund con gli esempi e le medie mensili, verificata in `main`).
- 01/10/2026: step 4d (Equities) sul ramo `ristrutturazione/step-4d`: pagina `/markets/equities/` (`dashboard/mercati/equities.py`) con 6 numeri chiave (S&P 500, Euro Stoxx 50, Nikkei 225, KOSPI, ACWI, VIX), tabella di performance unica a gruppi
  (United States / Euro area / Asia / World) con la colonna "Last" (ultimo livello) e le variazioni 1W / 1M / YTD / 1Y, sezioni "Equity indices compared" (`gl-borse`, interruttore Local currency / In USD), "Regional detail" (`usa-indici-azionari`, `eur-indici-azionari`, `usa-concentrazione`)
  e "Volatility" (`usa-vix`), con "How to read it". Tolti dalle pagine dei Paesi i grafici di borsa; `jp-nikkei`, `cn-csi300`, `cn-hangseng`, `kr-kospi` assorbiti da `gl-borse` e dalla tabella (il livello in punti resta nella colonna "Last").
  Nuovo meccanismo `Sezione.gruppi_performance` per le tabelle con righe di titolo; nuova nota `vix-definition`; nella pagina USA la sezione "Financial conditions and labour" diventa "Labour" (resta solo la disoccupazione, che andrà in Economies/USA allo step 5).
- 01/10/2026: step 4d unito in `main` (frase sui dividendi nella riga del confronto borse, verificata in `main`). L'utente ha deciso di dividere lo step 4e in 4e-1 (tassi di policy e curve) e 4e-2 (inflazione e tassi reali).
- 01/10/2026: step 4e-1 sul ramo `ristrutturazione/step-4e1`: pagina `/markets/rates/` (`dashboard/mercati/rates.py`) con 6 numeri chiave (Fed funds, deposito BCE, Treasury 10Y, AAA 10Y, JGB 10Y, 10Y-2Y USA) e sezioni "Policy rates" (`gl-policy`, nuovo `mk-rates-fed-ecb`),
  "Government yield curves" (`usa-curva-oggi`, `eur-curva-oggi`), "10-year yields compared" (`gl-rendimenti`), "Curve slope and inversions" (nuovo `mk-rates-slope` con area rossa delle inversioni, `usa-spread`) e "Yields by country" (`usa-rendimenti`, `eur-rendimenti`, `jp-jgb`).
  Assorbiti: `usa-dff` + `eur-dfr` in `mk-rates-fed-ecb`; `jp-policy`, `cn-lpr`, `kr-policy` in `gl-policy`; `kr-ktb` in `gl-rendimenti`; `eur-pendenza` in `mk-rates-slope`. Tolte dalle pagine dei Paesi le sezioni di tassi, curve e rendimenti: restano solo
  inflazione, tassi reali (USA) e disoccupazione, che si spostano nello step 4e-2 e nello step 5. Nuove note `fed-ecb-rates`, `curve-snapshot`, `aaa-bund-proxy`.
- 01/10/2026: step 4e-1 unito in `main`, con i due ritocchi (verificati in `main`): eccezione dell'inversione 2022-2024 (USREC: nessuna recessione NBER dopo aprile 2020 fino ad agosto 2026; 10Y-2Y negativo da aprile 2022 a settembre 2024, 10Y-3M da ottobre 2022 a ottobre 2025,
  e per questo la riga di `usa-spread` dice "10Y-2Y until 2024, 10Y-3M until 2025") e yield curve control della BoJ 2016-2024 nella riga JGB.
- 01/10/2026: step 4e-2 sul ramo `ristrutturazione/step-4e2`: `/markets/rates/` ora ha anche "Inflation and real rates" (`gl-inflazione`, `usa-reali`) e "Inflation by country" (`usa-inflazione`, `eur-inflazione`, `jp-inflazione`), 8 numeri chiave (con CPI USA e HICP area euro), tutti con "How to read it".
  `cn-inflazione` e `kr-inflazione` assorbiti da `gl-inflazione`. Le pagine Euro area, Japan, China, South Korea, Global comparison sono rimaste senza grafici: non si generano più (`senza_pagina: true`) e i vecchi indirizzi rimandano a `markets/` (Global comparison a `markets/rates/`).
  Resta temporaneamente la pagina `usa` (solo disoccupazione, in menu come "United States") fino allo step 5. Rinominate cinque serie di inflazione con il prefisso US / Euro-area. **Tutti i grafici di Markets sono fatti: lo step 4 è completo.** `markets/rates` pesa 2,15 MB (da ridurre allo step 7).
- 01/10/2026: step 4e-2 unito in `main`. La riga del Giappone è stata completata dopo aver verificato i dati: l'inflazione totale giapponese è stata sopra il 2% da aprile 2022 a dicembre 2025 (massimo 4,4% a gennaio 2023) ed è tornata per lo più sotto il 2% nel 2026
  (1,96% ad agosto 2026); il tasso BoJ (BIS) è passato da −0,10% a 0,05% a marzo 2024 e poi è salito più volte. La frase proposta dall'utente ("Since 2022 inflation has stayed above 2%") non era esatta per i dati più recenti, quindi la riga dice "from April 2022 to the end of 2025".
- 01/10/2026: step 5 sul ramo `ristrutturazione/step-5`. Nuova sezione Economies: hub `/economies/` e pagine `economies/usa` (disoccupazione, con "How to read it"; `dashboard/economie/usa.py`), `economies/italy`, `economies/euro-area`, `economies/uk`, `economies/compare` (pagine vuote "coming soon" con navigazione precedente/successiva)
  e schede "later" per Japan, China, South Korea. Stati delle pagine nel blocco `pagine`: `attiva`, `in-arrivo` (pagina vuota), `dopo` (solo scheda). Rimosso il blocco `regioni`, il pacchetto `dashboard/regions/` (il modello è ora `dashboard/modello.py`),
  i campi `regione` e `riepilogo` delle serie (le serie hanno `paese`; la pagina Series status mostra l'"area" dal nome del Paese) e le pagine Home provvisoria "Countries"/"Global comparison". Aggiunte le voci colore `de` (Germany) e `global` come etichette.
  Vecchi indirizzi: `usa/` → `economies/usa/`; `eurozona/`, `giappone/`, `cina/`, `corea/` → `markets/`; `globale/` → `markets/rates/`; `commodities/` → `markets/commodities/`.
- 01/10/2026: step 5 unito in `main` (riga della disoccupazione con la definizione corretta di forza lavoro, verificata in `main`; riga del Giappone approvata dall'utente nella versione verificata sui dati).
- 01/10/2026: step 6 avviato sul ramo `ristrutturazione/step-6`. Prima del codice, proposta di dettaglio del calcolo "What changed this week" con un prototipo su dati reali (fuori dal progetto): 66 serie candidate giornaliere/settimanali, 18 sopra 1,5× in una settimana volatile per i tassi;
  con al massimo una serie per gruppo restano 8 gruppi su 21 sopra 1,5× (primi: Real yield 10Y TIPS 3,0×, AAA 3M −2,6×, JGB 2Y 2,5×, HY USA 2,5×, spread euro vs AAA 2,2×).
- 01/10/2026: step 6 (Overview) sul ramo `ristrutturazione/step-6`. Decisioni dell'utente sul calcolo: deviazione standard; **soglia 2×** (non 1,5×) con massimo 5 righe, motivata nella pagina Method (con 1,5× circa il 13% delle serie la supera per caso in una settimana normale, con 2× circa il 5%);
  gruppi come proposti; nota "non sono probabilità" sotto la tabella. Codice: `dashboard/movimenti.py` (funzioni pure), `dashboard/sparkline.py` (mini-grafici SVG), 54 serie con `movimenti: true` e `gruppo_movimenti` in 21 gruppi, blocco `panoramica:` con i 14 numeri chiave (3 gruppi),
  template `panoramica.html.j2` (home), sezione "What changed this week" in `/method/`. Test: `tests/test_movimenti.py` (19 test su dati inventati + 3 episodi storici con `PROVE_CON_RETE=1`: WTI settimana al 9/3/2020 −34% = −8,1×, VIX settimana al 27/2/2020 +152% = +8,1×).
  Scoperta dai test sui dati veri: il VIX, in settimane già turbolente (al 13/3/2020, +38%), vale solo 1,8× perché si muove molto anche in settimane normali (deviazione standard ~21%): lo dice anche la pagina Method.
  Risultato di oggi: 9 serie su 54 sopra 2×; in lista: US 10Y real yield +28 bp 3,0×, Euro AAA 3M −14 bp 2,6×, Japan 2Y +10 bp 2,5×, US high-yield spread +40 bp 2,5×, Euro-area spread vs AAA 10Y +6 bp 2,2×. Il test in CI non è ancora nel workflow GitHub (da decidere).
- 01/10/2026: step 6 unito in `main`; test aggiunti al workflow prima della build (verificato: un test rosso su un ramo di prova ferma il job e non pubblica; ramo di prova cancellato).
- 01/10/2026: step 7 sul ramo `ristrutturazione/step-7` (non ancora unito). Fatto: bundle `plotly-basic` al posto di `plotly` (da 1,47 MB a 0,40 MB di JavaScript, tutti i 45 grafici disegnano, anche due pannelli e curve);
  peso misurato compresso (come lo scarica il browser): rates 0,47 MB, equities 0,49 MB, commodities 0,23 MB → sotto 1 MB, quindi niente caricamento a parte dei dati; icona della scheda (nessun 404); controllo "ogni grafico è nella pagina promessa dalla mappa" in `tools/inventario.py sito`;
  README riscritto, screenshot `docs/dashboard.jpg`, CLAUDE.md riscritto (struttura, regole, flusso); nessun codice morto trovato (solo `valida_palette.peggiore`, helper di ricerca palette, tenuto).
  Controllo link esterni: 84, 57 rispondono 200; i link FRED sono andati in timeout (il sito risponde lentamente ai bot, formato standard); 4 link Yahoo (`^GDAXIP`, `510300.SS`, `EXV1.DE`, `KRW=X`) rispondono 404 alle richieste automatiche
  (Yahoo reindirizza al consenso privacy nel browser): DA VERIFICARE A MANO. Non fatto: tema chiaro/scuro con interruttore (mai implementato), nomi interni in inglese (opzionale).
- 01/10/2026: step 7 unito in `main`; Action verificata (test, build e pubblicazione riusciti). L'utente ha controllato a mano i link Yahoo e FRED (funzionano). Le email di notifica di GitHub per le Action fallite: risposta dell'utente non chiara nel messaggio (segnaposto non compilato), quindi NON confermate.
- 01/10/2026: interruttore del tema (◐) nella testata di ogni pagina: tre stati Auto (segue il sistema) → Light → Dark → Auto; la scelta sta solo nel `localStorage` del browser di chi visita e si applica prima del disegno (niente lampo);
  `data-theme` su `<html>` guida sia le variabili del CSS sia i colori dei Paesi (`render.css_colori`); i grafici già disegnati si ricolorano al clic. Verificato nel browser: ciclo dei tre stati, persistenza dopo il ricaricamento, ricolorazione di un grafico, telefono a 375 px senza scorrimento orizzontale.
  I nomi interni in italiano restano (decisione dell'utente). **Ristrutturazione completata.** Lavoro successivo: riempire le pagine di Economies (vedi CLAUDE.md).
- 01/10/2026: step 9 (verifica delle fonti per Economies, nessun codice) sul ramo `ristrutturazione/step-9`: tabelle in [economies-fonti.md](economies-fonti.md), piano degli step 9–13 nella sezione 10.
- 01/10/2026: piano rivisto dopo le decisioni dell'utente: livello B in `country.html?c=ISO3`, snapshot FMI a ogni WEO con freschezza a semestri, bozza di e-mail all'FMI (`docs/bozza-email-fmi.md`), debito/deficit USA dal FMI, ESI, mappa e link Markets ↔ Economies (nuovo step 14);
  verificato che `HF6X` e `AA6H` dell'ONS esistono (percorso sbagliato nel primo test), UK HPI funziona, il percentile WGI non esiste più (solo score 0-100). Attesa dell'ok dell'utente prima del commit.
- 01/10/2026: piano approvato dall'utente con tre aggiunte (elenco/ricerca dei Paesi accanto alla mappa; deficit UK sullo stesso periodo; punti aperti chiusi: solo score WGI, mappa con PIL pro capite PPA e ultimo anno effettivo, importatore WEO come riserva). Step 9 unito in `main` (solo documenti). Lo step 10 si apre dopo la lettura del piano finale.
- 01/10/2026: step 9b sul ramo `ristrutturazione/step-9b` (solo documenti): step 9 segnato in `main`; tolta la frase sul rango; step 10 diviso in 10a (dati) e 10b (pagine); aggiunto al step 12 il grafico di sostenibilità del debito italiano (serie Eurostat verificate); proposta per l'aggiornamento dello snapshot della Banca Mondiale (workflow mensile che apre una pull request solo se i dati cambiano; sul limite dei 60 giorni la documentazione GitHub non dice cosa conti come attività). Attesa dell'ok prima del commit.
- 01/10/2026: step 9b approvato con due aggiunte (formula e ipotesi sull'SFA nello step 12; il workflow della Banca Mondiale esegue test e controlli prima di aprire la PR). Unito in `main`; aperto il ramo `ristrutturazione/step-10a`, che parte dal test delle API FMI e Banca Mondiale da GitHub Actions.
- 01/10/2026: step 10a, prova delle API da GitHub Actions (workflow temporaneo `prova-api.yml`, run `36890801783`, ramo `ristrutturazione/step-10a`; 14 richieste, 13 riuscite). **FMI `api.imf.org` (SDMX): HTTP 200** da Actions per un indicatore su tutti i Paesi in CSV (circa 20 MB, 1,5-1,7 s, 9.956 righe) e per l'Italia in JSON, con tutti e due gli `User-Agent` provati. **Banca Mondiale: HTTP 200** per WDI (17.490 voci, aggiornata 13/07/2026), WGI `GOV_WGI_CC.SC` (5.832 voci, 25/09/2026) ed elenco Paesi.
  Il vecchio DataMapper dell'FMI risponde 200 con lo `User-Agent` predefinito di Python (8-11 s) e **403 con uno da browser**: blocco fragile, scartato. Conseguenza: `imf.py` e `worldbank.py` possono essere chiamati anche da un workflow, ma l'FMI resta a mano (termini d'uso) e la Banca Mondiale è automatica con pull request. Workflow e script di prova cancellati in questo commit.
- 01/10/2026: step 10a completato sul ramo `ristrutturazione/step-10a` (non ancora unito). Fatto: `dashboard/annuali.py` (catalogo `indicatori:` con 20 voci in `config.yaml`, snapshot, freschezza, confronto), `sources/imf.py` (SDMX 3.0 con `attributes=LATEST_ACTUAL_ANNUAL_DATA`: 6 colonne, ~0,6 MB per indicatore invece di ~20 MB),
  `sources/imf_file.py` + `tools/importa_weo.py`, `sources/worldbank.py`, `tools/aggiorna_weo.py`, `tools/aggiorna_bm.py`, `tools/riepilogo_snapshot.py`, `tools/descrizione_pr.py`, `dashboard/attivita.py` e `tools/controlla_attivita.py`, workflow `aggiorna-dati-bm.yml`; Method (sezione "Annual data by country"; l'avviso dei 45 giorni non è sul sito: vedi la voce successiva) e Series status (tabella "Annual indicators by country") aggiornati; 56 test (34 nuovi in `tests/test_annuali.py`; 3 saltati senza rete).
  Snapshot: `dati/weo/` 95.492 valori di 197 Paesi, 2,4 MB (WEO aprile 2026, pubblicato 14/04/2026); `dati/bm/` 86.545 valori, 217 Paesi e 43 aggregati, 2,8 MB. Tolti dallo snapshot FMI i 13 aggregati (G001...): l'API e il file "By Countries" hanno così lo stesso contenuto.
  Scoperte: (1) la Banca Mondiale, con `page=1` esplicito, per `SP.POP.TOTL` rispondeva con un'altra sorgente (25, aggiornata un anno prima): si manda `page` solo dalla seconda pagina e si controlla `sourceid`; (2) i PIL in dollari hanno 13 cifre e i decimali erano rumore binario, quindi da 1 milione in su i valori si scrivono interi;
  (3) `LATEST_ACTUAL_ANNUAL_DATA` manca per tutto `PPPPC` (si copia da `NGDPD`, dichiarato nel catalogo e in `meta.json`) e per gli aggregati, vale `FY2024/25` per i Paesi con anno fiscale (si legge 2024), e per `GIN` `LP` non c'è (1 coppia su 2.154); per 11 coppie (LKA, MAC, SYR, WBG) l'ultimo anno effettivo è oltre l'ultimo anno con dato e 8 Paesi non hanno anni di stima.
  Prove: due scarichi di fila danno file identici byte per byte, anche tra il PC Windows e il runner Linux di GitHub; il workflow `Aggiorna dati Banca Mondiale` in modalità prova (run `36893180966`) ha scaricato lo snapshot (nessuna differenza), eseguito test, build, inventario e link su Actions (tutti superati) e saltato la creazione della pull request, che resta da provare dopo il merge con un avvio a mano.
  L'importatore del file WEO è provato su un file nel formato documentato costruito dallo snapshot (UTF-16, migliaia con la virgola, n/a): 95.492 valori e 2.153 ultimi anni identici, snapshot identico byte per byte; **non è ancora provato sul file vero dell'FMI** (il sito blocca lo scarico automatico: serve il permesso dell'utente per scaricarlo, o il file scaricato a mano).
- 01/10/2026: step 10a, correzioni prima del merge (richieste dall'utente). (1) **PPPPC**: dall'indicatore NGDPD si copia solo l'**anno** dell'ultimo dato effettivo (`annuali.completa_ultimo_effettivo`, che tocca solo il dizionario degli anni), mai i valori; nel file vero dell'FMI `LATEST_ACTUAL_ANNUAL_DATA` di PPPPC è vuoto per tutti i 208 Paesi. Esempio (ultimo anno effettivo usato): ITA 2025, PPPPC 63.537,964 int.$ e NGDPD 2.550,111 miliardi di USD; USA 2025, 89.991,152 e 30.767,075; IND 2024 (anno fiscale 2024/25), 10.747,418 e 3.760,814.
  (2) **Avviso dei 45 giorni**: tolto dal sito pubblico (c'era in ogni pagina e in Method); ora il job `controlla-attivita` del workflow giornaliero esegue `tools/controlla_attivita.py`, che apre **una sola issue** (titolo esatto, mai duplicata) quando l'ultimo commit supera i 45 giorni e la chiude da sola quando torna un commit. Provato su Actions con la issue vera (run `36894603484`, issue di prova #1, chiusa): apre, alla seconda esecuzione non ne apre un'altra, alla terza la chiude; 5 test con `gh` finto.
  (3) **File WEO vero** (scaricato dall'utente: CSV del portale `dataset_..._IMF.RES_WEO_9.0.0.csv`, non il vecchio `.xls`): formato diverso da quello assunto (colonne `SERIES_CODE`, `LATEST_ACTUAL_ANNUAL_DATA`, `PUBLICATION_DATE`, una colonna per anno); l'importatore ora legge entrambi i formati e prende la data di pubblicazione dal file. Il confronto ha trovato due differenze reali, corrette: **scala** (l'API dà l'unità grezza con l'esponente `SCALE`, il file i miliardi/milioni: ora si divide per 10^SCALE; 18.750 valori erano diversi, solo NGDPD e LP) e **arrotondamento** (il file arrotonda per eccesso a metà, Python `round()` al pari: 93 valori differivano di 0,001; ora `formatta_valore` usa `Decimal` con `ROUND_HALF_UP`). Esito finale: 95.492 valori e 2.153 ultimi anni effettivi uguali, `dati.csv`, `ultimo_effettivo.csv` e `meta.json` identici byte per byte tra lo snapshot dell'API e quello del file vero.
- 01/10/2026: step 10b (pagina del Paese) sul ramo `ristrutturazione/step-10b` (non ancora unito), con le modifiche dell'utente alla proposta: righe "How to read it" solo con episodi chiusi da almeno due anni (Italia 2020-21 e 2022, Grecia 2024), mai valori correnti né classifiche (test); link "→ Economy" e "Full page →" verso una pagina di livello A **solo se `completa: true`** (nessuna lo è: USA → `country.html?c=USA`); `gdp_per_capita_usd` e `population_imf` tolti (catalogo a 18 indicatori); colonna `anno_fiscale` in `ultimo_effettivo.csv` (200 coppie, 33 Paesi; API e file vero ancora identici byte per byte); un file di dati per Paese più `ultimi-valori.json` (per la mappa); periodi 10Y/25Y/Max contati dall'ultimo anno effettivo con le proiezioni sempre visibili; nessun interruttore di fonte (Banca Mondiale per PIL, crescita e PIL pro capite solo per i 21 Paesi senza FMI); inflazione: solo la media annua, il fine anno nel tooltip; Taiwan col nome dell'FMI.
  Fatto: `dashboard/paesi.py`, `contenuti/paese.yaml`, `templates/paese.html.j2`, `static/paese.js`, 5 note nel registro, blocco `paesi:` (link e riquadro Markets), `nomi_paesi:` (North Korea, Egypt...), link "→ Economy" sotto i grafici Markets, schede dell'hub (Japan, China, South Korea, Country explorer), controlli in `inventario.py sito` e `controlla_link.py` (anche `?c=`). Test: 92 (30 nuovi in `tests/test_paesi.py`, 7 in `test_annuali.py`).
  Scoperte: i Paesi sono 218 (non 194; KOS e WBG unificati con XKX e PSE); senza proiezioni sono Eritrea, Sri Lanka, Siria e Cisgiordania e Gaza (Macao le ha, tranne il saldo primario); peso: country.html 13 KB compressi, `paese.js` 9 KB, un file di dati al massimo 2,8 KB, `ultimi-valori.json` 7,9 KB (con Plotly 0,40 MB: ~0,43 MB alla prima visita). Verificato nel browser: ITA, USA, JPN, SYR, IND (anno fiscale), CUB (solo Banca Mondiale), TWN (solo FMI), `?c=XYZ`, nessun parametro, ricerca e tastiera, 375 px senza scorrimento orizzontale.
- 01/10/2026: step 10b, ultime modifiche prima del merge: righe Population e Government balance (Grecia senza cifre) riscritte; il test sugli anni delle righe calcola il limite dall'anno corrente (anno corrente − 1); regola dei nomi dei Paesi in CLAUDE.md con `nome_fonte` in config (test: coincide con la Banca Mondiale); **scala logaritmica simmetrica dell'inflazione** (attiva con almeno un anno sopra il 100% nella finestra visibile, ricalcolata a ogni periodo, pulsanti Linear/Log e nota sempre coerenti, scelta manuale valida fino al cambio di Paese, tooltip con i valori veri; verificata su VEN, LBN, ARG, TUR e su JPN con scala forzata). Bug trovato e corretto: i pulsanti dei periodi (e il cambio di tema) cancellavano il grafico perché `disegnaGrafico` svuotava il contenitore prima di `Plotly.react`.
- 01/10/2026: step 10c (ridisegno dell'hub Economies) sul ramo `ristrutturazione/step-10c`: **solo proposta** nella sezione "Step 10c" (wireframe desktop e 375 px, componente unico `ricerca_paesi` + `elenco-paesi.js`, riquadri con crescita e inflazione dell'ultimo anno effettivo da `ultimi-valori.json`, bandiere sconsigliate con i motivi, peso stimato, verifiche, 3 domande aperte). Nessun codice scritto; attesa dell'ok dell'utente.
- 01/10/2026: step 10c completato sul ramo `ristrutturazione/step-10c` (non ancora unito). Fatto: macro `ricerca_paesi` + `static/elenco-paesi.js` (ricerca condivisa con il selettore di `country.html?c=`), `paesi.riquadri_paesi/chiave_ricerca/chiavi_paese` con 15 test nuovi (110 test in tutto, 3 saltati), blocchi `nomi_alternativi` e `hub_economies` in `config.yaml`, hub e `country.html` senza `c` con lo stesso componente, `tools/inventario.py` aggiornato (riquadri; hub e `country.html` elencano gli stessi 218 Paesi). **Pesi misurati (gzip)**: hub `economies/` 160 KB grezzi, **14 KB compressi** (prima ~2 KB); `country.html` 205 KB grezzi, **21 KB compressi** (prima 13 KB: +8 KB, più della stima di 3: i riquadri hanno due numeri e l'anno); `elenco-paesi.js` 2 KB; `style.css` 6 KB. Verifica nel browser (desktop e 375 px, chiaro e scuro): ricerca "tur" (3 risultati: Turkiye, Turkmenistan, Turks and Caicos), tutti gli alias e "Curaçao" trovati, clic su Featured (USA -> `country.html?c=USA`) e su un riquadro di regione, Invio sul primo risultato, tasto Indietro, codice non valido, nessuno scorrimento orizzontale a 375 px (`scrollWidth` 375), console senza errori; contrasti ≥ 4,5:1 per i testi e ≥ 3:1 per il bordo del campo (corretti `--testo-tenue` -> `--testo-2` per anno e codice). Screenshot in `docs/schermate-10c/`. Scoperta: `inventario.py sito` cercava il vecchio markup dell'elenco di `country.html`.
- 01/10/2026: step 10c, ultime richieste prima del merge: scheda "Compare" con la regola dell'Euro area (fino allo step 13), `docs/schermate-*/` in `.gitignore`, prova senza JavaScript (barra di ricerca nascosta, riquadri e regioni come link).
