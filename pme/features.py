"""Catalogo delle funzionalita' di Python: la fonte di verita' del progetto.

Ogni scheda di versione (``versions/python-X.Y.md``), ogni tabella riassuntiva e
ogni esempio del repository derivano da questo modulo. Non esiste un secondo
elenco da tenere allineato: se una funzionalita' non e' qui, non viene
documentata, e i test verificano questa coerenza.

Un :class:`Feature` risponde alle domande di ``agent.md`` §26:

* ``Introduced: Python X.Y``  -> :attr:`Feature.introduced`
* ``Deprecated: Python X.Y``  -> :attr:`Feature.deprecated`
* ``Removed: Python X.Y``     -> :attr:`Feature.removed`
* ``Requires: Python X.Y+``   -> :attr:`Feature.requires`

I campi ``before`` e ``after` contengono il codice che mostra la trasformazione,
perche' il progetto non si limita a elencare le novita' ma le confronta.

Esempio::

    >>> from pme.features import get, headline_features
    >>> from pme.version import Version
    >>> get("f-string").introduced
    Version(major=3, minor=6)
    >>> [f.id for f in headline_features(Version(3, 10))]
    ['pattern-matching', 'union-types', 'parenthesized-with']
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterator, Optional, Tuple

from pme.version import Version

__all__ = [
    "Category",
    "Feature",
    "FEATURES",
    "by_id",
    "changed_between",
    "deprecated_in",
    "headline_features",
    "introduced_in",
    "iter_features",
    "removed_in",
    "requires",
    "topical_index",
]


class Category(str, Enum):
    """Le aree tematiche da tracciare, come elencate in ``agent.md`` §8.

    Non sono le "sezioni della scheda versione": sono gli argomenti trasversali
    che permettono di seguire una singola idea attraverso le versioni (per
    esempio tutte le forme di annotazione di tipo, da 3.0 a 3.14).
    """

    SYNTAX = "Sintassi"
    TYPES = "Tipi"
    FUNCTIONS = "Funzioni"
    OOP = "OOP"
    ITERATORS = "Iteratori e generatori"
    DECORATORS = "Decoratori"
    TYPING = "Type hints"
    EXCEPTIONS = "Gestione degli errori"
    ASYNC = "Async"
    PERFORMANCE = "Performance"
    STDLIB = "Standard library"
    IOTOOLS = "Strumenti di sistema"
    PACKAGING = "Packaging"
    TESTING = "Testing"
    COMPATIBILITY = "Compatibilita' e porting"
    BASELINE = "Punto di partenza"

    def __str__(self) -> str:
        """Restituisce l'etichetta leggibile della categoria."""
        return self.value


class Kind(str, Enum):
    """Il tipo di cambiamento descritto da una scheda.

    Determina in quale sezione della scheda versione la funzionalita' compare,
    come richiesto dalla struttura di `agent.md` §7.
    """

    SYNTAX = "Nuova sintassi"
    LANGUAGE = "Miglioramento del linguaggio"
    API = "Nuove API"
    PERFORMANCE = "Miglioramenti delle performance"
    DEPRECATION = "Deprecazioni"
    REMOVAL = "Rimozioni"
    ADVICE = "Guida moderna"

    def __str__(self) -> str:
        """Restituisce l'etichetta leggibile del tipo."""
        return self.value


@dataclass(frozen=True)
class Feature:
    """Una scheda di funzionalita' o di cambiamento di comportamento.

    Attributes:
        id: identificativo stabile, usato da CLI, esempi e test.
        title: nome leggibile della funzionalita'.
        introduced: versione che l'ha introdotta (o che ha cambiato il
            comportamento). Per le rimozioni e' la versione che l'ha rimossa.
        category: area tematica trasversale.
        kind: tipo di cambiamento, usato per raggruppare le sezioni.
        summary: descrizione in una frase.
        pep: PEP di riferimento, se esiste.
        before: codice precedente, mostrato come "COME ERA".
        after: codice successivo, mostrato come "COME SI USA OGGI".
        before_version: versione a cui appartiene ``before``.
        after_version: versione a cui appartiene ``after``.
        deprecated: versione che ha deprecato la funzionalita', se presente.
        removed: versione che l'ha rimossa, se presente.
        reason: perche' e' stata fatta la modifica (l'obiettivo di `agent.md` §30).
        source: fonte ufficiale che conferma il dato.
        notes: precisazioni aggiuntive.
        status: stato della scheda: ``"stable"``, ``"provisional"``,
            ``"experimental"`` oppure ``"planned"``.
        headline: ``True`` se la scheda rappresenta la novita' principale della
            versione. Serve alla tabella cronologica di ``agent.md`` §21 e viene
            impostato a mano: nessuna classifica automatica sa quale novita'
            definisca davvero una versione.
    """

    id: str
    title: str
    introduced: Version
    category: Category
    kind: Kind
    summary: str = ""
    pep: Optional[str] = None
    before: str = ""
    after: str = ""
    before_version: Optional[Version] = None
    after_version: Optional[Version] = None
    deprecated: Optional[Version] = None
    removed: Optional[Version] = None
    reason: str = ""
    source: str = ""
    notes: str = ""
    status: str = "stable"
    headline: bool = False

    @property
    def requires(self) -> Version:
        """Versione minima necessaria per usare la funzionalita'."""
        return self.introduced

    @property
    def is_removed(self) -> bool:
        """``True`` se la funzionalita' non e' piu' disponibile."""
        return self.removed is not None

    @property
    def is_deprecated(self) -> bool:
        """``True`` se la funzionalita' e' ancora disponibile ma sconsigliata."""
        return self.deprecated is not None and self.removed is None

    @property
    def lifecycle(self) -> str:
        """Stato sintetico della scheda in forma testuale."""
        if self.removed is not None:
            return "rimossa"
        if self.deprecated is not None:
            return "deprecata"
        if self.status in ("provisional", "experimental", "planned"):
            return self.status
        return "stabile"

    def compatibility_note(self) -> str:
        """Restituisce le tre righe ``Introduced/Requires`` di `agent.md` §26."""
        lines = [f"Introduced: Python {self.introduced}", f"Requires: Python {self.requires}+"]
        if self.deprecated is not None:
            lines.append(f"Deprecated: Python {self.deprecated}")
        if self.removed is not None:
            lines.append(f"Removed: Python {self.removed}")
        return "\n".join(lines)

    def has_example(self) -> bool:
        """``True`` se la scheda contiene codice di esempio."""
        return bool(self.before.strip() or self.after.strip())


_WHATSNEW = "https://docs.python.org/3/whatsnew/{}.html"


def _src(version: Version) -> str:
    """URL della pagina "What's New" usata come fonte predefinita."""
    return _WHATSNEW.format(str(version))


def _f(
    feature_id: str,
    title: str,
    introduced: Version,
    category: Category,
    kind: Kind,
    summary: str,
    *,
    pep: Optional[str] = None,
    before: str = "",
    after: str = "",
    before_version: Optional[Version] = None,
    after_version: Optional[Version] = None,
    deprecated: Optional[Version] = None,
    removed: Optional[Version] = None,
    reason: str = "",
    source: Optional[str] = None,
    notes: str = "",
    status: str = "stable",
    headline: bool = False,
) -> Feature:
    """Costruttore compatto per il catalogo.

    ``before_version`` e ``after_version`` hanno come default rispettivamente la
    versione precedente e quella di introduzione: nella maggior parte dei casi
    e' esattamente quello che si vuole.
    """
    previous = _previous(introduced)
    return Feature(
        id=feature_id,
        title=title,
        introduced=introduced,
        category=category,
        kind=kind,
        summary=summary,
        pep=pep,
        before=before,
        after=after,
        before_version=before_version if before_version is not None else previous,
        after_version=after_version if after_version is not None else introduced,
        deprecated=deprecated,
        removed=removed,
        reason=reason,
        source=source if source is not None else _src(introduced),
        notes=notes,
        status=status,
        headline=headline,
    )


#: Versione immediatamente precedente a ``version`` sulla linea 3.x.
#: Serve come default per il blocco "prima".
def _previous(version: Version) -> Optional[Version]:
    """Versione documentata immediatamente precedente, se esiste."""
    if version.is_python3:
        return Version(3, version.minor - 1) if version.minor > 0 else None
    return Version(2, 7)


_V2 = Version(2, 7)
_V30 = Version(3, 0)
_V31 = Version(3, 1)
_V32 = Version(3, 2)
_V33 = Version(3, 3)
_V34 = Version(3, 4)
_V35 = Version(3, 5)
_V36 = Version(3, 6)
_V37 = Version(3, 7)
_V38 = Version(3, 8)
_V39 = Version(3, 9)
_V310 = Version(3, 10)
_V311 = Version(3, 11)
_V312 = Version(3, 12)
_V313 = Version(3, 13)
_V314 = Version(3, 14)
_V315 = Version(3, 15)
_V316 = Version(3, 16)


# ---------------------------------------------------------------------------
# Baseline: cosa caratterizzava Python 2 e cosa è stato rimosso.
# ---------------------------------------------------------------------------

FEATURES: Tuple[Feature, ...] = (
    _f(
        "python-27-baseline",
        "Python 2.7, l'ultima versione della serie 2",
        _V2,
        Category.BASELINE,
        Kind.LANGUAGE,
        "La base di partenza di quasi ogni migrazione: stringhe byte per "
        "default, `print` come istruzione, divisione intera con `/`.",
        before="# Python 2.7\nimport ConfigParser\nvalori = open('dati.txt').read()\nprint len(valori) / 2",
        after="# Python 3\nimport configparser\nvalori = open('dati.txt', encoding='utf-8').read()\nprint(len(valori) // 2)",
        after_version=_V30,
        before_version=Version(2, 6),
        reason=(
            "Python 2.7 ha segnato la fine del ramo 2: dal 1 gennaio 2020 "
            "riceve solo correzioni di sicurezza. E' la versione da cui si "
            "migra e il riferimento per capire cosa e' cambiato."
        ),
        notes=(
            "Le tre differenze piu' insidiose non sono sintattiche: le "
            "stringhe sono byte, `/` tronca e `dict.keys()` restituiva una "
            "lista. Le altre due rimozioni (print, ConfigParser) si vedono subito."
        ),
        headline=True,
    ),
    _f(
        "print-statement",
        "`print` era un'istruzione, non una funzione",
        _V30,
        Category.SYNTAX,
        Kind.REMOVAL,
        "In Python 2 `print` e' una dichiarazione con sintassi propria, con argomenti "
        "separati da virgole e redirezione via `>>`.",
        before='print "ciao", nome\nprint >>sys.stderr, "errore"',
        after='print("ciao", nome)\nprint("errore", file=sys.stderr)',
        before_version=Version(2, 6),
        reason=(
            "Una dichiarazione speciale impediva di usare `print` come valore "
            "prima di chiamata, non aveva `sep`/`end` e non si poteva redirigere "
            "senza una sintassi separata. La funzione risolve tutti e tre i punti."
        ),
        notes="Sintassi non valida in Python 3: non e' convertibile automaticamente in tutti i casi.",
        headline=True,
    ),
    _f(
        "raw-input",
        "`raw_input()` rinominato in `input()`",
        _V30,
        Category.COMPATIBILITY,
        Kind.REMOVAL,
        "Python 2 aveva due funzioni di lettura: `input()` valutava l'espressione "
        "letta (pericoloso), `raw_input()` restituiva la stringa.",
        before='nome = raw_input("Nome: ")',
        after='nome = input("Nome: ")',
        before_version=Version(2, 6),
        reason=(
            "Avere una sola funzione di lettura evita che `input()` valuti codice "
            "arbitrario: in Python 3 `input()` non esegue nulla."
        ),
    ),
    _f(
        "xrange",
        "`xrange()` sostituito da `range()`",
        _V30,
        Category.ITERATORS,
        Kind.REMOVAL,
        "In Python 2 `range()` costruiva una lista; `xrange()` restituiva un "
        "generatore di interi.",
        before="for i in xrange(10):\n    print i",
        after="for i in range(10):\n    print(i)",
        before_version=Version(2, 6),
        reason=(
            "Due funzioni con lo stesso nome e comportamento diverso era una "
            "trappola frequente. `range()` e' diventata pigra e Accepta anche "
            "numeri arbitrariamente grandi."
        ),
    ),
    _f(
        "iteritems",
        "`dict.iteritems()` e amici rimossi",
        _V30,
        Category.COMPATIBILITY,
        Kind.REMOVAL,
        "I metodi `iterkeys`, `itervalues`, `iteritems` producevano iteratori; "
        "`keys`, `values`, `items` restituivano liste.",
        before="for chiave, valore in d.iteritems():\n    print chiave, valore",
        after="for chiave, valore in d.items():\n    print(chiave, valore)",
        before_version=Version(2, 6),
        reason=(
            "`keys()`, `values()` e `items()` restituiscono ora viste, che sono "
            "iterabili, efficienti e permettono di evitare la copia della lista."
        ),
        notes="Le viste non hanno `.sort()`: usare `sorted(d)`.",
    ),
    _f(
        "has-key",
        "`dict.has_key()` rimosso",
        _V30,
        Category.COMPATIBILITY,
        Kind.REMOVAL,
        "Membro esistenziale del dizionario come metodo.",
        before='if d.has_key("nome"):\n    ...',
        after='if "nome" in d:\n    ...',
        before_version=Version(2, 6),
        reason="`in` funziona su ogni tipo di contenitore, non solo sui dizionari.",
    ),
    _f(
        "unicode-type",
        "`unicode` rimosso: `str` e' gia' testo Unicode",
        _V30,
        Category.TYPES,
        Kind.REMOVAL,
        "In Python 2 `str` conteneva byte e `unicode` conteneva caratteri. "
        "In Python 3 esiste un solo tipo per il testo.",
        before='def f(s):\n    if isinstance(s, basestring):\n        ...\n    return u"testo" + s',
        after='def f(s: str) -> str:\n    return "testo" + s',
        before_version=Version(2, 6),
        reason=(
            "La distinzione obbligava a decodificare in modo esplicito e "
            "produceva la maggior parte dei bug di codifica."
        ),
        notes=(
            "Gli equivalenti sono: `unicode` -> `str`, `str` (byte) -> `bytes`, "
            "`basestring` -> `str`."
        ),
        headline=True,
    ),
    _f(
        "text-vs-data",
        "Testo e dati binari non si mescolano piu'",
        _V30,
        Category.TYPES,
        Kind.LANGUAGE,
        "Python 3 distingue `str` (testo) da `bytes` (dati); concatenarli e' "
        "un `TypeError`, non una coercizione silenziosa.",
        before='risultato = "ciao " + "mondo"   # Python 2: str + str = byte + byte',
        after='risultato = "ciao " + "mondo"   # Python 3: str + str = testo + testo',
        before_version=Version(2, 6),
        reason=(
            "In Python 2 la somma tra `str` e `unicode` riusciva solo se i byte "
            "erano ASCII: il fallimento dipendeva dal contenuto del dato."
        ),
        notes="Conversione esplicita con `str.encode()`, `bytes.decode()`, `str(b, encoding=...)`.",
    ),
    _f(
        "true-division",
        "`/` e' divisione reale, `//` e' divisione intera",
        _V30,
        Category.TYPES,
        Kind.LANGUAGE,
        "In Python 2 `/` fra due interi troncava verso zero. In Python 3 `/` "
        "restituisce sempre un `float`.",
        before="# Python 2\nmedia = (3 + 4) / 2      # 3\nquota = 7 / 2          # 3",
        after="# Python 3\nmedia = (3 + 4) / 2      # 3.5\nquota = 7 // 2         # 3",
        before_version=Version(2, 6),
        reason=(
            "La divisione che tronca e' stata spostata su un operatore esplicito "
            "(`//`), eliminando la classe di bug silenziosi piu' insidiosi del mondo Python 2."
        ),
        notes=(
            "In Python 2 era possibile ripristinare il comportamento con "
            "`from __future__ import division`, disponibile dal 2.2."
        ),
        headline=True,
    ),
    _f(
        "print-function",
        "`print()` come funzione",
        _V30,
        Category.SYNTAX,
        Kind.SYNTAX,
        "L'istruzione `print` e' diventata una funzione con parole chiave "
        "`sep`, `end`, `file`, `flush`.",
        pep="PEP 3105",
        after='print("trovati", n, "record", sep=", ", end="\\n", file=sys.stderr)',
        reason="Rende `print` utilizzabile come valore e uniforma le chiamate.",
        notes="Era gia' disponibile in Python 2.6 con `from __future__ import print_function`.",
    ),
    _f(
        "nonlocal",
        "`nonlocal` per le variabili di funzioni annidate",
        _V30,
        Category.FUNCTIONS,
        Kind.SYNTAX,
        "Assegnazione diretta a un nome appartenente a uno scope esterno ma "
        "non globale.",
        pep="PEP 3104",
        before="# Python 2: solo con trucco\ndef esterna():\n    x = 1\n    def interna():\n        x += 1  # NameError\n        return x",
        after="def esterna():\n    x = 1\n    def interna():\n        nonlocal x\n        x += 1\n        return x",
        reason="Prima serviva passare la variabile in una lista mutabile per aggirare la regola.",
    ),
    _f(
        "keyword-only-args",
        "Argomenti keyword-only",
        _V30,
        Category.FUNCTIONS,
        Kind.SYNTAX,
        "I parametri che seguono un `*` possono essere passati solo per nome.",
        pep="PEP 3102",
        after="def connetti(host, /, *, timeout=10, retries=3):\n    ...",
        reason=(
            "Permette di aggiungere opzioni senza rompere le chiamate posizionali "
            "esistenti: e' il modo standard per proteggere l'API dalla crescita."
        ),
        notes="Il marcatore `/` per i positional-only e' arrivato dopo, con Python 3.8 (PEP 570).",
    ),
    _f(
        "exception-chaining",
        "Concatenamento esplicito delle eccezioni",
        _V30,
        Category.EXCEPTIONS,
        Kind.LANGUAGE,
        "`raise ... from ...` collega esplicitamente un errore a quello che lo ha causato.",
        pep="PEP 3134",
        before="# Python 2\ntry:\n    valore = int(testo)\nexcept ValueError:\n    raise ValueError('valore non valido')",
        after="try:\n    valore = int(testo)\nexcept ValueError as exc:\n    raise ValueError('valore non valido') from exc",
        before_version=_V2,
        reason=(
            "In Python 2 la nuova eccezione nascondeva completamente la causa "
            "originale; il traceback mostrava solo il sintomo."
        ),
        notes="`raise X from None` sopprime l'intera catena.",
    ),
    _f(
        "function-annotations",
        "Annotazioni di funzione",
        _V30,
        Category.TYPING,
        Kind.SYNTAX,
        "Annotazioni su parametri e valore di ritorno, introspecabili a runtime.",
        pep="PEP 3107",
        before="# Python 2: nessun supporto\ndef somma(a, b):\n    return a + b",
        after="def somma(a: int, b: int) -> int:\n    return a + b",
        reason="Danno un punto di aggancio a strumenti di verifica e documentazione.",
        notes="Nessuna semantica a runtime: le annotazioni non vengono controllate da CPython.",
    ),
    _f(
        "metaclass-syntax",
        "Sintassi nuova per le metaclassi",
        _V30,
        Category.OOP,
        Kind.LANGUAGE,
        "La metaclassi si indica nella intestazione della classe.",
        pep="PEP 3115",
        before="# Python 2\nclass Base(object):\n    __metaclass__ = Meta",
        after="class Base(metaclass=Meta):\n    ...",
        before_version=_V2,
        reason="La variabile `__metaclass__` nel corpo della classe era ignorata in molti casi.",
    ),
    _f(
        "classic-classes",
        "Le classi vecchie sono sparite",
        _V30,
        Category.OOP,
        Kind.REMOVAL,
        "In Python 2 esistevano due modelli di classe, selezionati da "
        "`__metaclass__`; in Python 3 esiste solo il modello nuovo.",
        before="# Python 2: classe vecchia\nclass Vecchia:\n    pass",
        after="# Python 3: un solo modello, derivato da object\nclass Nuova:\n    pass",
        before_version=_V2,
        reason="I due modelli avevano regole diverse per descrittori, proprietà e MRO.",
        notes="`super()` senza argomenti funziona con qualsiasi classe in Python 3.",
    ),
    _f(
        "reduce-moved",
        "`reduce()` non e' piu' un builtin",
        _V30,
        Category.FUNCTIONS,
        Kind.REMOVAL,
        "La funzione e' stata spostata in `functools` dove non era in conflitto "
        "con concetti non correlati.",
        before="risultato = reduce(lambda a, b: a + b, [1, 2, 3])",
        after="from functools import reduce\n\nrisultato = reduce(lambda a, b: a + b, [1, 2, 3])",
        before_version=_V2,
        reason="Era una delle pochissime funzioni non intuitive fra i builtin.",
    ),
    _f(
        "backtick-repr",
        "Le parentesi acute per il repr sono state rimosse",
        _V30,
        Category.SYNTAX,
        Kind.REMOVAL,
        "Il backtick restituiva la rappresentazione testuale di un valore.",
        before="testo = `valore`",
        after="testo = repr(valore)",
        before_version=_V2,
        reason="La sintassi coincideva con il carattere di sostituzione in vari linguaggi.",
    ),
    _f(
        "except-comma",
        "`except E, e:` rimosso in favore di `except E as e:`",
        _V30,
        Category.EXCEPTIONS,
        Kind.REMOVAL,
        "La variabile della clausola `except` veniva eliminata automaticamente.",
        pep="PEP 3110",
        before="try:\n    ...\nexcept ValueError, exc:\n    print exc.message",
        after="try:\n    ...\nexcept ValueError as exc:\n    print(exc)",
        before_version=_V2,
        reason="La forma con virgola era ambigua con la tupla di eccezioni in Python 3.",
    ),
    _f(
        "dict-comprehension",
        "Comprensioni per dizionari e set",
        _V30,
        Category.SYNTAX,
        Kind.SYNTAX,
        "Python 3 aggiunge le comprensioni di dizionari e di set.",
        before="# Python 2\nquadrati = dict((x, x * x) for x in range(10))",
        after="# Python 3\nquadrati = {x: x * x for x in range(10)}",
        before_version=_V2,
        reason="Uniforma la sintassi: le comprensioni di lista esistevano gia' in 2.0.",
    ),
    # -----------------------------------------------------------------------
    # 3.1
    # -----------------------------------------------------------------------
    _f(
        "ordereddict",
        "`collections.OrderedDict`",
        _V31,
        Category.TYPES,
        Kind.API,
        "Dizionario che conserva l'ordine di inserimento.",
        pep="PEP 372",
        after="from collections import OrderedDict\n\nd = OrderedDict([('b', 1), ('a', 2)])",
        reason="Prima l'ordine di un dizionario era un dettaglio dell'implementazione, non un contratto.",
        notes=(
            "L'ordine di `dict` e' diventato parte del linguaggio solo con Python 3.7; "
            "3.6 e' il primo `dict` a conservarlo in CPython come dettaglio di implementazione."
        ),
        headline=True,
    ),
    _f(
        "float-repr",
        "`repr()` dei float usa la forma piu' corta che fa riscontro esatto",
        _V31,
        Category.TYPES,
        Kind.LANGUAGE,
        "`repr(1.1)` restituisce `'1.1'` invece di 17 cifre.",
        before="# Python 2\nrepr(1.1)   # '1.1000000000000001'",
        after="# Python 3.1+\nrepr(1.1)   # '1.1'",
        before_version=_V30,
        reason="Mantiene il valore leggibile senza perdere la precisione della conversione.",
        notes="`1.1 + 2.2 != 3.3` resta vero: la rappresentazione non e' un'aritmetica esatta.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.2
    # -----------------------------------------------------------------------
    _f(
        "concurrent-futures",
        "`concurrent.futures`",
        _V32,
        Category.IOTOOLS,
        Kind.API,
        "Esecuzione parallela con pool di thread e di processi, pensata per "
        "codice di lunga durata.",
        pep="PEP 3148",
        after="from concurrent.futures import ThreadPoolExecutor\n\nwith ThreadPoolExecutor() as pool:\n    risultati = list(pool.map(analizza, record))",
        reason="Prima si usavano `threading` e `multiprocessing` con API diverse e parallele.",
        headline=True,
    ),
    _f(
        "lru-cache",
        "`functools.lru_cache`",
        _V32,
        Category.DECORATORS,
        Kind.API,
        "Memoizzazione con limite di dimensione.",
        after="from functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef lento(x: int) -> int:\n    return x * x",
        reason="Rende il pattern cache-delle-funzionalita' di alto livello, senza scrivere una classe.",
        notes="`functools.cache` (senza parametri) e' arrivato con Python 3.9.",
        headline=True,
    ),
    _f(
        "pycache",
        "Cache dei bytecode in `__pycache__`",
        _V32,
        Category.IOTOOLS,
        Kind.LANGUAGE,
        "I file `.pyc` non stanno piu' accanto ai sorgenti.",
        pep="PEP 3147",
        after="import mio_modulo  # crea __pycache__/mio_modulo.cpython-312.pyc",
        reason="I `.pyc` accanto ai sorgenti rendevano impossibile il backup incrementale.",
        headline=True,
    ),
    _f(
        "new-gil",
        "Il GIL e' stato riscritto",
        _V32,
        Category.PERFORMANCE,
        Kind.PERFORMANCE,
        "Semaforo e condizioni aggiornate, con intervallo di commutazione "
        "esplicito e configurabile.",
        after="import sys\n\nsys.setswitchinterval(0.005)",
        reason="Meno contention sul lock e un comportamento di commutazione prevedibile.",
        notes=(
            "Il GIL e' stato rimosso solo con la build free-threaded sperimentale "
            "di Python 3.13 (PEP 703); la build standard lo mantiene."
        ),
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.3
    # -----------------------------------------------------------------------
    _f(
        "yield-from",
        "`yield from` per la delegazione fra generatori",
        _V33,
        Category.ITERATORS,
        Kind.SYNTAX,
        "Un generatore puo' delegare a un altro e riceverne il valore di ritorno.",
        pep="PEP 380",
        before="# Python 2: ciclo esplicito\ndef wrapper(seq):\n    for x in seq:\n        yield x",
        after="def wrapper(seq):\n    return (yield from seq)",
        before_version=_V32,
        reason="Semplifica la composizione di generatori e rende possibile il ritorno di un valore.",
        headline=True,
    ),
    _f(
        "os-error-hierarchy",
        "Gerarchia delle eccezioni di sistema ridefinita",
        _V33,
        Category.EXCEPTIONS,
        Kind.LANGUAGE,
        "`IOError` e `EnvironmentError` sono alias di `OSError`; le nuove "
        "sottoclassi distinguono i casi.",
        pep="PEP 3151",
        before="# Python 2\ntry:\n    apri()\nexcept IOError:\n    ...  # non si distingue il motivo",
        after="# Python 3.3+\ntry:\n    apri()\nexcept FileNotFoundError:\n    ...\nexcept PermissionError:\n    ...",
        before_version=_V32,
        reason="`except IOError:` era troppo generico per gestire gli errori reali.",
        notes="Le nuove classi includono `FileNotFoundError`, `TimeoutError`, `ConnectionError` e derivate.",
        headline=True,
    ),
    _f(
        "namespace-packages",
        "Pacchetti namespace senza `__init__.py`",
        _V33,
        Category.PACKAGING,
        Kind.LANGUAGE,
        "Una directory puo' diventare un pacchetto senza `__init__.py`.",
        pep="PEP 420",
        reason="Permette di dividere un pacchetto fra piu' distribuzioni.",
        notes="Comportamento di `pkgutil`, `setuptools` e `pip` con namespace package: da verificare.",
        headline=True,
    ),
    _f(
        "unittest-mock",
        "Modulo `unittest.mock`",
        _V33,
        Category.TESTING,
        Kind.API,
        "Basi in stdlib per il mocking, senza dipendenze esterne.",
        after="from unittest.mock import patch\n\nwith patch('modulo.servizio') as servizio:\n    servizio.restituisce.return_value = 42",
        reason="Il mocking era disponibile solo tramite librerie di terze parti.",
        notes="Le pagine 'What's New' ufficiali non associano un PEP a questo modulo.",
        headline=True,
    ),
    _f(
        "time-monotonic",
        "`time.monotonic()` e orologi robusti",
        _V33,
        Category.IOTOOLS,
        Kind.API,
        "Sostituisce `time.clock()` con un orologio immune ai cambi di ora di sistema.",
        pep="PEP 418",
        after="inizio = time.monotonic()\nelapsed = time.monotonic() - inizio",
        reason="`time.clock()` misurava il tempo di CPU su Unix e il tempo di parete su Windows.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.4
    # -----------------------------------------------------------------------
    _f(
        "pathlib",
        "`pathlib`: percorsi come oggetti",
        _V34,
        Category.IOTOOLS,
        Kind.API,
        "Percorsi manipolabili con gli operatori e con i metodi.",
        pep="PEP 428",
        before="import os\n\npercorso = os.path.join(\"dati\", \"file.txt\")\nif os.path.exists(percorso):\n    with open(percorso) as f:\n        dati = f.read()",
        after="from pathlib import Path\n\npercorso = Path(\"dati\") / \"file.txt\"\nif percorso.exists():\n    dati = percorso.read_text(encoding=\"utf-8\")",
        before_version=_V33,
        reason="`os.path` e' una raccolta di funzioni che non compone, senza stato ne' oggetti.",
        notes="API provvisoria in 3.4, in stabilizzazione nelle versioni successive.",
        status="stable",
        headline=True,
    ),
    _f(
        "enum",
        "Modulo `enum`",
        _V34,
        Category.TYPES,
        Kind.API,
        "Tipi enumerati con metodo `name`/`value`.",
        pep="PEP 435",
        after="from enum import Enum\n\nclass Stato(Enum):\n    ATTIVO = 'attivo'\n    SPENTO = 'spento'",
        reason="Le costanti a stringa spariscono in favore di un tipo controllabile.",
        notes="`Flag` e `IntFlag` sono arrivati con Python 3.6, `StrEnum` con 3.11.",
        headline=True,
    ),
    _f(
        "asyncio",
        "Modulo `asyncio`",
        _V34,
        Category.ASYNC,
        Kind.API,
        "Prima API standard per l'I/O asincrono.",
        pep="PEP 3156",
        after="import asyncio\n\nasync def attendi() -> None:\n    await asyncio.sleep(1)",
        reason="Prima esistevano solo soluzioni di terze parti con API diverse.",
        notes="Stabile da Python 3.6; `asyncio.run()` da 3.7.",
        status="provisional",
        headline=True,
    ),
    _f(
        "singledispatch",
        "`functools.singledispatch`",
        _V34,
        Category.FUNCTIONS,
        Kind.API,
        "Dispatch generico basato sul tipo del primo argomento.",
        pep="PEP 443",
        after="from functools import singledispatch\n\n@singledispatch\ndef mostra(oggetto: object) -> str:\n    return str(oggetto)",
        reason="Alternativa leggibile all'overloading per tipo.",
        status="stable",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.5
    # -----------------------------------------------------------------------
    _f(
        "async-await",
        "Coroutine con `async` e `await`",
        _V35,
        Category.ASYNC,
        Kind.SYNTAX,
        "Parole chiave per scrivere codice asincrono, con ciclo di vita esplicito.",
        pep="PEP 492",
        before="# Python 2: generatori con decoratore\nimport asyncio\n\n@asyncio.coroutine\ndef attendi():\n    yield from asyncio.sleep(1)",
        after="async def attendi() -> None:\n    await asyncio.sleep(1)",
        before_version=_V34,
        reason=(
            "I generatori decorati erano indistinguibili da quelli normali: gli "
            "errori di runtime erano frequenti e il debugging impossibile."
        ),
        notes=(
            "`async` e `await` diventano parole chiave riservate con Python 3.7; "
            "il decoratore `@asyncio.coroutine` e' stato rimosso nel 3.11."
        ),
        headline=True,
    ),
    _f(
        "typing-module",
        "Modulo `typing`",
        _V35,
        Category.TYPING,
        Kind.API,
        "Annotazioni di tipo con strutture parametriche: `List`, `Dict`, `Optional`, `Union`.",
        pep="PEP 484",
        before="def somma(a, b):\n    # nessuna informazione sul dominio\n    return a + b",
        after="from typing import Optional\n\ndef somma(a: int, b: int) -> int:\n    return a + b",
        reason="Nessun controllo a runtime, ma uno strumento statico comune (mypy, pyright, IDE).",
        notes="Nella 3.5 `List[str]` era obbligatorio: `list[str]` arriva con Python 3.9 (PEP 585).",
        headline=True,
    ),
    _f(
        "unpacking-generalization",
        "Generalizzazione dell'unpacking con `*` e `**`",
        _V35,
        Category.FUNCTIONS,
        Kind.SYNTAX,
        "Piu' di un `*` nelle chiamate, piu' di un `**`, e piu' elementi spreads "
        "nei display di lista, set e dizionario.",
        pep="PEP 448",
        before="def f(a, b, c):\n    ...\n\nlista = [1, 2] + [3, 4]\nargs = [1, 2]\nf(*args, 3)",
        after="def f(a, b, c):\n    ...\n\nlista = [1, 2, *[3, 4]]\nargs = [1, 2]\nf(*args, 3)",
        before_version=_V34,
        reason="Compositione di liste e chiamate senza costruire liste intermedie.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.6
    # -----------------------------------------------------------------------
    _f(
        "f-string",
        "f-string",
        _V36,
        Category.SYNTAX,
        Kind.SYNTAX,
        "Stringhe formattate letterali, valutate a runtime come una normale "
        "espressione.",
        pep="PEP 498",
        before="# Python 2/3.5\nnome = \"Ada\"\neta = 36\nmessaggio = \"{} ha {} anni\".format(nome, eta)\nvecchio = \"%s ha %d anni\" % (nome, eta)",
        after="nome = \"Ada\"\neta = 36\nmessaggio = f\"{nome} ha {eta} anni\"",
        before_version=_V35,
        reason=(
            "`%` e `.format()` hanno sintassi diverse fra loro e non sono "
            "sicuri: un campo sbagliato fallisce tardi e lontano dal punto di errore."
        ),
        notes=(
            "L'upgrade da `.format()` e' quasi sempre meccanico; dall'upgrade da `%` "
            "richiede attenzione ai formati `%r`, `%d` e alla precedenza."
        ),
        headline=True,
    ),
    _f(
        "variable-annotations",
        "Annotazioni di variabile",
        _V36,
        Category.TYPING,
        Kind.SYNTAX,
        "Annotazioni su variabili locali, di istanza e di classe.",
        pep="PEP 526",
        before="# Python 3.5\nclass Utente:\n    def __init__(self, nome):\n        self.nome = nome  # nessun tipo",
        after="class Utente:\n    nome: str\n\n    def __init__(self, nome: str) -> None:\n        self.nome = nome",
        before_version=_V35,
        reason="I tipi delle strutture dati non erano esprimibili senza una dichiarazione a runtime.",
        notes="Le annotazioni di variabile non sono accessibili a runtime come quelle di funzione.",
        headline=True,
    ),
    _f(
        "numeric-literals",
        "Separatori `_` nei letterali numerici",
        _V36,
        Category.SYNTAX,
        Kind.SYNTAX,
        "Il carattere `_` puo' separare le cifre di letterali interi, float e esadecimali.",
        pep="PEP 515",
        after="budget = 1_000_000\nmaschera = 0xFF_FF_FF\npiccolo = 1_0.5",
        before_version=_V35,
        reason="Legibilita' dei numeri grandi senza perdere la precisione.",
        headline=True,
    ),
    _f(
        "async-generators",
        "Generatori asincroni",
        _V36,
        Category.ASYNC,
        Kind.SYNTAX,
        "`yield` dentro `async def` produce un generatore asincrono.",
        pep="PEP 525",
        before="# Python 3.5: non consentito\nasync def stream():\n    yield 1  # SyntaxError",
        after="async def stream():\n    yield 1",
        before_version=_V35,
        reason="In 3.5 non si poteva produrre uno stream asincrono con un generatore.",
        notes="Dal 3.7 e' ammesso anche `await` dentro la comprensione di una f-string.",
        headline=True,
    ),
    _f(
        "async-comprehensions",
        "Comprensioni asincrone",
        _V36,
        Category.ASYNC,
        Kind.SYNTAX,
        "`async for` e `await` sono ammessi dentro le comprensioni.",
        pep="PEP 530",
        before="# Python 3.5\nrisultati = [x for x in stream_sincrono()]\nasinc = [x async for x in stream_async()]  # SyntaxError",
        after="async def raccogli(stream):\n    return [x async for x in stream]",
        before_version=_V35,
        reason="In 3.5 le comprensioni non potevano contenere `await` o `async for`.",
    ),
    _f(
        "pathlike",
        "Protocollo `os.PathLike`",
        _V36,
        Category.IOTOOLS,
        Kind.API,
        "Gli oggetti percorso sono accettati da `open()` e dalle funzioni di `os`.",
        pep="PEP 519",
        after="from pathlib import Path\n\nwith open(Path('dati') / 'x.txt') as f:\n    ...",
        reason="Le API di sistema accettavano solo `str`, quindi `pathlib` era scomodo da usare.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.7
    # -----------------------------------------------------------------------
    _f(
        "dataclasses",
        "Modulo `dataclasses`",
        _V37,
        Category.OOP,
        Kind.API,
        "Il decoratore `@dataclass` genera `__init__`, `__repr__`, `__eq__` e "
        "`__hash__` a partire dalle annotazioni.",
        pep="PEP 557",
        before="class Persona:\n    def __init__(self, nome: str, eta: int) -> None:\n        self.nome = nome\n        self.eta = eta\n\n    def __repr__(self) -> str:\n        return f\"Persona(nome={self.nome!r}, eta={self.eta!r})\"\n\n    def __eq__(self, altro: object) -> bool:\n        if not isinstance(altro, Persona):\n            return NotImplemented\n        return (self.nome, self.eta) == (altro.nome, altro.eta)",
        after="from dataclasses import dataclass\n\n@dataclass\nclass Persona:\n    nome: str\n    eta: int",
        before_version=_V36,
        reason="Il codice di boilerplate per i semplici contenitori di dati era ripetuto ovunque.",
        notes=(
            "`frozen=True` da 3.7; `kw_only` e `slots` da 3.10; "
            "`kw_only` sugli argomenti di `field` richiede 3.10."
        ),
        headline=True,
    ),
    _f(
        "postponed-annotations",
        "`from __future__ import annotations`",
        _V37,
        Category.TYPING,
        Kind.SYNTAX,
        "Le annotazioni diventano stringhe, quindi i riferimenti in avanti "
        "non richiedono le virgolette.",
        pep="PEP 563",
        after="from __future__ import annotations\n\ndef crea(nome: Utente | None = None) -> Utente | None:\n    ...",
        before_version=_V36,
        reason="I riferimenti in avanti costringevano a scrivere stringhe ovunque.",
        notes=(
            "Il futuro rimane sospeso anche in 3.14: la valutazione differita e' "
            "diventata il comportamento predefinito con PEP 649, e il futuro e' "
            "incompatibile con quella."
        ),
        headline=True,
    ),
    _f(
        "async-keywords",
        "`async` e `await` sono parole chiave riservate",
        _V37,
        Category.SYNTAX,
        Kind.REMOVAL,
        "Non sono piu' usabili come nomi di variabili o funzioni.",
        before="# Python 3.5-3.6\nasync = 1        # ammesso, con DeprecationWarning dal 3.6\ndef await_(x):\n    ...  # serve una variante con '_' in coda",
        after="def attendi(x):\n    ...",
        before_version=_V36,
        reason="Le parole chiave esplicite rendono il codice asincrono riconoscibile a colpo d'occhio.",
        notes="E' la rimozione che ha rotto piu' codice 3.5/3.6 di tutto il resto della release.",
        headline=True,
    ),
    _f(
        "dict-ordering",
        "L'ordine dei dizionari diventa parte del linguaggio",
        _V37,
        Category.TYPES,
        Kind.LANGUAGE,
        "L'ordine di inserimento e' garantito dalla specifica, non piu' solo "
        "dall'implementazione.",
        before="# 3.6: ordine garantito da CPython, non dalla specifica\nfor k in d:\n    print(k)  # ordine non garantito dalla specifica",
        after="# 3.7+: ordine di inserimento garantito\nfor k in d:\n    print(k)  # ordine di inserimento",
        before_version=_V36,
        reason="Dipendere da un dettaglio dell'implementazione non e' un contratto sostenibile.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.8
    # -----------------------------------------------------------------------
    _f(
        "walrus",
        "Operatore walrus (`:=`)",
        _V38,
        Category.SYNTAX,
        Kind.SYNTAX,
        "Assegnazione dentro un'espressione.",
        pep="PEP 572",
        before="def cerca(d: dict[str, int]) -> int | None:\n    if 'a' in d:\n        risultato = d['a']\n        return risultato\n    return None",
        after="def cerca(d: dict[str, int]) -> int | None:\n    if (risultato := d.get('a')) is not None:\n        return risultato\n    return None",
        before_version=_V37,
        reason="Evita la variabile temporanea quando il valore serve sia per il test sia per l'uso.",
        notes="Da usare con parenesi: quasi sempre serve `(x := f())`.",
        headline=True,
    ),
    _f(
        "f-string-debug",
        "Specificatore `=` nelle f-string",
        _V38,
        Category.SYNTAX,
        Kind.SYNTAX,
        "`f'{x=}'` scrive il testo dell'espressione insieme al suo valore.",
        before="# fino alla 3.7\nprint('x =', x)\nprint('risultato =', risultato)",
        after="print(f'x={x}')\nprint(f'{risultato=}')  # risultato = 42",
        before_version=_V37,
        reason=(
            "Il formato piu' comune del debugging era ripetere il nome della "
            "variabile due volte, con il rischio di scrivere due nomi diversi."
        ),
        notes="Il `=` non accetta conversioni né specificatori di formato: `f'{x=:.2f}'` non e' valido.",
    ),
    _f(
        "positional-only",
        "Parametri positional-only con `/`",
        _V38,
        Category.FUNCTIONS,
        Kind.SYNTAX,
        "I parametri prima di `/` non possono essere passati per nome.",
        pep="PEP 570",
        before="# fino alla 3.7\ndef confronta(a, b, chiave=None):\n    ...",
        after="def confronta(a, b, /, chiave=None):\n    ...",
        before_version=_V37,
        reason=(
            "Permette di rinominare un parametro interno senza rompere i chiamanti, "
            "e di accettare che un parametro si chiami come un altro nella chiamata."
        ),
        headline=True,
    ),
    _f(
        "typing-extensions-core",
        "`TypedDict`, `Literal`, `Final`, `Protocol` in `typing`",
        _V38,
        Category.TYPING,
        Kind.API,
        "Tipizzazione di dizionari, valori letterali, costanti e protocolli strutturali.",
        pep="PEP 589",
        after="from typing import Literal, Protocol, TypedDict\n\nclass Config(TypedDict):\n    host: str\n\nclass SupportaLen(Protocol):\n    def __len__(self) -> int: ...",
        before_version=_V37,
        reason="Permette di descrivere tipi che non sono classi: dizionari e protocolli.",
        notes="`TypedDict` e' PEP 589, `Protocol` e' PEP 544, `Literal` PEP 586, `Final` PEP 591.",
        headline=True,
    ),
    _f(
        "cached-property",
        "`functools.cached_property`",
        _V38,
        Category.DECORATORS,
        Kind.API,
        "Proprieta' calcolata una volta sola e memorizzata nell'istanza.",
        after="from functools import cached_property\n\nclass Relazione:\n    @cached_property\n    def righe(self) -> list[str]:\n        return self._carica_righe()",
        before_version=_V37,
        reason="Prima serviva un decoratore di terze parti o il trucco con `self._cache`.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.9
    # -----------------------------------------------------------------------
    _f(
        "builtin-generics",
        "Generics sulle raccolte standard (`list[str]`)",
        _V39,
        Category.TYPING,
        Kind.SYNTAX,
        "Le raccolte standard accettano parametri di tipo direttamente.",
        pep="PEP 585",
        before="from typing import Dict, List, Optional, Set, Tuple\n\ndef carica(ids: List[int]) -> Dict[int, str]:\n    ...",
        after="def carica(ids: list[int]) -> dict[int, str]:\n    ...",
        before_version=_V38,
        reason="`typing.List` era una copia necessaria perche' `list` non era sottoscrivibile.",
        notes="Le annotazioni diventano subscriptable a runtime: `list[str]` e' un `types.GenericAlias`.",
        headline=True,
    ),
    _f(
        "dict-union",
        "Unione di dizionari con `|`",
        _V39,
        Category.TYPES,
        Kind.SYNTAX,
        "L'unione e l'aggiornamento tra dizionari diventano operatori.",
        pep="PEP 584",
        before="default = dict(base)\ndefault.update(extra)",
        after="default = base | extra\ndefault |= {'debug': True}",
        before_version=_V38,
        reason="Tre righe di copia e mutazione diventano una, e la copia e' esplicita.",
        headline=True,
    ),
    _f(
        "removeprefix",
        "`str.removeprefix()` e `str.removesuffix()`",
        _V39,
        Category.SYNTAX,
        Kind.API,
        "Rimozione controllata di un prefisso o suffisso.",
        pep="PEP 616",
        after="percorso = '/srv/app/utenti.txt'\nrelativo = percorso.removeprefix('/srv/')",
        before_version=_V38,
        reason="Si evita il test `startswith()` seguito da `len()` e slicing.",
        headline=True,
    ),
    _f(
        "peg-parser",
        "Nuovo parser PEG",
        _V39,
        Category.IOTOOLS,
        Kind.LANGUAGE,
        "Il parser basato su PEG sostituisce quello LL(1).",
        pep="PEP 617",
        reason=(
            "La grammatica era frammentata fra parser e compilatore; il PEG "
            "consente una singola fonte e una diagnostica migliore."
        ),
        notes=(
            "In 3.9 il parser precedente era ancora selezionabile con "
            "`-X oldparser`; l'opzione e' stata rimossa in 3.10."
        ),
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.10
    # -----------------------------------------------------------------------
    _f(
        "pattern-matching",
        "Structural pattern matching (`match` / `case`)",
        _V310,
        Category.SYNTAX,
        Kind.SYNTAX,
        "`match` e `case` sono parole chiave morbide: funzionano come "
        "identificatori se non sono usati in posizione di pattern.",
        pep="PEP 634",
        before="# fino alla 3.9\ndef esegui(comando):\n    if isinstance(comando, str):\n        if comando == 'start':\n            return start()\n        elif comando == 'stop':\n            return stop()\n    elif isinstance(comando, list):\n        return [esegui(c) for c in comando]\n    raise ValueError(comando)",
        after="def esegui(comando):\n    match comando:\n        case 'start':\n            return start()\n        case 'stop':\n            return stop()\n        case [primo, *resto]:\n            return [primo, *[esegui(c) for c in resto]]\n        case str() as testo:\n            raise ValueError(testo)\n        case _:\n            raise ValueError(f'comando non gestito: {comando!r}')",
        before_version=_V39,
        reason=(
            "I confronti annidati su tipo e forma richiedevano catene di `if` e "
            "controlli ripetuti sullo stesso valore."
        ),
        notes=(
            "Non e' un `switch`: i pattern si controllano dall'alto verso il "
            "basso e il primo che corrisponde vince."
        ),
        headline=True,
    ),
    _f(
        "union-types",
        "Unioni di tipo con `X | Y`",
        _V310,
        Category.TYPING,
        Kind.SYNTAX,
        "Le unioni si scrivono con l'operatore `|`, anche a runtime.",
        pep="PEP 604",
        before="from typing import Optional, Union\n\ndef cerca(id: Union[int, str, None] = None) -> Optional[int]:\n    ...",
        after="def cerca(id: int | str | None = None) -> int | None:\n    ...",
        before_version=_V39,
        reason="`Optional[X]` era zucchero per `Union[X, None]`: due modi per lo stesso tipo.",
        notes="Usabile anche in `isinstance(x, int | str)`.",
        headline=True,
    ),
    _f(
        "parenthesized-with",
        "Context manager tra parentesi",
        _V310,
        Category.SYNTAX,
        Kind.SYNTAX,
        "Gli elementi di un `with` possono essere racchiusi fra parentesi e "
        "suddivisi su piu' righe.",
        after="with (\n    open('a.txt') as a,\n    open('b.txt') as b,\n):\n    ...",
        before_version=_V39,
        reason=(
            "La continuazione con barra rovesciata era scomoda e fragile; il "
            "parser PEG rende possibile la grammatica con parentesi."
        ),
        notes="Se il `with` attraversa piu' righe, le parentesi sono consigliate anche per compatibilita'.",
        headline=True,
    ),
    _f(
        "zip-strict",
        "`zip(strict=True)`",
        _V310,
        Category.FUNCTIONS,
        Kind.API,
        "Lo zip segnala un errore se le sequenze hanno lunghezza diversa.",
        pep="PEP 618",
        after="for a, b in zip(seq_a, seq_b, strict=True):\n    ...",
        reason="Lo zip silenziosamente troncava, nascondendo un bug di allineamento dei dati.",
        notes="`strict=False` e' il comportamento predefinito, identico a prima.",
        headline=True,
    ),
    _f(
        "dataclass-slots-kw-only",
        "`dataclasses`: `slots=True` e `kw_only=True`",
        _V310,
        Category.OOP,
        Kind.API,
        "Le dataclassi possono occupare gli slot e imporre argomenti per nome.",
        after="from dataclasses import dataclass\n\n@dataclass(slots=True)\nclass Punto:\n    x: float\n    y: float",
        reason="Gli slot riducono il consumo di memoria e l'attrito sugli attributi.",
    ),
    # -----------------------------------------------------------------------
    # 3.11
    # -----------------------------------------------------------------------
    _f(
        "except-star",
        "`ExceptionGroup` e `except*`",
        _V311,
        Category.EXCEPTIONS,
        Kind.SYNTAX,
        "Permette di propagare piu' eccezioni indipendenti insieme.",
        pep="PEP 654",
        before="def carica_tutto(risorse):\n    errori = []\n    risultati = []\n    for risorsa in risorse:\n        try:\n            risultati.append(elabora(risorsa))\n        except ErroreDominio as exc:\n            errori.append(exc)\n    if errori:\n        raise ErroreDominio(errori)  # lista dentro l'eccezione",
        after="def carica_tutto(risorse):\n    risultati = []\n    for risorsa in risorse:\n        risultati.append(elabora(risorsa))  # solleva da sola\n\nasync def carica_insieme(rs):\n    try:\n        async with asyncio.TaskGroup() as gruppo:\n            for r in rs:\n                gruppo.create_task(elabora(r))\n    except* ErroreDominio as gruppo_errori:\n        log.error('falliti: %s', gruppo_errori.exceptions)",
        before_version=_V310,
        reason=(
            "Accumulare gli errori in una lista dentro l'eccezione perdi informazione: "
            "non si distingue piu' quale operazione e' fallita."
        ),
        notes=(
            "Dentro `except*` non sono ammessi `return`, `break` e `continue`: "
            "e' un errore di sintassi, non un avviso."
        ),
        headline=True,
    ),
    _f(
        "exception-notes",
        "`BaseException.add_note()`",
        _V311,
        Category.EXCEPTIONS,
        Kind.API,
        "Aggiunge righe di contesto mostrate nel traceback.",
        pep="PEP 678",
        after="def recupera(utente: str) -> None:\n    try:\n        carica(utente)\n    except KeyError as exc:\n        exc.add_note(f'utente richiesto: {utente!r}')\n        raise",
        reason="Arricchire il traceback senza perdere il tipo dell'eccezione originale.",
        headline=True,
    ),
    _f(
        "exception-error-locations",
        "Posizioni di errore fini nel traceback",
        _V311,
        Category.EXCEPTIONS,
        Kind.LANGUAGE,
        "Il traceback indica colonna e fine riga oltre che il numero di riga.",
        pep="PEP 657",
        after="def calcola(totale, divisore):\n    # il traceback del 3.11 indica anche colonna e fine riga\n    return totale / divisore",
        notes="Esempio di traceback: `File 'esempio.py', line 2, in calcola` seguito da "
        "`    return totale / divisore` con il caret sotto la divisione.",
        reason="Su una riga sola l'indicazione della riga non basta a individuare l'errore.",
        headline=True,
    ),
    _f(
        "self-type",
        "`typing.Self`",
        _V311,
        Category.TYPING,
        Kind.API,
        "Annota un metodo che restituisce il tipo dell'istanza, non della classe.",
        pep="PEP 673",
        after="from typing import Self\n\nclass Fabbrica:\n    def nuovo(self) -> Self:\n        return type(self)()",
        reason="Prima si usava un TypeVar, verboso e non sempre corretto con l'ereditarieta'.",
        headline=True,
    ),
    _f(
        "specializing-interpreter",
        "Interprete adattivo con specializzazione",
        _V311,
        Category.PERFORMANCE,
        Kind.PERFORMANCE,
        "CPython 3.11 specializza i bytecode sulla situazione osservata a runtime.",
        pep="PEP 659",
        reason="Permette di ottimizzare i percorsi caldi senza costi per i percorsi freddi.",
        notes=(
            "Il GIL non e' stato rimosso: serve la build free-threaded "
            "sperimentale introdotta con Python 3.13."
        ),
        headline=True,
    ),
    _f(
        "tomllib",
        "Modulo `tomllib`",
        _V311,
        Category.PACKAGING,
        Kind.API,
        "Lettore TOML nella standard library, in sola lettura.",
        pep="PEP 680",
        after="import tomllib\n\nwith open('pyproject.toml', 'rb') as f:\n    config = tomllib.load(f)",
        reason="TOML e' il formato di `pyproject.toml`: leggero in stdlib evita una dipendenza.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.12
    # -----------------------------------------------------------------------
    _f(
        "type-params",
        "Sintassi dei type parameter (PEP 695)",
        _V312,
        Category.TYPING,
        Kind.SYNTAX,
        "I parametri di tipo si dichiarano con `def f[T]` e `class C[T]`.",
        pep="PEP 695",
        before="# fino alla 3.11\nfrom typing import Generic, TypeVar\n\nT = TypeVar('T')\n\ndef primo(items: list[T]) -> T:\n    return items[0]\n\nclass Scatola(Generic[T]):\n    ...",
        after="def primo[T](items: list[T]) -> T:\n    return items[0]\n\nclass Scatola[T]:\n    ...",
        before_version=_V311,
        reason=(
            "Il `TypeVar` globale creava conflitti di nome fra moduli e rendeva "
            "la dichiarazione lontana dalla funzione che la usa."
        ),
        notes=(
            "Introduce anche `type Alias = ...` e l'ambiente di annotazione separato "
            "dalle variabili del modulo."
        ),
        headline=True,
    ),
    _f(
        "f-string-multiline",
        "f-string multilinea e riutilizzo delle quote",
        _V312,
        Category.SYNTAX,
        Kind.LANGUAGE,
        "Le f-string possono contenere a capo, commenti e gli stessi delimitatori.",
        pep="PEP 701",
        before="# fino alla 3.11\nsql = (\"SELECT *\\n\"\n       \"FROM utenti\\n\"\n       \"WHERE attivo = 1\")",
        after="sql = f\"\"\"SELECT *\nFROM utenti\nWHERE attivo = {1}\n\"\"\"",
        before_version=_V311,
        reason=(
            "Prima la grammatica vieta-va le stesse virgolette all'interno della "
            "f-string e le sequenze di escape andavano raddoppiate."
        ),
        notes="Compatibile all'indietro: il codice 3.12 resta valido nelle versioni precedenti.",
        headline=True,
    ),
    _f(
        "typing-override",
        "Decoratore `typing.override`",
        _V312,
        Category.TYPING,
        Kind.API,
        "Segnala che un metodo sovrascrive un metodo della classe base.",
        pep="PEP 698",
        after="from typing import override\n\nclass Base:\n    def salva(self) -> None: ...\n\nclass Derivata(Base):\n    @override\n    def salva(self) -> None: ...",
        before="# fino alla 3.11: nessuna verifica\nclass Derivata(Base):\n    def salva(self) -> None: ...   # errore di nome non segnalato",
        before_version=_V311,
        reason="Un errore di battitura nel nome del metodo non veniva segnalato da nessun strumento.",
        headline=True,
    ),
    _f(
        "sys-monitoring",
        "`sys.monitoring`",
        _V312,
        Category.IOTOOLS,
        Kind.API,
        "API di monitoraggio a basso impatto per strumenti come profiler e debugger.",
        pep="PEP 669",
        after="import sys\n\ndef profilo(code, offset):\n    ...\n\nsys.monitoring.register_callback(sys.monitoring.PROFILE, profilo)\nsys.monitoring.set_events(sys.monitoring.PROFILE)",
        reason="`sys.settrace` e' invasivo e lento; questa API usa un meccanismo distinto.",
        headline=True,
    ),
    _f(
        "distutils-removed",
        "`distutils` rimosso dalla standard library",
        _V312,
        Category.PACKAGING,
        Kind.REMOVAL,
        "Il modulo di packaging storico e' stato rimosso dopo la deprecazione "
        "annunciata in Python 3.10.",
        pep="PEP 632",
        before="from distutils.core import setup\n\nsetup(name='mio', version='1.0')",
        after="from setuptools import setup\n\nsetup(name='mio', version='1.0')",
        before_version=_V311,
        reason="Duplicava `setuptools` e dipendeva da `imp`, rimosso nella stessa release.",
        notes="`setuptools>=61` dichiara i metadati direttamente in `pyproject.toml` (PEP 621).",
        headline=True,
    ),
    _f(
        "per-interpreter-gil",
        "GIL per interprete",
        _V312,
        Category.PERFORMANCE,
        Kind.LANGUAGE,
        "Ogni interprete secondario puo' avere il proprio GIL.",
        pep="PEP 684",
        after="import _testcapi\n\nid = _testcapi.make_gil_switching_interpreter()",
        reason="Apre la strada agli interpreti indipendenti nella standard library.",
        notes=(
            "API riservata alla C API. Il supporto pubblico e' arrivato con "
            "`concurrent.interpreters` in Python 3.14 (PEP 734)."
        ),
        headline=True,
    ),
    _f(
        "comprehension-inlining",
        "Inlining delle comprensioni",
        _V312,
        Category.PERFORMANCE,
        Kind.PERFORMANCE,
        "Le comprensioni sono state trasformate in codice inline, senza "
        "chiamata di funzione.",
        pep="PEP 709",
        reason="Le comprensioni hanno un proprio scope: l'inlining elimina il costo della funzione.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.13
    # -----------------------------------------------------------------------
    _f(
        "free-threading",
        "Build free-threaded sperimentale",
        _V313,
        Category.PERFORMANCE,
        Kind.LANGUAGE,
        "CPython puo' essere compilato senza GIL.",
        pep="PEP 703",
        after="import sys\n\nif not sys._is_gil_enabled():\n    print('esecuzione senza GIL')",
        reason="Il GIL e' il limite principale all'uso di piu' core per codice puro Python.",
        notes=(
            "La modalita' e' sperimentale e ha un costo in single-thread. "
            "La prima release con free-threading supportato ufficialmente e' 3.14 (PEP 779)."
        ),
        status="experimental",
        headline=True,
    ),
    _f(
        "experimental-jit",
        "JIT sperimentale",
        _V313,
        Category.PERFORMANCE,
        Kind.LANGUAGE,
        "Un compilatore just-in-time opzionale, attivato in compilazione.",
        pep="PEP 744",
        after="import sys\n\nif hasattr(sys, '_jit'):\n    attivo = sys._jit.is_available()",
        reason="Dopo anni di ottimizzazioni statiche, la compilazione a runtime diventa praticabile.",
        notes="Da riga di comando si abilita con `python3.13 --enable-experimental-jit`. "
        "Il guadagno medio dichiarato e' di pochi punti percentuali: verificare con "
        "le proprie misure.",
        status="experimental",
        headline=True,
    ),
    _f(
        "copy-replace",
        "`copy.replace()` e il protocollo `__replace__`",
        _V313,
        Category.TYPES,
        Kind.API,
        "Copia modificando campi, con supporto per dataclassi, namedtuple e oggetti immutabili.",
        after="import copy\n\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass Utente:\n    nome: str\n    admin: bool\n\nu2 = copy.replace(u1, admin=True)",
        reason="Prima si usava `dataclasses.replace` o si ricostruiva l'oggetto a mano.",
        headline=True,
    ),
    _f(
        "deprecated-2to3-removed",
        "Rimossi `2to3` e `lib2to3`",
        _V313,
        Category.COMPATIBILITY,
        Kind.REMOVAL,
        "Lo strumento che automatizzava la conversione da Python 2 e' stato "
        "rimosso, insieme al modulo `lib2to3` su cui si basava.",
        before="# Python 3.12 e precedenti\npython -m lib2to3 -w -n mio_progetto/\n\nfrom lib2to3.refactor import RefactoringTool",
        after="# Python 3.13: il percorso di migrazione e' leggere il codice,\n# capire cosa e' cambiato e riscrivere a mano",
        before_version=_V312,
        deprecated=_V311,
        removed=_V313,
        reason=(
            "`2to3` riscriveva il codice senza capire il significato: produceva "
            "risultati che a volte compilavano e a volte no, e la correzione "
            "manuale restava necessaria. Mantenerlo in mantenimento era un costo "
            "che il progetto ha deciso di non pagare."
        ),
        notes=(
            "Per questo progetto la scelta e' la stessa: gli esempi Python 2 "
            "restano intatti e vengono analizzati come testo da `pme.legacy`, "
            "invece di essere riscritti automaticamente."
        ),
        source="https://docs.python.org/3/whatsnew/3.13.html",
        headline=True,
    ),
    _f(
        "typeddict-fields-deprecation",
        "L'argomento `fields` di `TypedDict`",
        _V313,
        Category.TYPING,
        Kind.DEPRECATION,
        "Non passare `None` (o omettere i campi) alla forma funzionale di "
        "`TypedDict`: dal 3.13 e' deprecato e dal 3.16 solleva `ValueError`.",
        before="from typing import TypedDict\n\nFilm = TypedDict('Film')\n\nRegista = TypedDict('Regista', nome=str)",
        after="from typing import TypedDict\n\nFilm = TypedDict('Film', {})  # nessun campo\n\nclass Regista(TypedDict):\n    nome: str",
        before_version=_V38,
        deprecated=_V313,
        removed=_V316,
        reason=(
            "`TypedDict('Film')` non poteva essere costruito in modo coerente: "
            "la forma funzionale accettava un nome senza campi, mentre "
            "l'API di subscript richiede una lista di campi. La deprecazione "
            "chiude il caso ambiguo a favore della sintassi con classe o con "
            "dizionario esplicito."
        ),
        notes=(
            "Lo stesso vale per `importlib.metadata.EntryPoints`, deprecata "
            "dopo che ne era cambiata la forma restituita, e per "
            "`mimetypes.MimeTypes.add_type()` con estensione gia' puntata: "
            "dal 3.16 anche l'errore diventa esplicito invece di silenzioso."
        ),
        source="https://docs.python.org/3/deprecations/index.html",
    ),
    _f(
        "warnings-deprecated",
        "`warnings.deprecated`",
        _V313,
        Category.IOTOOLS,
        Kind.API,
        "Decoratore che segnala l'uso di un'API deprecata e informa i type checker.",
        pep="PEP 702",
        after="from warnings import deprecated\n\n@deprecated('usare parse_v2()')\ndef parse_v1(testo: str) -> dict:\n    ...",
        reason="Unificare il deprecamento fra runtime e analisi statica.",
        headline=True,
    ),
    _f(
        "dead-batteries-removed",
        "Rimossi 19 moduli \"dead batteries\"",
        _V313,
        Category.COMPATIBILITY,
        Kind.REMOVAL,
        "Moduli rimossi dopo PEP 594: `cgi`, `telnetlib`, `nntplib`, `imghdr`, "
        "`audioop`, `crypt`, `mailcap`, `pipes`, `uu`, `xdrlib` e altri.",
        pep="PEP 594",
        before="import cgi\n\nform = cgi.FieldStorage(fp=stream)\nvalori = dict(form)",
        after="import email\n\nmessaggio = email.message_from_binary_file(stream)\nvalori = dict(messaggio)",
        before_version=_V312,
        reason="Moduli senza manutentori, con problemi di sicurezza noti e sostituiti.",
        notes="I sostituti sono indicati in `PEP 594` e in `docs.python.org/3/whatsnew/3.13.html`.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.14
    # -----------------------------------------------------------------------
    _f(
        "t-string",
        "t-string (stringhe template)",
        _V314,
        Category.SYNTAX,
        Kind.SYNTAX,
        "Come le f-string, ma il risultato e' un `Template` con i valori "
        "esposti come metadati, non ancora serializzati.",
        pep="PEP 750",
        before="# fino alla 3.13\nsql = f\"SELECT * FROM utenti WHERE nome = '{nome}'\"",
        after="from string.templatelib import Template\n\nsql = t\"SELECT * FROM utenti WHERE nome = {nome!r}\"\n# Template con .strings e .interpolations: si puo' ispezionare e validare",
        before_version=_V313,
        reason=(
            "Le f-string rendono impossibile distinguere il codice dal dato: "
            "una SQL costruita con f-string e' un rischio di iniezione."
        ),
        status="stable",
        headline=True,
    ),
    _f(
        "deferred-annotations",
        "Valutazione differita delle annotazioni (PEP 649)",
        _V314,
        Category.TYPING,
        Kind.LANGUAGE,
        "Le annotazioni vengono valutate solo quando servono, tramite "
        "descrittori; `annotationlib` permette di forzarne la valutazione.",
        pep="PEP 649",
        after="def somma(a: int, b: int) -> int:\n    return a + b\n\n# forward reference senza stringhe\ne = somma(1, 2)\nassert 'somma' in annotationlib.get_annotations(somma)",
        reason=(
            "In 3.10-3.13 le annotazioni erano valutate alla definizione, il che "
            "costringeva a usare stringhe per i riferimenti in avanti."
        ),
        notes=(
            "`from __future__ import annotations` e' incompatibile con PEP 649: "
            "il futuro e' stato messo in sospeso indefinitamente con Python 3.11."
        ),
        headline=True,
    ),
    _f(
        "except-without-parens",
        "`except E1, E2:` senza parentesi",
        _V314,
        Category.EXCEPTIONS,
        Kind.SYNTAX,
        "La clausola `except` (e `except*`) puo' elencare piu' eccezioni senza "
        "le parentesi.",
        pep="PEP 758",
        after="try:\n    carica()\nexcept FileNotFoundError, PermissionError:\n    log.error('risorsa non disponibile')",
        before_version=_V313,
        reason="Le parentesi erano necessarie solo per un motivo grammaticale ormai risolto.",
        notes="Vale anche per `except*`, dove pero' resta vietato uscire dal blocco con `return`.",
        headline=True,
    ),
    _f(
        "multiple-interpreters",
        "`concurrent.interpreters`",
        _V314,
        Category.PERFORMANCE,
        Kind.API,
        "Interpreti Python indipendenti nella standard library, ognuno con il proprio GIL.",
        pep="PEP 734",
        after="from concurrent.futures import InterpreterPoolExecutor\n\nwith InterpreterPoolExecutor() as pool:\n    risultati = list(pool.submit(analizza, riga).result() for riga in righe)",
        reason=(
            "Il lavoro parallelo su piu' core senza thread era possibile solo "
            "con processi, con il costo della serializzazione."
        ),
        notes="In 3.12 la stessa idea era disponibile solo via C API (PEP 684).",
        headline=True,
    ),
    _f(
        "finally-control-flow",
        "`return`/`break`/`continue` vietati nel `finally`",
        _V314,
        Category.SYNTAX,
        Kind.LANGUAGE,
        "Uscire da un blocco `finally` con un salto di controllo produce una "
        "`SyntaxWarning`: il codice viene eseguito ma il flusso era ambiguo.",
        pep="PEP 765",
        after="def chiudi(risorsa):\n    try:\n        usa(risorsa)\n    finally:\n        risorsa.chiedi_chiusura()\n        # niente return: il finally deve chiudere, non restituire",
        reason="Il salto nel `finally` scartava silenziosamente eccezioni in volo.",
        notes="Da notare l'inversione: nel 3.8 era stato *consentito* il `continue` nel `finally`.",
        headline=True,
    ),
    _f(
        "zstd",
        "Modulo `compression.zstd`",
        _V314,
        Category.IOTOOLS,
        Kind.API,
        "Supporto Zstandard nella standard library.",
        pep="PEP 784",
        after="from compression import zstd\n\ndati = zstd.compress(grezzo)",
        reason="`bz2`, `lzma` e `gzip` non coprono il formato comunemente usato come Zstandard.",
        headline=True,
    ),
    _f(
        "remote-debug-interface",
        "Interfaccia di debug remoto sicura",
        _V314,
        Category.IOTOOLS,
        Kind.LANGUAGE,
        "`sys.remote_exec()` permette a un debugger esterno di eseguire codice, "
        "con protezioni e disattivazione esplicita.",
        pep="PEP 768",
        reason="Il debug da remoto era legato a meccanismi non sicuri.",
        notes="La superficie e' ampia per definizione: va disattivata con `PYTHON_DISABLE_REMOTE_DEBUG`.",
        headline=True,
    ),
    # -----------------------------------------------------------------------
    # 3.15 (prerelease, dato pianificato: PEP 790)
    # -----------------------------------------------------------------------
    _f(
        "utf8-default",
        "UTF-8 come encoding predefinito",
        _V315,
        Category.TYPES,
        Kind.LANGUAGE,
        "Le operazioni di I/O senza `encoding` esplicito usano UTF-8, "
        "indipendentemente dall'impostazione di sistema.",
        pep="PEP 686",
        before="# fino alla 3.14: dipende dalla locale\nwith open('dati.txt') as f:\n    ...",
        after="# 3.15: sempre UTF-8\nwith open('dati.txt', encoding='utf-8') as f:\n    ...",
        before_version=_V314,
        reason="I default dipendenti dalla locale rendevano il comportamento non portabile.",
        notes="Stato prerelease: verificare alla data di rilascio (PEP 790 prevedeva il 2026-10-01).",
        status="planned",
        headline=True,
    ),
    _f(
        "lazy-imports",
        "Import espliciti lazy",
        _V315,
        Category.PACKAGING,
        Kind.LANGUAGE,
        "Gli import rimandati diventano dichiarativi.",
        pep="PEP 810",
        reason="Riduce il costo di avvio senza rinunciare alla chiarezza del codice.",
        status="planned",
        headline=True,
    ),
    _f(
        "frozendict",
        "Tipo built-in `frozendict`",
        _V315,
        Category.TYPES,
        Kind.API,
        "Un dizionario immutabile e hashabile nella standard library.",
        pep="PEP 814",
        reason="Era disponibile solo come `types.MappingProxyType`, che non e' confrontabile.",
        status="planned",
        headline=True,
    ),
)


_INDEX: Dict[str, Feature] = {feature.id: feature for feature in FEATURES}


def _validate() -> None:
    """Controlla l'integrita' del catalogo all'import del modulo.

    Sono errori di sviluppo, non condizioni gestibili: e' preferibile che
    l'import fallisca subito invece di produrre schede sbagliate.
    """
    from pme.probes import PROBES

    if len(_INDEX) != len(FEATURES):
        duplicates = sorted(
            {f.id for f in FEATURES if sum(1 for g in FEATURES if g.id == f.id) > 1}
        )
        raise ValueError(f"identificativi duplicati nel catalogo: {duplicates}")

    for feature in FEATURES:
        if feature.deprecated and feature.removed and feature.deprecated > feature.removed:
            raise ValueError(f"{feature.id}: deprecazione successiva alla rimozione")
        if feature.kind is not Kind.REMOVAL:
            # per una rimozione `introduced` indica la versione in cui l'elemento
            # e' sparito, quindi la deprecazione puo' legittimamente precederla;
            # per ogni altra scheda deve invece venire dopo l'introduzione
            if feature.deprecated and feature.deprecated < feature.introduced:
                raise ValueError(f"{feature.id}: deprecazione precedente all'introduzione")
            if feature.removed and feature.removed < feature.introduced:
                raise ValueError(f"{feature.id}: rimozione precedente all'introduzione")
        elif feature.removed and feature.removed != feature.introduced:
            raise ValueError(f"{feature.id}: per una rimozione `removed` coincide con `introduced`")
        if not feature.summary:
            raise ValueError(f"{feature.id}: riassunto mancante")
        if not feature.reason:
            raise ValueError(f"{feature.id}: motivazione mancante")
        if not feature.source.startswith("https://"):
            raise ValueError(f"{feature.id}: fonte non ufficiale o assente")
        # il codice "come si usa oggi" deve essere Python valido: e' il
        # contralto del catalogo, e se non e' eseguibile non e' documentazione
        if feature.after:
            try:
                compile(feature.after, f"<catalogo:{feature.id}:after>", "exec")
            except SyntaxError as err:
                raise ValueError(
                    f"{feature.id}: il codice 'dopo' non compila ({err.msg}, "
                    f"riga {err.lineno})"
                ) from err

    known = {probe.feature_id for probe in PROBES if probe.feature_id}
    dangling = known - set(_INDEX)
    if dangling:
        raise ValueError(f"le sonde riferiscono a funzionalita' assenti: {sorted(dangling)}")


_validate()


def iter_features() -> Iterator[Feature]:
    """Itera su tutte le schede in ordine di introduzione."""
    return iter(sorted(FEATURES, key=lambda f: (f.introduced, f.id)))


def by_id(feature_id: str) -> Feature:
    """Restituisce la scheda con l'identificativo indicato.

    Raises:
        KeyError: se l'identificativo non esiste.
    """
    return _INDEX[feature_id]


def get(feature_id: str) -> Feature:
    """Come :func:`by_id`, ma con un messaggio d'errore piu' utile."""
    try:
        return _INDEX[feature_id]
    except KeyError:
        raise KeyError(
            f"funzionalita' sconosciuta: {feature_id!r} "
            f"(disponibili: {', '.join(sorted(_INDEX))})"
        ) from None


def introduced_in(version: Version) -> Tuple[Feature, ...]:
    """Schede la cui introduzione cade in ``version``."""
    return tuple(f for f in FEATURES if f.introduced == version)


def deprecated_in(version: Version) -> Tuple[Feature, ...]:
    """Schede deprecate in ``version``."""
    return tuple(f for f in FEATURES if f.deprecated == version)


def removed_in(version: Version) -> Tuple[Feature, ...]:
    """Schede rimosse in ``version``."""
    return tuple(f for f in FEATURES if f.removed == version)


def headline_features(version: Version, limit: int = 3) -> Tuple[Feature, ...]:
    """Restituisce le schede piu' rappresentative di una versione.

    Se esistono schede con :attr:`Feature.headline` attivo, vengono usate
    quelle: la scelta e' redazionale, non automatica. Altrimenti si ricade su
    un punteggio deterministico che privilegia le schede con codice prima/dopo e
    motivazione scritta, perche' sono le piu' utili alla lettura.
    """
    in_version = [f for f in FEATURES if f.introduced == version]
    marked = [f for f in in_version if f.headline]
    if marked:
        # l'ordine di dichiarazione nel catalogo e' quello di importanza redazionale
        return tuple(marked[:limit])

    candidates = [f for f in in_version if f.kind is not Kind.ADVICE]
    candidates.sort(
        key=lambda f: (
            -(
                2 * (bool(f.before) + bool(f.after))
                + bool(f.pep)
                + bool(f.reason)
                + (f.kind is Kind.SYNTAX)
            ),
            f.id,
        )
    )
    return tuple(candidates[:limit])


def changed_between(older: Version, newer: Version) -> Dict[str, Tuple[Feature, ...]]:
    """Riepilogo dei cambiamenti fra due versioni.

    Il risultato e' pensato per essere stampato dalla CLI e per generare le
    sezioni "Impatto sul codice esistente" delle schede.

    La classificazione segue il tipo della scheda prima della finestra: una
    scheda di rimozione con ``introduced`` al 3.0 e' un cambiamento del 3.0,
    non una novita' del 3.0.

    Args:
        older: versione di partenza (esclusa).
        newer: versione di arrivo (inclusa).

    Returns:
        Mappa con le chiavi ``"introdotte"``, ``"deprecate"``, ``"rimosse"`` e
        ``"cambiate"``, dove ``"cambiate"`` raccoglie le schede il cui comportamento
        e' mutato nella finestra senza essere nuove.

    Raises:
        ValueError: se ``older`` e' successiva a ``newer``.
    """
    if older > newer:
        raise ValueError(f"finestra non valida: {older} -> {newer}")

    def added_at(feature: Feature) -> Optional[Version]:
        """Versione in cui la scheda introduce qualcosa di nuovo, se esiste."""
        return None if feature.kind is Kind.REMOVAL else feature.introduced

    def deprecated_at(feature: Feature) -> Optional[Version]:
        return feature.deprecated

    def removed_at(feature: Feature) -> Optional[Version]:
        if feature.removed is not None:
            return feature.removed
        # per le schede di rimozione pure `introduced` *e'* la data della rimozione
        return feature.introduced if feature.kind is Kind.REMOVAL else None

    def in_window(version: Optional[Version]) -> bool:
        return version is not None and older < version <= newer

    def by_id_sorted(features: Iterator[Feature]) -> Tuple[Feature, ...]:
        return tuple(sorted(features, key=lambda f: f.id))

    return {
        "introdotte": by_id_sorted(f for f in FEATURES if in_window(added_at(f))),
        "deprecate": by_id_sorted(f for f in FEATURES if in_window(deprecated_at(f))),
        "rimosse": by_id_sorted(f for f in FEATURES if in_window(removed_at(f))),
        "cambiate": by_id_sorted(
            f for f in FEATURES if in_window(deprecated_at(f)) or in_window(removed_at(f))
        ),
    }


def topical_index() -> Dict[Category, Tuple[Feature, ...]]:
    """Raggruppa tutte le schede per area tematica, in ordine di introduzione."""
    index: Dict[Category, list[Feature]] = {category: [] for category in Category}
    for feature in iter_features():
        index[feature.category].append(feature)
    return {category: tuple(items) for category, items in index.items()}


def requires(feature_id: str) -> Version:
    """Versione minima richiesta dalla funzionalita' indicata."""
    return by_id(feature_id).requires