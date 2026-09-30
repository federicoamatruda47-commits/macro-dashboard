"""Registro delle regioni: collega l'id della regione (config.yaml) al file che ne costruisce la pagina.

Per aggiungere una regione (es. Asia):
  1. crea dashboard/regions/asia.py con una funzione `costruisci(serie, config)`
  2. aggiungi qui:  "asia": asia.costruisci,
  3. in config.yaml metti `attiva: true` per la regione e aggiungi le sue serie
"""

from . import eurozona, usa
from .modello import Grafico, Sezione

REGIONI = {
    "usa": usa.costruisci,
    "eurozona": eurozona.costruisci,
}

__all__ = ["REGIONI", "Grafico", "Sezione"]
