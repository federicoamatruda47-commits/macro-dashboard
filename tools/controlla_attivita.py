"""Controlla da quanti giorni non c'è un commit e, se sono più di 45, apre UNA issue su GitHub (mai due uguali); quando torna un commit la chiude.

Perché: GitHub disattiva i workflow programmati dei repository pubblici senza "attività" da 60 giorni, senza avvisi (la documentazione non dice cosa conti
come attività; per le fonti della comunità contano i commit e i push, mentre un push fatto da un workflow con GITHUB_TOKEN potrebbe non contare).
La build giornaliera si fermerebbe e il sito resterebbe online con i dati vecchi. L'avviso NON sta sul sito pubblico: arriva come issue (e-mail di GitHub).

Uso (dal job `controlla-attivita` di .github/workflows/aggiorna-dashboard.yml, con GH_TOKEN e il permesso `issues: write`; in locale serve `gh` autenticato):
    python tools/controlla_attivita.py                  # controlla e, se serve, apre o chiude la issue
    python tools/controlla_attivita.py --solo-stampa    # stampa soltanto lo stato, non tocca GitHub
    python tools/controlla_attivita.py --soglia 0 --prova   # PROVA: titolo con "[PROVA]" e soglia a 0 (per provare il flusso con la issue vera)

La data è quella dell'ultimo commit del ramo che il workflow ha scaricato (main). Una sola issue aperta alla volta: si riconosce dal titolo esatto.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from dashboard import attivita  # noqa: E402

TITOLO = "Nessun commit da più di 45 giorni: GitHub potrebbe spegnere la build giornaliera"


def gh(*argomenti: str) -> str:
    """Esegue un comando `gh`; se fallisce esce con un messaggio chiaro (il job diventa rosso e GitHub manda l'e-mail)."""
    risultato = subprocess.run(["gh", *argomenti], capture_output=True, text=True, encoding="utf-8", cwd=RADICE)
    if risultato.returncode != 0:
        print(f"ERRORE: gh {' '.join(argomenti[:2])} ha fallito: {risultato.stderr.strip() or risultato.stdout.strip()}")
        sys.exit(1)
    return risultato.stdout.strip()


def issue_aperta(titolo: str) -> int | None:
    """Numero della issue aperta con questo titolo esatto (None se non c'è)."""
    elenco = json.loads(gh("issue", "list", "--state", "open", "--limit", "100", "--json", "number,title") or "[]")
    numeri = [i["number"] for i in elenco if i["title"] == titolo]
    return min(numeri) if numeri else None


def testo_issue(giorni: int, ultimo: str, soglia: int, url_run: str | None) -> str:
    return "\n".join([
        f"L'ultimo commit del ramo principale è del **{ultimo}**, cioè **{giorni} giorni fa** (soglia: {soglia}).",
        "",
        f"GitHub disattiva i workflow programmati dei repository pubblici dopo {attivita.LIMITE_GITHUB_GIORNI} giorni senza attività, **senza avvisare**: "
        "la build giornaliera si fermerebbe e il sito resterebbe online con i dati vecchi. La documentazione di GitHub non dice cosa conti come "
        "\"attività\": secondo le segnalazioni degli utenti contano i commit e i push; un push fatto da un workflow con `GITHUB_TOKEN` potrebbe non contare.",
        "",
        "**Cosa fare**: fare un commit su `main` (anche piccolo, per esempio una riga nel registro di `docs/ristrutturazione.md`), oppure controllare nella scheda "
        "*Actions* che il workflow \"Aggiorna dashboard\" sia ancora attivo e, se è disattivato, riattivarlo.",
        "",
        "Questa issue è aperta da `tools/controlla_attivita.py` (job `controlla-attivita`) e si chiude da sola alla prima esecuzione dopo un nuovo commit."
        + (f" Esecuzione: {url_run}" if url_run else ""),
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Apre una issue se l'ultimo commit ha più di 45 giorni")
    parser.add_argument("--soglia", type=int, default=attivita.SOGLIA_GIORNI)
    parser.add_argument("--solo-stampa", action="store_true", help="non tocca GitHub")
    parser.add_argument("--prova", action="store_true", help='titolo con "[PROVA]": per provare il flusso senza confondersi con la issue vera')
    argomenti = parser.parse_args()

    oggi = datetime.now(timezone.utc).date()
    stato = attivita.valuta(attivita.data_ultimo_commit(RADICE), oggi, argomenti.soglia)
    if stato is None:
        print("Non riesco a leggere la data dell'ultimo commit (git assente o checkout senza storia): nessuna azione.")
        return 0
    ultimo = f"{stato.ultimo_commit.day} {stato.ultimo_commit:%b %Y}"
    print(f"Ultimo commit: {ultimo} ({stato.giorni} giorni fa, soglia {stato.soglia}).")
    if argomenti.solo_stampa:
        return 0

    titolo = ("[PROVA] " if argomenti.prova else "") + TITOLO
    aperta = issue_aperta(titolo)
    if stato.in_ritardo:
        if aperta is not None:
            print(f"C'è già la issue #{aperta}: non ne apro un'altra.")
            return 0
        url_run = (f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                   if all(k in os.environ for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")) else None)
        indirizzo = gh("issue", "create", "--title", titolo, "--body", testo_issue(stato.giorni, ultimo, stato.soglia, url_run))
        print(f"Aperta una issue: {indirizzo}")
    elif aperta is not None:
        gh("issue", "close", str(aperta), "--comment", f"C'è un commit recente ({ultimo}, {stato.giorni} giorni fa): chiudo la issue.")
        print(f"Chiusa la issue #{aperta}: l'attività è tornata sotto la soglia.")
    else:
        print("Tutto a posto: nessuna issue da aprire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
