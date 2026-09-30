/* =====================================================================
   Comportamento della pagina:
   1. tab delle regioni
   2. disegno dei grafici Plotly (solo quando stanno per entrare nello schermo)
   3. pulsanti di periodo 1A / 5A / 10A / Max con scala verticale adattata
   4. colori dei grafici presi dal tema (chiaro o scuro) del CSS
   ===================================================================== */
(function () {
  "use strict";

  const ANNI_PERIODO = { "1A": 1, "5A": 5, "10A": 10 };
  const schermoTouch = window.matchMedia("(pointer: coarse)").matches;
  const disegnati = new Set(); // grafici già disegnati

  // ------------------------------------------------------------------
  // 1. Tab delle regioni
  // ------------------------------------------------------------------
  const tabs = Array.from(document.querySelectorAll(".tab"));

  function mostraRegione(id, aggiornaIndirizzo) {
    tabs.forEach((tab) => {
      const attiva = tab.dataset.regione === id;
      tab.setAttribute("aria-selected", attiva ? "true" : "false");
      tab.tabIndex = attiva ? 0 : -1;
      document.getElementById("pannello-" + tab.dataset.regione).hidden = !attiva;
    });
    if (aggiornaIndirizzo) history.replaceState(null, "", "#" + id);
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => mostraRegione(tab.dataset.regione, true));
    // Frecce sinistra/destra per spostarsi tra le tab da tastiera
    tab.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      const prossima = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
      prossima.focus();
      mostraRegione(prossima.dataset.regione, true);
    });
  });

  const daIndirizzo = location.hash.slice(1);
  if (tabs.some((t) => t.dataset.regione === daIndirizzo)) mostraRegione(daIndirizzo, false);
  else if (tabs.length) mostraRegione(tabs[0].dataset.regione, false);

  // Se plotly.js non si carica (es. offline) mostriamo un messaggio al posto dei grafici
  if (typeof Plotly === "undefined") {
    document.querySelectorAll(".grafico").forEach((el) => {
      el.classList.add("grafico-vuoto");
      el.textContent = "Impossibile caricare la libreria dei grafici (serve una connessione a Internet).";
    });
    return;
  }

  // ------------------------------------------------------------------
  // 4. Colori dal tema CSS
  // ------------------------------------------------------------------
  function leggiTema() {
    const stile = getComputedStyle(document.documentElement);
    const v = (nome) => stile.getPropertyValue(nome).trim();
    return {
      superficie: v("--superficie"), testo: v("--testo"), testo2: v("--testo-2"),
      tenue: v("--testo-tenue"), griglia: v("--griglia"), asse: v("--asse"),
      serie: [1, 2, 3, 4, 5, 6, 7, 8].map((i) => v("--s" + i)),
    };
  }

  function applicaTema(data, layout) {
    const t = leggiTema();
    layout.paper_bgcolor = t.superficie;
    layout.plot_bgcolor = t.superficie;
    layout.font = Object.assign({}, layout.font, { color: t.testo2 });
    layout.xaxis = Object.assign({}, layout.xaxis, {
      color: t.tenue, linecolor: t.asse, showline: true, spikecolor: t.tenue,
    });
    layout.yaxis = Object.assign({}, layout.yaxis, { color: t.tenue, gridcolor: t.griglia });
    layout.legend = Object.assign({}, layout.legend, { font: { color: t.testo2, size: 12 } });
    layout.hoverlabel = { bgcolor: t.superficie, bordercolor: t.griglia, font: { color: t.testo } };
    layout.dragmode = schermoTouch ? false : "zoom"; // sul telefono il dito deve scorrere la pagina
    data.forEach((traccia) => {
      const slot = traccia.meta && traccia.meta.slot;
      if (!slot) return;
      const colore = t.serie[slot - 1];
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

  // Minimo e massimo dei valori visibili nel periodo scelto (+ margine del 6%)
  function intervalloY(data, layout, da, a) {
    let min = Infinity;
    let max = -Infinity;
    data.forEach((tr) => {
      if (!tr.x || !tr.y) return;
      for (let i = 0; i < tr.x.length; i++) {
        const x = giorno(tr.x[i]);
        const y = tr.y[i];
        if (y === null || (da && x < da) || (a && x > a)) continue;
        if (y < min) min = y;
        if (y > max) max = y;
      }
    });
    ((layout.meta && layout.meta.riferimenti) || []).forEach((r) => {
      if (r < min) min = r;
      if (r > max) max = r;
    });
    if (!isFinite(min)) return null;
    const margine = (max - min || Math.abs(max) || 1) * 0.06;
    return [min - margine, max + margine];
  }

  function segnaPulsante(id, periodo) {
    document.querySelectorAll('.periodi button[data-grafico="' + id + '"]').forEach((b) => {
      b.setAttribute("aria-pressed", b.dataset.periodo === periodo ? "true" : "false");
    });
  }

  async function impostaPeriodo(el, periodo) {
    const x = intervalloX(el.data, periodo);
    const y = intervalloY(el.data, el.layout, x && x[0], x && x[1]);
    const modifiche = x ? { "xaxis.range": x, "xaxis.autorange": false } : { "xaxis.autorange": true };
    if (y) Object.assign(modifiche, { "yaxis.range": y, "yaxis.autorange": false });
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
    locale: "it",
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
      const x = intervalloX(data, periodo);
      if (x) layout.xaxis.range = x;
      const y = intervalloY(data, layout, x && x[0], x && x[1]);
      if (y) layout.yaxis.range = y;
    }

    Plotly.newPlot(el, data, layout, opzioni).then(() => {
      // Zoom manuale (trascinando col mouse): adatta la scala verticale
      el.on("plotly_relayout", (evento) => {
        if (el._daPulsante || !periodo) return;
        const cambiaX = "xaxis.range[0]" in evento || "xaxis.range" in evento || "xaxis.autorange" in evento;
        if (!cambiaX) return;
        const r = el.layout.xaxis.range;
        const y = intervalloY(el.data, el.layout, giorno(r[0]), giorno(r[1]));
        segnaPulsante(el.id, "xaxis.autorange" in evento ? "Max" : "");
        if (y) {
          el._daPulsante = true;
          Plotly.relayout(el, { "yaxis.range": y }).then(() => { el._daPulsante = false; });
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

  // Cambio tema del sistema (chiaro <-> scuro) mentre la pagina è aperta
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    disegnati.forEach((id) => {
      const el = document.getElementById(id);
      applicaTema(el.data, el.layout);
      el.layout.datarevision = Date.now(); // forza Plotly a ridisegnare i colori
      Plotly.react(el, el.data, el.layout);
    });
  });
})();
