"""Registro delle regioni: collega l'id della regione (config.yaml) al file che ne costruisce la pagina.

Per aggiungere una regione (es. India):
  1. crea dashboard/regions/india.py con una funzione `costruisci(serie, config)`
  2. aggiungi qui:  "india": india.costruisci,
  3. in config.yaml metti `attiva: true` per la regione e aggiungi le sue serie

Una "regione" può anche essere una pagina tematica, come le commodities.
"""

from . import cina, commodities, corea, eurozona, giappone, globale, usa
from .modello import Grafico, Sezione

REGIONI = {
    "usa": usa.costruisci,
    "eurozona": eurozona.costruisci,
    "commodities": commodities.costruisci,
    "giappone": giappone.costruisci,
    "cina": cina.costruisci,
    "corea": corea.costruisci,
    "globale": globale.costruisci,
}

__all__ = ["REGIONI", "Grafico", "Sezione"]
