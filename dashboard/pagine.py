"""Pagine del sito: percorsi, link relativi e menu a due righe.

Ogni pagina è un file site/<percorso>/index.html. I link sono sempre RELATIVI, così il sito funziona
anche sotto un sottopercorso (GitHub Pages: https://utente.github.io/nome-repo/): ogni pagina conosce
la propria "radice" ("" per la home, "../" per le pagine di primo livello, "../../" per quelle di secondo...).
"""

from dataclasses import dataclass, field

HOME = "home"


def percorso(id_pagina: str) -> str:
    """Cartella della pagina dentro site/ ("" = la home)."""
    return "" if id_pagina == HOME else id_pagina.strip("/") + "/"


def radice(id_pagina: str) -> str:
    """Prefisso per tornare alla radice del sito: "" , "../", "../../"..."""
    return "../" * len([parte for parte in percorso(id_pagina).split("/") if parte])


@dataclass
class VoceMenu:
    titolo: str
    href: str
    attiva: bool = False
    figli: list["VoceMenu"] = field(default_factory=list)


def titoli_pagine(config: dict) -> dict[str, str]:
    titoli = {r["id"]: r["nome"] for r in config["regioni"]}
    titoli[HOME] = "Home"
    return titoli


def costruisci_menu(config: dict, id_attiva: str) -> tuple[list[VoceMenu], list[VoceMenu]]:
    """Restituisce (prima riga, seconda riga) del menu per la pagina `id_attiva`.

    La seconda riga contiene le pagine figlie della voce attiva (vuota se la voce non ha figli).
    """
    titoli = titoli_pagine(config)
    base = radice(id_attiva)

    def voce_pagina(id_pagina: str) -> VoceMenu:
        return VoceMenu(titoli[id_pagina], base + percorso(id_pagina) or "./", id_pagina == id_attiva)

    prima, seconda = [], []
    for voce in config["menu"]:
        if "figli" in voce:
            figli = [voce_pagina(i) for i in voce["figli"]]
            attiva = any(f.attiva for f in figli)
            prima.append(VoceMenu(voce["titolo"], figli[0].href, attiva, figli))
            if attiva:
                seconda = figli
        else:
            v = voce_pagina(voce["pagina"])
            if "titolo" in voce:
                v.titolo = voce["titolo"]
            prima.append(v)
    return prima, seconda
