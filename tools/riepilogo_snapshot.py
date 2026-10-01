"""Riepilogo in Markdown delle differenze di uno snapshot (dati/weo o dati/bm) rispetto a un commit (predefinito: HEAD).

Uso (dalla cartella del progetto, con l'ambiente virtuale attivo):
    python tools/riepilogo_snapshot.py dati/bm                  # file nella cartella di lavoro contro HEAD
    python tools/riepilogo_snapshot.py dati/bm --base origin/main

Lo scrive il workflow `aggiorna-dati-bm.yml` nella descrizione della pull request. Esce con 0 se ci sono differenze, 3 se non ce ne sono.
"""

import argparse
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from dashboard import annuali  # noqa: E402


def da_git(base: str, percorso: str) -> str | None:
    """Contenuto di un file a un certo commit (None se non esisteva)."""
    risultato = subprocess.run(["git", "show", f"{base}:{percorso}"], cwd=RADICE, capture_output=True, text=True, encoding="utf-8")
    return risultato.stdout if risultato.returncode == 0 else None


def leggi(testo: str | None) -> pd.DataFrame:
    if not testo:
        return pd.DataFrame(columns=annuali.COLONNE_DATI).astype({"anno": int, "valore": float})
    return pd.read_csv(io.StringIO(testo), dtype={"paese": str, "indicatore": str, "anno": int, "valore": float})


def main() -> int:
    parser = argparse.ArgumentParser(description="Riepilogo delle differenze di uno snapshot")
    parser.add_argument("cartella", help="es. dati/bm")
    parser.add_argument("--base", default="HEAD")
    argomenti = parser.parse_args()

    cartella = argomenti.cartella.rstrip("/")
    prima = leggi(da_git(argomenti.base, f"{cartella}/dati.csv"))
    dopo = leggi((RADICE / cartella / "dati.csv").read_text(encoding="utf-8"))
    d = annuali.differenze(prima, dopo)
    meta_prima, meta_dopo = da_git(argomenti.base, f"{cartella}/meta.json") or "", (RADICE / cartella / "meta.json").read_text(encoding="utf-8")
    if d.identici and meta_prima == meta_dopo:
        print(f"Nessuna differenza in {cartella}.")
        return 3

    print(f"### Snapshot `{cartella}` rispetto a `{argomenti.base}`\n")
    print(f"- Dati invariati: {d.uguali:,}")
    print(f"- **Valori cambiati: {d.cambiate:,}**, aggiunti: {d.aggiunte:,}, rimossi: {d.rimosse:,}")
    if d.per_indicatore:
        print("- Per indicatore: " + ", ".join(f"`{i}` {n:,}" for i, n in d.per_indicatore.items()))
    if meta_prima != meta_dopo:
        print("- `meta.json` cambiato (date di aggiornamento della fonte)")
    if d.esempi:
        print("\n| Stato | Paese | Indicatore | Anno | Prima | Dopo |\n|---|---|---|---|---|---|")
        for stato, paese, indicatore, anno, vecchio, nuovo in d.esempi:
            fmt = lambda v: "—" if v is None else annuali.formatta_valore(v)  # noqa: E731
            print(f"| {stato} | {paese} | `{indicatore}` | {anno} | {fmt(vecchio)} | {fmt(nuovo)} |")
    if (RADICE / cartella / "ultimo_effettivo.csv").exists():
        antico = da_git(argomenti.base, f"{cartella}/ultimo_effettivo.csv")
        if antico != (RADICE / cartella / "ultimo_effettivo.csv").read_text(encoding="utf-8"):
            print("\n- `ultimo_effettivo.csv` cambiato: l'FMI ha aggiornato l'ultimo anno con dato reale di qualche Paese")
    return 0


if __name__ == "__main__":
    sys.exit(main())
