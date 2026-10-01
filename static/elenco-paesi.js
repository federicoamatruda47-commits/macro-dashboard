/* =====================================================================
   Elenco dei Paesi con ricerca (componente `ricerca_paesi`, templates/_componenti.html.j2).
   Usato dall'hub Economies e da country.html; la stessa ricerca (`ElencoPaesi.cerca`) serve anche al selettore a tendina di country.html?c=.
   L'HTML dei riquadri è già completo: qui si fa solo filtro, contatore e altezza della testata. Senza JavaScript restano link normali.
   Ogni riquadro porta data-chiavi: codice ISO3, nome, nome originale della fonte e nomi alternativi, già senza accenti e minuscoli
   (dashboard.paesi.chiavi_paese), separati da "|". Il testo digitato si normalizza allo stesso modo.
   ===================================================================== */
(function () {
  "use strict";

  const norma = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

  // voci = [{c, nome, chiavi}]; restituisce quelle che contengono il testo in una chiave. Prima il codice esatto, poi i nomi che iniziano col testo, poi il resto in ordine alfabetico.
  function cerca(voci, testo, limite) {
    const q = norma(testo).replace(/\|/g, "");
    if (!q) return [];
    const punteggio = (v) => {
      const parti = v.chiavi.split("|");
      return parti[0] === q ? 0 : parti.some((p) => p.startsWith(q)) ? 1 : 2;
    };
    const trovati = voci.filter((v) => v.chiavi.includes(q));
    trovati.sort((a, b) => punteggio(a) - punteggio(b) || norma(a.nome).localeCompare(norma(b.nome)));
    return limite ? trovati.slice(0, limite) : trovati;
  }

  // Le voci di un componente (solo i Paesi delle regioni: "Featured" ripete alcuni Paesi e non conta)
  function voci(radice) {
    return Array.from(radice.querySelectorAll(".ep-regione .ep-riquadro")).map((li) => ({
      li, c: li.dataset.c, nome: li.dataset.nome, nomeFonte: li.dataset.nomeFonte, regione: li.dataset.regione, chiavi: li.dataset.chiavi || "",
    }));
  }

  function avvia(radice) {
    const barra = radice.querySelector(".ep-barra");
    const campo = radice.querySelector(".ep-cerca");
    const pulisci = radice.querySelector(".ep-pulisci");
    const conteggio = radice.querySelector(".ep-conteggio");
    const nessuno = radice.querySelector(".ep-nessuno");
    const tutte = voci(radice);
    const regioni = Array.from(radice.querySelectorAll(".ep-regione"));
    const evidenza = radice.querySelector(".ep-evidenza");
    const salti = radice.querySelector(".ep-salti");
    const nota = radice.querySelector(".ep-nota");
    const totale = tutte.length;
    barra.hidden = false;

    function filtra() {
      const testo = campo.value;
      const attiva = norma(testo) !== "";
      const visibili = new Set(attiva ? cerca(tutte, testo) : tutte);
      tutte.forEach((v) => { v.li.hidden = !visibili.has(v); });
      regioni.forEach((r) => {
        const n = r.querySelectorAll(".ep-riquadro:not([hidden])").length;
        r.hidden = n === 0;
        const etichetta = r.querySelector(".ep-n");
        etichetta.textContent = attiva ? "(" + n + " of " + etichetta.dataset.totale + ")" : "(" + etichetta.dataset.totale + ")";
      });
      if (evidenza) evidenza.hidden = attiva;     // altrimenti un Paese comparirebbe due volte
      if (salti) salti.hidden = attiva;
      if (nota) nota.hidden = attiva;               // durante la ricerca i risultati salgono in alto
      pulisci.hidden = !attiva;
      conteggio.textContent = attiva ? visibili.size + " of " + totale + " countries" : totale + " countries";
      nessuno.hidden = !(attiva && visibili.size === 0);
      nessuno.querySelector(".ep-query").textContent = testo.trim();
    }
    function svuota() { campo.value = ""; filtra(); campo.focus(); }

    campo.addEventListener("input", filtra);
    campo.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { if (campo.value) { e.preventDefault(); svuota(); } }
      else if (e.key === "Enter") {
        const primo = tutte.find((v) => !v.li.hidden);
        const link = primo && primo.li.querySelector("a.ep-link");
        if (norma(campo.value) && link) { e.preventDefault(); link.click(); }
      }
    });
    pulisci.addEventListener("click", svuota);
    radice.querySelector(".ep-pulisci-testo").addEventListener("click", svuota);
    filtra();
  }

  // La testata del sito resta in cima mentre si scorre: la barra di ricerca si ferma sotto di essa (altezza misurata, non scritta a mano)
  function altezzaTestata() {
    const testata = document.querySelector(".testata-sito");
    if (!testata) return;
    const imposta = () => document.documentElement.style.setProperty("--altezza-testata", testata.offsetHeight + "px");
    imposta();
    window.addEventListener("resize", imposta);
    if (window.ResizeObserver) new ResizeObserver(imposta).observe(testata);
  }

  window.ElencoPaesi = { norma, cerca, voci };
  document.querySelectorAll("[data-elenco-paesi]").forEach(avvia);
  altezzaTestata();
})();
