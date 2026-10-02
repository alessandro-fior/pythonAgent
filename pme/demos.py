"""Dimostrazioni eseguibili delle novita' di ogni versione.

Una sonda (:mod:`pme.probes`) risponde a una domanda secca: *questo parser
accetta il costrutto?*. Una dimostrazione risponde a una domanda utile: *a cosa
serve, e cosa stampa?*.

La differenza e' che una dimostrazione viene eseguita. Ogni blocco qui sotto e'
un programma completo che produce un risultato visibile, perche' una feature
senza un output osservabile e' difficile da ricordare e impossibile da testare.

Il vantaggio di tenere il codice qui dentro una stringa, invece che in un file
``.py`` di esempio, e' che il modulo resta analizzabile da qualunque versione
di Python: il sorgente viene compilato solo al momento giusto. Un repository
documentale che contiene esempi di sintassi dal 3.6 al 3.14 puo' cosi' avere una
sola suite di test, eseguita su un solo interprete.

Esempio::

    >>> from pme.demos import demo_ids, get_demo, render
    >>> "f-string" in demo_ids()
    True
    >>> render(get_demo("walrus")).startswith("### ")
    True
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, Optional, Tuple

from pme.version import Version, current_runtime_version

__all__ = [
    "Demo",
    "DEMOS",
    "demo_ids",
    "get_demo",
    "render",
    "run",
    "run_available",
    "supported_ids",
]


@dataclass(frozen=True)
class Demo:
    """Una dimostrazione eseguibile di una novita'.

    Attributes:
        id: identificativo stabile della dimostrazione.
        title: titolo leggibile, con la versione gia' indicata.
        since: versione che ha introdotto il costrutto dimostrato.
        description: cosa mostra, in una frase.
        source: programma completo che produce un risultato.
        expected: valore che ``source`` deve lasciare in ``risultato``.
        feature_id: scheda corrispondente nel catalogo :mod:`pme.features`.
    """

    id: str
    title: str
    since: Version
    description: str
    source: str
    expected: object
    feature_id: Optional[str] = None

    def available(self) -> bool:
        """``True`` se l'interprete corrente puo' eseguire la dimostrazione."""
        return run(self) is not _SKIP

    def result(self) -> object:
        """Esegue la dimostrazione e restituisce il valore di ``risultato``.

        Raises:
            RuntimeError: se l'interprete non e' abbastanza recente, oppure se il
                codice non lascia il valore atteso (il che significa che la
                dimostrazione e' rotta e va sistemata).
        """
        if self.since > current_runtime_version():
            raise RuntimeError(
                f"{self.id}: richiede Python {self.since}, "
                f"l'interprete in esecuzione e' Python {current_runtime_version()}"
            )
        namespace: Dict[str, object] = {}
        try:
            exec(compile(self.source, f"<pme.demo:{self.id}>", "exec"), namespace)
        except BaseException as err:  # noqa: BLE001 - l'errore va riportato
            raise RuntimeError(f"{self.id}: la dimostrazione e' fallita ({err!r})") from err
        if "risultato" not in namespace:
            raise RuntimeError(f"{self.id}: il codice non ha assegnato `risultato`")
        valore = namespace["risultato"]
        if valore != self.expected:
            raise RuntimeError(
                f"{self.id}: risultato inatteso, atteso {self.expected!r}, ottenuto {valore!r}"
            )
        return valore


#: Valore sentinella: distingue "non eseguibile qui" da un risultato falsy.
_SKIP = object()


def run(demo: Demo) -> object:
    """Esegue ``demo`` e restituisce il risultato, o :data:`_SKIP` se impossibile."""
    try:
        return demo.result()
    except RuntimeError:
        return _SKIP


#: Dimostrazioni in ordine di introduzione.
DEMOS: Tuple[Demo, ...] = (
    Demo(
        id="print-function",
        title="`print` come funzione",
        since=Version(3, 0),
        description="`sep`, `end` e `flush` diventano parametri, e l'output si intercetta.",
        source="import contextlib\n"
        "import io\n"
        "\n"
        "buffer = io.StringIO()\n"
        "with contextlib.redirect_stdout(buffer):\n"
        '    print("ciao", "mondo", sep="-", end="!", flush=True)\n'
        'risultato = buffer.getvalue()',
        expected="ciao-mondo!",
        feature_id="print-function",
    ),
    Demo(
        id="f-string",
        title="f-string, Python 3.6",
        since=Version(3, 6),
        description="Interpolazione dentro la stringa, con formattazione riutilizzabile.",
        source="importante = 42\n"
        'report = f"{importante:>5} | {importante / 2:.1f} | {importante!r}"\n'
        "risultato = report.strip()",
        expected="42 | 21.0 | 42",
        feature_id="f-string",
    ),
    Demo(
        id="walrus",
        title="Operatore morsa (`:=`), Python 3.8",
        since=Version(3, 8),
        description="Assegnare e usare una variabile nella stessa espressione, senza chiamare due volte.",
        source="import re\n"
        'testo = "rilascio 3.14 stabile"\n'
        'risultato = (trovato := re.search(r"\\d+\\.\\d+", testo)).group()',
        expected="3.14",
        feature_id="walrus",
    ),
    Demo(
        id="pattern-matching",
        title="`match`, Python 3.10",
        since=Version(3, 10),
        description="Smontare una struttura con schemi invece di confronti annidati.",
        source="def decodifica(evento):\n"
        '    match evento:\n'
        '        case {"tipo": "click", "x": int(x), "y": int(y)}:\n'
        "            return (\"click\", x, y)\n"
        '        case {"tipo": "key", "chiave": str(k)}:\n'
        '            return ("key", k)\n'
        "        case _:\n"
        '            return "ignoto"\n'
        'risultato = decodifica({"tipo": "click", "x": 3, "y": 4})',
        expected=("click", 3, 4),
        feature_id="pattern-matching",
    ),
    Demo(
        id="except-star",
        title="`except*`, Python 3.11",
        since=Version(3, 11),
        description="Gestire i gruppi di eccezioni separando cio' che e' stato risolto.",
        source="def recupera(lavori):\n"
        "    errori = []\n"
        "    for lavoro in lavori:\n"
        "        try:\n"
        "            if lavoro == 0:\n"
        '                raise ValueError("lavoro nullo")\n'
        "            if lavoro < 0:\n"
        '                raise TypeError("negativo")\n'
        "        except* ValueError as gruppo:\n"
        "            errori.append(f\"value:{len(gruppo.exceptions)}\")\n"
        "        except* TypeError as gruppo:\n"
        "            errori.append(f\"type:{len(gruppo.exceptions)}\")\n"
        "    return errori\n"
        "risultato = recupera([0, -1, 1])",
        expected=["value:1", "type:1"],
        feature_id="except-star",
    ),
    Demo(
        id="type-parameters",
        title="Type parameter espliciti, Python 3.12",
        since=Version(3, 12),
        description="Dichiarare i parametri di tipo senza creare una classe base.",
        source="def primo[T](elementi: list[T]) -> T:\n"
        "    return elementi[0]\n"
        "risultato = primo([3, 1, 2])",
        expected=3,
        feature_id="type-params",
    ),
    Demo(
        id="t-string",
        title="t-string, Python 3.14",
        since=Version(3, 14),
        description="La t-string non e' una `str`: espone `strings`, `interpolations` e i "
        "valori, e va ricomposta a chi la usa come testo.",
        source="utente = \"paolo\"\n"
        't = t"ciao {utente}, benvenuto"\n'
        "espressione = t.interpolations[0].expression\n"
        "ricomposta = \"\".join([t.strings[0], str(t.interpolations[0].value), *t.strings[1:]])\n"
        'risultato = f"{espressione}: {ricomposta}"',
        expected="utente: ciao paolo, benvenuto",
        feature_id="t-string",
    ),
)


def demo_ids() -> Tuple[str, ...]:
    """Identificativi delle dimostrazioni, in ordine di introduzione."""
    return tuple(demo.id for demo in DEMOS)


def supported_ids() -> Tuple[str, ...]:
    """Identificativi delle dimostrazioni eseguibili sull'interprete corrente."""
    return tuple(demo.id for demo in DEMOS if demo.available())


def get_demo(demo_id: str) -> Demo:
    """Restituisce la dimostrazione indicata.

    Raises:
        KeyError: se l'identificativo non esiste.
    """
    for demo in DEMOS:
        if demo.id == demo_id:
            return demo
    raise KeyError(f"dimostrazione sconosciuta: {demo_id!r} (disponibili: {', '.join(demo_ids())})")


def render(demo: Demo) -> str:
    """Restituisce la dimostrazione come blocco Markdown."""
    righe = [f"### {demo.title}", "", demo.description, "", "```python", demo.source, "```"]
    return "\n".join(righe)


def run_available() -> Iterator[Tuple[Demo, object]]:
    """Itera sulle dimostrazioni eseguibili, restituendo anche il risultato."""
    for demo in DEMOS:
        esito = run(demo)
        if esito is not _SKIP:
            yield demo, esito
