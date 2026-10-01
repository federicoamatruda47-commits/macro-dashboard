# Proposta step 10b: la pagina `economies/country.html?c=ISO3` (livello B)

Solo proposta, nessun codice. Ramo: `ristrutturazione/step-10b`. Dati già in `main`: snapshot `dati/weo` (197 Paesi) e `dati/bm` (217 Paesi), catalogo di 20 indicatori.
Tutti i numeri degli esempi sono stati letti dagli snapshot il 01/10/2026.

## 0. Cose trovate guardando i dati (cambiano o precisano il piano)

1. **Paesi: 218, non 194.** Unione di FMI (197) e Banca Mondiale (217) dopo aver unificato due codici che differiscono: FMI `KOS` = Banca Mondiale `XKX` (Kosovo) e FMI `WBG` = `PSE` (Cisgiordania e Gaza). 196 hanno tutte e due le fonti, 21 solo la Banca Mondiale (Cuba, Corea del Nord, territori: Bermuda, Guam, Groenlandia...), 1 solo l'FMI (`TWN`, Taiwan: manca il nome nell'elenco della Banca Mondiale, si scrive a mano in `paesi:`).
2. **Paesi senza proiezioni: sono 4, non quelli che avevi elencato.** Per la crescita reale non hanno anni dopo l'ultimo dato effettivo: **Eritrea** (dati fino al 2019), **Sri Lanka** (2024), **Siria** (2010), **Cisgiordania e Gaza** (2024). **Macao ha le proiezioni** fino al 2031 per quasi tutto; gli manca solo il saldo primario (dati fino al 2022). Altri 3 hanno proiezioni molto corte: **Afghanistan e Bolivia 1 anno** dopo l'ultimo effettivo, **Libano 4 anni** (ultimo effettivo 2021, dati fino al 2025: quasi tutto "stima"); gli altri 190 hanno almeno 6 anni. Regola per tutti: il tratteggio compare solo se esistono anni dopo l'ultimo effettivo.
3. **Anni fiscali: riguardano 33 Paesi e dipendono dall'indicatore.** Nel file dell'FMI l'ultimo anno effettivo è scritto `FY2024/25` per tutti i 33 sui dati di finanza pubblica (saldo, debito), per 19 anche sui conti nazionali (crescita, PIL), per 15 sull'inflazione, 18 sul conto corrente, 12 sulla popolazione. Esempi: India, Egitto, Pakistan, Bangladesh, Etiopia, Iran, Tailandia, Singapore, Hong Kong, Sudafrica. L'anno fiscale è mostrato sotto l'anno in cui inizia (India "2024" = 2024/25).
   **Conseguenza: lo snapshot FMI non conserva questa informazione** (`ultimo_effettivo.csv` ha solo l'anno). Serve una piccola estensione del formato, nel primo commit di 10b: una quarta colonna `anno_fiscale` (vuota oppure `1`) in `ultimo_effettivo.csv`, prodotta nello stesso modo dallo script (attributo dell'API) e dall'importatore (colonna del file); si rigenera, si riconfronta con il file vero.
4. **Peso: conviene un file di dati per Paese.** Un file unico con 18 indicatori è circa 0,54 MB compressi; un file per Paese è circa 3,4 KB compressi (misurato su ITA, USA, IND, LUX, TUV, SYR). La pagina carica solo il Paese scelto. Totale pagina alla prima visita: HTML + JavaScript ~25 KB + `plotly-basic` 0,40 MB (già in cache se si arriva da un'altra pagina) + 3-4 KB di dati: **circa 0,45 MB compressi**, sotto il limite di 1 MB. Per la mappa (step 14) si aggiungerà un `ultimi-valori.json` a parte.
5. **Dei 20 indicatori ne servono 18; due si possono togliere dal catalogo** (vedi §2): `gdp_per_capita_usd` e `population_imf`. Proposta: toglierli dal catalogo e dallo snapshot nel primo commit di 10b (meno dati inutili, nessuna pagina li usa).

## 1. Wireframe

### Desktop (≥ 900 px)
```
Menu: Overview · Markets · [Economies] · Method & sources                     ◐
Economies › Country explorer
┌──────────────────────────────────────────────────────────────────────────────┐
│ H1: Italy                          ISO ITA · Europe & Central Asia           │
│ Una riga: Annual data from the IMF and the World Bank.   [Full page → ]      │ ← solo se esiste la pagina A attiva
│ IMF WEO April 2026 (next: October) · World Bank July 2026                    │
│                                                                              │
│ Country  [ Search a country…          ▾ ]   ( ← prev ) ( next → )            │ ← selettore con ricerca, sticky
└──────────────────────────────────────────────────────────────────────────────┘
⚠ Avvisi (snapshot in ritardo, ecc.)   [On this page: Output · Prices · Labour · Public finances · External · Governance · IMF outlook]

KEY NUMBERS (7 schede, ultimo anno EFFETTIVO accanto al valore)
 GDP 2,550 USD bn (2025) │ GDP per head PPP 63,538 int.$ (2025) │ Population 58.9 m (2025) │ Real growth +0.5% (2025)
 Inflation 1.6% (2025)   │ Unemployment 6.4% (2025)·ILO modelled │ Gov. debt 137.1% of GDP (2025)

MARKETS  (solo dove ci sono serie di mercato: USA, Giappone, Cina, Corea, Francia, Germania, Italia)
 ┌ Markets in Italy ───────────────────────────────────────────────────────────┐
 │ BTP 10Y 3.x%   BTP-Bund spread +xx bp   FTSE MIB 4x,xxx   [→ Rates] [→ Equities] │
 └─────────────────────────────────────────────────────────────────────────────┘

── Output & growth ──────────────────────────────────────────────────────────────
 ┌ Real GDP growth ─────────── [10Y][25Y][Max]  Source ◉ IMF  ○ World Bank ┐ ┌ Nominal GDP … (stessa forma)  ┐
 │ barre (dopo l'anno effettivo: barre chiare + contorno)  | linea di riferimento a 0                    │
 │ How to read it … · Source: IMF WEO ↗ · Latest actual 2025 · Notes › │
 └──────────────────────────────────────────────────────────────────────────┘ └──────────────────────────────┘
 ┌ GDP per head, PPP ─────────────────┐ ┌ Population ───────────────────────┐
── Prices ── Inflation (media annua e fine anno)
── Labour ── Unemployment (ILO modelled estimate) · Employment ratio 15+ (ILO modelled estimate)
── Public finances ── Government balance (barre) + primary balance (linea) · Government debt
── External ── Current account
── Governance ── Control of corruption (score 0-100, banda 90%)
── IMF outlook ── tabella: Latest actual | 2026 | 2027 | 2028 | 2031 per crescita, inflazione, saldo, debito, conto corrente
Footer: fonti, licenza FMI (citazione), edizione
```
Griglia a 2 colonne dai 900 px in su, come le altre pagine; le 7 schede in una fila a capo.

### Telefono (375 px)
```
Menu a due righe (come ora)
Economies › Country explorer
H1: Italy      ITA
Europe & Central Asia
IMF WEO Apr 2026 · WB Jul 2026
[ 🔍 Search a country…        ]   ← campo largo; sotto: elenco filtrato a tutta larghezza,
 Italy                       ITA     voci alte 44 px (si toccano anche i Paesi piccoli)
 Ivory Coast … (max 8 voci, scorrevole)
 ‹ Previous      Next ›
[Full page →]   (se c'è)
⚠ avvisi
chips scorrevoli: Output · Prices · Labour · …
KEY NUMBERS: 2 colonne (7 schede, l'ultima da sola)
MARKETS: scheda a una colonna (3-5 numeri) + link
── Output & growth ──
 grafico a tutta larghezza (altezza 260 px); pulsanti 10Y 25Y Max e interruttore fonte sopra, a capo
 How to read it · Source · Notes
 (un grafico sotto l'altro)
── IMF outlook ── tabella scorrevole in orizzontale dentro il riquadro (la pagina non scorre di lato)
```
Il selettore resta in cima alla pagina (non sticky sul telefono: occuperebbe troppo schermo); un link "↑ Change country" in fondo a ogni sezione.

## 2. Grafici per sezione (18 indicatori su 20)

| Sezione | Grafico | Forma | Indicatori (id catalogo) | Unità | Fonte | Note |
|---|---|---|---|---|---|---|
| Output & growth | Real GDP growth | **barre**, linea a 0 | `gdp_growth` (FMI) / `gdp_growth_wb` | % y/y | FMI WEO 1980-2031; variante Banca Mondiale 1961-2025 | interruttore "Source: IMF / World Bank" (mai le due nello stesso grafico) |
| | Nominal GDP | linea | `gdp_nominal` / `gdp_nominal_wb` | USD bn (WB: convertito in miliardi) | come sopra, WB dal 1960 | scala: l'FMI in miliardi, la WB in dollari: la pagina divide per 1e9 |
| | GDP per head, PPP | linea | `gdp_per_capita_ppp` / `gdp_per_capita_ppp_wb` | international $ | FMI 1980-2031; WB 1990-2025 | WB: ultimo anno effettivo = ultimo anno con dato |
| | Population | linea | `population` (WB) | millions | Banca Mondiale 1960-2025 | solo WB: l'FMI (`population_imf`) si toglie |
| Prices | Inflation | **due linee**: media annua (piena), fine anno (puntinata) | `inflation_average`, `inflation_end_of_period` | % y/y | FMI | stessa fonte, stessa unità |
| Labour | Unemployment rate | linea | `unemployment_ilo` | % of labour force | Banca Mondiale (ILO) | etichetta "ILO modelled estimate" nel titolo e nota |
| | Employment ratio, 15+ | linea | `employment_ilo` | % of population 15+ | Banca Mondiale (ILO) | idem |
| Public finances | Government balance | **barre** (saldo) + **linea** (saldo primario), linea a 0 | `government_balance`, `government_primary_balance` | % of GDP | FMI | lo stesso perimetro (PA) |
| | Government debt | linea | `government_debt` | % of GDP | FMI | debito lordo |
| External | Current account | **barre**, linea a 0 | `current_account` | % of GDP | FMI | |
| Governance | Control of corruption | linea con **banda** | `corruption_score` + `_low` + `_high` | score 0-100 | Banca Mondiale (WGI) | vedi §4 |
| IMF outlook | tabella | **solo numeri** | crescita, inflazione media, saldo, debito, conto corrente | come sopra | FMI | colonne: ultimo effettivo, 2026, 2027, 2028, 2031 |
| Key numbers | 7 schede | numero + anno | PIL, PIL pro capite PPA, popolazione, crescita, inflazione, disoccupazione, debito | | FMI/WB | l'anno è quello **effettivo** |

**Lasciati fuori dalla pagina:**
- `gdp_per_capita_usd` (PIL pro capite in dollari correnti): ridondante con PIL e popolazione e fuorviante nei confronti (segue il cambio): da togliere dal catalogo.
- `population_imf`: duplica la popolazione della Banca Mondiale (che ha storia più lunga, dal 1960); l'FMI la dà in milioni con 3 decimali, poco precisa per i Paesi piccoli: da togliere dal catalogo.
- Non sono fuori ma usati in modo particolare: `inflation_end_of_period` e `government_primary_balance` (seconde serie di un grafico, non grafici propri); le tre varianti Banca Mondiale (`*_wb`) sono l'alternativa "Source: World Bank" e, per i 21 Paesi senza FMI, l'unica fonte; `corruption_score_low/high` sono la banda.
- Periodi dei pulsanti: **10Y, 25Y, Max** (dati annuali: 1Y e 5Y non hanno senso); predefinito 25Y, che include le proiezioni. Niente bande di recessione (sono previste solo nei grafici di una sola economia con una fonte per le date).
- Colori: i Paesi con un colore fisso in `colori:` (USA, Italia, Giappone, Cina, Corea, UK, Francia; Germania e area euro usano quello dell'area euro) lo mantengono; gli altri usano il colore neutro "mondo". Proiezione e banda = stesso colore, tratteggio/trasparenza.

## 3. Come si vedono proiezioni e stime

- **Linee**: piene fino all'ultimo anno effettivo, poi **tratteggiate** dallo stesso punto (nessuno stacco). **Barre**: dopo l'ultimo anno effettivo più chiare con il contorno. Una sottile linea verticale e l'etichetta "IMF projections" nel punto di passaggio; sfondo leggermente diverso non necessario.
- **Tooltip** di ogni punto: `2027 · IMF projection · 0.5%` (oppure `2025 · actual · …`). Nei Paesi con anno fiscale: `2024 (fiscal year 2024/25) · actual`.
- **Accanto al valore** (schede e tabella IMF outlook): l'anno effettivo, per esempio `63,538 int.$ (2025)`; se l'ultimo anno effettivo è diverso tra indicatori (accade: Grecia, debito 2024; Italia, debito 2025) si vede subito.
- **Sotto ogni grafico FMI**: "IMF WEO April 2026 · latest actual year 2025" (per i Paesi con anni diversi per indicatore l'anno è quello dell'indicatore).
- **Paesi senza proiezioni** (Eritrea, Sri Lanka, Siria, Cisgiordania e Gaza): nessun tratteggio e, nell'intestazione del grafico, la nota "The IMF publishes no projections for this country: latest year 2024". La Siria ha i dati FMI fermi al 2010: nota "IMF data stop in 2010". Macao: normale; per il saldo primario nota "IMF data end in 2022".
- **Anni fiscali** (33 Paesi, dipende dall'indicatore): nota sotto i grafici interessati: "For this country the IMF reports fiscal years (for example April–March for India): the year shown is the one in which the fiscal year starts, so 2024 means 2024/25." Il flag viene dallo snapshot esteso (§0.3).
- **Paesi con ultimo anno effettivo > ultimo anno con dato** (Sri Lanka, Macao, Siria, Cisgiordania e Gaza: 11 coppie) o **senza ultimo anno** (Guinea, popolazione): nessun tratteggio; la scheda dice `—` per l'anno.
- **Variante Banca Mondiale**: tutta "actual" (nessuna proiezione).
- Il **tratteggio dei dati dell'FMI "stima"** non è una proiezione: sono anni già passati non ancora confermati dalle statistiche nazionali (l'anno 2025 per molti Paesi): la legenda dice "Estimate or projection (IMF)" in un'unica voce.

## 4. WGI (controllo della corruzione)

- Linea del **punteggio 0-100** (`GOV_WGI_CC.SC`) con **banda all'intervallo al 90%** (`_LB`/`_UB`, area semitrasparente dello stesso colore) e **marcatori** sui punti (i dati sono 1996, 1998, 2000 poi annuali: tra i primi tre anni la linea non deve far credere a dati annuali, quindi marcatori visibili e tratto continuo solo dal 2002).
- Asse 0-100 fisso; titolo "Control of Corruption, score (0-100)"; mai "rank". Etichetta: "Higher = better control of corruption, as perceived".
- Tooltip: `2025 · 59.8 (90% interval 54.5–65.1)`. Scheda "Governance": valore + intervallo + anno.
- Nota sotto il grafico (nel registro `contenuti/note.yaml`): è un indicatore composto di **percezioni**, metodo WGI 2.0 (2025) ricalcolato dal 1996; "an interval is wide: differences smaller than the band are not meaningful" (la larghezza mediana dell'intervallo è 11 punti, fino a 64 per i Paesi con poche fonti).

## 5. Link "→ Economy" da Markets e riquadro Markets

**Blocco `paesi:` in `config.yaml`** (nuovo): una voce per ogni chiave `paese` di `colori` che è un Paese: `{iso3, nome, pagina}`; `pagina` = id della pagina di livello A se esiste (`economies/usa`, `economies/italy`, `economies/uk`, `economies/euro-area`), assente per gli altri. Chiavi: `us`→USA, `it`→ITA, `uk`→GBR, `jp`→JPN, `cn`→CHN, `kr`→KOR, `fr`→FRA, `de`→DEU, `ea` senza iso3 (pagina `economies/euro-area`). Le chiavi `global` e i gruppi di materie prime non hanno voce: nessun link.

**Regola della destinazione** (una sola funzione, testata):
1. se il Paese ha `pagina` **e** quella pagina è `attiva` → la pagina A (`economies/usa/`);
2. altrimenti, se ha un `iso3` → `economies/country.html?c=<ISO3>`;
3. area euro: se `economies/euro-area` non è attiva → **nessun link**;
4. mai un link a un Paese che non è nei dati (`?c=` controllato contro l'elenco dei 218 Paesi) né a una pagina `in-arrivo`: se non c'è destinazione, il link non si scrive.
Oggi: USA → `economies/usa/` (attiva, solo la disoccupazione); Italia e UK → `country.html?c=ITA`/`GBR` (le loro pagine sono "coming soon"); Giappone, Cina, Corea, Francia, Germania → `country.html?c=…`; area euro → niente. Quando negli step 11-13 una pagina A diventa attiva, i link cambiano da soli.

**Dove compaiono nei grafici Markets**: nel piè di ogni grafico, accanto a "Source": per i grafici di un solo Paese `→ Economy: Japan`; per i grafici di confronto un elenco `Economies: Japan · China · South Korea` (solo i Paesi presenti nel grafico, con destinazione valida). **Hub Economies**: le tre schede "later" (Japan, China, South Korea) diventano link a `country.html?c=…`; si aggiunge una scheda "Country explorer" (tutti i Paesi) e il campo di ricerca.
**Riquadro Markets** nella pagina Paese: generato dal campo `paese` delle serie di quel Paese, con una lista di serie in `paesi:` (`mercati: [...]`): Giappone (tasso BoJ, JGB 10Y, Nikkei 225, USD/JPY), Cina (LPR, CSI 300, USD/CNY), Corea (tasso BoK, KOSPI, USD/KRW), Francia (OAT 10Y, spread OAT-Bund, CAC 40), Germania (Bund 10Y, DAX), Italia (BTP 10Y, spread BTP-Bund, FTSE MIB), USA (Fed funds, Treasury 10Y, S&P 500, VIX). Con link alla pagina Markets giusta. I Paesi senza serie di mercato (tutti gli altri, UK incluso finché non ne ha) non hanno il riquadro.
`tools/controlla_link.py` verifica anche questi link (`?c=` valido, destinazione attiva).

## 6. Comportamento della pagina

- **File e indirizzo**: `site/economies/country.html` (un solo file; la parte `?c=` non conta per GitHub Pages). Link sempre relativi (`country.html?c=ITA` dalla stessa cartella; `../economies/country.html?c=ITA` da Markets). La pagina scrive il menu "Economies" come attivo.
- **Dati**: `site/economies/dati/<ISO3>.json` (≈3-4 KB compressi), caricato solo per il Paese scelto, più un elenco leggero dei Paesi (codice, nome, regione) dentro la pagina (circa 8 KB compressi) per il selettore e il `noscript`.
- **Selettore**: campo di ricerca (nome, in inglese, o codice ISO3, senza distinguere maiuscole/accenti), elenco filtrato sotto il campo, tastiera ↑↓ Invio Esc, voci di 44 px; pulsanti Previous/Next in ordine alfabetico; accessibile (ruolo `combobox`/`listbox`, annuncio del Paese caricato).
- **URL**: scegliendo un Paese l'indirizzo diventa `country.html?c=ITA` (`history.pushState`: il tasto Indietro e i link condivisi funzionano; `popstate` ricarica il Paese); `?c=ita` in minuscolo funziona (si normalizza); anche il titolo della scheda diventa "Italy · Macro dashboard".
- **Codice non valido** (`?c=XYZ` o assente nei dati): al posto delle sezioni compare un messaggio "We have no data for 'XYZ'" con il selettore e l'elenco dei Paesi (stesso elenco dello stato iniziale). **Nessun parametro**: introduzione + elenco dei Paesi raggruppato per regione, 4 Paesi principali in evidenza.
- **Errore di rete** nel caricare il file: messaggio con "Try again" e il selettore; i dati non vengono mai sostituiti da zeri.
- **`noscript`**: l'elenco completo dei 218 Paesi come link (`country.html?c=ITA` ecc.) e la frase "The charts need JavaScript" (senza JavaScript non ci sono dati: i dati non stanno nel HTML).
- **Peso**: vedi §0.4 (circa 0,45 MB compressi alla prima visita; 25 KB di HTML+JS+elenco; 3-4 KB di dati per Paese). JavaScript: un nuovo `static/paese.js` (~12 KB) che riusa Plotly e i colori come `app.js`; test: funzioni pure (preparazione dei dati: tratteggio, anno effettivo, anno fiscale, banda, scala) in Python e un controllo del peso in `inventario.py sito`.
- **Avvisi**: gli avvisi di freschezza degli snapshot compaiono nella pagina come nelle altre (soglia 210/456 giorni).

## 7. Righe "How to read it" (bozze, una per indicatore)

Tutti gli esempi sono dati reali dello snapshot, ultimo anno **effettivo** (non proiezione). Da rivedere prima del merge.

| # | Grafico | Riga proposta ("How to read it") | Numeri verificati |
|---|---|---|---|
| 1 | Real GDP growth | How much the economy's output grew compared with the year before, after removing price changes. Bars after the last actual year are IMF projections. Big one-off swings are usually shocks: Italy fell 8.9% in 2020 and rebounded 8.9% in 2021. | ITA 2020 −8,868; 2021 +8,931 (FMI) |
| 2 | Nominal GDP | The value of everything the economy produces, in US dollars at that year's exchange rate. It moves with growth, prices and the exchange rate, so a country can look smaller in dollars just because its currency weakened. | (definizione) |
| 3 | GDP per head, PPP | Output per person, adjusted for price differences between countries so incomes can be compared. The top of the ranking is held by small financial centres (in 2025: Liechtenstein, Singapore, Luxembourg, Ireland, Macao), so compare with similar economies: Italy is 34th of 193. | PPPPC 2025: LIE 192.420, SGP 164.318, LUX 152.966, IRL 152.632, MAC 134.485; ITA 63.538, 34° su 193 |
| 4 | Population | Number of residents, from the World Bank. In this series India overtook China in 2021. | WB 2021: India − Cina = +1,8 milioni; 2022 +13,2 |
| 5 | Inflation | Average inflation over the year (solid line) and December-on-December inflation (dotted). When prices move fast the two can differ a lot: Italy averaged 8.7% in 2022 but ended the year at 12.2%. | ITA 2022: 8,747 / 12,212; (ARG 2023: 133,5 / 211,4) |
| 6 | Unemployment | Share of people in the labour force without a job. These are ILO modelled estimates, made to be comparable across countries, so they can differ from the national figure: for Italy in 2025 the ILO estimate is 6.4% while Eurostat's own figure is 6.1%. | WB ITA 2025 6,391; Eurostat (15-74) 6,1; DEU 3,711 / 3,8 |
| 7 | Employment ratio | Share of everyone aged 15 or over who has a job (ILO modelled estimate). It depends on retirement ages and on how many women and young people work, not only on unemployment: in 2025 it was 46% in Italy, 58% in Germany, 59% in the US and 62% in Japan. | WB 2025: ITA 46,2; DEU 58,3; USA 59,1; JPN 61,9 |
| 8 | Government balance | Government revenue minus spending, as a share of GDP: below zero is a deficit. The line is the primary balance, which leaves out interest payments. Greece ran an overall surplus of 1.2% in 2024, and 4.7% before interest; the US deficit was 6.8% in 2025. | GRC 2024: 1,2 / 4,7 (ultimo effettivo 2024); USA 2025: −6,824 |
| 9 | Government debt | Gross debt of the general government as a share of GDP. A high ratio is not by itself a crisis: who holds the debt, in which currency and at what interest rate matter too. Japan was at 214% in 2024, Greece 155% in 2024, Italy 137% and the US 124% in 2025, Germany 63%. | JPN 2024 214,5; GRC 2024 155,4; ITA 2025 137,1; USA 123,9; DEU 62,9 |
| 10 | Current account | Net trade with the rest of the world, including income and transfers, as a share of GDP. A surplus means the country lends to the rest of the world, a deficit that it borrows: Germany +4.4% and Japan +4.8% in 2025; the US −4.0% and the UK −3.0% in 2024. | DEU 2025 4,416; JPN 4,829; USA 2024 −4,0; GBR 2024 −3,0 |
| 11 | Control of corruption | How well public power is kept from private gain, as perceived by surveys and experts (higher is better), on a 0–100 score; the band is the 90% interval. Differences smaller than the band are not meaningful: Italy scored 59.8 in 2025 (interval 54.5–65.1), the US 65.5, Denmark 93.6. | WGI 2025: ITA 59,82 [54,52–65,12]; USA 65,50; DNK 93,62; larghezza mediana 11 punti |
| 12 | IMF outlook (tabella) | IMF staff forecasts from the April 2026 World Economic Outlook, revised every April and October. The further ahead the year, the more uncertain the forecast; grey figures are years not yet confirmed by national statistics. | (definizione; WEO aprile 2026) |
| 13 | Markets (riquadro) | Market prices for this economy; the Markets pages compare them across countries. | — |

Tra le righe da non scrivere (non verificabili): "Japan's debt is sustainable", cause della crescita o previsioni.

## 8. Piano dei commit di 10b (dopo l'ok)

1. Snapshot: colonna `anno_fiscale`, via `gdp_per_capita_usd` e `population_imf` dal catalogo, alias `KOS`→`XKX`, `WBG`→`PSE`; test; riconfronto con il file vero.
2. Blocco `paesi:` e funzione di destinazione (testata); link "→ Economy" nei piè dei grafici Markets e schede dell'hub.
3. Preparazione dei dati per Paese (Python puro, testata): file `dati/<ISO3>.json`, tratteggio, anno effettivo, anno fiscale, banda WGI, scala; elenco Paesi.
4. Pagina `country.html` (template, `static/paese.js`, CSS), riquadro Markets, noscript, messaggi.
5. Note nel registro (ILO modellato, WGI, anni fiscali, stime FMI, Paesi non inclusi: 21 solo Banca Mondiale, Taiwan), tabella delle righe da rivedere, `controlla_link.py` e `inventario.py sito` estesi (peso, `?c=` validi).
6. Verifica nel browser: desktop e 375 px, Paesi di prova (ITA, USA, IND con anno fiscale, SYR senza proiezioni, TWN solo FMI, CUB solo WB, XYZ non valido), tema chiaro/scuro; riepilogo e **attesa dell'ok prima del merge**.

## 9. Decisioni da confermare

1. Togliere `gdp_per_capita_usd` e `population_imf` dal catalogo e dagli snapshot.
2. Estensione del formato di `ultimo_effettivo.csv` (colonna `anno_fiscale`).
3. Un file di dati per Paese (3,4 KB) invece di uno solo (0,54 MB).
4. Varianti "Source: IMF / World Bank" per crescita, PIL nominale e PIL pro capite PPA (storia lunga dal 1960 contro proiezioni FMI); in alternativa solo FMI e la WB solo dove l'FMI manca.
5. Periodi 10Y / 25Y / Max (predefinito 25Y).
6. Riquadro Markets: elenco delle serie per Paese come in §5.
