"""Generazione del materiale Markdown a partire dai dati del catalogo.

Il progetto ha due registri diversi, e va tenuta la differenza:

* la documentazione scritta a mano spiega *perche'* e *come si usa*;
* le schede di :mod:`pme.features` contengono il dato verificabile, con la fonte.

Questo modulo produce il secondo registro in forma di Markdown: le version card
di ``versions/``, la tabella cronologica e l'indice per area tematica. Il primo
registro resta scritto a mano e cita il secondo.

La generazione e' deliberatamente senza stato e senza dipendenze: la stessa
funzione che produce il testo a schermo produce il file, cosi' quello che si
vede nella CLI e quello che finisce nel repository non possono divergere.

Esempio::

    >>> from pme.report import render_feature
    >>> from pme.features import get
    >>> render_feature(get("print-function")).startswith("# `print()` come funzione")
    True
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from pme.demos import DEMOS
from pme.features import Feature, Kind, iter_features
from pme.version import PYTHON4_NOTE, PYTHON4_RELEASED, Release, Version, iter_releases

__all__ = [
    "render_feature",
    "render_feature_index",
    "render_version_card",
    "render_timeline",
    "render_catalog",
    "render_future",
    "version_card_names",
    "write_version_cards",
    "write_future_card",
]

#: Separazione fra le sezioni di una scheda.
_SEP = "\n\n"


def _titolo_cartegoria(kind: Kind) -> str:
    """Etichetta leggibile per una sezione di scheda."""
    return str(kind)


def _rimossa_in(feature: Feature) -> Optional[Version]:
    """Versione che ha rimosso la funzionalita', se e' il caso.

    Segue la convenzione del catalogo: per una scheda di tipo ``Rimozioni`` la
    data della rimozione coincide con ``introduced``, e non c'e' bisogno di
    duplicarla in ``removed``.
    """
    if feature.removed is not None:
        return feature.removed
    return feature.introduced if feature.kind is Kind.REMOVAL else None


def render_feature(feature: Feature) -> str:
    """Restituisce la scheda di una funzionalita' come Markdown.

    La sezione "codice" mostra solo quello che esiste: una scheda senza esempi
    non mente sul formato della trasformazione.

    Args:
        feature: scheda da rendere.

    Returns:
        Testo Markdown, terminato da una riga vuota.
    """
    parti: List[str] = [f"# {feature.title}", "", feature.summary, ""]
    metadati = [
        f"- **introdotta in**: Python {feature.introduced}",
        f"- **categoria**: {feature.category}",
        f"- **tipo**: {feature.kind}",
    ]
    if feature.deprecated is not None:
        metadati.append(f"- **deprecata in**: Python {feature.deprecated}")
    if _rimossa_in(feature) is not None:
        metadati.append(f"- **rimossa in**: Python {_rimossa_in(feature)}")
    if feature.pep is not None:
        metadati.append(f"- **PEP**: {feature.pep}")
    if feature.status != "stable":
        metadati.append(f"- **stato**: {feature.status}")
    parti.append("\n".join(metadati))
    if feature.before:
        versione = feature.before_version or feature.introduced
        parti.append(
            f"## Come era (Python {versione})\n\n```python\n{feature.before}\n```"
        )
    if feature.after:
        versione = feature.after_version or feature.introduced
        parti.append(
            f"## Come si usa oggi (Python {versione})\n\n```python\n{feature.after}\n```"
        )
    parti.append(f"## Perche'\n\n{feature.reason}")
    if feature.notes:
        parti.append(f"## Note\n\n{feature.notes}")
    demo = next((d for d in DEMOS if d.feature_id == feature.id), None)
    if demo is not None:
        esito = ""
        try:
            esito = f"\n\nRisultato: `{demo.result()!r}`"
        except RuntimeError:
            esito = ""
        parti.append(
            "## Dimostrazione\n\n```python\n"
            f"{demo.source}\n```{esito}"
        )
    parti.append(f"Fonte: {feature.source}")
    return _SEP.join(parti) + "\n"


def render_feature_index(features: Optional[Sequence[Feature]] = None) -> str:
    """Restituisce l'indice di tutte le schede, raggruppate per tipo."""
    schede = tuple(features) if features is not None else tuple(iter_features())
    parti: List[str] = ["# Indice delle funzionalita'", ""]
    for kind in Kind:
        gruppo = [f for f in schede if f.kind is kind]
        if not gruppo:
            continue
        parti.append(f"## {_titolo_cartegoria(kind)}")
        parti.append("")
        for feature in gruppo:
            stato = ""
            rimossa = _rimossa_in(feature)
            if rimossa is not None:
                stato = f" (rimossa in {rimossa})"
            elif feature.deprecated is not None:
                stato = f" (deprecata in {feature.deprecated})"
            parti.append(
                f"- `{feature.id}` — {feature.title} — {feature.category}, "
                f"Python {feature.introduced}{stato}"
            )
        parti.append("")
    parti.append(f"Totale: {len(schede)} schede.")
    return "\n".join(parti).rstrip() + "\n"


def render_timeline(releases: Optional[Sequence[Release]] = None) -> str:
    """Restituisce la tabella cronologica dei rilasci in formato Markdown."""
    righe = tuple(releases) if releases is not None else tuple(iter_releases())
    parti = [
        "# Calendario dei rilasci",
        "",
        "| Versione | Rilascio | Stato | Fine supporto |",
        "| --- | --- | --- | --- |",
    ]
    for release in righe:
        fine = release.eol.isoformat() if release.eol else "-"
        stato = str(release.lifecycle)
        if release.version.major == 2:
            stato += " (EOL)"
        parti.append(
            f"| {release.version} | {release.released.isoformat()} | {stato} | {fine} |"
        )
    return "\n".join(parti) + "\n"


def render_version_card(version: Version) -> str:
    """Restituisce la scheda di una versione (``versions/python-X.Y.md``).

    La scheda elenca le novita' per tipo di cambiamento, come richiede
    ``agent.md`` §7, e riporta sempre le fonti ufficiali.

    Raises:
        KeyError: se la versione non e' nel catalogo dei rilasci.
    """
    try:
        release = next(r for r in iter_releases() if r.version == version)
    except StopIteration:
        conosciute = ", ".join(str(r.version) for r in iter_releases())
        raise KeyError(f"nessun rilascio per {version} (noti: {conosciute})") from None
    schede = [f for f in iter_features() if f.introduced == version]
    deprecate = [f for f in iter_features() if f.deprecated == version]
    rimosse = [f for f in iter_features() if f.removed == version]

    titolo = f"# Python {version}"
    if release.last_patch:
        titolo += f" (ultima versione: {release.last_patch})"
    parti: List[str] = [titolo, ""]
    stato = f"Stato al momento della ricerca: **{release.lifecycle}**"
    if release.released:
        stato += f", rilasciata il {release.released.isoformat()}"
    if release.eol:
        stato += f", fine supporto {release.eol.isoformat()}"
    parti.append(stato)
    if release.note:
        parti.append("")
        parti.append(release.note)
    if release.pep:
        parti.append("")
        parti.append(f"Calendario di rilascio: {release.pep}")

    if not schede and not deprecate and not rimosse:
        parti.append("")
        parti.append(
            "Nessuna scheda registrata per questa versione: il catalogo copre le "
            "novita' con impatto sul codice, non l'elenco completo delle modifiche."
        )
    for kind in Kind:
        gruppo = [f for f in schede if f.kind is kind]
        if not gruppo:
            continue
        parti.append("")
        parti.append(f"## {kind}")
        for feature in gruppo:
            titolo_feature = feature.title
            if feature.pep:
                titolo_feature += f" ({feature.pep})"
            parti.append(f"### {titolo_feature}")
            parti.append("")
            parti.append(feature.summary)
            if feature.reason:
                parti.append("")
                parti.append(f"**Perche'**: {feature.reason}")
            if feature.after:
                parti.append("")
                parti.append("```python")
                parti.append(feature.after)
                parti.append("```")
            parti.append("")
            parti.append(f"Fonte: {feature.source}")
            parti.append("")
    for etichetta, gruppo in (
        ("Deprecazioni introdotte", deprecate),
        ("Rimozioni", rimosse),
    ):
        if not gruppo:
            continue
        parti.append("")
        parti.append(f"## {etichetta}")
        parti.append("")
        for feature in gruppo:
            dettaglio = f" (rimossa in {_rimossa_in(feature)})" if _rimossa_in(feature) else ""
            parti.append(f"- {feature.title}{dettaglio} - {feature.source}")
    parti.append("")
    parti.append(f"Fonte del rilascio: {release.source}")
    return "\n".join(parti).rstrip() + "\n"


def render_catalog() -> str:
    """Restituisce l'intero catalogo come un unico documento Markdown."""
    parti: List[str] = []
    for feature in iter_features():
        parti.append(render_feature(feature))
    return "\n".join(parti)


def version_card_names() -> Tuple[str, ...]:
    """Nomi dei file di version card da generare, in ordine di versione."""
    return tuple(f"python-{release.version}.md" for release in iter_releases())


def render_future() -> str:
    """Restituisce la scheda delle versioni non ancora rilasciate.

    Le schede contrassegnate come ``planned`` non descrivono un rilascio ma
    una proposta: PEP e date possono cambiare. Il testo lo dichiara, per non
    presentare come certa un'informazione che non lo e'.
    """
    future = [r for r in iter_releases() if not r.is_released]
    schede = [f for f in iter_features() if f.status == "planned"]
    parti: List[str] = ["# Versioni future", ""]
    if PYTHON4_RELEASED:
        parti.append("Python 4 e' stato rilasciato: aggiornare questa scheda.")
    else:
        parti.append(f"**Python 4 non e' stato rilasciato.** {PYTHON4_NOTE}")
    parti.append("")
    parti.append(
        "Quello che segue e' pianificato, non rilasciato: le date sono quelle "
        "annunciate dal progetto e possono cambiare."
    )
    for release in future:
        parte = ["", f"## Python {release.version}", ""]
        parte.append(f"- stato: **{release.lifecycle}**")
        if release.pep:
            parte.append(f"- calendario: {release.pep}")
        parte.append(f"- fonte: {release.source}")
        if release.note:
            parte.append("")
            parte.append(release.note)
        gruppo = [f for f in schede if f.introduced == release.version]
        if gruppo:
            parte.append("")
            for feature in gruppo:
                titolo = feature.title
                if feature.pep:
                    titolo += f" ({feature.pep})"
                parte.append(f"### {titolo}")
                parte.append("")
                parte.append(feature.summary)
                if feature.reason:
                    parte.append("")
                    parte.append(f"**Perche'**: {feature.reason}")
                parte.append("")
        parti.append("\n".join(parte))
    return "\n".join(parti).rstrip() + "\n"


def write_version_cards(directory: Path) -> List[Path]:
    """Scrive una version card per ogni release e restituisce i file scritti.

    Args:
        directory: cartella di destinazione; viene creata se manca.

    Returns:
        I percorsi dei file scritti, in ordine di versione.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    scritti: List[Path] = []
    for release in iter_releases():
        destinazione = directory / f"python-{release.version}.md"
        contenuto = render_version_card(release.version)
        if destinazione.exists() and destinazione.read_text(encoding="utf-8") == contenuto:
            continue
        destinazione.write_text(contenuto, encoding="utf-8", newline="\n")
        scritti.append(destinazione)
    return scritti


def write_future_card(directory: Path) -> Path:
    """Scrive ``versions/future.md`` e restituisce il percorso."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destinazione = directory / "future.md"
    contenuto = render_future()
    if not destinazione.exists() or destinazione.read_text(encoding="utf-8") != contenuto:
        destinazione.write_text(contenuto, encoding="utf-8", newline="\n")
    return destinazione
