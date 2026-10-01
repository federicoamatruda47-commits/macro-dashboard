"""Registro delle pagine di Economies: collega l'id della pagina (blocco "pagine" di config.yaml)
alla funzione che ne costruisce le sezioni.

Le pagine con `stato: in-arrivo` non hanno un costruttore: si genera una pagina vuota "coming soon".
Per riempirne una (es. Italy):
  1. crea dashboard/economie/italy.py con una funzione `costruisci(serie, config) -> list[Sezione]`
  2. aggiungi qui:  "economies/italy": italy.costruisci,
  3. in config.yaml metti `stato: attiva` per quella pagina (e i suoi numeri chiave)
"""

from . import usa

PAGINE = {
    "economies/usa": usa.costruisci,
}
