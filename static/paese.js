/* =====================================================================
   Pagina del Paese (economies/country.html?c=ISO3).
   1. selettore con ricerca (nome o codice ISO3), pulsanti Previous/Next, tastiera;
   2. l'indirizzo segue il Paese (?c=ITA, tasto Indietro incluso); codice non valido = messaggio con il selettore;
   3. i dati di ogni Paese stanno in dati/<ISO3>.json (generati da dashboard/paesi.py); qui si disegnano schede, grafici (Plotly) e tabella "IMF outlook";
   4. dopo l'ultimo anno effettivo (stima o proiezione dell'FMI) linee tratteggiate e barre chiare;
   5. periodi 10Y / 25Y / Max contati dall'ultimo anno effettivo: le proiezioni restano sempre visibili.
   La struttura della pagina (sezioni, titoli, righe "How to read it") è già nell'HTML; i colori vengono dal tema (variabili CSS --c-<chiave>).
   ===================================================================== */
(function () {
  "use strict";

  const specEl = document.getElementById("spec-paese");
  if (!specEl) return;
  const SPEC = JSON.parse(specEl.textContent);
  const $ = (id) => document.getElementById(id);
  const ANNI_PERIODO = { "10Y": 10, "25Y": 25 };
  const PERIODO_INIZIALE = "25Y";

  // ----------------------------------------------------------------------
  // Utilità
  // ----------------------------------------------------------------------
  const norma = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const num = (v, cifre) => Number(v).toLocaleString("en-US", { minimumFractionDigits: cifre, maximumFractionDigits: cifre });
  const conUnita = (testo, unita) => testo + (unita && unita.charAt(0) === "%" ? unita : unita ? " " + unita : "");
  const etichettaAnno = (anno, fiscale) => (fiscale ? anno + "/" + String(anno + 1).slice(2) : String(anno));
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function leggiTema() {
    const stile = getComputedStyle(document.documentElement);
    const v = (nome) => stile.getPropertyValue(nome).trim();
    return { superficie: v("--superficie"), testo: v("--testo"), testo2: v("--testo-2"), tenue: v("--testo-tenue"), griglia: v("--griglia"),
             asse: v("--asse"), colore: (chiave) => v("--c-" + chiave) || v("--c-mondo") || v("--testo") };
  }
  function rgba(colore, alfa) {
    const m = /^#([0-9a-f]{6})$/i.exec(colore);
    if (!m) return colore;
    const n = parseInt(m[1], 16);
    return "rgba(" + (n >> 16) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alfa + ")";
  }

  // ----------------------------------------------------------------------
  // Elenco dei Paesi (sono link normali nell'HTML: senza JavaScript restano utilizzabili)
  // ----------------------------------------------------------------------
  const voci = Array.from(document.querySelectorAll("#paese-elenco a[data-c]")).map((a) => ({
    c: a.dataset.c, nome: a.dataset.nome, regione: a.dataset.regione, chiave: norma(a.dataset.nome),
  }));
  const perCodice = new Map(voci.map((v) => [v.c, v]));
  const alfabetico = voci.slice().sort((a, b) => a.chiave.localeCompare(b.chiave));

  let corrente = null;       // codice mostrato
  let sequenza = 0;          // per ignorare le risposte arrivate in ritardo
  const cache = new Map();   // codice -> dati

  // ----------------------------------------------------------------------
  // Selettore
  // ----------------------------------------------------------------------
  const campo = $("cerca-paese"), lista = $("risultati-paese");
  let risultati = [], attivo = -1;

  function chiudiLista() {
    lista.hidden = true; campo.setAttribute("aria-expanded", "false"); campo.removeAttribute("aria-activedescendant"); attivo = -1;
  }
  function cerca(q) {
    q = norma(q.trim());
    if (!q) return [];
    const trovati = voci.filter((v) => v.chiave.includes(q) || v.c.toLowerCase().startsWith(q));
    trovati.sort((a, b) => (b.chiave.startsWith(q) - a.chiave.startsWith(q)) || (b.c.toLowerCase() === q) - (a.c.toLowerCase() === q) || a.chiave.localeCompare(b.chiave));
    return trovati.slice(0, 12);
  }
  function mostraLista() {
    risultati = cerca(campo.value);
    lista.innerHTML = "";
    if (!risultati.length) {
      if (campo.value.trim()) {
        const li = document.createElement("li");
        li.className = "nessuno"; li.textContent = "No country matches “" + campo.value.trim() + "”";
        lista.appendChild(li);
        lista.hidden = false; campo.setAttribute("aria-expanded", "true");
      } else chiudiLista();
      return;
    }
    risultati.forEach((v, i) => {
      const li = document.createElement("li");
      li.id = "opzione-" + i; li.setAttribute("role", "option"); li.dataset.c = v.c;
      li.innerHTML = "<span>" + esc(v.nome) + "</span><small>" + esc(v.c) + "</small>";
      lista.appendChild(li);
    });
    lista.hidden = false; campo.setAttribute("aria-expanded", "true"); impostaAttivo(0);
  }
  function impostaAttivo(i) {
    const opzioni = lista.querySelectorAll('[role="option"]');
    opzioni.forEach((o, k) => o.setAttribute("aria-selected", k === i ? "true" : "false"));
    attivo = i;
    if (opzioni[i]) { campo.setAttribute("aria-activedescendant", opzioni[i].id); opzioni[i].scrollIntoView({ block: "nearest" }); }
  }
  function scegli(codice) {
    chiudiLista();
    mostra(codice, { push: true });
  }
  campo.addEventListener("input", mostraLista);
  campo.addEventListener("focus", () => { campo.select(); if (campo.value.trim() && campo.value !== (perCodice.get(corrente) || {}).nome) mostraLista(); });
  campo.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); if (lista.hidden) mostraLista(); else impostaAttivo(Math.min(attivo + 1, risultati.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); impostaAttivo(Math.max(attivo - 1, 0)); }
    else if (e.key === "Enter") { if (!lista.hidden && risultati[attivo]) { e.preventDefault(); scegli(risultati[attivo].c); } }
    else if (e.key === "Escape") { chiudiLista(); campo.value = corrente ? perCodice.get(corrente).nome : ""; }
  });
  // mousedown (non click): il campo non deve perdere il fuoco prima della scelta
  lista.addEventListener("mousedown", (e) => { const li = e.target.closest("[data-c]"); if (li) { e.preventDefault(); scegli(li.dataset.c); } });
  lista.addEventListener("touchend", (e) => { const li = e.target.closest("[data-c]"); if (li) { e.preventDefault(); scegli(li.dataset.c); } });
  document.addEventListener("click", (e) => { if (!e.target.closest(".selettore-campo")) chiudiLista(); });

  function vicino(passo) {
    const i = corrente ? alfabetico.findIndex((v) => v.c === corrente) : -1;
    const k = i < 0 ? (passo > 0 ? 0 : alfabetico.length - 1) : (i + passo + alfabetico.length) % alfabetico.length;
    mostra(alfabetico[k].c, { push: true });
  }
  $("paese-prec").addEventListener("click", () => vicino(-1));
  $("paese-succ").addEventListener("click", () => vicino(1));
  $("selettore").hidden = false;

  // I link dell'elenco restano link veri (aprono la pagina del Paese), ma senza ricaricare la pagina
  document.querySelectorAll("#paese-elenco a[data-c]").forEach((a) => {
    a.addEventListener("click", (e) => {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
      e.preventDefault(); mostra(a.dataset.c, { push: true });
    });
  });

  // ----------------------------------------------------------------------
  // Caricamento e cambio di Paese
  // ----------------------------------------------------------------------
  function mostraStatoIniziale(messaggio) {
    corrente = null;
    $("paese-contenuto").hidden = true;
    $("paese-elenco").hidden = false;
    const errore = $("paese-errore");
    errore.hidden = !messaggio;
    errore.innerHTML = messaggio || "";
    $("paese-titolo").textContent = "Country explorer";
    document.title = "Country explorer · Macro dashboard";
    campo.value = "";
    const riga = $("paese-riga");
    if (riga && riga.dataset.testo) riga.textContent = riga.dataset.testo;
  }

  async function mostra(codice, opzioni) {
    opzioni = opzioni || {};
    const voce = perCodice.get(codice);
    if (!voce) { mostraStatoIniziale("We have no data for “" + esc(codice) + "”. Search for a country above or choose one from the list."); return; }
    const mia = ++sequenza;
    $("paese-contenuto").setAttribute("aria-busy", "true");
    let dati = cache.get(codice);
    if (!dati) {
      try {
        const risposta = await fetch("dati/" + encodeURIComponent(codice) + ".json");
        if (!risposta.ok) throw new Error("HTTP " + risposta.status);
        dati = await risposta.json();
        cache.set(codice, dati);
      } catch (errore) {
        if (mia !== sequenza) return;
        mostraStatoIniziale("The data for " + esc(voce.nome) + " could not be loaded. <button type=\"button\" id=\"riprova\" class=\"pulsante-paese\">Try again</button>");
        $("riprova").addEventListener("click", () => mostra(codice, { push: false, replace: true }));
        return;
      }
    }
    if (mia !== sequenza) return;        // nel frattempo si è scelto un altro Paese
    corrente = codice;
    const indirizzo = "country.html?c=" + encodeURIComponent(codice) + (opzioni.conHash ? location.hash : "");
    if (opzioni.push) history.pushState({ c: codice }, "", indirizzo);
    else if (opzioni.replace) history.replaceState({ c: codice }, "", indirizzo);
    disegnaPaese(voce, dati);
    $("paese-contenuto").removeAttribute("aria-busy");
    $("paese-annuncio").textContent = "Showing " + voce.nome;
    if (opzioni.push) { const h1 = $("paese-titolo"); h1.tabIndex = -1; h1.focus({ preventScroll: false }); }
  }

  window.addEventListener("popstate", () => {
    const c = parametro();
    if (c && perCodice.has(c)) mostra(c, {});
    else mostraStatoIniziale(c ? "We have no data for “" + esc(c) + "”. Search for a country above or choose one from the list." : "");
  });

  function parametro() {
    const c = new URLSearchParams(location.search).get("c");
    return c ? c.trim().toUpperCase() : null;
  }

  // ----------------------------------------------------------------------
  // Disegno del Paese
  // ----------------------------------------------------------------------
  const titoloPerId = {};
  SPEC.sezioni.forEach((s) => s.grafici.forEach((g) => { titoloPerId[g.serie[0]] = g.titolo; }));
  const schede = Array.from(document.querySelectorAll(".scheda-grafico[data-grafico]"));
  const grafico = (id) => SPEC.sezioni.flatMap((s) => s.grafici).find((g) => g.id === id);

  function disegnaPaese(voce, d) {
    $("paese-elenco").hidden = true;
    $("paese-errore").hidden = true;
    $("paese-contenuto").hidden = false;
    $("paese-titolo").textContent = voce.nome;
    document.title = voce.nome + " · Macro dashboard";
    campo.value = voce.nome;
    const riga = $("paese-riga");
    if (!riga.dataset.testo) riga.dataset.testo = riga.textContent;
    riga.textContent = (voce.regione ? voce.regione + " · " : "") + "ISO " + voce.c + " · " +
      (d.fonte === "imf" ? "IMF World Economic Outlook and World Bank data" : "World Bank data only: this country is not in the IMF World Economic Outlook");

    const completa = SPEC.pagina_completa[voce.c];
    $("paese-info").innerHTML = completa ? '<a class="pulsante-paese" href="' + esc(completa) + '">Full page →</a>' : "";
    disegnaSchede(d);
    document.querySelectorAll(".riquadro-markets").forEach((r) => { r.hidden = r.dataset.c !== voce.c; });

    const mancanti = [];
    schede.forEach((scheda) => {
      const g = grafico(scheda.dataset.grafico);
      scheda._periodo = PERIODO_INIZIALE;
      scheda.querySelectorAll(".periodi-paese button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.periodo === PERIODO_INIZIALE ? "true" : "false"));
      if (!disegnaGrafico(scheda, g, d)) mancanti.push(g.titolo);
    });
    disegnaOutlook(d);
    // Le sezioni senza nessun grafico e i loro chip spariscono
    document.querySelectorAll("section[data-sezione]").forEach((s) => {
      if (s.id === "outlook") return;
      const visibile = Array.from(s.querySelectorAll(".scheda-grafico")).some((c) => !c.hidden);
      s.hidden = !visibile;
      document.querySelectorAll('#paese-chips a[data-sezione="' + s.dataset.sezione + '"]').forEach((a) => { a.parentElement.hidden = !visibile; });
    });
    const nota = $("paese-mancanti");
    nota.hidden = !mancanti.length;
    nota.textContent = mancanti.length ? "Not available for this country: " + mancanti.join(", ") + "." : "";
    if (location.hash && /^#chart-|^#outlook|^#sez-/.test(location.hash)) {
      const bersaglio = document.querySelector(location.hash);
      if (bersaglio && !bersaglio.hidden) requestAnimationFrame(() => bersaglio.scrollIntoView());
    }
  }

  function ultimoEffettivo(d, id) {
    const e = d.ultimo[id];
    return e ? e[0] : null;
  }

  function disegnaSchede(d) {
    const contenitore = $("paese-kpi");
    contenitore.innerHTML = "";
    SPEC.numeri_chiave.forEach((k) => {
      const meta = SPEC.indicatori[k.id];
      const u = d.ultimo[k.id];
      const el = document.createElement("article");
      el.className = "kpi";
      if (!u) {
        el.innerHTML = "<h3>" + esc(k.nome) + '</h3><p class="kpi-valore">n/a</p><p class="kpi-data">no data</p>';
      } else {
        const fiscale = d.fiscale.includes(k.id);
        el.innerHTML = "<h3>" + esc(k.nome) + '</h3><p class="kpi-valore">' + num(u[1], meta.decimali) +
          ' <span class="kpi-unita">' + esc(meta.unita) + '</span></p><p class="kpi-data">' + etichettaAnno(u[0], fiscale) + (fiscale ? " (fiscal year)" : "") + "</p>";
      }
      contenitore.appendChild(el);
    });
  }

  // ---- Grafici -----------------------------------------------------------
  const finale = (s) => s.y + s.v.length - 1;
  const valoreIn = (s, anno) => { const v = s.v[anno - s.y]; return v === undefined ? null : v; };

  /** Tracce di una serie: parte effettiva (piena) e parte di stima/proiezione (tratteggiata o chiara). `tipo`: "linea" o "barre". */
  function traccePerSerie(id, s, d, g, opzioni) {
    const eff = d.effettivo[id];
    const fiscale = d.fiscale.includes(id);
    const meta = SPEC.indicatori[id];
    const unita = g.unita;
    const extra = (g.tooltip_extra || []).map((e) => ({ id: e, s: d.serie[e], meta: SPEC.indicatori[e] })).filter((e) => e.s);
    const anni = s.v.map((_, i) => s.y + i);
    const testo = (anno, v) => {
      const stima = eff != null && anno > eff;
      let t = "<b>" + etichettaAnno(anno, fiscale) + (fiscale ? " (fiscal year)" : "") + "</b> · " + (stima ? "IMF estimate or projection" : "actual") +
        "<br>" + (opzioni.etichetta ? opzioni.etichetta + ": " : "") + conUnita(num(v, g.decimali), unita);
      extra.forEach((e) => {
        const w = valoreIn(e.s, anno);
        if (w !== null) t += "<br>" + (e.id === "inflation_end_of_period" ? "December-on-December: " : esc(e.meta.nome) + ": ") + conUnita(num(w, g.decimali), unita);
      });
      return t;
    };
    const punti = (filtro) => {
      const x = [], y = [], t = [];
      anni.forEach((a, i) => { if (filtro(a)) { x.push(a); y.push(s.v[i]); t.push(s.v[i] === null ? "" : testo(a, s.v[i])); } });
      return { x, y, t };
    };
    const reale = punti((a) => eff == null || a <= eff);
    const stimato = eff == null ? { x: [], y: [], t: [] } : punti((a) => (opzioni.forma === "linea" ? a >= eff : a > eff));
    const colore = opzioni.colore;
    const tracce = [];
    if (opzioni.forma === "barre") {
      tracce.push({ type: "bar", x: reale.x, y: reale.y, hovertext: reale.t, hoverinfo: "text", marker: { color: colore }, name: opzioni.etichetta || meta.nome, showlegend: !!opzioni.legenda, meta: { colore: opzioni.chiave } });
      if (stimato.x.length) tracce.push({ type: "bar", x: stimato.x, y: stimato.y, hovertext: stimato.t, hoverinfo: "text", marker: { color: rgba(colore, 0.4), line: { color: colore, width: 1 } }, showlegend: false });
    } else {
      const stile = opzioni.stile || {};
      tracce.push({ type: "scatter", mode: "lines", x: reale.x, y: reale.y, hovertext: reale.t, hoverinfo: "text", connectgaps: false,
                    line: Object.assign({ color: colore, width: 2 }, stile), name: opzioni.etichetta || meta.nome, showlegend: !!opzioni.legenda });
      if (stimato.x.length > 0 && eff != null) {
        const t2 = stimato.t.slice(); t2[0] = reale.t.length ? reale.t[reale.t.length - 1] : t2[0];   // il primo punto è l'ultimo effettivo
        tracce.push({ type: "scatter", mode: "lines", x: stimato.x, y: stimato.y, hovertext: t2, hoverinfo: "text", connectgaps: false,
                      line: Object.assign({ color: colore, width: 2 }, stile, { dash: "dash" }), showlegend: false });
      }
    }
    return tracce;
  }

  function finestra(g, d, serie) {
    const principale = serie[0];
    const primo = Math.min(...serie.map((s) => s.s.y));
    const ultimo = Math.max(...serie.map((s) => finale(s.s)));
    const eff = d.effettivo[serie[0].id];
    const ancora = eff != null ? eff : finale(principale.s);
    return { primo, ultimo, ancora };
  }

  /** Disegna un grafico; restituisce false (e nasconde la scheda) se il Paese non ha dati per la serie principale. */
  function disegnaGrafico(scheda, g, d) {
    const div = scheda.querySelector(".grafico-paese");
    const serie = g.serie.map((id) => ({ id: id, s: d.serie[id] })).filter((x) => x.s);
    if (!serie.length || serie[0].id !== g.serie[0]) { scheda.hidden = true; if (div.data) Plotly.purge(div); return false; }
    scheda.hidden = false;
    if (typeof Plotly === "undefined") { div.textContent = "The chart library could not be loaded (an Internet connection is required)."; div.classList.add("grafico-vuoto"); return true; }
    div.classList.remove("grafico-vuoto"); div.textContent = "";

    const t = leggiTema();
    const chiave = SPEC.colori[d.c] || "mondo";
    const colore = t.colore(chiave);
    const w = finestra(g, d, serie);
    const anni = ANNI_PERIODO[scheda._periodo];
    const da = anni ? Math.max(w.primo, w.ancora - anni + 1) : w.primo;
    const a = w.ultimo;
    const eff = d.effettivo[g.serie[0]];
    const tracce = [];
    const layout = {
      margin: { l: 54, r: 12, t: 14, b: 34 }, paper_bgcolor: t.superficie, plot_bgcolor: t.superficie, font: { color: t.testo2, size: 12 },
      xaxis: { type: "linear", tickformat: "d", range: [da - 0.5, a + 0.5], fixedrange: true, color: t.tenue, linecolor: t.asse, showline: true, gridcolor: t.griglia, nticks: 8 },
      yaxis: { fixedrange: true, color: t.tenue, gridcolor: t.griglia, zeroline: !!g.riga0, zerolinecolor: t.asse, zerolinewidth: 1.5, ticksuffix: g.unita && g.unita.charAt(0) === "%" ? "%" : "" },
      showlegend: false, hovermode: "closest", hoverlabel: { bgcolor: t.superficie, bordercolor: t.griglia, font: { color: t.testo } }, dragmode: false,
      shapes: [], annotations: [], bargap: 0.25,
    };
    let valoriY = [];

    if (g.forma === "banda") {
      const punteggio = serie[0].s, basso = d.serie[g.serie[1]], alto = d.serie[g.serie[2]];
      const bande = basso && alto;
      const anniP = punteggio.v.map((_, i) => punteggio.y + i);
      const testoP = (an) => {
        const v = valoreIn(punteggio, an);
        if (v === null) return "";
        const lo = bande ? valoreIn(basso, an) : null, hi = bande ? valoreIn(alto, an) : null;
        return "<b>" + an + "</b><br>Score " + num(v, 1) + (lo !== null && hi !== null ? " (90% interval " + num(lo, 1) + "–" + num(hi, 1) + ")" : "");
      };
      const annuale = anniP.filter((x) => x >= 2002);
      const presto = anniP.filter((x) => x < 2002 && valoreIn(punteggio, x) !== null);
      if (bande) {
        tracce.push({ type: "scatter", mode: "lines", x: annuale, y: annuale.map((x) => valoreIn(basso, x)), line: { width: 0 }, hoverinfo: "skip", showlegend: false });
        tracce.push({ type: "scatter", mode: "lines", x: annuale, y: annuale.map((x) => valoreIn(alto, x)), line: { width: 0 }, fill: "tonexty", fillcolor: rgba(colore, 0.2), hoverinfo: "skip", showlegend: false });
      }
      tracce.push({ type: "scatter", mode: "lines+markers", x: annuale, y: annuale.map((x) => valoreIn(punteggio, x)), hovertext: annuale.map(testoP), hoverinfo: "text",
                    line: { color: colore, width: 2 }, marker: { color: colore, size: 5 }, showlegend: false });
      if (presto.length) {
        tracce.push({ type: "scatter", mode: "markers", x: presto, y: presto.map((x) => valoreIn(punteggio, x)), hovertext: presto.map(testoP), hoverinfo: "text",
                      marker: { color: colore, size: 6 },
                      error_y: bande ? { type: "data", symmetric: false, array: presto.map((x) => (valoreIn(alto, x) || 0) - valoreIn(punteggio, x)),
                                         arrayminus: presto.map((x) => valoreIn(punteggio, x) - (valoreIn(basso, x) || 0)), color: rgba(colore, 0.7), thickness: 1, width: 3 } : undefined,
                      showlegend: false });
      }
      layout.yaxis.range = [0, 100];
      layout.xaxis.range = [Math.max(da, w.primo) - 0.5, a + 0.5];
    } else {
      serie.forEach((x, i) => {
        const principale = i === 0;
        const forma = g.forma === "barre" || (g.forma === "barre-linea" && principale) ? "barre" : "linea";
        const etichetta = g.etichette ? g.etichette[x.id] : null;
        const opz = { forma: forma, colore: principale || g.forma !== "barre-linea" ? colore : t.testo, chiave: chiave, etichetta: etichetta,
                      legenda: g.forma === "barre-linea", stile: !principale && g.forma === "barre-linea" ? { width: 2.5 } : null };
        traccePerSerie(x.id, x.s, d, g, opz).forEach((tr) => { tracce.push(tr); });
      });
      tracce.forEach((tr) => tr.y.forEach((v, k) => { if (v !== null && tr.x[k] >= da && tr.x[k] <= a) valoriY.push(v); }));
      if (valoriY.length) {
        let min = Math.min(...valoriY), max = Math.max(...valoriY);
        if (g.forma !== "linea" || g.riga0) { min = Math.min(min, 0); max = Math.max(max, 0); }
        const margine = (max - min || Math.abs(max) || 1) * 0.08;
        layout.yaxis.range = [min - margine, max + margine];
      }
      layout.showlegend = g.forma === "barre-linea" && serie.length > 1;
      if (layout.showlegend) layout.legend = { orientation: "h", x: 0, y: 1.14, font: { color: t.testo2, size: 12 } };
      if (g.forma === "barre-linea") layout.margin.t = 28;
    }

    // Linea verticale tra dati effettivi e stime/proiezioni dell'FMI
    const haProiezioni = eff != null && a > eff && g.forma !== "banda" && d.fonte === "imf";
    if (haProiezioni && eff + 0.5 > da - 0.5) {
      layout.shapes.push({ type: "line", xref: "x", yref: "paper", x0: eff + 0.5, x1: eff + 0.5, y0: 0, y1: 1, line: { color: t.tenue, width: 1, dash: "dot" } });
    }
    Plotly.react(div, tracce, layout, { responsive: true, displaylogo: false, displayModeBar: false, scrollZoom: false });
    scheda._tracce = true;
    notaGrafico(scheda, g, d, serie, w, haProiezioni && eff + 0.5 > da - 0.5);
    fonteGrafico(scheda, g, d);
    return true;
  }

  function notaGrafico(scheda, g, d, serie, w, proiezioniVisibili) {
    const note = [];
    if (proiezioniVisibili) note.push("To the right of the dotted line, dashed lines and lighter bars are IMF estimates and projections.");
    const principale = g.serie[0];
    const eff = d.effettivo[principale];
    if (g.fonte === "imf" && d.fonte === "wb") {
      note.push("This country is not in the IMF data: the figures come from the World Bank (all actual, with no projections).");
    } else if (g.fonte === "imf") {
      const fin = d.finale[principale];
      const senzaProiezioni = eff != null && fin <= eff;
      if (SPEC.anno_weo && fin < SPEC.anno_weo - 1) {
        note.push("The IMF data for this country stop in " + fin + (senzaProiezioni ? " and there are no projections." : "."));
      } else if (senzaProiezioni) {
        note.push("The IMF publishes no projections for this country: the latest year is " + fin + ".");
      }
      serie.slice(1).forEach((x) => {
        if (d.finale[x.id] < fin) note.push("The IMF data for the " + ((g.etichette && g.etichette[x.id]) || x.id).toLowerCase() + " end in " + d.finale[x.id] + ".");
      });
      g.serie.slice(1).forEach((id) => { if (!d.serie[id]) note.push("The " + ((g.etichette && g.etichette[id]) || id).toLowerCase() + " is not available for this country."); });
      if (d.fiscale.includes(principale)) {
        note.push("For this country the IMF reports fiscal years: the year shown is the one in which the fiscal year starts, so " + (eff || 2024) + " means " + etichettaAnno(eff || 2024, true) + ".");
      }
    }
    const nodo = scheda.querySelector("[data-note-dinamiche]");
    nodo.hidden = !note.length;
    nodo.innerHTML = note.map((n) => "<p>ⓘ " + esc(n) + "</p>").join("");
  }

  function fonteGrafico(scheda, g, d) {
    const a = scheda.querySelector("[data-fonte]");
    const f = (g.fonte === "imf" && d.fonte === "wb" && g.fonti.alternativa) ? g.fonti.alternativa : g.fonti.principale;
    a.textContent = f.nome + " ↗"; a.href = f.url;
    const eff = ultimoEffettivo(d, g.serie[0]);
    scheda.querySelector("[data-ultimo]").textContent = eff != null ? "Latest actual year " + etichettaAnno(eff, d.fiscale.includes(g.serie[0])) : "Latest actual year not flagged";
  }

  // ---- Tabella "IMF outlook" ---------------------------------------------
  function disegnaOutlook(d) {
    const sezione = $("outlook"), tab = $("outlook-tabella"), nota = $("outlook-nota");
    tab.innerHTML = "";
    nota.hidden = true;
    if (d.fonte !== "imf") { sezione.hidden = false; nota.hidden = false; nota.innerHTML = "<p>ⓘ This country is not in the IMF World Economic Outlook: no estimates or projections.</p>"; return; }
    const righe = SPEC.outlook.indicatori.filter((id) => d.serie[id]);
    sezione.hidden = false;
    document.querySelectorAll('#paese-chips a[data-sezione="outlook"]').forEach((a) => { a.parentElement.hidden = !righe.length; });
    if (!righe.length) { sezione.hidden = true; return; }
    const A = SPEC.anno_weo || 2026, ultimo = SPEC.anno_ultimo_weo || A + 5;
    let colonne = Array.from(new Set([A, A + 1, A + 2, ultimo])).sort((x, y) => x - y);
    // Paese senza nessuna proiezione: la tabella ha solo l'ultimo dato effettivo (le colonne degli anni sarebbero tutte "—")
    const haProiezioni = righe.some((id) => colonne.some((c) => valoreIn(d.serie[id], c) !== null && d.effettivo[id] != null && c > d.effettivo[id]));
    if (!haProiezioni) colonne = [];
    let html = '<table class="tabella-outlook"><thead><tr><th>Indicator</th><th class="num">Latest actual</th>' + colonne.map((c) => '<th class="num">' + c + "</th>").join("") + "</tr></thead><tbody>";
    const note = [];
    righe.forEach((id) => {
      const s = d.serie[id], meta = SPEC.indicatori[id], eff = d.effettivo[id], fiscale = d.fiscale.includes(id);
      const cella = (anno) => {
        const v = valoreIn(s, anno);
        if (v === null) return '<td class="num">—</td>';
        const stima = eff != null && anno > eff;
        return '<td class="num' + (stima ? " stima" : "") + '">' + num(v, meta.decimali) + "</td>";
      };
      const u = d.ultimo[id];
      html += "<tr><th scope=\"row\">" + esc(titoloPerId[id] || meta.nome) + ' <span class="unita-riga">' + esc(meta.unita) + "</span></th><td class=\"num\">" +
        (u ? num(u[1], meta.decimali) + ' <span class="anno-effettivo">' + etichettaAnno(u[0], fiscale) + "</span>" : "—") + "</td>" + colonne.map(cella).join("") + "</tr>";
      if (haProiezioni && eff != null && d.finale[id] <= eff) note.push((titoloPerId[id] || meta.nome) + ": no IMF projections for this country.");
      if (fiscale) note.push((titoloPerId[id] || meta.nome) + ": fiscal years (" + etichettaAnno(2024, true) + " is shown under 2024).");
    });
    tab.innerHTML = html + "</tbody></table>";
    if (!haProiezioni) note.unshift("The IMF publishes no projections for this country: the table shows only the latest actual figures.");
    if (note.length) { nota.hidden = false; nota.innerHTML = note.map((n) => "<p>ⓘ " + esc(n) + "</p>").join(""); }
  }

  // ---- Periodi, tema, avvio ----------------------------------------------
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".periodi-paese button");
    if (!b) return;
    const scheda = b.closest(".scheda-grafico");
    if (!corrente || !cache.has(corrente)) return;
    scheda._periodo = b.dataset.periodo;
    scheda.querySelectorAll(".periodi-paese button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
    disegnaGrafico(scheda, grafico(scheda.dataset.grafico), cache.get(corrente));
  });
  function ridisegna() {
    if (!corrente || !cache.has(corrente)) return;
    schede.forEach((s) => { if (!s.hidden) disegnaGrafico(s, grafico(s.dataset.grafico), cache.get(corrente)); });
  }
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ridisegna);
  window.addEventListener("tema-cambiato", ridisegna);
  $("cambia-paese").addEventListener("click", () => { setTimeout(() => campo.focus(), 0); });

  const riga0 = $("paese-riga");
  if (riga0) riga0.dataset.testo = riga0.textContent;
  const iniziale = parametro();
  if (iniziale === null) mostraStatoIniziale("");
  else if (perCodice.has(iniziale)) mostra(iniziale, { replace: true, conHash: true });          // ?c=ita diventa ?c=ITA
  else mostraStatoIniziale("We have no data for “" + esc(iniziale) + "”. Search for a country above or choose one from the list.");
})();
