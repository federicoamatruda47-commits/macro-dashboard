"""Grafici riutilizzabili, indipendenti dalla regione.

Ogni funzione riceve oggetti `Serie` e restituisce una figura Plotly.
I colori definitivi (tema chiaro/scuro) li applica il JavaScript della pagina:
qui ogni linea riceve solo un numero di "slot" (1, 2, 3...) in `meta`.
Il JavaScript usa lo slot per scegliere il colore giusto della palette.
"""

import pandas as pd
import plotly.graph_objects as go

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
    return serie.round(3).tolist()


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


def _aggiungi_recessioni(figura: go.Figure, recessioni, inizio: pd.Timestamp, fine: pd.Timestamp) -> None:
    """Disegna le bande grigie, solo per le recessioni dentro il periodo del grafico."""
    visibili = [(a, b) for a, b in recessioni if b > inizio and a < fine]
    for a, b in visibili:
        figura.add_vrect(x0=max(a, inizio).strftime("%Y-%m-%d"), x1=min(b, fine).strftime("%Y-%m-%d"),
                         fillcolor=COLORE_RECESSIONE, line_width=0, layer="below")
    if visibili:
        # Voce di legenda "finta" per spiegare cosa sono le bande grigie
        figura.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Recessione NBER",
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
                   evidenzia_inversioni: bool = False) -> go.Figure | None:
    """Grafico a linee nel tempo, con recessioni e (opzionali) inversioni o linea di riferimento.

    Le serie non disponibili vengono saltate: il grafico mostra quelle rimaste.
    Restituisce None se nessuna serie è disponibile.
    """
    disponibili = [s for s in serie if s.ok]
    if not disponibili:
        return None

    unita = disponibili[0].unita
    suffisso = _suffisso(unita)
    figura = go.Figure(layout=_layout_base(unita))

    inizio = min(s.prima_data for s in disponibili)
    fine = max(s.ultima_data for s in disponibili)
    _aggiungi_recessioni(figura, recessioni or [], inizio, fine)

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
            hovertemplate=f"%{{y:.2f}}{suffisso}<extra>{s.nome}</extra>",
        ))

    if evidenzia_inversioni:
        _aggiungi_linea_riferimento(figura, 0, "")
    if riferimento is not None:
        _aggiungi_linea_riferimento(figura, *riferimento)
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
