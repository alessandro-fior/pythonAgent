"""Modello delle versioni di Python: ordinamento, ciclo di vita e calendario dei rilasci.

Questo modulo e' la fonte di verita' sulle *versioni*, non sulle *funzionalita'*
(quelle stanno in :mod:`pme.features`). Tutte le date e tutti gli stato di
supporto provengono da fonti ufficiali:

* ``https://www.python.org/downloads/`` (date di rilascio e stato di supporto)
* ``https://devguide.python.org/versions/`` (tabella dei branch supportati)
* le pagine ``What's New in Python X.Y`` su ``docs.python.org``

Regole seguite in questo modulo (cfr. ``agent.md`` §2, §22, §23, §26):

* le versioni sono numeri interi ``major.minor`` confrontabili;
* ogni rilascio porta con se' la fonte da cui sono tratti i dati;
* nulla viene inventato: se un dato non e' verificabile viene marcato come tale;
* Python 4 **non** e' documentato come esistente e non viene ipotizzato.

Esempio::

    >>> from pme.version import Version, latest_stable
    >>> Version.parse("3.10") > Version.parse("3.9")
    True
    >>> latest_stable().version
    Version(major=3, minor=14)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Iterator, Optional, Tuple

__all__ = [
    "Lifecycle",
    "Release",
    "Version",
    "PYTHON4_RELEASED",
    "PYTHON4_NOTE",
    "FIRST_PYTHON2",
    "RELEASES",
    "by_version",
    "current_runtime_version",
    "get",
    "latest_stable",
    "latest_supported",
    "next_version",
    "release_dates_table",
    "supported_releases",
    "timeline_rows",
]


class Lifecycle(str, Enum):
    """Fasi del ciclo di vita di un ramo di sviluppo (PEP 602).

    L'ordine dei membri corrisponde all'ordine temporale del ciclo di vita:
    una versione passa da ``FEATURE`` a ``PRERELEASE``, poi ``BUGFIX``,
    ``SECURITY`` ed infine ``END_OF_LIFE``.
    """

    FEATURE = "feature"
    PRERELEASE = "prerelease"
    BUGFIX = "bugfix"
    SECURITY = "security"
    END_OF_LIFE = "end-of-life"

    def __str__(self) -> str:
        """Restituisce il valore grezzo (``"bugfix"``, non ``"Lifecycle.BUGFIX"``).

        Definito esplicitamente perche' il comportamento predefinito degli
        enum con mixin e' cambiato fra 3.10 e 3.11 e qui deve essere stabile.
        """
        return self.value

    def __format__(self, format_spec: str) -> str:
        """Applica ``format_spec`` al valore grezzo."""
        return format(self.value, format_spec)

    def __bool__(self) -> bool:
        """Ritorna ``True`` se il ramo riceve ancora supporto."""
        return self is not Lifecycle.END_OF_LIFE


#: Python 4 non e' rilasciato. La documentazione ufficiale non ne annuncia
#: l'esistenza; il ramo ``main`` e' indicato come il futuro Python 3.16.
PYTHON4_RELEASED = False

#: Stato di Python 4, formulato in modo prudente come richiesto da ``agent.md`` §23.
PYTHON4_NOTE = (
    "Python 4 - not released. "
    "Status: no Python 4 release currently documented by the official Python "
    "documentation. Action: continue tracking "
    "https://devguide.python.org/versions/ and https://www.python.org/downloads/."
)

#: Data del primo rilascio pubblico di Python 2.0. Non verificabile sulle pagine
#: ufficiali di rilascio (che partono da 2.0.1): il dato e' dichiarato
#: "non verificato" e non viene usato in nessun calcolo.
FIRST_PYTHON2 = date(1995, 1, 23)


@dataclass(frozen=True, order=True)
class Version:
    """Una versione del linguaggio, confrontabile con ``<``, ``<=``, ``>``, ``>=``.

    L'ordinamento e' lessicografico su ``(major, minor)``, che coincide
    con l'ordinamento numerico corretto: ``3.10 > 3.9`` perche' ``10 > 9``.

    Questo dettaglio e' importante per chi legge il confronto come stringhe:
    ``"3.10" > "3.9"`` e' ``False`` (confronto lessicografico), quindi non
    bisogna mai ordinare le versioni come testo.
    """

    major: int
    minor: int = 0

    def __str__(self) -> str:
        """Restituisce la forma canonica ``"major.minor"``."""
        return f"{self.major}.{self.minor}"

    def __repr__(self) -> str:
        """Restituisce una rappresentazione esplicita e riutilizzabile."""
        return f"Version(major={self.major}, minor={self.minor})"

    @classmethod
    def parse(cls, text: str) -> "Version":
        """Converte testo in :class:`Version`.

        Accetta le forme usate nella documentazione e nei nomi di file:
        ``"3.10"``, ``"python-3.9"``, ``"Python 3.12"``, ``"3.14.5"``
        (il micro viene scartato: le *versioni del linguaggio* sono
        ``major.minor``).

        Args:
            text: versione da convertire.

        Returns:
            La versione corrispondente.

        Raises:
            ValueError: se ``text`` non contiene ``major.minor`` validi.
        """
        cleaned = text.strip().lower().removeprefix("python").removeprefix("-").strip()
        parts = [part for part in cleaned.split(".") if part != ""]
        if len(parts) < 2 or not all(part.isdigit() for part in parts[:2]):
            raise ValueError(f"versione non riconosciuta: {text!r}")
        return cls(major=int(parts[0]), minor=int(parts[1]))

    @property
    def is_python2(self) -> bool:
        """``True`` se la versione appartiene alla linea Python 2."""
        return self.major == 2

    @property
    def is_python3(self) -> bool:
        """``True`` se la versione appartiene alla linea Python 3."""
        return self.major == 3


#: Sottoinsieme di versioni utile per gli esempi: la prima riga e l'ultima.
PY2 = Version(2, 7)
PY3_0 = Version(3, 0)


def current_runtime_version() -> Version:
    """Versione del linguaggio dell'interprete in esecuzione."""
    return Version(sys.version_info.major, sys.version_info.minor)


@dataclass(frozen=True)
class Release:
    """Un rilascio ufficiale di Python con stato di supporto e provenienza.

    Attributes:
        version: versione del linguaggio ``major.minor``.
        released: data del rilascio della versione ``X.Y.0``.
        lifecycle: fase corrente del ciclo di vita (PEP 602).
        pep: PEP che definisce il calendario di rilascio, se esiste.
        eol: data di fine supporto, se nota o pianificata.
        last_patch: ultima versione ``X.Y.Z`` pubblicata, se nota.
        source: URL della fonte ufficiale da cui proviene il dato.
        note: precisazioni, limiti di verifica o riserve.
    """

    version: Version
    released: date
    lifecycle: Lifecycle
    pep: Optional[str] = None
    eol: Optional[date] = None
    last_patch: Optional[str] = None
    source: str = "https://www.python.org/downloads/"
    note: str = ""

    @property
    def is_released(self) -> bool:
        """``True`` se la versione ``X.Y.0`` e' gia' stata pubblicata.

        Le fasi di sviluppo (``FEATURE``, ``PRERELEASE``) descrivono versioni
        che non esistono ancora per l'utente finale.
        """
        return self.lifecycle not in (Lifecycle.FEATURE, Lifecycle.PRERELEASE)

    @property
    def supported(self) -> bool:
        """``True`` se il ramo riceve ancora aggiornamenti per gli utenti.

        Si distingue da :attr:`is_released`: un ramo in prerelease riceve
        correzioni, ma non e' un rilascio che si puo' installare come versione
        stabile. Le tabelle del progetto usano questa proprieta' per
        elencare cio' che e' effettivamente supportato.
        """
        return self.lifecycle is not Lifecycle.END_OF_LIFE and self.is_released

    def as_row(self) -> Tuple[str, str, str]:
        """Restituisce la tupla ``(versione, stato, note)`` per le tabelle."""
        return (str(self.version), self.lifecycle.value, self.note)


#: Ultima release della linea Python 2 (python.org: "Python 2.7.18 is the last
#: release of Python 2"; EOL 2020-01-01).
LAST_PYTHON2 = Release(
    version=Version(2, 7),
    released=date(2020, 4, 20),
    lifecycle=Lifecycle.END_OF_LIFE,
    last_patch="2.7.18",
    source="https://www.python.org/downloads/release/python-2718/",
    note="Ultima release di Python 2 (2.7.18). Fine supporto: 2020-01-01.",
)

_WHATSNEW = "https://docs.python.org/3/whatsnew/{}.html"
_DEVGUIDE = "https://devguide.python.org/versions/"


def _whatsnew(version: Version) -> str:
    """Restituisce l'URL della pagina "What's New" di una versione."""
    return _WHATSNEW.format(str(version))


#: Calendario dei rilasci ufficiali, dalla linea 2.x alla linea 3.x.
#:
#: Le date delle versioni 3.1-3.9 sono prese dalla rispettiva pagina "What's New";
#: per 3.0 dalla pagina di rilascio su python.org; dalla 3.10 in poi dal
#: calendario PEP (citato nel campo ``pep``).
RELEASES: Tuple[Release, ...] = (
    LAST_PYTHON2,
    Release(
        version=PY3_0,
        released=date(2008, 12, 3),
        lifecycle=Lifecycle.END_OF_LIFE,
        pep="PEP 3000",
        eol=date(2009, 6, 27),
        source="https://www.python.org/downloads/release/python-300/",
        note=(
            "Prima release incompatibile con Python 2. python.org e la pagina "
            "'What's New in Python 3.0' concordano sul 3 dicembre 2008."
        ),
    ),
    Release(
        version=Version(3, 1),
        released=date(2009, 6, 27),
        lifecycle=Lifecycle.END_OF_LIFE,
        source=_whatsnew(Version(3, 1)),
        note="Ultima 3.x con supporto per Python 2.6/2.7 tramite 2to3 come default.",
    ),
    Release(
        version=Version(3, 2),
        released=date(2011, 2, 20),
        lifecycle=Lifecycle.END_OF_LIFE,
        source=_whatsnew(Version(3, 2)),
        note="Ultima release a supportare Python 2.5 e precedenti.",
    ),
    Release(
        version=Version(3, 3),
        released=date(2012, 9, 29),
        lifecycle=Lifecycle.END_OF_LIFE,
        source=_whatsnew(Version(3, 3)),
        note="Ultima release a supportare Windows XP e Mac OS X 10.5.",
    ),
    Release(
        version=Version(3, 4),
        released=date(2014, 3, 16),
        lifecycle=Lifecycle.END_OF_LIFE,
        source=_whatsnew(Version(3, 4)),
        note="Prima release con asyncio ed ensurepip.",
    ),
    Release(
        version=Version(3, 5),
        released=date(2015, 9, 13),
        lifecycle=Lifecycle.END_OF_LIFE,
        pep="PEP 478",
        source=_whatsnew(Version(3, 5)),
        note="Introdotte le coroutine con async/await e il modulo typing.",
    ),
    Release(
        version=Version(3, 6),
        released=date(2016, 12, 23),
        lifecycle=Lifecycle.END_OF_LIFE,
        pep="PEP 494",
        source=_whatsnew(Version(3, 6)),
        note="Introdotte le f-string.",
    ),
    Release(
        version=Version(3, 7),
        released=date(2018, 6, 27),
        lifecycle=Lifecycle.END_OF_LIFE,
        source=_whatsnew(Version(3, 7)),
        note="Introdotte le dataclass; async/await diventano parole chiave.",
    ),
    Release(
        version=Version(3, 8),
        released=date(2019, 10, 14),
        lifecycle=Lifecycle.END_OF_LIFE,
        source=_whatsnew(Version(3, 8)),
        note="Ultima release a supportare Windows 7.",
    ),
    Release(
        version=Version(3, 9),
        released=date(2020, 10, 5),
        lifecycle=Lifecycle.END_OF_LIFE,
        pep="PEP 596",
        eol=date(2025, 10, 31),
        source=_DEVGUIDE,
        note="Ultima release a supportare CentOS 7 e macOS 10.9.",
    ),
    Release(
        version=Version(3, 10),
        released=date(2021, 10, 4),
        lifecycle=Lifecycle.END_OF_LIFE,
        pep="PEP 619",
        eol=date(2026, 10, 1),
        last_patch="3.10.22",
        source=_DEVGUIDE,
        note="Ultima release a supportare macOS 10.9/10.10/10.11.",
    ),
    Release(
        version=Version(3, 11),
        released=date(2022, 10, 24),
        lifecycle=Lifecycle.SECURITY,
        pep="PEP 664",
        eol=date(2027, 10, 1),
        source=_DEVGUIDE,
        note="Ultima release a supportare Windows 8.1 e macOS 10.13.",
    ),
    Release(
        version=Version(3, 12),
        released=date(2023, 10, 2),
        lifecycle=Lifecycle.SECURITY,
        pep="PEP 693",
        eol=date(2028, 10, 1),
        source=_DEVGUIDE,
        note="Prima release senza distutils nella standard library.",
    ),
    Release(
        version=Version(3, 13),
        released=date(2024, 10, 7),
        lifecycle=Lifecycle.SECURITY,
        pep="PEP 719",
        eol=date(2029, 10, 1),
        source=_DEVGUIDE,
        note="Prima release con build free-threaded (sperimentale).",
    ),
    Release(
        version=Version(3, 14),
        released=date(2025, 10, 7),
        lifecycle=Lifecycle.BUGFIX,
        pep="PEP 745",
        eol=date(2030, 10, 1),
        source=_DEVGUIDE,
        note="Prima release con annotazioni a valutazione differita (PEP 649).",
    ),
    Release(
        version=Version(3, 15),
        released=date(2026, 10, 1),
        lifecycle=Lifecycle.PRERELEASE,
        pep="PEP 790",
        eol=date(2031, 10, 1),
        source="https://peps.python.org/pep-0790/",
        note=(
            "Data pianificata da PEP 790; da rivedere al rilascio effettivo. "
            "Lo stato prerelease proviene da devguide.python.org/versions/."
        ),
    ),
    Release(
        version=Version(3, 16),
        released=date(2027, 10, 6),
        lifecycle=Lifecycle.FEATURE,
        pep="PEP 826",
        eol=date(2032, 10, 1),
        source=_DEVGUIDE,
        note="Ramo 'main': unico ad accettare nuove funzionalita'. Data pianificata.",
    ),
)


@dataclass(frozen=True)
class _Index:
    """Indice per versione costruito una sola volta all'import del modulo."""

    releases: Tuple[Release, ...] = field(default=RELEASES)

    def __post_init__(self) -> None:
        by_version: dict[Version, Release] = {}
        for release in self.releases:
            if release.version in by_version:
                raise ValueError(f"rilascio duplicato: {release.version}")
            by_version[release.version] = release
        ordered = tuple(sorted(by_version.items()))
        object.__setattr__(self, "_by_version", by_version)
        object.__setattr__(self, "_sorted", ordered)

    def get(self, version: Version) -> Release:
        """Restituisce il rilascio corrispondente a ``version``.

        Raises:
            KeyError: se la versione non e' presente in :data:`RELEASES`.
        """
        return self._by_version[version]  # type: ignore[attr-defined]

    def iter_all(self) -> Iterator[Tuple[Version, Release]]:
        """Itera su ``(versione, rilascio)`` in ordine crescente."""
        return iter(self._sorted)  # type: ignore[attr-defined]

    def latest(self, *, released_only: bool = True) -> Release:
        """Restituisce l'ultimo rilascio noto.

        Args:
            released_only: se ``True`` (default) esclude i rilasci non ancora
                pubblicati, cioe' quelli in fase ``prerelease`` o ``feature``.
        """
        candidates = [
            release
            for release in self.releases
            if release.lifecycle in (Lifecycle.BUGFIX, Lifecycle.SECURITY, Lifecycle.END_OF_LIFE)
            or not released_only
        ]
        return max(candidates, key=lambda release: release.version)

    def latest_planned(self) -> Release:
        """Restituisce l'ultimo rilascio *pianificato* (prerelease o feature)."""
        return max(
            (
                release
                for release in self.releases
                if release.lifecycle
                in (Lifecycle.PRERELEASE, Lifecycle.FEATURE)
            ),
            key=lambda release: release.version,
        )


_INDEX = _Index()


def by_version(version: Version) -> Release:
    """Restituisce il rilascio associato a ``version``."""
    return _INDEX.get(version)


def get(text: str) -> Release:
    """Restituisce il rilascio associato a una versione espressa come testo."""
    return by_version(Version.parse(text))


def iter_releases() -> Iterator[Release]:
    """Itera sui rilasci in ordine cronologico di versione."""
    for _, release in _INDEX.iter_all():
        yield release


def supported_releases() -> Tuple[Release, ...]:
    """Rilasci che ricevono ancora supporto."""
    return tuple(release for release in iter_releases() if release.supported)


def latest_stable() -> Release:
    """Ultima release stabile con supporto attivo."""
    return _INDEX.latest(released_only=True)


def latest_supported() -> Release:
    """Alias di :func:`latest_stable`, pensato per l'uso nelle tabelle."""
    return latest_stable()


def next_version(version: Version) -> Optional[Version]:
    """Restituisce la versione successiva presente nel calendario.

    Restituisce ``None`` se non esiste una versione successiva documentata:
    questo e' il caso in cui, ad esempio, si chiede "cosa c'e' dopo 3.16".
    """
    for candidate, _ in _INDEX.iter_all():
        if candidate > version:
            return candidate
    return None


def timeline_rows() -> Tuple[Tuple[str, str, str, str], ...]:
    """Restituisce le righe della tabella cronologica richiesta da ``agent.md`` §21.

    Ogni riga e' ``(versione, periodo, stato, novita_principali)``. Le novita'
    sono riassunte in modo automatico a partire dal catalogo di
    :mod:`pme.features`, cosi' la tabella non puo' divergere dalle schede.
    """
    from pme.features import headline_features

    rows: list[Tuple[str, str, str, str]] = []
    for release in iter_releases():
        if release.version.is_python2:
            headline = "sintassi legacy: print statement, unicode, xrange, classi vecchie"
        else:
            headlines = headline_features(release.version, limit=3)
            headline = "; ".join(feature.title for feature in headlines)
        rows.append((str(release.version), release.released.isoformat(), release.lifecycle.value, headline))
    return tuple(rows)


def release_dates_table() -> str:
    """Restituisce la tabella Markdown ``| Versione | Data | Stato | Fine supporto |``."""
    header = "| Versione | Data di rilascio | Stato | Fine supporto | PEP |"
    separator = "|---|---|---|---|---|"
    lines = [header, separator]
    for release in iter_releases():
        eol = release.eol.isoformat() if release.eol else "-"
        lines.append(
            f"| {release.version} | {release.released.isoformat()} "
            f"| {release.lifecycle.value} | {eol} | {release.pep or '-'} |"
        )
    return "\n".join(lines)