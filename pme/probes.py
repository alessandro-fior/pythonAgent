"""Sonde sintattiche: verificare se il *parser corrente* accetta un costrutto.

Il motivo di questo modulo e' che la versione dichiarata non basta. ``match``
richiede il parser PEG introdotto con Python 3.10, ma anche 3.10 puo' essere
compilato in un modo che non lo supporta; i generatori asincroni hanno
restrizioni grammaticali che sono cambiate piu' volte fra 3.5 e 3.6; le t-string
richiedono 3.14 *e* una compilazione senza flag restrittivi.

La tecnica e' semplice e affidabile: si chiede a ``compile()`` di compilare un
frammento minimale e si considera il costrutto supportato se la compilazione
riusce. Non si esegue nulla, quindi non c'e' rischio di effetti collaterali.

Una conseguenza utile: questo permette di scrivere esempi che dimostrano la
sintassi di *qualsiasi* versione dentro file che restano analizzabili dalla
versione in esecuzione, chiamando ``compile()`` sul sorgente solo al momento
giusto. E' la tecnica usata da :mod:`pme.demos`.

Esempio::

    >>> from pme.probes import probe_syntax
    >>> probe = next(p for p in probe_syntax() if p.id == "walrus")
    >>> probe.since
    Version(major=3, minor=8)
    >>> isinstance(probe.available(), bool)
    True
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, Optional, Tuple

from pme.version import Version

__all__ = ["SyntaxProbe", "PROBES", "probe_syntax", "get_probe", "supported_ids"]


@dataclass(frozen=True)
class SyntaxProbe:
    """Una sonda che verifica il supporto di un costrutto sintattico.

    Attributes:
        id: identificativo stabile della sonda (usato anche dalla CLI).
        since: versione che ha introdotto il costrutto.
        source: frammento minimo, sintatticamente valido solo da ``since``.
        description: descrizione in italiano del costrutto.
        pep: PEP di riferimento, se esiste.
        feature_id: identificativo della funzionalita' corrispondente nel
            catalogo :mod:`pme.features`, se presente.
    """

    id: str
    since: Version
    source: str
    description: str
    pep: Optional[str] = None
    feature_id: Optional[str] = None

    def available(self) -> bool:
        """``True`` se il parser corrente compila il frammento.

        Qualsiasi ``BaseException`` viene trattata come "non supportato": oltre
        a :class:`SyntaxError`, un compilatore puo' sollevare anche
        :class:`MemoryError` o errori interni su frammenti enormi, e in tutti
        questi casi la risposta utile resta "non lo so usare".
        """
        try:
            compile(self.source, f"<pme.probe:{self.id}>", "exec")
        except BaseException:  # noqa: BLE001 - la sonda non deve mai propagare
            return False
        return True


#: Sonde in ordine di introduzione. L'ordine e' quello del catalogo
#: :mod:`pme.features`, non quello alfabetico.
PROBES: Tuple[SyntaxProbe, ...] = (
    SyntaxProbe(
        id="print-function",
        since=Version(3, 0),
        source="print('x', end='')",
        description="print() come funzione",
        pep="PEP 3105",
        feature_id="print-function",
    ),
    SyntaxProbe(
        id="nonlocal",
        since=Version(3, 0),
        source="def f():\n    x = 1\n    def g():\n        nonlocal x\n        x = 2\n    g()",
        description="istruzione nonlocal",
        pep="PEP 3104",
        feature_id="nonlocal",
    ),
    SyntaxProbe(
        id="exception-chaining",
        since=Version(3, 0),
        source="try:\n    pass\nexcept ValueError as exc:\n    raise RuntimeError from exc",
        description="raise ... from (concatenamento di eccezioni)",
        pep="PEP 3134",
        feature_id="exception-chaining",
    ),
    SyntaxProbe(
        id="keyword-only-args",
        since=Version(3, 0),
        source="def f(a, *, b):\n    return a, b",
        description="argomenti keyword-only",
        pep="PEP 3102",
        feature_id="keyword-only-args",
    ),
    SyntaxProbe(
        id="yield-from",
        since=Version(3, 3),
        source="def a():\n    yield 1\n\ndef b():\n    yield from a()",
        description="yield from (delegazione a subgeneratore)",
        pep="PEP 380",
        feature_id="yield-from",
    ),
    SyntaxProbe(
        id="async-await",
        since=Version(3, 5),
        source="async def f():\n    return 1",
        description="coroutine con async def",
        pep="PEP 492",
        feature_id="async-await",
    ),
    SyntaxProbe(
        id="async-generator",
        since=Version(3, 6),
        source="async def f():\n    yield 1",
        description="generatori asincroni (yield dentro async def)",
        pep="PEP 525",
        feature_id="async-generators",
    ),
    SyntaxProbe(
        id="async-comprehension",
        since=Version(3, 6),
        source="async def f():\n    return [x async for x in f()]",
        description="comprensioni asincrone",
        pep="PEP 530",
        feature_id="async-comprehensions",
    ),
    SyntaxProbe(
        id="f-string",
        since=Version(3, 6),
        source="x = 1\nf'x={x}'",
        description="f-string (stringhe formattate)",
        pep="PEP 498",
        feature_id="f-string",
    ),
    SyntaxProbe(
        id="variable-annotation",
        since=Version(3, 6),
        source="x: int = 1",
        description="annotazioni di variabile",
        pep="PEP 526",
        feature_id="variable-annotations",
    ),
    SyntaxProbe(
        id="walrus",
        since=Version(3, 8),
        source="if (n := 10) > 5:\n    pass",
        description="operatore walrus (:=)",
        pep="PEP 572",
        feature_id="walrus",
    ),
    SyntaxProbe(
        id="positional-only",
        since=Version(3, 8),
        source="def f(a, /, b):\n    return a, b",
        description="parametri positional-only con /",
        pep="PEP 570",
        feature_id="positional-only",
    ),
    SyntaxProbe(
        id="f-string-debug",
        since=Version(3, 8),
        source="x = 1\nf'{x=}'",
        description="specificatore = nelle f-string",
        pep=None,
        feature_id="f-string-debug",
    ),
    SyntaxProbe(
        id="builtin-generics",
        since=Version(3, 9),
        source="def f(x: list[str]) -> dict[str, int]:\n    return {}",
        description="generics delle raccolte standard (PEP 585)",
        pep="PEP 585",
        feature_id="builtin-generics",
    ),
    SyntaxProbe(
        id="dict-union",
        since=Version(3, 9),
        source="a = {'x': 1}\nb = a | {'y': 2}",
        description="unione di dizionari con |",
        pep="PEP 584",
        feature_id="dict-union",
    ),
    SyntaxProbe(
        id="pattern-matching",
        since=Version(3, 10),
        source="def f(c):\n    match c:\n        case {'k': v}:\n            return v\n        case [a, *rest]:\n            return rest\n        case str() as s:\n            return s\n        case _:\n            return None",
        description="structural pattern matching (match/case)",
        pep="PEP 634",
        feature_id="pattern-matching",
    ),
    SyntaxProbe(
        id="union-type",
        since=Version(3, 10),
        source="def f(x: int | str) -> None:\n    pass\nassert isinstance(1, int | str)",
        description="unioni di tipo con | (PEP 604)",
        pep="PEP 604",
        feature_id="union-types",
    ),
    SyntaxProbe(
        id="except-star",
        since=Version(3, 11),
        # Nota: dentro un blocco except* non sono ammessi `return`, `break` e
        # `continue`. Per questo la sonda assegna invece di restituire: e' una
        # delle trappole piu' frequenti quando si adotta ExceptionGroup.
        source="def f(g):\n    caught = None\n    try:\n        g()\n    except* ValueError as eg:\n        caught = eg\n    return caught",
        description="except* e ExceptionGroup",
        pep="PEP 654",
        feature_id="except-star",
    ),
    SyntaxProbe(
        id="exception-notes",
        since=Version(3, 11),
        source="def f():\n    e = ValueError('x')\n    e.add_note('nota')\n    return e",
        description="BaseException.add_note",
        pep="PEP 678",
        feature_id="exception-notes",
    ),
    SyntaxProbe(
        id="type-params",
        since=Version(3, 12),
        source="def first[T](items: list[T]) -> T:\n    return items[0]\n\ntype Alias = int\nclass Box[T]:\n    value: T",
        description="sintassi dei type parameter (PEP 695)",
        pep="PEP 695",
        feature_id="type-params",
    ),
    SyntaxProbe(
        id="f-string-multiline",
        since=Version(3, 12),
        source="x = 1\nf'''{\n    x  # commento\n}'''",
        description="f-string multilinea con stesse quote (PEP 701)",
        pep="PEP 701",
        feature_id="f-string-multiline",
    ),
    SyntaxProbe(
        id="typing-override",
        since=Version(3, 12),
        source="from typing import override\n\nclass A:\n    def f(self) -> None: ...\n\nclass B(A):\n    @override\n    def f(self) -> None: ...",
        description="decoratore typing.override",
        pep="PEP 698",
        feature_id="typing-override",
    ),
    SyntaxProbe(
        id="warnings-deprecated",
        since=Version(3, 13),
        source="from warnings import deprecated\n\n@deprecated('motivo')\ndef f() -> None: ...",
        description="decoratore warnings.deprecated",
        pep="PEP 702",
        feature_id="warnings-deprecated",
    ),
    SyntaxProbe(
        id="t-string",
        since=Version(3, 14),
        source="name = 'x'\nt'ciao {name}'",
        description="t-string (stringhe template)",
        pep="PEP 750",
        feature_id="t-string",
    ),
    SyntaxProbe(
        id="parenthesized-with-items",
        since=Version(3, 10),
        source="class C:\n    def __enter__(self): return self\n    def __exit__(self, *a): return False\n\nwith (\n    C() as primo,\n    C() as secondo,\n):\n    pass",
        description="with su piu' righe fra parentesi tonde",
        pep=None,
        feature_id="parenthesized-with",
    ),
    SyntaxProbe(
        id="except-without-parens",
        since=Version(3, 14),
        source="try:\n    pass\nexcept TypeError, ValueError:\n    pass",
        description="except E1, E2: senza parentesi (PEP 758)",
        pep="PEP 758",
        feature_id="except-without-parens",
    ),
)


def probe_syntax() -> Iterator[SyntaxProbe]:
    """Itera su tutte le sonde sintattiche."""
    return iter(PROBES)


def get_probe(probe_id: str) -> Optional[SyntaxProbe]:
    """Restituisce la sonda con l'identificativo indicato, se esiste."""
    for probe in PROBES:
        if probe.id == probe_id:
            return probe
    return None


def supported_ids() -> Tuple[str, ...]:
    """Restituisce gli identificativi delle sonde supportate dal parser corrente."""
    return tuple(probe.id for probe in PROBES if probe.available())


def check(predicate: Callable[[], object]) -> bool:
    """Esegue ``predicate`` e restituisce ``False`` se solleva un'eccezione.

    Utilitaria pensata per le sonde non sintattiche, dove il fallimento si
    manifesta come eccezione a runtime e non come errore di compilazione.
    """
    try:
        predicate()
    except BaseException:  # noqa: BLE001
        return False
    return True