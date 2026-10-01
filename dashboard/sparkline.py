"""Mini-grafico (sparkline) in SVG per le schede dell'Overview: l'ultimo anno di una serie in poche centinaia di byte.

Niente Plotly e niente JavaScript: è un'immagine SVG scritta direttamente nella pagina, quindi non pesa e si vede subito.
Il colore è quello fisso della serie (variabile CSS --c-<chiave>, come nei grafici).
"""

import pandas as pd

LARGHEZZA, ALTEZZA, MARGINE = 120, 34, 3
PUNTI_MASSIMI = 60          # oltre questo numero di punti se ne prendono di equidistanti (basta per un anno)
PUNTI_MINIMI = 8            # una serie mensile ha solo 12 punti all'anno: se ne servono almeno 8 per disegnare una linea utile


def sparkline_svg(dati: pd.Series, chiave_colore: str, anni: int = 1) -> str:
    """L'SVG dell'ultimo anno di `dati`, oppure una stringa vuota se i punti sono troppo pochi."""
    dati = dati.dropna()
    if len(dati) < 2:
        return ""
    recenti = dati[dati.index >= dati.index[-1] - pd.DateOffset(years=anni)]
    if len(recenti) < PUNTI_MINIMI:             # serie con pochi dati: si allarga con gli ultimi 13 valori
        recenti = dati.iloc[-13:]
    if len(recenti) > PUNTI_MASSIMI:
        posizioni = sorted({round(i * (len(recenti) - 1) / (PUNTI_MASSIMI - 1)) for i in range(PUNTI_MASSIMI)})
        recenti = recenti.iloc[posizioni]
    valori = recenti.to_numpy(dtype=float)
    tempi = recenti.index.astype("int64").to_numpy().astype(float)
    minimo, massimo = valori.min(), valori.max()
    durata = (tempi[-1] - tempi[0]) or 1.0
    intervallo = (massimo - minimo) or 1.0

    def punto(t: float, v: float) -> tuple[float, float]:
        x = MARGINE + (t - tempi[0]) / durata * (LARGHEZZA - 2 * MARGINE)
        y = MARGINE + (1 - (v - minimo) / intervallo) * (ALTEZZA - 2 * MARGINE)
        return round(x, 1), round(y, 1)

    punti = [punto(t, v) for t, v in zip(tempi, valori)]
    linea = " ".join(f"{x},{y}" for x, y in punti)
    x_fine, y_fine = punti[-1]
    return (f'<svg class="sparkline" viewBox="0 0 {LARGHEZZA} {ALTEZZA}" role="img" aria-label="Trend over the last year" '
            f'style="color: var(--c-{chiave_colore})"><polyline fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linejoin="round" stroke-linecap="round" points="{linea}"/>'
            f'<circle cx="{x_fine}" cy="{y_fine}" r="2.4" fill="currentColor"/></svg>')
