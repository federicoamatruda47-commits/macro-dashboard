# Ristrutturazione del sito (piano approvato)

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
| 5 | Economies (hub + 5 segnaposto + UNRATE in USA); `regioni` → `pagine` nel config; via le vecchie pagine e il Confronto globale | **fatto sul ramo** `ristrutturazione/step-5`, in attesa dell'ok per il merge |
| 6 | Overview (14 numeri chiave con sparkline, "What changed this week", schede, avvisi); diventa `/` | da fare |
| 7 | Rifinitura: peso pagine, link rotti, README e screenshot, CLAUDE.md, codice morto (opz.: nomi interni in inglese) | da fare |

Flusso di lavoro: un ramo per step (`ristrutturazione/step-N`); a fine step riepilogo all'utente e **attesa dell'ok prima del merge** su `main`
(il merge pubblica il sito tramite GitHub Actions). Il merge si fa a fine di ogni step (non tutto alla fine), con `git push origin main`. Nessun commit/push fuori da questo flusso senza richiesta.

Strumenti di controllo: `python tools/inventario.py controlla` (deve passare a ogni step), `python tools/inventario.py sito` (dopo `python build.py`: controlla le pagine HTML vere e ne stampa il peso), `python tools/controlla_link.py` (link interni rotti, dopo `build.py`), `python tools/inventario.py salva`
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
