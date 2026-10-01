"""Registro delle pagine di mercato (Markets): collega l'id della pagina (blocco "pagine" di config.yaml)
alla funzione che ne costruisce le sezioni.

Per aggiungere una pagina:
  1. crea dashboard/mercati/<nome>.py con una funzione `costruisci(serie, config) -> list[Sezione]`
  2. aggiungi qui:  "markets/<nome>": <nome>.costruisci,
  3. in config.yaml, nel blocco "pagine", metti `stato: attiva` (e i numeri chiave); aggiungila anche al "menu"
"""

from . import commodities, credit, fx

PAGINE = {
    "markets/credit": credit.costruisci,
    "markets/fx": fx.costruisci,
    "markets/commodities": commodities.costruisci,
}
