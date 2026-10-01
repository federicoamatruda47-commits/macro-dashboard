"""Pagina Confronto globale: svuotata nello step 4e-2 (tutti i suoi grafici sono passati alle pagine Markets).

Resta solo perché la regione è ancora nel registro: sparisce del tutto allo step 5 (docs/ristrutturazione.md).
"""

from ..data import Serie
from .modello import Sezione


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    return []
