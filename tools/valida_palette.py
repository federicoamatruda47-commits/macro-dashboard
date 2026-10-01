"""Controllo della palette dei grafici (porting in Python di validate_palette.js della skill "dataviz").

Serve a verificare che i colori fissi dei Paesi si distinguano tra loro anche per chi ha un daltonismo,
senza "andare a occhio". Stesse soglie e stesso modello di simulazione dello script originale
(Machado, Oliveira e Fernandes 2009, severità 1; distanze in OKLab × 100).

Uso (dalla cartella del progetto):
    python tools/valida_palette.py            # controlla i colori scritti in config.yaml (blocco "colori:")
    python tools/valida_palette.py "#2a78d6,#eb6834,#1baf7a" --mode light --pairs all

Esce con codice 1 se un controllo fallisce. Gli avvisi (WARN) non fanno fallire: valgono solo se il grafico
ha anche un secondo segnale oltre al colore (legenda sempre presente, stile della linea diverso).
"""

import itertools
import math
import sys
from pathlib import Path

BANDA = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}   # luminosità OKLCH ammessa
CROMA_MIN = 0.10
CVD_OBIETTIVO, CVD_MINIMO = 8.0, 6.0
NORMALE_MINIMO = 15.0
CONTRASTO_MIN = 3.0
SUPERFICIE = {"light": "#fcfcfb", "dark": "#1a1a19"}

MACHADO = {
    "protan": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
    "tritan": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
}


def _lineare(esadecimale: str) -> list[float]:
    h = esadecimale.strip().lstrip("#")
    canali = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canali]


def _oklab(rgb: list[float]) -> tuple[float, float, float]:
    r, g, b = rgb
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _simula(esadecimale: str, tipo: str) -> list[float]:
    r, g, b = _lineare(esadecimale)
    return [max(0.0, min(1.0, riga[0] * r + riga[1] * g + riga[2] * b)) for riga in MACHADO[tipo]]


def distanza(a: str, b: str, tipo: str | None = None) -> float:
    """Distanza di colore (OKLab × 100); con `tipo` ("protan", "deutan", "tritan") simula il daltonismo."""
    ca = _oklab(_simula(a, tipo) if tipo else _lineare(a))
    cb = _oklab(_simula(b, tipo) if tipo else _lineare(b))
    return 100 * math.dist(ca, cb)


def luminosita_croma(esadecimale: str) -> tuple[float, float]:
    L, a, b = _oklab(_lineare(esadecimale))
    return L, math.hypot(a, b)


def contrasto(a: str, b: str) -> float:
    def lum(x):
        r, g, b_ = _lineare(x)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b_
    alto, basso = sorted((lum(a), lum(b)), reverse=True)
    return (alto + 0.05) / (basso + 0.05)


def peggiore(colori: list[str], coppie: list[tuple[int, int]]) -> tuple[float, float]:
    """(peggior distanza con daltonismo protan/deutan, peggior distanza a vista normale) sulle coppie date."""
    cvd = min((distanza(colori[i], colori[j], t) for i, j in coppie for t in ("protan", "deutan")), default=99.0)
    normale = min((distanza(colori[i], colori[j]) for i, j in coppie), default=99.0)
    return cvd, normale


def valida(colori: list[str], modo: str = "light", coppie: str = "adjacent", nomi: list[str] | None = None) -> bool:
    nomi = nomi or colori
    superficie = SUPERFICIE[modo]
    n = len(colori)
    elenco = list(itertools.combinations(range(n), 2)) if coppie == "all" else [(i, i + 1) for i in range(n - 1)]
    ok = True
    print(f"\nPalette ({modo}, superficie {superficie}, coppie: {coppie}): {n} colori")

    fuori = [(nomi[i], round(luminosita_croma(c)[0], 3)) for i, c in enumerate(colori)
             if not BANDA[modo][0] <= luminosita_croma(c)[0] <= BANDA[modo][1]]
    print(f"  [{'FAIL' if fuori else 'PASS'}] Banda di luminosità {BANDA[modo]}" + (f": fuori {fuori}" if fuori else ""))
    ok &= not fuori

    grigi = [(nomi[i], round(luminosita_croma(c)[1], 3)) for i, c in enumerate(colori) if luminosita_croma(c)[1] < CROMA_MIN]
    print(f"  [{'FAIL' if grigi else 'PASS'}] Croma minimo {CROMA_MIN}" + (f": sembrano grigi {grigi}" if grigi else ""))
    ok &= not grigi

    peggio = None
    for t in ("protan", "deutan"):
        for i, j in elenco:
            d = distanza(colori[i], colori[j], t)
            if peggio is None or d < peggio[0]:
                peggio = (d, t, nomi[i], nomi[j])
    if peggio:
        stato = "PASS" if peggio[0] >= CVD_OBIETTIVO else "WARN" if peggio[0] >= CVD_MINIMO else "FAIL"
        print(f"  [{stato}] Daltonismo: peggior coppia {peggio[2]} / {peggio[3]} ΔE {peggio[0]:.1f} ({peggio[1]})")
        ok &= stato != "FAIL"

    norm = min(((distanza(colori[i], colori[j]), nomi[i], nomi[j]) for i, j in elenco), default=None)
    if norm:
        stato = "PASS" if norm[0] >= NORMALE_MINIMO else "FAIL"
        print(f"  [{stato}] Vista normale: peggior coppia {norm[1]} / {norm[2]} ΔE {norm[0]:.1f} (minimo {NORMALE_MINIMO:.0f})")
        ok &= stato != "FAIL"

    bassi = [(nomi[i], round(contrasto(c, superficie), 2)) for i, c in enumerate(colori) if contrasto(c, superficie) < CONTRASTO_MIN]
    print(f"  [{'WARN' if bassi else 'PASS'}] Contrasto con lo sfondo ≥ {CONTRASTO_MIN}:1"
          + (f": sotto soglia {bassi} (serve legenda sempre visibile)" if bassi else ""))
    print(f"  → {'TUTTO OK' if ok else 'NON PASSA'}")
    return ok


def main() -> int:
    argomenti = sys.argv[1:]
    modo = argomenti[argomenti.index("--mode") + 1] if "--mode" in argomenti else None
    coppie = argomenti[argomenti.index("--pairs") + 1] if "--pairs" in argomenti else "all"
    if argomenti and not argomenti[0].startswith("--"):
        colori = [c.strip() for c in argomenti[0].split(",") if c.strip()]
        return 0 if all(valida(colori, m, coppie) for m in ([modo] if modo else ["light", "dark"])) else 1

    import yaml
    config = yaml.safe_load((Path(__file__).resolve().parent.parent / "config.yaml").read_text(encoding="utf-8"))
    tutti_ok = True
    for m in ([modo] if modo else ["light", "dark"]):
        voci = [(k, v) for k, v in config["colori"].items() if v.get("gruppo") == "paese"]
        tutti_ok &= valida([v["chiaro" if m == "light" else "scuro"] for _, v in voci], m, coppie, [k for k, _ in voci])
    return 0 if tutti_ok else 1


if __name__ == "__main__":
    sys.exit(main())
