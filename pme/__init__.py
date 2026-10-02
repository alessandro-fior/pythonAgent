"""Documentazione dell'evoluzione di Python, dalla versione 2 a oggi.

Questo pacchetto e' la parte eseguibile del progetto: mette in codice le
risposte che ``agent.md`` chiede di documentare.

    "Da quale epoca arriva?"
        :mod:`pme.legacy` analizza codice reale e restituisce, per ogni
        costrutto, la versione che l'ha introdotto o rimossa.
    "Quali problemi di compatibilita' presenta?"
        Lo stesso modulo classifica ogni ritrovamento per gravita'.
    "Come lo trasformo in Python moderno?"
        :func:`pme.legacy.modernize` applica le riscritture deterministiche.
    "Quale versione minima di Python devo utilizzare?"
        :func:`pme.legacy.minimum_version` calcola il requisito.

Il contenuto documentale vive in moduli di sola lettura:

* :mod:`pme.version` elenca le release e il loro stato di supporto (PEP 602);
* :mod:`pme.features` e' il catalogo delle funzionalita', con la versione che
  le ha introdotte e il codice "prima" e "dopo";
* :mod:`pme.probes` contiene le sonde sintattiche che verificano quali
  costrutti l'interprete corrente supporta;
* :mod:`pme.demos` contiene programmi completi, con il risultato atteso, che
  dimostrano le novita' principali di ogni versione;
* :mod:`pme.runtime` fotografa l'interprete in esecuzione;
* :mod:`pme.report` trasforma i dati in Markdown e :mod:`pme.cli` li espone da
  terminale (``python -m pme``).

Le dimostrazioni si eseguono e verificano il proprio risultato: se una scheda
promette ``('click', 3, 4)`` e il codice produce altro, la suite di test lo
segnala. E' il motivo per cui gli esempi vivono in stringhe e non in file
importati.

Uso rapido::

    >>> from pme import latest_stable, introduced_in, Version
    >>> latest_stable().version
    Version(major=3, minor=14)
    >>> Version.parse("3.10") > Version.parse("3.9")
    True
    >>> [f.id for f in introduced_in(Version(3, 10))][:2]
    ['pattern-matching', 'union-types']

Ogni dato ha una fonte ufficiale registrata nel campo ``source`` della scheda
corrispondente. Quando una fonte non e' verificabile, la scheda lo dichiara
invece di presentare il dato come certo.
"""

from __future__ import annotations

from pme.features import (
    Category,
    Feature,
    by_id,
    changed_between,
    deprecated_in,
    introduced_in,
    iter_features,
    removed_in,
    requires,
    topical_index,
)
from pme.legacy import (
    Finding,
    ModernizeResult,
    Severity,
    detect,
    minimum_version,
    modernize,
)
from pme.probes import SyntaxProbe, get_probe, probe_syntax, supported_ids
from pme.runtime import RuntimeInfo, require, runtime_info, supports
from pme.version import (
    PYTHON4_NOTE,
    PYTHON4_RELEASED,
    Lifecycle,
    Release,
    Version,
    by_version,
    current_runtime_version,
    iter_releases,
    latest_stable,
    next_version,
    supported_releases,
)

__all__ = [
    "Category",
    "Feature",
    "Finding",
    "Lifecycle",
    "ModernizeResult",
    "PYTHON4_NOTE",
    "PYTHON4_RELEASED",
    "Release",
    "RuntimeInfo",
    "Severity",
    "SyntaxProbe",
    "Version",
    "by_id",
    "by_version",
    "changed_between",
    "current_runtime_version",
    "deprecated_in",
    "detect",
    "get_probe",
    "introduced_in",
    "iter_features",
    "iter_releases",
    "latest_stable",
    "minimum_version",
    "modernize",
    "next_version",
    "probe_syntax",
    "removed_in",
    "require",
    "requires",
    "runtime_info",
    "supported_ids",
    "supported_releases",
    "supports",
    "topical_index",
]

__version__ = "0.1.0"