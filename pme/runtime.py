"""Rilevamento delle capacita' dell'interprete reale.

Questo modulo risponde a una domanda che tutto il progetto si pone: *"posso
eseguire questo codice qui?"*. Invece di fidarsi di ``sys.version_info`` da solo,
:class:`RuntimeInfo` incrocia:

* la versione dichiarata (``sys.version_info``);
* l'implementazione (``CPython``, ``PyPy``, ...);
* i *capabilities* opzionali (free-threading, JIT, ``t-strings``, ...), che esistono
  gia' in versioni diverse a seconda che siano abilitate o meno in compilazione;
* le capacita' **sintattiche**, che dipendono dal parser e non dalla versione.

Le capacita' sintattiche sono il punto delicato: ``match`` richiede un parser
PEG, quindi non basta confrontare ``3.10 <= sys.version_info``. :func:`supports`
di :mod:`pme.probes` risolve il problema chiedendo al parser corrente di
compilare un frammento minimale.

Esempio::

    >>> from pme.runtime import runtime_info
    >>> runtime_info.version.major
    3
    >>> runtime_info.version_string.startswith("3.")
    True
    >>> runtime_info.supports_version("3.0")
    True
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from pme.probes import SyntaxProbe, probe_syntax
from pme.version import Version, current_runtime_version

__all__ = [
    "RuntimeInfo",
    "runtime_info",
    "require",
    "supports",
    "syntax_support",
]


@dataclass(frozen=True)
class RuntimeInfo:
    """Fotografia completa dell'interprete in esecuzione.

    Attributi come :attr:`syntax` e :attr:`capabilities` sono mappe di sola
    lettura: sono calcolate una volta e non vanno modificate dagli esempi.
    """

    implementation: str
    version: Version
    version_string: str
    releaselevel: str
    gil_enabled: bool
    jit_available: bool
    sys_builtin_module_names: frozenset[str]
    syntax: Mapping[str, bool]
    capabilities: Mapping[str, bool]

    def supports_version(self, minimum: Version | str) -> bool:
        """``True`` se l'interprete e' almeno ``minimum``.

        E' un controllo *solo di versione*: non tiene conto delle capacita'
        opzionali. Per una verifica completa usare :func:`pme.runtime.supports`.
        """
        return self.version >= Version.parse(str(minimum))

    def as_table(self) -> Mapping[str, str]:
        """Restituisce le informazioni come mappa stringa/stringa, per la CLI."""
        data = {
            "implementazione": self.implementation,
            "versione": self.version_string,
            "releaselevel": self.releaselevel,
            "free-threaded": "no" if self.gil_enabled else "si' (PEP 703)",
            "jit": "disponibile" if self.jit_available else "non disponibile",
            "piattaforma": platform.platform(terse=True),
        }
        data["sintassi supportate"] = ", ".join(
            name for name, ok in sorted(self.syntax.items()) if ok
        ) or "nessuna rilevata"
        return MappingProxyType(data)

    def missing_version_requirements(self, minimum: Version | str) -> tuple[str, ...]:
        """Elenca le funzionalita' richieste da ``minimum`` ma mancanti qui."""
        required = Version.parse(str(minimum))
        missing = []
        for probe in probe_syntax():
            if probe.since > self.version or probe.since <= required:
                continue
            if not self.syntax.get(probe.id, False):
                missing.append(probe.id)
        return tuple(missing)


def _detect_gil() -> bool:
    """Rileva se il GIL e' attivo.

    Le build "free-threaded" di CPython 3.13+ (PEP 703) espongono
    ``sys._is_gil_enabled``; se l'attributo non esiste il GIL e' attivo.
    """
    probe = getattr(sys, "_is_gil_enabled", None)
    if probe is None:
        return True
    return bool(probe())


def _detect_jit() -> bool:
    """Rileva la presenza del JIT sperimentale (PEP 744, Python 3.13+)."""
    return hasattr(sys, "_jit")


def _detect_capabilities() -> Mapping[str, bool]:
    """Rileva le capacita' *non sintattiche*, cioe' dipendenti dalla build.

    Le voci sono dichiarate qui invece che nel catalogo perche' la loro
    presenza dipende da come e' stato compilato l'interprete, non dalla versione.
    """
    checks = {
        "t-string (PEP 750)": _has_templatelib,
        "compression.zstd (PEP 784)": lambda: _module_exists("compression.zstd"),
        "concurrent.interpreters (PEP 734)": lambda: _module_exists("concurrent.interpreters"),
        "annotationlib (PEP 649)": lambda: _module_exists("annotationlib"),
        "tomllib (PEP 680)": lambda: _module_exists("tomllib"),
        "zoneinfo (PEP 615)": lambda: _module_exists("zoneinfo"),
        "math.prod (3.8)": lambda: hasattr(_lazy("math"), "prod"),
        "functools.cache (3.9)": lambda: hasattr(_lazy("functools"), "cache"),
        "itertools.batched (3.12)": lambda: hasattr(_lazy("itertools"), "batched"),
    }
    return MappingProxyType({name: bool(check()) for name, check in checks.items()})


def _lazy(module_name: str):
    """Importa un modulo standard, restituendo ``None`` se assente."""
    try:
        __import__(module_name)
    except ImportError:
        return None
    return sys.modules[module_name]


def _module_exists(dotted: str) -> bool:
    """``True`` se il modulo indicato e' importabile.

    Serve per distinguere "non esiste in questa versione" da "esiste ma non e'
    compilato", condizioni che danno comportamenti diversi per l'utente.
    """
    try:
        __import__(dotted)
    except ImportError:
        return False
    return True


def _has_templatelib() -> bool:
    """``True`` se le t-string sono disponibili (``string.templatelib``, 3.14+)."""
    return _module_exists("string.templatelib")


def _build_runtime_info() -> RuntimeInfo:
    """Costruisce :class:`RuntimeInfo` interrogando l'interprete corrente."""
    version = current_runtime_version()
    return RuntimeInfo(
        implementation=platform.python_implementation(),
        version=version,
        version_string=platform.python_version(),
        releaselevel=sys.version_info.releaselevel,
        gil_enabled=_detect_gil(),
        jit_available=_detect_jit(),
        sys_builtin_module_names=frozenset(getattr(sys, "builtin_module_names", ())),
        syntax=MappingProxyType({p.id: p.available() for p in probe_syntax()}),
        capabilities=_detect_capabilities(),
    )


#: Istanza unica, calcolata all'import del modulo.
runtime_info: RuntimeInfo = _build_runtime_info()


def supports(minimum: Version | str) -> bool:
    """``True`` se l'interprete corrente puo' eseguire codice di ``minimum``.

    Combina due controlli: la versione deve essere sufficiente *e* ogni
    funzionalita' sintattica introdotta dopo ``minimum`` deve essere gia'
    supportata. Il secondo controllo e' quello che salva le build particolari:
    per esempio CPython 3.10 compilato senza parser PEG non accetterebbe
    ``match``, pur avendo la versione dichiarata sufficiente.

    Args:
        minimum: versione minima richiesta, come ``Version`` o testo.

    Returns:
        ``True`` se il codice puo' essere eseguito qui.

    Example:
        >>> supports("3.10") <= supports("3.11")
        True
    """
    return runtime_info.supports_version(minimum) and not runtime_info.missing_version_requirements(
        minimum
    )


def require(minimum: Version | str) -> None:
    """Solleva ``RuntimeError`` se l'interprete non soddisfa ``minimum``.

    Pensata per la guardia all'inizio degli esempi: fallisce subito e con un
    messaggio utile invece di produrre un ``SyntaxError`` piu' a valle.

    Raises:
        RuntimeError: se la versione o le capacita' non bastano.

    Example:
        >>> require("3.0")  # non solleva su un interprete 3.x
    """
    if supports(minimum):
        return
    missing = runtime_info.missing_version_requirements(minimum)
    detail = f"; capacita' mancanti: {', '.join(missing)}" if missing else ""
    raise RuntimeError(
        f"questo esempio richiede Python {Version.parse(str(minimum))} o successivo, "
        f"l'interprete in esecuzione e' Python {runtime_info.version}{detail}"
    )


def syntax_support() -> Mapping[str, SyntaxProbe]:
    """Restituisce le sonde sintattiche indicizzate per identificativo."""
    return MappingProxyType({probe.id: probe for probe in probe_syntax()})