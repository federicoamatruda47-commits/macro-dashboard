"""Avviso "da quanto tempo non c'è un commit su main".

GitHub disattiva i workflow programmati dei repository PUBBLICI senza "attività" da 60 giorni, e lo fa senza avvisi
(la documentazione non dice cosa conti come attività; le fonti della comunità dicono che contano i commit e i push, e un push fatto
da un workflow con GITHUB_TOKEN potrebbe non contare). Se la build giornaliera si fermasse, il sito resterebbe online con i dati
vecchi. Per accorgersene prima: la build legge la data dell'ultimo commit (HEAD del ramo che sta costruendo, su GitHub è main) e, se
sono passati più di 45 giorni, il sito mostra un avviso. Su GitHub il checkout contiene almeno l'ultimo commit, che basta.
"""

import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

SOGLIA_GIORNI = 45     # l'avviso compare prima del limite dei 60 giorni di GitHub
LIMITE_GITHUB_GIORNI = 60


@dataclass
class StatoAttivita:
    ultimo_commit: date
    giorni: int
    soglia: int = SOGLIA_GIORNI

    @property
    def in_ritardo(self) -> bool:
        return self.giorni > self.soglia


def valuta(ultimo_commit: date | None, oggi: date, soglia: int = SOGLIA_GIORNI) -> StatoAttivita | None:
    """Lo stato dell'attività (None se la data dell'ultimo commit non si conosce)."""
    if ultimo_commit is None:
        return None
    return StatoAttivita(ultimo_commit=ultimo_commit, giorni=max((oggi - ultimo_commit).days, 0), soglia=soglia)


def data_ultimo_commit(radice: Path) -> date | None:
    """Data (UTC) dell'ultimo commit del ramo corrente; None se git non c'è o la cartella non è un repository."""
    try:
        risultato = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=radice, capture_output=True, text=True, timeout=20, check=True)
        return datetime.fromisoformat(risultato.stdout.strip()).astimezone(timezone.utc).date()
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
