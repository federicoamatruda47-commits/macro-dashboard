"""Errore comune a tutte le fonti dati."""


class ErroreFonte(Exception):
    """Una serie non è stata scaricata.

    Il messaggio finisce sul sito pubblico: deve essere breve, in italiano
    e non deve MAI contenere la chiave API.
    """
