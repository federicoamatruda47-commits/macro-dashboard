"""Grafici riutilizzabili, indipendenti dalla regione.

Ogni funzione riceve oggetti `Serie` e restituisce una figura Plotly.
I colori definitivi (tema chiaro/scuro) li applica il JavaScript della pagina:
qui ogni linea riceve solo un numero di "slot" (1, 2, 3...) in `meta`.
Il JavaScript usa lo slot per scegliere il colore giusto della palette.
"""

from dataclasses import replace

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .data import Serie

# Palette categoriale (tema chiaro): usata solo come valore di partenza.
# Deve restare allineata alle variabili --s1...--s8 in static/style.css.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
COLORE_RECESSIONE = "rgba(137, 135, 129, 0.22)"  # grigio semitrasparente, leggibile in entrambi i temi
COLORE_INVERSIONE = "rgba(227, 73, 72, 0.45)"    # rosso semitrasparente per le inversioni della curva

# Per non appesantire la pagina: dati giornalieri completi solo per gli
# ultimi N anni; prima si tiene l'ultimo valore di ogni settimana.
ANNI_DATI_GIORNALIERI = 5


# ---------------------------------------------------------------------
# Funzioni di supporto
# ---------------------------------------------------------------------

def alleggerisci(serie: pd.Series) -> pd.Series:
    """Riduce i punti dei dati giornalieri più vecchi (settimanali invece di giornalieri)."""
    if len(serie) < 2000:
        return serie
    confine = serie.index[-1] - pd.DateOffset(years=ANNI_DATI_GIORNALIERI)
    vecchi = serie[serie.index < confine].resample("W").last().dropna()
    recenti = serie[serie.index >= confine]
    return pd.concat([vecchi, recenti])


def _date(serie: pd.Series) -> list[str]:
    return serie.index.strftime("%Y-%m-%d").tolist()


def _valori(serie: pd.Series) -> list[float]:
    return serie.round(4).tolist()  # 4 decimali: servono per i cambi (es. EUR/USD 1,1355)


def _suffisso(unita: str) -> str:
    """Suffisso per asse e tooltip: '%' per tassi e variazioni annue, niente per indici."""
    return "%" if unita.startswith("%") else ""


def periodi_recessione(usrec: Serie | None) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Trasforma la serie mensile USREC (1 = recessione) in coppie (inizio, fine).

    La fine è il primo giorno del mese successivo all'ultimo mese di recessione,
    così la banda copre tutto l'ultimo mese.
    """
    if usrec is None or not usrec.ok:
        return []
    in_recessione = usrec.dati >= 0.5
    periodi = []
    inizio = None
    for data, flag in in_recessione.items():
        if flag and inizio is None:
            inizio = data
        elif not flag and inizio is not None:
            periodi.append((inizio, data))  # 'data' è il primo mese di espansione
            inizio = None
    if inizio is not None:  # recessione ancora in corso
        periodi.append((inizio, usrec.dati.index[-1] + pd.DateOffset(months=1)))
    return periodi


def periodi_da_trimestri(elenco: list[dict] | None) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Trasforma un elenco di recessioni datate per trimestre (es. CEPR) in coppie (inizio, fine).

    Ogni voce ha "picco" e "minimo" nel formato "2008Q1". Come per il NBER, la recessione
    va dal trimestre DOPO il picco fino al trimestre del minimo compreso:
    picco 2008Q1, minimo 2009Q2 -> banda dal 1° aprile 2008 al 1° luglio 2009.
    """
    periodi = []
    for voce in elenco or []:
        picco = pd.Period(str(voce["picco"]), freq="Q")
        minimo = pd.Period(str(voce["minimo"]), freq="Q")
        periodi.append(((picco + 1).start_time.normalize(), (minimo + 1).start_time.normalize()))
    return periodi


def _layout_base(unita: str) -> dict:
    """Impostazioni comuni a tutti i grafici (i colori li completa il JavaScript)."""
    return dict(
        margin=dict(l=8, r=8, t=8, b=8),
        hovermode="x unified",
        separators=",.",  # virgola decimale e punto per le migliaia, all'italiana
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.0, xanchor="left", yanchor="bottom", font=dict(size=12)),
        xaxis=dict(type="date", showgrid=False, hoverformat="%d %b %Y", automargin=True,
                   showspikes=True, spikemode="across", spikethickness=1, spikedash="solid"),
        yaxis=dict(ticksuffix=_suffisso(unita), zeroline=False, automargin=True, gridwidth=1),
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", size=12),
    )


def _titolo_unita(unita: str) -> dict:
    """Titolo dell'asse verticale con l'unità di misura (es. '$/barile')."""
    return dict(text=unita, font=dict(size=11), standoff=6)


def _aggiungi_recessioni(figura: go.Figure, recessioni, inizio: pd.Timestamp, fine: pd.Timestamp,
                         etichetta: str, tutti_i_pannelli: bool = False) -> None:
    """Disegna le bande grigie, solo per le recessioni dentro il periodo del grafico."""
    visibili = [(a, b) for a, b in recessioni if b > inizio and a < fine]
    # Nei grafici a più pannelli la banda va disegnata in ognuno
    # (exclude_empty_subplots=False: le bande si aggiungono prima delle linee, a pannelli ancora vuoti)
    pannelli = dict(row="all", col=1, exclude_empty_subplots=False) if tutti_i_pannelli else {}
    for a, b in visibili:
        figura.add_vrect(x0=max(a, inizio).strftime("%Y-%m-%d"), x1=min(b, fine).strftime("%Y-%m-%d"),
                         fillcolor=COLORE_RECESSIONE, line_width=0, layer="below", **pannelli)
    if visibili:
        # Voce di legenda "finta" per spiegare cosa sono le bande grigie
        figura.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=etichetta,
                                    marker=dict(symbol="square", size=12, color=COLORE_RECESSIONE),
                                    hoverinfo="skip"))


def _aggiungi_linea_riferimento(figura: go.Figure, valore: float, etichetta: str) -> None:
    """Linea orizzontale tratteggiata (es. obiettivo di inflazione al 2%)."""
    annotazione = dict(annotation_text=etichetta, annotation_position="top left",
                       annotation_font=dict(size=11, color="#898781")) if etichetta else {}
    figura.add_hline(y=valore, line=dict(width=1.5, dash="dash", color="#898781"), **annotazione)
    # Il JavaScript include questi valori quando ricalcola la scala verticale
    meta = dict(figura.layout.meta or {})
    meta["riferimenti"] = meta.get("riferimenti", []) + [valore]
    figura.layout.meta = meta


# ---------------------------------------------------------------------
# Tipi di grafico
# ---------------------------------------------------------------------

def linee_storiche(serie: list[Serie], recessioni=None, riferimento: tuple[float, str] | None = None,
                   evidenzia_inversioni: bool = False,
                   etichetta_recessioni: str = "Recessione NBER",
                   mostra_unita: bool = False) -> go.Figure | None:
    """Grafico a linee nel tempo, con recessioni e (opzionali) inversioni o linea di riferimento.

    Le serie non disponibili vengono saltate: il grafico mostra quelle rimaste.
    Restituisce None se nessuna serie è disponibile.
    mostra_unita=True scrive l'unità di misura sull'asse verticale (es. per i prezzi).
    """
    disponibili = [s for s in serie if s.ok]
    if not disponibili:
        return None

    unita = disponibili[0].unita
    suffisso = _suffisso(unita)
    figura = go.Figure(layout=_layout_base(unita))
    if mostra_unita:
        figura.update_yaxes(title=_titolo_unita(unita))

    inizio = min(s.prima_data for s in disponibili)
    fine = max(s.ultima_data for s in disponibili)
    _aggiungi_recessioni(figura, recessioni or [], inizio, fine, etichetta_recessioni)

    for slot, s in enumerate(serie, start=1):  # lo slot segue la posizione in lista, non la disponibilità
        if not s.ok:
            continue
        dati = alleggerisci(s.dati)

        if evidenzia_inversioni:
            # Area rossa tra zero e la parte NEGATIVA dello spread (= curva invertita)
            negativi = dati.clip(upper=0)
            figura.add_trace(go.Scatter(
                x=_date(negativi), y=_valori(negativi), mode="lines", line=dict(width=0),
                fill="tozeroy", fillcolor=COLORE_INVERSIONE, hoverinfo="skip",
                name="Inversione (spread < 0)", legendgroup="inversione", showlegend=(slot == 1),
            ))

        figura.add_trace(go.Scatter(
            x=_date(dati), y=_valori(dati), mode="lines", name=s.nome,
            line=dict(width=2, color=PALETTE[slot - 1]), meta={"slot": slot},
            hovertemplate=f"%{{y:.{s.decimali}f}}{suffisso}<extra>{s.nome}</extra>",
        ))

    if evidenzia_inversioni:
        _aggiungi_linea_riferimento(figura, 0, "")
    if riferimento is not None:
        _aggiungi_linea_riferimento(figura, *riferimento)
    return figura


def con_nome(s: Serie, nome: str) -> Serie:
    """Copia della serie con un altro nome (per le legende dei confronti: "Giappone" invece di "JGB 10 anni")."""
    return replace(s, nome=nome)


def linee_base100(serie: list[tuple]) -> go.Figure | None:
    """Confronto di serie con scale diverse: tutte partono da 100 all'inizio del periodo scelto.

    `serie` è una lista di coppie (Serie, invertita), con un terzo elemento facoltativo (dizionario):
      slot       numero del colore (predefinito: la posizione in lista)
      variante   id della variante in cui la linea è visibile (vedi Grafico.varianti); senza, è sempre visibile
      benchmark  True = linea più spessa e tratteggiata, nel colore neutro del testo (es. indice mondiale)
    invertita=True usa 1/valore: serve per i cambi quotati "valuta estera per dollaro" (USD/JPY...),
    così per ogni linea "sale" = la valuta si rafforza.
    Qui i dati sono quelli grezzi: la ribasatura a 100 la fa il JavaScript (static/app.js) a ogni cambio
    di periodo, partendo dalla prima data in cui esistono TUTTE le serie (visibili).
    """
    voci = [(s, inv, (extra[0] if extra else {})) for s, inv, *extra in serie]
    if not any(s.ok for s, _, _ in voci):
        return None
    figura = go.Figure(layout=_layout_base(""))
    _aggiungi_linea_riferimento(figura, 100, "")
    varianti = list(dict.fromkeys(o["variante"] for _, _, o in voci if "variante" in o))
    figura.layout.meta = {**dict(figura.layout.meta), "base100": True, **({"varianti": varianti} if varianti else {})}

    for posizione, (s, inv, opzioni) in enumerate(voci, start=1):
        if not s.ok:
            continue
        slot = opzioni.get("slot", posizione)
        valori = 1 / s.dati[s.dati != 0] if inv else s.dati
        dati = alleggerisci(valori)
        meta = {"slot": slot}
        linea = dict(width=2, color=PALETTE[(slot - 1) % len(PALETTE)])
        if "variante" in opzioni:
            meta["variante"] = opzioni["variante"]
        if opzioni.get("benchmark"):
            meta["neutro"] = True  # il JavaScript usa il colore del testo, adatto a tema chiaro e scuro
            linea.update(width=3.5, dash="dash")
        figura.add_trace(go.Scatter(
            x=_date(dati), y=[round(v, 8) for v in dati.tolist()], mode="lines", name=s.nome,
            line=linea, meta=meta, hovertemplate=f"%{{y:.1f}}<extra>{s.nome}</extra>",
        ))
    return figura


def due_pannelli(sopra: Serie, sotto: Serie, recessioni=None, inverti_sotto: bool = False,
                 etichetta_recessioni: str = "Recessione NBER") -> go.Figure | None:
    """Due grafici a linee uno sopra l'altro, con lo stesso asse del tempo.

    Serve a confrontare due serie con unità diverse (es. oro in $ e tasso reale in %)
    senza usare un doppio asse verticale: ogni pannello ha il suo asse.
    inverti_sotto=True capovolge l'asse del pannello in basso (valori alti in basso),
    utile quando le due serie di solito si muovono in direzioni opposte.
    Se entrambe sono disponibili, si mostra solo il periodo in cui esistono tutte e due.
    """
    disponibili = [s for s in (sopra, sotto) if s.ok]
    if not disponibili:
        return None
    inizio = max(s.prima_data for s in disponibili)  # periodo comune
    fine = max(s.ultima_data for s in disponibili)

    figura = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.07)
    layout = _layout_base("")
    asse_x, asse_y = layout.pop("xaxis"), layout.pop("yaxis")
    figura.update_layout(**layout)
    figura.update_xaxes(**asse_x)
    _aggiungi_recessioni(figura, recessioni or [], inizio, fine, etichetta_recessioni, tutti_i_pannelli=True)

    for riga, s in enumerate((sopra, sotto), start=1):
        titolo = s.unita + (" (asse invertito)" if riga == 2 and inverti_sotto else "")
        figura.update_yaxes(asse_y, row=riga, col=1)
        figura.update_yaxes(ticksuffix=_suffisso(s.unita), title=_titolo_unita(titolo), row=riga, col=1)
        if not s.ok:
            continue
        dati = alleggerisci(s.dati[s.dati.index >= inizio])
        suffisso = _suffisso(s.unita)
        figura.add_trace(go.Scatter(
            x=_date(dati), y=_valori(dati), mode="lines", name=s.nome,
            line=dict(width=2, color=PALETTE[riga - 1]), meta={"slot": riga},
            hovertemplate=f"%{{y:.{s.decimali}f}}{suffisso}<extra>{s.nome}</extra>",
        ), row=riga, col=1)

    if inverti_sotto:
        figura.update_yaxes(autorange="reversed", row=2, col=1)
        # Il JavaScript, quando ricalcola la scala, deve sapere quali assi sono capovolti
        figura.layout.meta = {"assi_invertiti": ["yaxis2"]}
    return figura


def curva_rendimenti(scadenze: list[tuple[str, Serie]]) -> tuple[go.Figure | None, pd.Timestamp | None]:
    """Curva dei rendimenti oggi, 1 mese fa e 1 anno fa.

    `scadenze` è una lista di coppie (etichetta, Serie), es. ("2A", DGS2).
    "Oggi" è l'ultimo giorno in cui TUTTE le scadenze disponibili hanno un dato.
    Restituisce la figura e la data usata come "oggi".
    """
    disponibili = [(etichetta, s) for etichetta, s in scadenze if s.ok]
    if len(disponibili) < 2:
        return None, None

    tabella = pd.DataFrame({etichetta: s.dati for etichetta, s in disponibili}).dropna()
    if tabella.empty:
        return None, None
    oggi = tabella.index[-1]

    confronti = [
        ("Oggi", oggi),
        ("1 mese fa", oggi - pd.DateOffset(months=1)),
        ("1 anno fa", oggi - pd.DateOffset(years=1)),
    ]
    figura = go.Figure(layout=_layout_base("%"))
    figura.update_layout(hovermode="x unified")
    figura.update_xaxes(type="category", showspikes=False, title=dict(text="Scadenza", font=dict(size=11)))

    for slot, (nome, data) in enumerate(confronti, start=1):
        riga = tabella.asof(data)  # ultimo giorno completo disponibile a quella data
        if riga.isna().all():
            continue
        data_effettiva = tabella.index[tabella.index <= data][-1]
        etichetta = f"{nome} ({data_effettiva:%d/%m/%Y})"
        figura.add_trace(go.Scatter(
            x=list(riga.index), y=riga.round(3).tolist(), mode="lines+markers", name=etichetta,
            line=dict(width=2, color=PALETTE[slot - 1]), marker=dict(size=9), meta={"slot": slot},
            hovertemplate=f"%{{y:.2f}}%<extra>{nome}</extra>",
        ))
    return figura, oggi
