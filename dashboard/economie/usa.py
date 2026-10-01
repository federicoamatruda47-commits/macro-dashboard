"""Pagina Economies / United States.

Per ora c'è solo il mercato del lavoro (la disoccupazione): crescita, prezzi e Fed arriveranno dopo.
Come le altre pagine: riceve le serie già pronte (dizionario id -> Serie) e decide come combinarle nei grafici.
Le note tecniche stanno in contenuti/note.yaml: qui si indicano solo gli id.
"""

from .. import charts
from ..data import Serie, trova_serie
from ..modello import Grafico, Sezione

DISOCCUPAZIONE = "UNRATE"


def costruisci(serie: dict[str, Serie], config: dict) -> list[Sezione]:
    recessioni = charts.periodi_recessione(serie.get("USREC"))
    disoccupazione = Grafico(
        id="usa-disoccupazione", titolo="Unemployment rate",
        figura=charts.linee_storiche([trova_serie(serie, DISOCCUPAZIONE)], recessioni=recessioni),
        serie_ids=[DISOCCUPAZIONE], periodo_iniziale="Max", largo=True, note=["bands-nber"],
        come_leggerlo="The unemployment rate is the share of people who want a job and are looking for one but cannot find it. "
                      "It has historically tended to rise quickly in recessions and to fall more slowly during recoveries.")
    return [
        Sezione("lavoro", "Labour",
                "How many people are out of work in the US. More indicators for the US economy will be added here.",
                grafici=[disoccupazione]),
    ]
