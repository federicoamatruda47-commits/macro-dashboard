"""Registro delle regioni: collega l'id della regione (config.yaml) al file che ne costruisce la pagina.

Per aggiungere una regione (es. Eurozona):
  1. crea dashboard/regions/eurozona.py con una funzione `costruisci(serie)`
  2. aggiungi qui:  "eurozona": eurozona.costruisci,
  3. in config.yaml metti `attiva: true` per la regione e aggiungi le sue serie
"""

from . import usa
from .modello import Grafico, Sezione

REGIONI = {
    "usa": usa.costruisci,
}

__all__ = ["REGIONI", "Grafico", "Sezione"]
