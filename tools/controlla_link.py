"""Controllo dei link INTERNI del sito generato (cartella site/): ogni link relativo deve portare a una pagina che esiste
e, se ha un frammento (#chart-..., #note-...), a un elemento con quell'id.

Uso (dopo `python build.py`):
    python tools/controlla_link.py

Non controlla i link esterni (fonti): richiederebbero la rete e cambiano spesso. Esce con codice 1 se trova link rotti.
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

SITO = Path(__file__).resolve().parent.parent / "site"


def main() -> int:
    pagine = {p: p.read_text(encoding="utf-8") for p in SITO.rglob("index.html")}
    id_per_pagina = {p: set(re.findall(r'\sid="([^"]+)"', h)) for p, h in pagine.items()}
    rotti, controllati = [], 0
    for pagina, html in pagine.items():
        for href in re.findall(r'<a [^>]*href="([^"]+)"', html):
            if re.match(r"(https?:|mailto:|javascript:)", href):
                continue
            controllati += 1
            url = urlparse(href)
            destinazione = (pagina.parent / unquote(url.path)).resolve() if url.path else pagina
            if destinazione.is_dir():
                destinazione = destinazione / "index.html"
            if not destinazione.exists():
                rotti.append(f"{pagina.relative_to(SITO)}: {href} -> pagina inesistente")
                continue
            if url.fragment and destinazione in id_per_pagina and url.fragment not in id_per_pagina[destinazione]:
                rotti.append(f"{pagina.relative_to(SITO)}: {href} -> manca l'elemento #{url.fragment}")
    print(f"{controllati} link interni controllati in {len(pagine)} pagine")
    for r in sorted(set(rotti)):
        print("✗", r)
    print("OK: nessun link rotto." if not rotti else f"{len(set(rotti))} link rotto/i.")
    return 1 if rotti else 0


if __name__ == "__main__":
    sys.exit(main())
