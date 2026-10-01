# Economies: verifica delle fonti (step 9, 01/10/2026; rivista dopo le decisioni dell'utente)

Solo verifica, nessun codice. Ogni riga è stata controllata con una **chiamata vera** il 01/10/2026 (contrassegno ✔) oppure è segnata **da verificare** (?) o **scartata** (✗).
"Ultimo dato" = ultima osservazione presente quel giorno. I paesi del livello B sono i **194 stati** (esclusi aggregati come "World", "Euro area", ecc.; territori piccoli inclusi quando hanno dati).

## Conclusioni in breve

1. **FMI**: il vecchio DataMapper (`www.imf.org/external/datamapper/api/v1/...`) risponde **403 Access Denied** (Akamai) a richieste automatiche, anche con intestazioni da browser. Funziona invece la **nuova API SDMX `api.imf.org`**, senza chiave. Il dataset DBnomics `IMF/WEO` non è utilizzabile: fermo (ultimo indicizzato 2025).
2. **Banca Mondiale**: API v2 senza chiave, funziona e riesce a restituire tutti i paesi in una chiamata. I dati WDI sono aggiornati al **13/07/2026** (anno 2025 per la maggior parte), i WGI al **25/09/2026** (anno 2025, 207 paesi).
3. **Eurostat, ECB, ONS, FRED** funzionano senza problemi. Due trappole nuove: (a) i dataset Eurostat con aggregato **`EA20` sono fermi a dicembre 2025** (dal 01/01/2026 l'area euro è a 21 paesi, Bulgaria): serve `EA21` (composizione variabile, da dichiarare in una nota); (b) **Eurostat `prc_hicp_manr` è fermo a 12/2025** come il vecchio dataset BCE `ICP` → per l'HICP si usa la BCE (`HICP/...4D0.ANR`, già nel progetto, ultimo dato 08/2026 per IT e area euro).
4. **Non c'è una fonte gratuita aggiornata** per: PMI (S&P Global/HCOB: proprietario), ISM (non più su FRED), fiducia OCSE su FRED (ferma a 01/2024). Sostituti gratuiti: ESI della Commissione UE (area euro, Italia), Michigan (USA, con licenza da leggere), per il UK da individuare.
5. **UK, ONS: l'API non è cambiata.** `HF6X` e `AA6H` esistono (debito netto/PIL e saldo di conto corrente/PIL): il 404 dipendeva dal **percorso** sbagliato (il codice va con la sezione giusta: `.../publicsectorfinance/timeseries/hf6x/pusf`, `.../balanceofpayments/timeseries/aa6h/ukea`). Debito e partite correnti del UK sono quindi coperti. Per i prezzi delle case funziona l'**UK House Price Index di HM Land Registry** (API JSON senza chiave).
6. **WGI: il rango percentile non esiste più.** Dal 2025 ("WGI 2.0") la Banca Mondiale pubblica la stima (−2,5…+2,5) e un **punteggio assoluto 0-100** ancorato a paesi di riferimento fissi, ricalcolato per tutta la serie dal 1996; il vecchio codice del percentile (`CC.PER.RNK`) restituisce vuoto. Il punteggio 0-100 (`GOV_WGI_CC.SC`) è ciò che più gli somiglia, ma **non è un rango**: va etichettato "score (0-100)". Decisione dell'utente: **solo il punteggio 0-100 con intervallo al 90%, nessun rango calcolato**.
7. **Licenze**: la più delicata è l'**FMI**: i dati statistici si possono copiare e ripubblicare con citazione, ma i termini vietano lo scarico "in massa" con automatismi senza permesso (vedi sotto). Va letta la pagina originale prima dello step 10 (non sono riuscito ad aprirla: 403).

## Livello B — tutti i paesi, dati annuali (FMI WEO + Banca Mondiale)

Chiamate usate: FMI `https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO/*.<INDICATORE>.A` (chiave = PAESE.INDICATORE.FREQUENZA, formato CSV con `Accept: application/vnd.sdmx.data+csv`);
Banca Mondiale `https://api.worldbank.org/v2/country/all/indicator/<CODICE>?format=json&per_page=20000` (WGI: aggiungere `&source=3`).
WEO: pubblicazione **14/04/2026** (aprile 2026; la prossima ottobre 2026), serie dal **1980** con **proiezioni fino al 2031**. "Paesi" = con almeno un dato; "al più recente" = paesi che hanno il dato per l'ultimo anno disponibile.

| Indicatore | Fonte | Codice / endpoint | Freq. | Inizio | Ultimo dato (dato "vero" + stime) | Paesi coperti (194 / 217 WB) | Note su definizioni e revisioni | Esito |
|---|---|---|---|---|---|---|---|---|
| PIL nominale (USD) | FMI WEO | `NGDPD` | A | 1980 | 2025 (stima per ~110 paesi); proiezioni a 2031 | **194** | Miliardi di USD correnti; converte il PIL in valuta locale al cambio medio: le variazioni mischiano crescita e cambio. Revisioni a ogni WEO (apr/ott). | ✔ |
| PIL nominale (USD) | Banca Mondiale | `NY.GDP.MKTP.CD` | A | 1960 | 2025 | 214 (186 al 2025) | Storia più lunga; alternativa se si vuole prima del 1980. | ✔ riserva |
| Crescita PIL reale | FMI WEO | `NGDP_RPCH` | A | 1980 | 2025 (dato per 72 paesi, stima per gli altri; 2024 il "dato" per 83); proiezioni a 2031 | **194** | % annua su prezzi costanti; base e metodo (catena) dichiarati per paese nel campo `METHODOLOGY`. | ✔ |
| Crescita PIL reale | Banca Mondiale | `NY.GDP.MKTP.KD.ZG` | A | 1961 | 2025 | 214 (186 al 2025) | Riserva e storia 1961–79. | ✔ riserva |
| PIL pro capite a PPA | FMI WEO | `PPPPC` | A | 1980 | 2025; proiezioni a 2031 | **194** | $ internazionali correnti. Le PPA sono riviste con i nuovi round ICP: i livelli passati cambiano anche molto (WEO e WB non coincidono). | ✔ |
| PIL pro capite a PPA | Banca Mondiale | `NY.GDP.PCAP.PP.CD` (e `.KD` a prezzi 2021) | A | 1990 | 2025 | 203 (185 al 2025) | Usare **una sola** fonte per grafico. | ✔ riserva |
| PIL pro capite (USD) | FMI WEO | `NGDPDPC` | A | 1980 | 2025; proiezioni 2031 | 194 | Non richiesto ma coerente con `NGDPD`/`LP`. | ✔ |
| Inflazione (media annua CPI) | FMI WEO | `PCPIPCH` (e `PCPIEPCH` fine periodo) | A | 1980 | 2025 (dato per 142 paesi, stima per gli altri); proiezioni | **194** (193 per fine periodo) | Media annua; i CPI nazionali differiscono per paniere (Argentina, Turchia ecc. con rotture). | ✔ |
| Inflazione | Banca Mondiale | `FP.CPI.TOTL.ZG` | A | 1960 | 2025 | 193 (165 al 2025) | Deriva dall'FMI (IFS): nessun vantaggio; copertura più bassa. | ✗ scartare |
| Disoccupazione | Banca Mondiale (ILO modellato) | `SL.UEM.TOTL.ZS` | A | 1991 | 2025 | **187** (182 al 2025) | **Stima modellata dell'ILO, non una statistica nazionale** (per molti paesi senza indagine sulle forze di lavoro è un'imputazione): confronta i paesi con una definizione uguale ma può differire dal dato ufficiale. Sul sito: etichetta "ILO modelled estimate" nel grafico e nota nel registro. | ✔ |
| Disoccupazione | FMI WEO | `LUR` | A | 1980 | 2025; proiezioni | **115** | Copertura troppo bassa: manca quasi tutta l'Africa e il Medio Oriente. | ✗ scartare (usare WB) |
| Tasso di occupazione (15+) | Banca Mondiale (ILO modellato) | `SL.EMP.TOTL.SP.ZS` | A | 1991 | 2025 | **187** (182 al 2025) | Occupati / popolazione 15+ (non 15-64): molto sensibile all'invecchiamento. **Stima modellata ILO** (stessa etichetta e nota della disoccupazione). | ✔ |
| Tasso di occupazione (stime nazionali) | Banca Mondiale | `SL.EMP.TOTL.SP.NE.ZS` | A | 1960 | 2025 solo 70 paesi | 209 (ma 70 al 2025) | Dati vecchi per molti paesi. | ✗ scartare |
| Deficit / PIL (saldo generale delle PA) | FMI WEO | `GGXCNL_NGDP` (anche saldo primario `GGXONLB_NGDP`) | A | 1980 | 2025 (64 dati, resto stime); proiezioni | **194** (primario 189) | Saldo netto delle amministrazioni pubbliche; il perimetro (centrale, generale) varia per paese: il WEO dichiara quale. | ✔ |
| Debito pubblico / PIL | FMI WEO | `GGXWDG_NGDP` | A | 1980 | 2025 (61 dati, resto stime); proiezioni | **190** | Debito lordo delle PA; il perimetro e la valutazione (nominale, mercato) cambiano per paese. | ✔ |
| Debito / PIL | Banca Mondiale | `GC.DOD.TOTL.GD.ZS` | A | 1970 | **2024 solo 33 paesi** | 109 | Solo governo centrale, copertura scarsa. | ✗ scartare |
| Partite correnti / PIL | FMI WEO | `BCA_NGDPD` | A | 1980 | 2025; proiezioni | **193** | Saldo/PIL in USD. | ✔ |
| Partite correnti / PIL | Banca Mondiale | `BN.CAB.XOKA.GD.ZS` | A | 1960 | 2025 solo 97 paesi (2024: 68) | 200 | Copertura dell'ultimo anno a metà. | ✗ scartare |
| Popolazione | FMI WEO | `LP` | A | 1980 | 2025; proiezioni | **194** | Milioni di persone. | ✔ |
| Popolazione | Banca Mondiale | `SP.POP.TOTL` | A | 1960 | 2025 | **217 (tutti)** | Storia lunga, tutti i paesi: **preferita** per la popolazione storica. | ✔ |
| Controllo della corruzione (WGI) | Banca Mondiale (WGI, source 3) | **principale: `GOV_WGI_CC.SC`** (punteggio assoluto 0-100, **non** un rango percentile) con intervallo al 90% `…SC_LB` / `…SC_UB`; di supporto `GOV_WGI_CC.EST` (stima −2,5…+2,5), `…SE`, `…SR` (n. fonti). `CC.PER.RNK` non esiste più | A | 1996 (1996, 1998, 2000, poi annuale) | **2025** (aggiornato 25/09/2026; ricalcolato dal 1996 col metodo 2025) | **207** (nessun rango: decisione dell'utente) | Indice composito di **percezioni** (non misura la corruzione): ha un margine d'errore ampio, piccole differenze tra paesi/anni non sono significative; mostrare l'intervallo. I vecchi codici (`CC.EST`) non esistono più: ora hanno prefisso `GOV_WGI_`. | ✔ |
| Previsioni FMI | FMI WEO | stessi codici di sopra: gli anni dopo l'ultimo "dato" (campo `LATEST_ACTUAL_ANNUAL_DATA`) sono stime/proiezioni | A | — | fino al 2031 (a 2 anni affidabili; 3-5 anni = medio periodo) | come l'indicatore | Distinguere **dato reale / stima / proiezione** con `LATEST_ACTUAL_ANNUAL_DATA` e `BASIS_OF_PROJECTIONS`. Le revisioni tra aprile e ottobre sono normali. | ✔ |

**Scelta consigliata per il livello B**: tutto ciò che è macro in una sola fonte (**FMI WEO**: PIL, crescita, PIL pro capite PPA, inflazione, deficit, debito, partite correnti, popolazione corrente, previsioni), e la **Banca Mondiale** solo per ciò che il WEO non ha o che ha scarso:
disoccupazione e occupazione (ILO), popolazione storica, **WGI** (corruzione). Storie più lunghe del 1980: Banca Mondiale come riserva (PIL, crescita).
Riempimento: gli anni dell'FMI senza dato reale sono **stime** per ~60-110 paesi: nel grafico vanno tratteggiati.

### Paesi: nota di copertura
- WEO: 194 "paesi" con almeno un dato, ma 210 entità con gli aggregati; mancano alcuni territori e Cuba (visti nella lista dei paesi senza dati: Gibilterra, Guam, Groenlandia, Isole Cayman...).
- WGI: 207 paesi/territori. Banca Mondiale: 217 con popolazione.
- Il livello B include **Giappone, Cina, Corea del Sud** (oggi schede "later" in Economies): coprono il vuoto lasciato dalle pagine nazionali.

## Livello A — USA, Italia, Area euro, Regno Unito (mensile/trimestrale)

Legenda: ✔ verificato oggi; ◐ verificato in parte; ? da verificare nello step indicato; ✗ scartato.
Per le serie in livello A il confronto con il livello B (annuale, FMI) resta disponibile nella stessa pagina per PIL pro capite a PPA, corruzione, previsioni FMI.

### Stati Uniti (FRED, chiave già nel progetto)

| Indicatore | Codice FRED | Freq. | Inizio | Ultimo dato | Note | Esito |
|---|---|---|---|---|---|---|
| PIL nominale | `GDP` | T | 1947-Q1 | 2026-Q2 | Miliardi di $, annualizzato, destagionalizzato. Revisioni forti per i 3 anni precedenti. | ✔ |
| Crescita PIL reale | `A191RL1Q225SBEA` (t/t annualizzata); `GDPC1` (livello, per calcolare a/a) | T | 1947-Q2 | 2026-Q2 | Quella pubblicata (BEA) è **annualizzata**, quella dell'Italia/UE è t/t non annualizzata: etichette chiare. | ✔ |
| PIL pro capite a PPA | nessuna serie nazionale; → livello B (FMI `PPPPC`) | A | 1980 | 2025 | | ◐ (da B) |
| Inflazione | `CPIAUCSL` (indice) → a/a con `yoy` | M | 1947 | 2026-08 | | ✔ |
| Disoccupazione | `UNRATE` | M | 1948 | 2026-08 | già nel sito | ✔ |
| Tasso di occupazione | `EMRATIO` (15+); `LNS12300060` (25-54, più confrontabile) | M | 1948 | 2026-08 | Scegliere 25-54 per evitare l'effetto invecchiamento; `CIVPART` = partecipazione. | ✔ |
| Deficit / PIL | **principale: FMI** `GGXCNL_NGDP` (amministrazioni pubbliche, livello B). **Grafico aggiuntivo: FRED** `FYFSGDA188S` (solo federale, annuale) | A | 1980 (FMI) / 1929 (FRED) | 2025 | Decisione dell'utente: il dato principale è quello delle PA (FMI, confrontabile); il federale è solo un secondo grafico con etichetta "Federal government only". | ✔ |
| Debito / PIL | **principale: FMI** `GGXWDG_NGDP` (PA, lordo). **Grafico aggiuntivo: FRED** `GFDEGDQ188S` (debito federale totale) | A (FMI) / T (FRED) | 1980 / 1966-Q1 | 2025 / 2026-Q1 | Come sopra; le due fonti non si mescolano nello stesso grafico. | ✔ |
| Partite correnti / PIL | `NETFI` (saldo in $, trimestrale) ÷ `GDP` (calcolata, stessa fonte FRED) | T | 1947-Q1 | 2026-Q2 | Rapporto da calcolare (regola della stessa fonte). `IEABCSN` è il saldo dei **servizi**, non usare. | ◐ |
| Popolazione | `POPTHM` | M | 1959 | 2026-08 | stima mensile Census, in migliaia. | ✔ |
| Prezzi delle case | `CSUSHPINSA` (S&P Cotality Case-Shiller, M); `USSTHPI` (FHFA, T) | M / T | 1987 / 1975 | 2026-07 / 2026-Q2 | Case-Shiller: dati di proprietà S&P, FRED ne mostra il copyright → preferire FHFA (ente pubblico). | ✔ |
| Fiducia / congiuntura | `UMCSENT` (Michigan) ✔ M 1952-2026-08; ISM PMI `NAPM` ✗ non più su FRED; `BSCICP03USM665S` (OCSE) ✗ ferma a 01/2024 | M | — | — | **Michigan solo se la licenza lo consente** (decisione dell'utente): i termini dell'Università del Michigan/FRED si leggono nello step 11; se non permettono la ripubblicazione, gli USA non hanno fiducia. Niente PMI/ISM/GfK. | ? (licenza) |
| Potenziale (opz.) | `GDPPOT` (CBO) | T | 1949 | 2036 | Stime CBO, ferme a febbraio 2026. | ✔ (opz.) |

### Italia e Area euro (Eurostat, BCE; ISTAT come riserva)

Eurostat: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/<dataset>?format=JSON&geo=IT&geo=EA21&...` (SDMX-JSON, senza chiave). BCE: `https://data-api.ecb.europa.eu/service/data/<dataset>/<chiave>`. ISTAT: `https://esploradati.istat.it/SDMXWS/rest/` risponde 200 (non testati i dati).

| Indicatore | Dataset e filtri | Freq. | Inizio (IT / EA) | Ultimo dato | Note | Esito |
|---|---|---|---|---|---|---|
| PIL nominale | Eurostat `namq_10_gdp` `unit=CP_MEUR`, `s_adj=SCA`, `na_item=B1GQ` | T | 1995-Q1 / 1995-Q1 | 2026-Q2 (agg. 30/09) | Milioni di €, aggregato `EA21` (con `EA20` fino a 2026-Q2 per il solo PIL). | ✔ |
| Crescita PIL reale | stesso dataset `unit=CLV_PCH_PRE` (t/t) o `CLV_PCH_SM` (a/a) | T | 1996-Q2 / 1995-Q2 | 2026-Q2 | BCE `MNA/Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.GY` (a/a) arriva solo a 2026-Q1: Eurostat più fresco. | ✔ |
| PIL pro capite a PPA | nessuna serie trimestrale; → livello B | A | — | — | | ◐ (da B) |
| Inflazione | **BCE** `HICP/M.IT.N.000000.4D0.ANR` e `HICP/M.U2.N.000000.4D0.ANR` | M | 1997 / 1991 | 2026-08 (3,2% entrambi) | Eurostat `prc_hicp_manr` è fermo a 12/2025 ✗. Core: `XEF000` (già nel progetto per l'area euro). | ✔ |
| Disoccupazione | Eurostat `une_rt_m` `s_adj=SA`, `age=TOTAL`, `sex=T`, `unit=PC_ACT` | M | 1983 / 2000 | 2026-08 (agg. 01/10) | Aggregare `EA21`. Definizione ILO armonizzata. | ✔ |
| Tasso di occupazione | Eurostat `lfsi_emp_q` `age=Y20-64`, `indic_em=EMP_LFS`, `unit=PC_POP` | T | 2009-Q1 / 2009-Q1 | 2026-Q2 | 20-64 anni (indicatore UE 2030), diverso da 15+ (livello B). | ✔ |
| Deficit / PIL | Eurostat `gov_10dd_edpt1` (annuale, `na_item=B9`) e `gov_10q_ggnfa` (trimestrale, non destagionalizzato) | A / T | 1995 / 1995 (A); 1999 / 2002 (T) | 2025 (A); 2026-Q1 (T) | Preferire l'annuale e il "4 trimestri mobili" per evitare la stagionalità. Il filtro di `B9` annuale da confermare. | ◐ (T ✔, A da confermare) |
| Debito / PIL | Eurostat `gov_10q_ggdebt` `sector=S13`, `na_item=GD`, `unit=PC_GDP` | T | 2000-Q1 / 2000-Q1 | 2026-Q1 | Definizione Maastricht (lordo consolidato). Ritardo di un trimestre in più del PIL. | ✔ |
| Partite correnti / PIL | Eurostat `tipsbp20` (IT annuale 1995–2025 ✔; area euro: nessun dato `EA21`); BCE `BP6/...` (chiave Italia trovata ma ferma al 2022-Q3: **non usare**) | A / T | 1995 | 2025 (A, solo IT) | **Da trovare nello step 12** (`bop_c6_q` da riscrivere con dimensioni giuste). | ? |
| Popolazione | Eurostat `demo_pjan` `age=TOTAL`, `sex=T` | A (1° gennaio) | 1960 / 2013 | 2025 | Il 2026 non c'è ancora. | ✔ |
| Prezzi delle case | Eurostat `prc_hpi_q` `purchase=TOTAL`, `unit=I15_Q` | T | 2010-Q1 / 2005-Q1 | 2026-Q2 (agg. 01/10) | Indice (2015=100), non in euro; controllare che `EA21` esista (`EA20` sì). | ✔ |
| Fiducia (ESI) | Eurostat `ei_bssi_m_r2` `indic=BS-ESI-I`, `s_adj=SA` | M | 1980 / 1980 | 2026-09 (agg. 29/09) | Indice di fiducia economica della Commissione UE, gratuito, `EA21` e IT fino a settembre 2026 (con `EA20` si ferma a 12/2025 ✗). PMI HCOB: ✗ proprietario. | ✔ |
| Fiducia (ISTAT) | non necessaria: l'**ESI** copre già Italia e area euro (decisione dell'utente) | — | — | — | Solo ESI per Italia e area euro. | — |

### Regno Unito (ONS, endpoint JSON `https://www.ons.gov.uk/<percorso>/timeseries/<codice>/<dataset>/data`)

| Indicatore | Serie ONS | Freq. | Inizio | Ultimo dato | Note | Esito |
|---|---|---|---|---|---|---|
| PIL nominale | `YBHA` (dataset `pn2`), £m | T | (anno da leggere nello step 13) | 2026-Q2 | | ✔ |
| Crescita PIL reale | `IHYQ` (t/t) e `IHYR` (a/a) (`qna`) | T | 1955-Q2 / 1956-Q1 | 2026-Q2 (agg. 29/09) | | ✔ |
| PIL pro capite a PPA | → livello B | A | — | — | | ◐ (da B) |
| Inflazione | `D7G7` (CPI, tasso annuo, `mm23`) | M | (da leggere) | 2026-08 (3,1%) | `CHAW` = RPI (indice, non usare per il target). | ✔ |
| Disoccupazione | `MGSX` (16+, dest., `lms`) | M | (da leggere) | 2026-06 (periodo mobile mag-lug) = 4,9% | **Attenzione**: i mesi sono medie mobili a 3 mesi, nel JSON `date` = mese centrale, `label` = intervallo. | ✔ |
| Tasso di occupazione | `LF24` (16-64) | M | (da leggere) | 2026-06 (mobile) = 75,1% | Come sopra. | ✔ |
| Deficit / PIL | principale: FMI `GGXCNL_NGDP` (comparabile). Nazionale ONS: `J5IJ` (PSNB escl. banche pubbliche, % PIL, **solo trimestrale**: 1955-Q4 → 2026-Q1 = 4,4%; le colonne annuale e mensile sono ferme/vuote) oppure `DZLS` (£m, a 2026-Q2) ÷ `YBHA` (PIL, £m), entrambe ONS, **con numeratore e denominatore sullo stesso periodo** (somma di 4 trimestri / PIL degli stessi 4 trimestri, non un anno diviso un altro) | T | 1955-Q4 (J5IJ) | 2026-Q1 (J5IJ) / 2026-Q2 (DZLS) | Il trimestrale è stagionale (CPNSA): usare 4 trimestri mobili. | ✔ |
| Debito / PIL | ONS `HF6X` (debito netto del settore pubblico escl. banche pubbliche, % PIL, dataset `pusf`): **esiste**, il 404 era un errore di percorso | M / T / A | 1993-03 (M), 1975-Q1 (T), 1975 (A) | 2026-08 = 93,8% (M); 2026-Q2 = 94,6% (T); 2025 = 94,2% (A) | **Debito netto**, diverso dal lordo di Maastricht/FMI: etichetta "Public sector net debt"; il lordo FMI resta il dato confrontabile. | ✔ |
| Partite correnti / PIL | ONS `AA6H` (saldo di conto corrente in % del PIL, dataset `ukea`): **esiste**, il 404 era un errore di percorso (`/bop/` sbagliato, `/ukea/` giusto); `HBOP` = in £m | T / A | 1955-Q1 / 1948 | 2026-Q2 = −2,5% (T); 2025 = −3,0% (A) | | ✔ |
| Popolazione | `UKPOP` (stima a metà anno, dataset `pop`) | A | 1971 | 2025 | Il percorso è giusto (JSON valido); i valori hanno le virgole ("55,928,000"): da ripulire in lettura. | ✔ |
| Prezzi delle case | **UK House Price Index (HM Land Registry)**: `https://landregistry.data.gov.uk/data/ukhpi/region/united-kingdom/month/<AAAA-MM>.json` (una richiesta per mese; esiste anche l'estrazione CSV dal sito); campi `housePriceIndex`, `averagePrice`, `percentageAnnualChange` | M | 1995-01 (verificato: indice 19,6) | 2026-07 (indice 104,5; +1,4% a/a) | Indice, non in £; base e metadati da leggere nello step 13. Gli ultimi mesi vengono rivisti. Licenza: Open Government Licence (da riverificare). Verificato solo il Regno Unito nel suo insieme. | ✔ |
| Fiducia | GfK, PMI (S&P): proprietari | M | — | — | **Esclusa** (decisione dell'utente: niente PMI/ISM/GfK): il UK non ha fiducia nella pagina. | ✗ |

## Licenze e ripubblicazione (cosa limita il sito)

| Fonte | Termini | Rischio per il sito |
|---|---|---|
| **FMI** (WEO, api.imf.org) | Le pagine dei termini (403 per i bot) non si sono aperte; dal riassunto di una ricerca: il copyright generale vieta di ripubblicare contenuti su siti non-FMI, ma per i **dati statistici** valgono "termini speciali" che permettono copia, opere derivate, pubblicazione e distribuzione **con citazione**; vietato lo **scarico in massa con automatismi senza permesso** e l'uso per addestrare modelli. Citazione suggerita: "International Monetary Fund, World Economic Outlook (WEO), https://data.imf.org/en/datasets/IMF.RES:WEO". | **Medio**: pochi dati/poche richieste (dataset di 12 indicatori, 2 volte l'anno), citazione sempre visibile; **da leggere i termini originali e, se serve, scrivere a datahelp@imf.org** prima dello step 10. |
| **Banca Mondiale** (WDI, WGI) | In genere CC BY 4.0 con citazione (non riverificato oggi). Alcuni indicatori WDI sono dati di terzi (es. l'inflazione e il debito centrale sono dell'FMI, l'occupazione dell'ILO) con termini loro. | Basso; per ILO/FMI citare l'ente originale (lo fa il campo `sourceOrganization`). |
| **Eurostat** | CC BY 4.0 per i dati della Commissione (non riverificato oggi). | Basso. |
| **BCE** | Riuso consentito con citazione della fonte (già usata dal progetto). | Basso. |
| **ONS** | Open Government Licence v3.0 (non riverificato oggi). | Basso. |
| **FRED / BEA / FHFA / BLS / CBO** | Dati pubblici USA (nessun diritto), ma FRED ospita anche **serie di terzi con copyright** (Case-Shiller → S&P, Università del Michigan, ICE per gli spread già usati nel progetto): ogni pagina FRED riporta una nota di copyright. | Basso per BEA/BLS/FHFA/CBO; **medio** per Michigan e Case-Shiller (evitare, oppure leggere le note). |
| **ISTAT** | CC BY 3.0 IT (da riverificare). | Basso. |
| PMI (S&P Global/HCOB/ISM), GfK | Proprietari. | **Escluderli**. |

## Rischi tecnici trovati
- DataMapper FMI bloccato da Akamai ai bot; `api.imf.org` risponde da questo PC, ma **non è provato da GitHub Actions** (indirizzi di data center): da provare con un workflow di prova nello step 10. Se bloccato, riserva: Banca Mondiale per le serie che esistono lì.
- Aggregato area euro: `EA20` (fermo a 12/2025 per le serie mensili) → `EA21`; nota su Bulgaria dal 01/01/2026.
- Frequenza: i dati del livello B cambiano 2-3 volte l'anno (WEO apr/ott, WDI lug, WGI set): non serve riscaricarli ogni giorno.
- Peso: 194 paesi × ~12 indicatori × ~45 anni ≈ 100.000 numeri; in JSON compatto circa 0,5-1 MB compressi: va scelto il disegno (una pagina con selettore del paese, non 194 pagine).

## Dati FMI: snapshot nel repository (decisione dell'utente) e alternativa del file scaricato a mano

**Decisione**: i dati WEO stanno in uno snapshot versionato nel repository (`dati/weo/*.csv`), aggiornato **a ogni nuovo WEO** (aprile e ottobre; quello di aprile 2026 è uscito il 14/04/2026, quello di ottobre 2026 esce a metà ottobre). La build giornaliera legge solo lo snapshot: non chiama mai l'FMI.

| | **A. API `api.imf.org` (script lanciato a mano sul PC dell'utente)** | **B. File WEO scaricato a mano dal sito FMI** |
|---|---|---|
| Come | `python tools/aggiorna_weo.py`: circa 12 richieste (una per indicatore, tutti i paesi), due volte l'anno | si scarica il file "By Countries / entire database" dalla pagina del WEO e lo si mette in `dati/weo/` |
| Pro | Ripetibile e verificabile; porta tutti gli attributi (`LATEST_ACTUAL_ANNUAL_DATA`, metodologia, data di pubblicazione, base delle proiezioni); poche richieste, avviate da una persona (compatibile con il divieto di scarico automatico in massa); un solo codice per tutti gli indicatori | Nessun blocco Akamai né API che può cambiare; è il prodotto ufficiale che l'FMI cita; il permesso d'uso è più chiaro (download manuale per uso non sistematico) |
| Contro | L'API è nuova e può cambiare (si romperebbe lo script); non si può lanciare da GitHub Actions perché potrebbe essere bloccata (per questo è manuale) | Passo manuale ogni volta; il file è un testo tabulato con una colonna per anno, con "n/a" e note a parte, quindi serve un importatore con più cura; meno metadati (la data di pubblicazione va scritta a mano); il sito FMI blocca anche i download automatici, quindi non si può automatizzare; più rischio di errori |
| Consiglio | **Principale** | **Riserva, da scrivere comunque nello step 10**: se l'FMI rifiuta lo script o l'API cambia si usa l'importatore del file (decisione dell'utente: non si ripiega sulla sola Banca Mondiale) |

Lo snapshot ha lo stesso formato nei due casi (colonne: paese ISO3, indicatore, anno, valore, `stima` sì/no, data di pubblicazione del WEO), quindi si può cambiare metodo senza toccare il resto.

### Controllo di freschezza a semestri
- Le serie WEO non hanno un "ultimo dato" giornaliero: contano la **data di pubblicazione dello snapshot** e il calendario (aprile e ottobre, a metà mese). Il controllo segnala se lo snapshot ha più di **210 giorni** dalla pubblicazione del WEO (6 mesi + circa 4 settimane di margine). Esempio: WEO del 14/04/2026 → avviso dal 10/11/2026 se non è arrivato quello di ottobre. Il WEO di ottobre 2026 (metà mese) non genera quindi falsi allarmi; l'avviso compare nelle pagine Economies e, in breve, nell'Overview.
- Banca Mondiale: WDI **annuale con aggiornamento a luglio** (13/07/2026), WGI **annuale a settembre** (25/09/2026): soglia di **15 mesi** dalla data dello snapshot, solo avviso.
- La soglia standard (10/21/75/120 giorni dalla fine del periodo) non vale per queste serie: si introducono le frequenze `semestrale` (WEO) e `annuale` (WB) in `data.py`, con il motivo scritto in `config.yaml`, come per `soglia_giorni`.
