/* =====================================================================
   Comportamento della pagina:
   1. redirect dei vecchi indirizzi con #regione
   2. disegno dei grafici Plotly (solo quando stanno per entrare nello schermo)
   3. pulsanti di periodo 1Y / 5Y / 10Y / Max con scala verticale adattata
      (nei grafici "base 100" i valori ripartono da 100 all'inizio del periodo)
   4. colori dei grafici presi dal tema (chiaro o scuro) del CSS
   ===================================================================== */
// ----------------------------------------------------------------------
// Interruttore del tema (◐): Auto (segue il sistema) -> Light -> Dark -> Auto.
// La scelta sta solo nel localStorage del browser di chi visita; senza scelta vale il sistema.
// Sta in un blocco a parte perché deve funzionare in tutte le pagine, anche senza grafici.
// ----------------------------------------------------------------------
(function () {
  "use strict";
  const pulsante = document.getElementById("interruttore-tema");
  if (!pulsante) return;
  const ORDINE = ["auto", "light", "dark"];
  const NOMI = { auto: "Auto", light: "Light", dark: "Dark" };

  function scelta() {
    try {
      const t = localStorage.getItem("tema");
      return t === "light" || t === "dark" ? t : "auto";
    } catch (e) { return "auto"; }
  }

  function mostra(tema) {
    if (tema === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", tema);
    const prossimo = ORDINE[(ORDINE.indexOf(tema) + 1) % ORDINE.length];
    pulsante.querySelector(".etichetta-tema").textContent = NOMI[tema];
    pulsante.title = "Colour theme: " + NOMI[tema] + (tema === "auto" ? " (follows your device)" : "") + ". Click for " + NOMI[prossimo] + ".";
    pulsante.setAttribute("aria-label", pulsante.title);
  }

  pulsante.hidden = false;
  mostra(scelta());
  pulsante.addEventListener("click", () => {
    const prossimo = ORDINE[(ORDINE.indexOf(scelta()) + 1) % ORDINE.length];
    try {
      if (prossimo === "auto") localStorage.removeItem("tema");
      else localStorage.setItem("tema", prossimo);
    } catch (e) { /* storage bloccato: il tema vale solo finché la pagina resta aperta */ }
    mostra(prossimo);
    window.dispatchEvent(new Event("tema-cambiato"));   // i grafici si ridisegnano con i nuovi colori
  });
})();

(function () {
  "use strict";

  const ANNI_PERIODO = { "1Y": 1, "5Y": 5, "10Y": 10 };
  const schermoTouch = window.matchMedia("(pointer: coarse)").matches;
  const disegnati = new Set(); // grafici già disegnati

  // ------------------------------------------------------------------
  // 1. Vecchi indirizzi: prima il sito era una pagina sola con le tab (index.html#usa).
  //    Ora ogni regione ha la sua pagina: chi arriva dalla home con un vecchio #usa va a usa/.
  // ------------------------------------------------------------------
  if (document.body.hasAttribute("data-home") && /^#[a-z]+$/.test(location.hash)) {
    const link = document.querySelector('.griglia-pagine a[href="' + location.hash.slice(1) + '/"]');
    if (link) { location.replace(link.getAttribute("href")); return; }
  }

  // Se plotly.js non si carica (es. offline) mostriamo un messaggio al posto dei grafici
  if (typeof Plotly === "undefined") {
    document.querySelectorAll(".grafico").forEach((el) => {
      el.classList.add("grafico-vuoto");
      el.textContent = "The chart library could not be loaded (an Internet connection is required).";
    });
    return;
  }

  // Nomi degli assi presenti nel layout: assi(layout, "y") -> ["yaxis", "yaxis2"]
  function assi(layout, lettera) {
    const schema = new RegExp("^" + lettera + "axis\\d*$");
    const trovati = Object.keys(layout).filter((k) => schema.test(k));
    return trovati.length ? trovati : [lettera + "axis"];
  }

  // Asse verticale di una traccia: "y2" -> "yaxis2", nessuno -> "yaxis"
  const asseDellaTraccia = (tr) => "yaxis" + String(tr.yaxis || "y").slice(1);

  // ------------------------------------------------------------------
  // 4. Colori dal tema CSS
  // ------------------------------------------------------------------
  function leggiTema() {
    const stile = getComputedStyle(document.documentElement);
    const v = (nome) => stile.getPropertyValue(nome).trim();
    return {
      superficie: v("--superficie"), testo: v("--testo"), testo2: v("--testo-2"),
      tenue: v("--testo-tenue"), griglia: v("--griglia"), asse: v("--asse"),
      colore: (chiave) => v("--c-" + chiave),   // colori fissi dei Paesi, definiti in config.yaml
    };
  }

  function applicaTema(data, layout) {
    const t = leggiTema();
    layout.paper_bgcolor = t.superficie;
    layout.plot_bgcolor = t.superficie;
    layout.font = Object.assign({}, layout.font, { color: t.testo2 });
    // Tutti gli assi: xaxis, xaxis2... (i grafici a due pannelli ne hanno più di uno)
    assi(layout, "x").forEach((k) => {
      layout[k] = Object.assign({}, layout[k], {
        color: t.tenue, linecolor: t.asse, showline: true, spikecolor: t.tenue,
      });
    });
    assi(layout, "y").forEach((k) => {
      layout[k] = Object.assign({}, layout[k], { color: t.tenue, gridcolor: t.griglia });
    });
    layout.legend = Object.assign({}, layout.legend, { font: { color: t.testo2, size: 12 } });
    layout.hoverlabel = { bgcolor: t.superficie, bordercolor: t.griglia, font: { color: t.testo } };
    layout.dragmode = schermoTouch ? false : "zoom"; // sul telefono il dito deve scorrere la pagina
    data.forEach((traccia) => {
      const chiave = traccia.meta && traccia.meta.colore;   // es. "us", "ea", "energia", "mondo"
      if (!chiave) return;
      const colore = t.colore(chiave) || t.testo;
      traccia.line = Object.assign({}, traccia.line, { color: colore });
      if (traccia.marker) traccia.marker = Object.assign({}, traccia.marker, { color: colore });
    });
  }

  // ------------------------------------------------------------------
  // 3. Periodi e scala verticale
  // ------------------------------------------------------------------
  const giorno = (x) => String(x).slice(0, 10); // "2024-05-17 12:00:00" -> "2024-05-17"

  function ultimaData(data) {
    let ultima = "";
    data.forEach((tr) => {
      if (tr.x && tr.x.length && tr.x[tr.x.length - 1] > ultima) ultima = tr.x[tr.x.length - 1];
    });
    return ultima;
  }

  function intervalloX(data, periodo) {
    const anni = ANNI_PERIODO[periodo];
    if (!anni) return null; // "Max" = tutto lo storico
    const fine = new Date(ultimaData(data));
    const inizio = new Date(fine);
    inizio.setFullYear(fine.getFullYear() - anni);
    return [inizio.toISOString().slice(0, 10), fine.toISOString().slice(0, 10)];
  }

  // Grafici "base 100" (confronti di valute e borse): tutte le linee valgono 100 nella stessa data iniziale.
  // La data è l'inizio del periodo scelto, ma mai prima della prima data in cui ESISTONO tutte le serie.
  // `originali` = dati grezzi [{x, y}] di ogni traccia. Restituisce l'intervallo del tempo e i nuovi valori.
  // Se il grafico ha due varianti (valuta locale / USD), per la data iniziale e finale contano solo le linee visibili.
  function base100(originali, periodo) {
    const attive = originali.filter((o) => o.visibile !== false);
    let inizio = "";
    attive.forEach((o) => { if (o.x.length && giorno(o.x[0]) > inizio) inizio = giorno(o.x[0]); });
    const fine = giorno(ultimaData(attive));
    const anni = ANNI_PERIODO[periodo];
    if (anni) {
      const d = new Date(fine);
      d.setFullYear(d.getFullYear() - anni);
      const dal = d.toISOString().slice(0, 10);
      if (dal > inizio) inizio = dal;
    }
    const y = originali.map((o) => {
      // Valore alla data iniziale; se in quel giorno la borsa era chiusa, l'ultimo disponibile prima
      let k = -1;
      o.x.forEach((x, i) => { if (giorno(x) <= inizio) k = i; });
      const base = o.y[k < 0 ? 0 : k];
      return o.y.map((v) => (v === null ? null : (v / base) * 100));
    });
    return { x: [inizio, fine], y: y };
  }

  // Per ogni asse verticale: minimo e massimo dei valori visibili nel periodo scelto (+ margine del 6%).
  // Restituisce es. { yaxis: [1, 5], yaxis2: [3, -1] }. Gli assi "invertiti" hanno l'intervallo al contrario.
  function intervalliY(data, layout, da, a) {
    const meta = layout.meta || {};
    const estremi = {};
    data.forEach((tr) => {
      if (!tr.x || !tr.y || tr.visible === false) return; // le linee nascoste (altra variante) non contano
      const asse = asseDellaTraccia(tr);
      const e = estremi[asse] || (estremi[asse] = { min: Infinity, max: -Infinity });
      for (let i = 0; i < tr.x.length; i++) {
        const x = giorno(tr.x[i]);
        const y = tr.y[i];
        if (y === null || (da && x < da) || (a && x > a)) continue;
        if (y < e.min) e.min = y;
        if (y > e.max) e.max = y;
      }
    });
    // Le linee di riferimento (es. obiettivo 2%) stanno sul primo asse
    if (estremi.yaxis) {
      (meta.riferimenti || []).forEach((r) => {
        if (r < estremi.yaxis.min) estremi.yaxis.min = r;
        if (r > estremi.yaxis.max) estremi.yaxis.max = r;
      });
    }
    const risultato = {};
    Object.keys(estremi).forEach((asse) => {
      const { min, max } = estremi[asse];
      if (!isFinite(min)) return;
      const margine = (max - min || Math.abs(max) || 1) * 0.06;
      const intervallo = [min - margine, max + margine];
      risultato[asse] = (meta.assi_invertiti || []).includes(asse) ? intervallo.reverse() : intervallo;
    });
    return risultato;
  }

  // Modifiche per Plotly.relayout: { "yaxis.range": [...], "yaxis.autorange": false, ... }
  function modificheY(intervalli) {
    const modifiche = {};
    Object.keys(intervalli).forEach((asse) => {
      modifiche[asse + ".range"] = intervalli[asse];
      modifiche[asse + ".autorange"] = false;
    });
    return modifiche;
  }

  function segnaPulsante(id, periodo) {
    document.querySelectorAll('.periodi button[data-grafico="' + id + '"]').forEach((b) => {
      b.setAttribute("aria-pressed", b.dataset.periodo === periodo ? "true" : "false");
    });
  }

  // Pulsanti "valuta locale / in USD" (Local / USD): mostrano solo le linee della variante scelta (le altre sono nascoste)
  const periodoAttuale = (el) => {
    const premuto = document.querySelector('.periodi button[data-grafico="' + el.id + '"][aria-pressed="true"]');
    return premuto ? premuto.dataset.periodo : "Max"; // dopo uno zoom manuale nessun pulsante è premuto
  };

  async function impostaVariante(el, variante) {
    el._originali.forEach((o) => { o.visibile = !o.variante || o.variante === variante; });
    await Plotly.restyle(el, { visible: el._originali.map((o) => o.visibile) });
    document.querySelectorAll('.varianti button[data-grafico="' + el.id + '"]').forEach((b) => {
      b.setAttribute("aria-pressed", b.dataset.variante === variante ? "true" : "false");
    });
    await impostaPeriodo(el, periodoAttuale(el));
  }

  document.querySelectorAll(".varianti button").forEach((pulsante) => {
    pulsante.addEventListener("click", () => {
      const el = document.getElementById(pulsante.dataset.grafico);
      if (disegnati.has(el.id)) impostaVariante(el, pulsante.dataset.variante);
    });
  });

  async function impostaPeriodo(el, periodo) {
    let x = intervalloX(el.data, periodo);
    if (el._originali) {  // grafico base 100: si ricalcolano i valori a partire dalla nuova data iniziale
      const r = base100(el._originali, periodo);
      x = r.x;
      await Plotly.restyle(el, { y: r.y });
    }
    const modifiche = modificheY(intervalliY(el.data, el.layout, x && x[0], x && x[1]));
    assi(el.layout, "x").forEach((asse) => {  // nei grafici a due pannelli il tempo è condiviso
      if (x) Object.assign(modifiche, { [asse + ".range"]: x, [asse + ".autorange"]: false });
      else modifiche[asse + ".autorange"] = true;
    });
    el._daPulsante = true;
    await Plotly.relayout(el, modifiche);
    el._daPulsante = false;
    segnaPulsante(el.id, periodo);
  }

  document.querySelectorAll(".periodi button").forEach((pulsante) => {
    pulsante.addEventListener("click", () => {
      const el = document.getElementById(pulsante.dataset.grafico);
      if (disegnati.has(el.id)) impostaPeriodo(el, pulsante.dataset.periodo);
    });
  });

  // ------------------------------------------------------------------
  // 2. Disegno dei grafici
  // ------------------------------------------------------------------
  const opzioni = {
    responsive: true,
    displaylogo: false,
    scrollZoom: false,
    // Niente barra degli strumenti: si sovrappone alla legenda. Lo zoom resta
    // disponibile trascinando col mouse, il doppio clic ripristina la vista.
    displayModeBar: false,
  };

  function disegna(el) {
    if (disegnati.has(el.id)) return;
    disegnati.add(el.id);

    const figura = JSON.parse(document.getElementById("dati-" + el.id).textContent);
    const data = figura.data;
    const layout = figura.layout;
    applicaTema(data, layout);

    // Periodo iniziale (solo per i grafici con asse temporale)
    const periodo = el.dataset.periodo;
    if (periodo) {
      let x = intervalloX(data, periodo);
      if (layout.meta && layout.meta.base100) {
        // La prima variante (es. valuta locale) è quella mostrata all'apertura; le linee dell'altra restano nascoste
        const prima = (layout.meta.varianti || [])[0];
        el._originali = data.map((tr) => {
          const variante = tr.meta && tr.meta.variante;
          const visibile = !variante || variante === prima;
          tr.visible = visibile;
          return { x: tr.x, y: tr.y, variante: variante, visibile: visibile };
        });
        const r = base100(el._originali, periodo);
        x = r.x;
        data.forEach((tr, i) => { tr.y = r.y[i]; });
      }
      if (x) assi(layout, "x").forEach((asse) => { layout[asse].range = x; });
      const intervalli = intervalliY(data, layout, x && x[0], x && x[1]);
      Object.keys(intervalli).forEach((asse) => {
        layout[asse] = Object.assign({}, layout[asse], { range: intervalli[asse], autorange: false });
      });
    }

    Plotly.newPlot(el, data, layout, opzioni).then(() => {
      // Zoom manuale (trascinando col mouse): adatta la scala verticale
      el.on("plotly_relayout", (evento) => {
        if (el._daPulsante || !periodo) return;
        // Chiave del tipo "xaxis.range[0]", "xaxis2.range" o "xaxis.autorange"
        const chiave = Object.keys(evento).find((k) => /^xaxis\d*\.(range|autorange)/.test(k));
        if (!chiave) return;
        const r = el.layout[chiave.split(".")[0]].range;
        const modifiche = modificheY(intervalliY(el.data, el.layout, giorno(r[0]), giorno(r[1])));
        segnaPulsante(el.id, chiave.endsWith("autorange") ? "Max" : "");
        if (Object.keys(modifiche).length) {
          el._daPulsante = true;
          Plotly.relayout(el, modifiche).then(() => { el._daPulsante = false; });
        }
      });
    });
  }

  const elementi = document.querySelectorAll(".grafico[id]");
  if ("IntersectionObserver" in window) {
    const osservatore = new IntersectionObserver((voci) => {
      voci.forEach((voce) => {
        if (voce.isIntersecting) {
          disegna(voce.target);
          osservatore.unobserve(voce.target);
        }
      });
    }, { rootMargin: "400px 0px" });
    elementi.forEach((el) => osservatore.observe(el));
  } else {
    elementi.forEach(disegna);
  }

  // Cambio tema (del sistema, o con l'interruttore) mentre la pagina è aperta: si ricolorano i grafici già disegnati
  function ricolora() {
    disegnati.forEach((id) => {
      const el = document.getElementById(id);
      applicaTema(el.data, el.layout);
      el.layout.datarevision = Date.now(); // forza Plotly a ridisegnare i colori
      Plotly.react(el, el.data, el.layout);
    });
  }
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ricolora);
  window.addEventListener("tema-cambiato", ricolora);
})();
