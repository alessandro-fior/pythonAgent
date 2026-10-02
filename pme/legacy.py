"""Rilevamento e modernizzazione del codice Python legacy.

Questo modulo risponde alle quattro domande con cui si chiude ``agent.md`` §30,
applicandole a codice reale invece che a esempi di fantasia:

    "Da quale epoca arriva?"
        :func:`detect` restituisce, per ogni costrutto, la versione che l'ha
        introdotto e quella che l'ha rimosso.
    "Quali problemi di compatibilita' presenta?"
    :attr:`Finding.severity` distingue gli errori bloccanti dai suggerimenti.
    "Come lo trasformo in Python moderno?"
    :func:`modernize` applica le riscritture deterministiche; per le altre
    proposte la correzione resta un suggerimento testuale.
    "Quale versione minima di Python devo utilizzare?"
    :func:`minimum_version` calcola la versione minima richiesta dal codice
    rimasto dopo la modernizzazione.

Come e' fatto, e perche' non usa ``ast``: il codice da analizzare e' spesso
Python 2, quindi **non e' analizzabile** con ``ast.parse``. Il modulo
``tokenize`` invece e' puramente lessicale e accetta senza problemi anche la
sintassi del ``print`` come istruzione. E' il punto di partenza obbligato per
un analizzatore di codice legacy.

Limiti dichiarati: questo non e' ``2to3``. Le regole sono volutamente poche,
deterministiche e verificabili da test; le trasformazioni strutturali (per
esempio `dict.has_key(k)` -> `k in d`) vengono segnalate ma non applicate,
perche' richiedono di riscrivere l'espressione e non solo sostituirvi un token.

Esempio::

    >>> from pme.legacy import detect, modernize, minimum_version
    >>> trovare = detect("print 'ciao'\\n")
    >>> trovare[0].rule
    'print-statement'
    >>> trovare[0].severity
    <Severity.ERROR: 'errore'>
    >>> minimum_version("for i in xrange(3):\\n    print i\\n")
    '3.0'
"""

from __future__ import annotations

import io
import token as token_module
import tokenize
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from pme.version import Version, latest_stable

__all__ = [
    "Finding",
    "ModernizeResult",
    "Severity",
    "TextEdit",
    "detect",
    "modernize",
    "minimum_version",
    "rules",
    "summarize",
]


class Severity(str, Enum):
    """Gravita' di un ritrovamento.

    ``ERRORE``
        Il codice non gira su Python 3 (sintassi o API rimosse).
    ``AVVERTENZA``
        Il codice gira ma cambia significato: e' il caso peggiore, perche'
        silenzioso.
    ``SUGGERIMENTO``
        Il codice funziona, ma esiste un modo moderno e preferibile.
    """

    ERROR = "errore"
    WARNING = "avvertenza"
    ADVICE = "suggerimento"

    def __str__(self) -> str:
        """Restituisce l'etichetta leggibile della gravita'."""
        return self.value


#: Ordine di gravita' decrescente, usato per ordinare i rapporti.
_SEVERITY_ORDER = (Severity.ERROR, Severity.WARNING, Severity.ADVICE)


@dataclass(frozen=True)
class TextEdit:
    """Una sostituzione testuale espressa in offset assoluti di carattere.

    Gli offset sono assoluti (non riga/colonna) perche' l'applicazione di piu'
    modifiche sullo stesso testo e' piu' semplice e verificabile procedendo a
    ritroso.
    """

    start: int
    end: int
    replacement: str


@dataclass(frozen=True)
class Finding:
    """Un ritrovamento del rilevatore.

    Attributes:
        rule: identificativo della regola che ha scattato.
        title: nome leggibile della regola.
        severity: gravita' del problema.
        line: numero di riga (1-based).
        column: colonna (0-based, come in ``tokenize``).
        excerpt: frammento di testo che ha fatto scattare la regola.
        message: spiegazione e correzione proposta.
        fix: correzione automatica applicata, se presente.
        introduced: versione che ha introdotto il costrutto.
        removed: versione che l'ha rimosso, se e' stato rimosso.
        deprecated: versione che l'ha deprecato, se e' stato deprecato.
        feature_id: identificativo della scheda corrispondente nel catalogo.
    """

    rule: str
    title: str
    severity: Severity
    line: int
    column: int
    excerpt: str
    message: str
    fix: Optional[str] = None
    introduced: Optional[Version] = None
    removed: Optional[Version] = None
    deprecated: Optional[Version] = None
    feature_id: Optional[str] = None

    @property
    def is_blocking(self) -> bool:
        """``True`` se il ritrovamento impedisce l'esecuzione su Python 3."""
        return self.severity is Severity.ERROR

    def location(self) -> str:
        """Restituisce ``riga:colonna`` in forma leggibile."""
        return f"{self.line}:{self.column}"

    def as_line(self) -> str:
        """Restituisce la riga di rapporto pronta per la console."""
        marker = {Severity.ERROR: "E", Severity.WARNING: "A", Severity.ADVICE: "S"}[self.severity]
        return f"{marker} {self.location():>8}  {self.rule:<24} {self.message}"


@dataclass(frozen=True)
class ModernizeResult:
    """Esito di :func:`modernize`.

    Attributes:
        source: il sorgente risultante.
        original: il sorgente iniziale.
        findings: tutti i ritrovamenti, applicati o meno.
        applied: numero di modifiche effettivamente applicate.
        skipped: modifiche non applicate, con il motivo.
    """

    source: str
    original: str
    findings: Tuple[Finding, ...] = ()
    applied: int = 0
    skipped: Tuple[Tuple[str, str], ...] = ()

    @property
    def changed(self) -> bool:
        """``True`` se il sorgente e' cambiato."""
        return self.source != self.original


# ---------------------------------------------------------------------------
# Infrastruttura di analisi lessicale
# ---------------------------------------------------------------------------

_SKIPPED_TOKENS = frozenset(
    {
        token_module.COMMENT,
        token_module.NL,
        token_module.INDENT,
        token_module.DEDENT,
    }
)


@dataclass
class _Source:
    """Il sorgente con gli offset assoluti gia' calcolati.

    ``tokenize`` lavora con coppie ``(riga, colonna)``; gli offset assoluti
    servono per costruire e applicare le correzioni in modo indolore.
    """

    text: str
    lines: Tuple[str, ...]
    line_starts: Tuple[int, ...]
    tokens: Tuple[tokenize.TokenInfo, ...] = field(default_factory=tuple)

    @classmethod
    def build(cls, text: str) -> "_Source":
        """Tokenizza ``text`` tollerando gli errori lessicali.

        Il codice Python 2 produce token che Python 3 non sa interpretare
        (per esempio il backtick, che arriva come ``ERRORTOKEN``): non e' un
        errore, e' esattamente il caso da analizzare.
        """
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = tuple(normalized.splitlines(keepends=True))
        starts: List[int] = []
        offset = 0
        for line in lines:
            starts.append(offset)
            offset += len(line)
        starts.append(offset)
        source = cls(text=normalized, lines=lines, line_starts=tuple(starts))
        try:
            source.tokens = tuple(
                tokenize.generate_tokens(io.StringIO(normalized).readline)
            )
        except (tokenize.TokenError, IndentationError, SyntaxError):
            # File malformato: si analizza comunque cio' che e' stato tokenizzato.
            pass
        return source

    def offset(self, row: int, column: int) -> int:
        """Converte ``(riga, colonna)`` 1-based in offset assoluto."""
        index = min(max(row, 1), len(self.line_starts)) - 1
        return self.line_starts[index] + column

    def span(self, start: tokenize.TokenInfo, end: tokenize.TokenInfo) -> TextEdit:
        """Costruisce l'edizione che sostituisce da ``start`` a ``end``."""
        return TextEdit(
            start=self.offset(*start.start),
            end=self.offset(*end.end),
            replacement="",
        )

    def text_between(self, start: tokenize.TokenInfo, end: tokenize.TokenInfo) -> str:
        """Estrae il testo compreso fra due token."""
        begin = self.offset(*start.start)
        finish = self.offset(*end.end)
        return self.text[begin:finish]


def _is_code(tok: tokenize.TokenInfo) -> bool:
    """``True`` se il token e' parte della logica del programma."""
    return tok.type not in _SKIPPED_TOKENS and tok.type != token_module.ENDMARKER


def _code_indices(source: _Source) -> Tuple[int, ...]:
    """Indici dei token "di codice", nell'ordine in cui compaiono."""
    return tuple(i for i, tok in enumerate(source.tokens) if _is_code(tok))


@dataclass
class _Context:
    """Contesto passato a ogni regola durante la scansione."""

    source: _Source
    tokens: Tuple[tokenize.TokenInfo, ...]
    findings: List[Finding] = field(default_factory=list)
    edits: List[TextEdit] = field(default_factory=list)

    def add(
        self,
        rule: "_Rule",
        token_index: int,
        message: str,
        *,
        fix: Optional[TextEdit] = None,
    ) -> None:
        """Registra un ritrovamento e l'eventuale correzione."""
        tok = self.tokens[token_index]
        excerpt = tok.string
        end_index = token_index
        while end_index + 1 < len(self.tokens) and not _is_code(self.tokens[end_index + 1]):
            end_index += 1
        finding = Finding(
            rule=rule.id,
            title=rule.title,
            severity=rule.severity,
            line=tok.start[0],
            column=tok.start[1],
            excerpt=excerpt,
            message=message,
            fix=fix.replacement if fix is not None else None,
            introduced=rule.introduced,
            removed=rule.removed,
            deprecated=rule.deprecated,
            feature_id=rule.feature_id,
        )
        self.findings.append(finding)
        if fix is not None:
            self.edits.append(fix)


# ---------------------------------------------------------------------------
# Definizione delle regole
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Rule:
    """Una regola di rilevamento.

    Le regole sono intenzionalmente poche e deterministiche. Una regola che
    richiede di capire l'intento del programmatore non appartiene a questo
    modulo: va trattata come revisione manuale.
    """

    id: str
    title: str
    severity: Severity
    introduced: Optional[Version] = None
    removed: Optional[Version] = None
    deprecated: Optional[Version] = None
    feature_id: Optional[str] = None
    check: Optional[Callable[["_Context", int], None]] = None
    fix_replacement: Optional[str] = None
    message: str = ""


_V30 = Version(3, 0)
_V31 = Version(3, 1)
_V32 = Version(3, 2)
_V33 = Version(3, 3)
_V38 = Version(3, 8)
_V39 = Version(3, 9)
_V310 = Version(3, 10)
_V314 = Version(3, 14)


# -- 1. print come istruzione ------------------------------------------------


def _check_print(context: _Context, i: int) -> None:
    """Rileva ``print`` usato come istruzione.

    In Python 2 ``print`` e' una dichiarazione; in Python 3 e' un builtin che va
    chiamato. Il caso ``print (x, y)`` e' deliberatamente trattato come
    istruzione: in Python 2 stampa la tupla, in Python 3 la stampa identica ma
    con un significato diverso, quindi segnalarlo e' comunque corretto.
    """
    following = _next_code(context.tokens, i)
    if following is not None and context.tokens[following].string == "(":
        return  # print(...) e' gia' una chiamata
    rule = _RULES_BY_ID["print-statement"]
    statement_end, _ = _statement_end(context.tokens, i)
    if statement_end is None:
        # `print` da solo: in Python 2 stampa una newline, in Python 3 va
        # chiamato come `print()`. Sostituisco solo il token, cosi' gli
        # eventuali spazi finali e il fine riga restano intatti.
        context.add(
            rule,
            i,
            "`print` da solo stampa una newline: in Python 3 va chiamato come `print()`",
            fix=TextEdit(
                start=context.source.offset(*context.tokens[i].start),
                end=context.source.offset(*context.tokens[i].end),
                replacement="print()",
            ),
        )
        return

    has_redirect = any(
        context.tokens[j].string == ">>" for j in range(i + 1, statement_end + 1)
    )
    if has_redirect:
        context.add(
            rule,
            i,
            "in Python 2 `print >>file, x` redirige l'output: "
            "in Python 3 diventa `print(x, file=file)`",
        )
        return

    last = statement_end
    end_token = context.tokens[last]
    replacement_tail = ""
    if end_token.string == ",":
        # `print x,` in Python 2 non andava a capo: in Python 3 serve
        # `print(x, end=' ')`
        replacement_tail = ", end=' '"
        last -= 1
        while last > i and not _is_code(context.tokens[last]):
            last -= 1

    if last <= i:
        return

    # l'intestazione assorbe anche gli spazi che seguono `print`, altrimenti
    # si otterrebbe `print( x)`
    primo = _next_code(context.tokens, i)
    if primo is None:
        return
    edit = TextEdit(
        start=context.source.offset(*context.tokens[i].start),
        end=context.source.offset(*context.tokens[primo].start),
        replacement="print(",
    )
    tail_edit = TextEdit(
        start=context.source.offset(*context.tokens[last].end),
        end=context.source.offset(*end_token.end),
        replacement=f"{replacement_tail})",
    )
    context.add(rule, i, "in Python 2 `print` e' un'istruzione: chiamarlo come funzione", fix=edit)
    context.edits.append(tail_edit)


# -- 2. Sostituzioni di nomi e chiamate rimosse in 3.0 ------------------------

#: Chiamate rimosse in Python 3.0 la cui riscrittura e' un semplice cambio di nome.
_RENAMED_CALLS: Tuple[Tuple[str, str, str, Optional[str]], ...] = (
    ("raw_input", "input", "raw-input", "Python 3.0"),
    ("xrange", "range", "xrange", "Python 3.0"),
    ("unicode", "str", "unicode-type", "Python 3.0"),
    ("unichr", "chr", "unicode-type", "Python 3.0"),
    ("long", "int", "unicode-type", "Python 3.0"),
)

#: Metodi dei dizionari sostituiti dalle viste di Python 3.
_DICT_VIEW_METHODS: Mapping[str, str] = {
    "iteritems": "items",
    "iterkeys": "keys",
    "itervalues": "values",
}

#: Nomi semplici da riscrivere (nessuna parentesi richiesta).
_RENAMED_NAMES: Tuple[Tuple[str, str, Optional[str], str], ...] = (
    ("basestring", "str", "unicode-type", "Python 3.0: `basestring` -> `str`"),
    ("long", "int", "unicode-type", "Python 3.0: `long` -> `int`"),
    ("unicode", "str", "unicode-type", "Python 3.0: `unicode` -> `str`"),
    ("reduce", None, "reduce-moved", "Python 3.0: `reduce` -> `from functools import reduce`"),
    ("reload", None, "reduce-moved", "Python 3.0: `reload` -> `from importlib import reload`"),
    ("cmp", "(a > b) - (a < b)", None, "Python 3.0: `cmp` non esiste piu'"),
    ("execfile", "exec(open(f).read())", None, "Python 3.0: `execfile` non esiste piu'"),
    ("apply", "f(*args)", None, "Python 3.0: `apply` non esiste piu'"),
    ("coerce", None, None, "Python 3.0: `coerce` non esiste piu'"),
    ("sys.maxint", "sys.maxsize", None, "Python 3.0: `sys.maxint` -> `sys.maxsize`"),
    ("ifilter", "filter", "unicode-type", "Python 3.0: `ifilter` -> `filter`"),
    ("imap", "map", "unicode-type", "Python 3.0: `imap` -> `map`"),
    ("izip", "zip", "unicode-type", "Python 3.0: `izip` -> `zip`"),
    ("StringIO", None, None, "Python 3.0: il modulo `StringIO` -> `io.StringIO`"),
)

#: Nomi composti da un modulo e un attributo: non sono token singoli, quindi
#: non possono passare dalla tabella delle regole basata sul testo del token.
_DOTTED_NAMES = frozenset({"sys.maxint"})


def _check_renamed_call(context: _Context, i: int) -> None:
    """``raw_input(...)``, ``xrange(...)``, ``unicode(...)`` e simili."""
    name = context.tokens[i].string
    following = _next_code(context.tokens, i)
    if following is None or context.tokens[following].string != "(":
        return
    previous = _prev_code(context.tokens, i)
    if previous is not None and context.tokens[previous].string == ".":
        return  # e' un metodo qualunque che per caso ha lo stesso nome
    for old, new, feature_id, _ in _RENAMED_CALLS:
        if old != name:
            continue
        context.add(
            _RULES_BY_ID[feature_id],
            i,
            f"Python 3.0: `{old}()` non esiste piu', usare `{new}()`",
            fix=_rename_edit(context, i, new),
        )
        return


def _check_dict_view(context: _Context, i: int) -> None:
    """``d.iteritems()``, ``d.iterkeys()``, ``d.itervalues()``."""
    name = context.tokens[i].string
    replacement = _DICT_VIEW_METHODS.get(name)
    if replacement is None:
        return
    previous = _prev_code(context.tokens, i)
    if previous is None or context.tokens[previous].string != ".":
        return
    context.add(
        _RULES_BY_ID["iteritems"],
        i,
        f"Python 3.0: `{name}()` e' stato rimosso, usare `{replacement}()`",
        fix=_rename_edit(context, i, replacement),
    )


def _check_renamed_name(context: _Context, i: int) -> None:
    """Nomi rimosse che compaiono senza chiamata esplicita.

    Il contesto conta: un metodo omonimo come ``d.reduce`` e il nome usato in
    ``def reduce(...)`` non sono chiamate a ``functools.reduce``.
    """
    name = context.tokens[i].string
    previous = _prev_code(context.tokens, i)
    if previous is not None and context.tokens[previous].string in (".", "def", "class"):
        return
    if context.tokens[i].line[: context.tokens[i].start[1]].rstrip().endswith(("def ", "class ")):
        return
    following = _next_code(context.tokens, i)
    if following is not None and context.tokens[following].string == "(":
        # `unicode(x)` e' gia' segnalata da `_check_renamed_call`: segnalarla
        # anche come nome produrrebbe due ritrovamenti sullo stesso token
        if any(old == name for old, _, _, _ in _RENAMED_CALLS):
            return

    for old, new, feature_id, message in _RENAMED_NAMES:
        if old != name or old in _DOTTED_NAMES:
            continue
        rule = _RULES_BY_ID[feature_id] if feature_id else _RULES_BY_ID["legacy-removed-call"]
        context.add(rule, i, message, fix=_rename_edit(context, i, new) if new else None)
        return


def _check_sys_maxint(context: _Context, i: int) -> None:
    """`sys.maxint` -> `sys.maxsize`."""
    if context.tokens[i].string != "maxint":
        return
    previous = _prev_code(context.tokens, i)
    if previous is None or context.tokens[previous].string != ".":
        return
    before = _prev_code(context.tokens, previous)
    if before is None or context.tokens[before].string != "sys":
        return
    context.add(
        _RULES_BY_ID["sys-maxint"],
        i,
        "Python 3.0: `sys.maxint` non esiste piu', usare `sys.maxsize`",
        fix=_rename_edit(context, i, "maxsize"),
    )


# -- 3. Sintassi rimossa in 3.0 -----------------------------------------------


def _check_backtick(context: _Context, i: int) -> None:
    """Il backtick, cioe' `` `expr` `` al posto di ``repr(expr)``.

    Nota: il tokenizer di Python 3 non lo classifica come errore lessicale, lo
    tratta come un operatore sconosciuto. Per questo la regola guarda solo il
    testo del token.
    """
    if context.tokens[i].string != "`":
        return
    context.add(
        _RULES_BY_ID["backtick-repr"],
        i,
        "Python 3.0: il backtick non esiste piu', usare `repr(...)`",
    )


def _check_angle_comparison(context: _Context, i: int) -> None:
    """L'operatore ``<>``, alternativa di ``!=``."""
    if context.tokens[i].string != "<>":
        return
    context.add(
        _RULES_BY_ID["angle-comparison"],
        i,
        "Python 3.0: l'operatore `<>` non esiste piu', usare `!=`",
        fix=_rename_edit(context, i, "!="),
    )


def _check_old_division(context: _Context, i: int) -> None:
    """Divisione fra due letterali interi con ``/``.

    La regola segnala solo i casi piu' evidenti (due letterali interi
    letterali). Non tenta di inferire i tipi: quello richiederebbe
    l'analisi del flusso, che e' fuori portata di un analizzatore lessicale.
    """
    if context.tokens[i].string != "/":
        return
    left = _prev_code(context.tokens, i)
    right = _next_code(context.tokens, i)
    if left is None or right is None:
        return
    lt, rt = context.tokens[left], context.tokens[right]
    if not _is_integer_literal(lt.string) or not _is_integer_literal(rt.string):
        return
    context.add(
        _RULES_BY_ID["true-division"],
        i,
        "Python 3.0: `/` fra interi restituisce un float, per troncare usare `//`",
    )


def _is_integer_literal(text: str) -> bool:
    """``True`` se ``text`` e' un letterale intero (decimale, esadecimale, ottale)."""
    body = text.rstrip("lL").replace("_", "")
    try:
        int(body, 0)
    except ValueError:
        return False
    return "." not in body and "e" not in body.lower() and not body.lower().startswith("0b")


def _check_long_suffix(context: _Context, i: int) -> None:
    """Suffisso ``L`` sui letterali interi.

    Il tokenizer di Python 3 scompone ``10L`` in due token, ``10`` (NUMBER) e
    ``L`` (NAME): la regola deve quindi lavorare sulla coppia, non sul singolo
    letterale.
    """
    number = context.tokens[i]
    if number.type != token_module.NUMBER:
        return
    following = _next_code(context.tokens, i)
    if following is None:
        return
    suffix = context.tokens[following]
    if suffix.type != token_module.NAME or suffix.string not in ("l", "L"):
        return
    context.add(
        _RULES_BY_ID["long-literal-suffix"],
        i,
        "Python 3.0: il suffisso `L` sui letterali interi non esiste piu'",
        fix=TextEdit(
            start=context.source.offset(*number.start),
            end=context.source.offset(*suffix.end),
            replacement=number.string,
        ),
    )


def _check_unicode_prefix(context: _Context, i: int) -> None:
    """Prefisso ``u`` sui letterali stringa.

    Il prefisso si riconosce dalla parte del token che precede la prima
    virgoletta: e' l'unico punto in cui Python distingue prefisso e contenuto.
    """
    tok = context.tokens[i]
    if tok.type != token_module.STRING:
        return
    quote_positions = [tok.string.find(char) for char in "\"'"]
    quote_positions = [pos for pos in quote_positions if pos >= 0]
    if not quote_positions:
        return
    prefix = tok.string[: min(quote_positions)]
    if "u" not in prefix.lower():
        return
    new_prefix = prefix.replace("u", "").replace("U", "")
    context.add(
        _RULES_BY_ID["unicode-literal-prefix"],
        i,
        "Python 3.0: il prefisso `u` non serve piu', `str` e' gia' Unicode",
        fix=TextEdit(
            start=context.source.offset(*tok.start),
            end=context.source.offset(*tok.end),
            replacement=new_prefix + tok.string[min(quote_positions) :],
        ),
    )


def _check_except_comma(context: _Context, i: int) -> None:
    """``except Error, e:`` al posto di ``except Error as e:``.

    Copre anche la forma con tupla, ``except (A, B), e:``, che era ammessa in
    Python 2: la virgola cercata e' quella a profondita' zero, cioe' quella
    che segue la parentesi chiusa.
    """
    if context.tokens[i].string != "except":
        return
    following = _next_code(context.tokens, i)
    if following is None or context.tokens[following].string == "as":
        return  # gia' nella forma moderna
    statement_end, _ = _statement_end(context.tokens, i)
    if statement_end is None:
        return
    comma_index = None
    depth = 0
    for j in range(i + 1, statement_end + 1):
        text = context.tokens[j].string
        if text in "([{":
            depth += 1
        elif text in ")]}":
            depth -= 1
        elif text == "," and depth == 0:
            comma_index = j
            break
        elif text == ":" and depth == 0:
            break
    if comma_index is None:
        return
    context.add(
        _RULES_BY_ID["except-comma"],
        i,
        "Python 3.0: `except E, e:` non esiste piu', usare `except E as e:`",
        fix=TextEdit(
            start=context.source.offset(*context.tokens[comma_index].start),
            end=context.source.offset(*context.tokens[comma_index].end),
            replacement=" as",
        ),
    )


def _check_old_raise(context: _Context, i: int) -> None:
    """``raise Error, value, traceback``."""
    if context.tokens[i].string != "raise":
        return
    following = _next_code(context.tokens, i)
    if following is None or context.tokens[following].string in ("NewError", "except", "finally"):
        return
    statement_end, depth = _statement_end(context.tokens, i)
    if statement_end is None:
        return
    commas = [
        j
        for j in range(i + 1, statement_end + 1)
        if context.tokens[j].string == "," and _depth_at(context.tokens, i + 1, j) == depth
    ]
    if not commas:
        return
    if len(commas) == 1:
        # `raise E, valore` si riscrive senza perdite in `raise E(valore)`
        context.add(
            _RULES_BY_ID["raise-old-form"],
            i,
            "Python 3.0: `raise E, valore` non esiste piu', usare `raise E(valore)`",
            fix=_rename_edit(context, commas[0], "("),
        )
        context.edits.append(
            TextEdit(
                start=context.source.offset(*context.tokens[statement_end].end),
                end=context.source.offset(*context.tokens[statement_end].end),
                replacement=")",
            )
        )
        return
    context.add(
        _RULES_BY_ID["raise-old-form"],
        i,
        "Python 3.0: `raise E, valore, traceback` non esiste piu': usare "
        "`raise E(valore)` e, per la causa, `raise ... from errore`",
    )


def _check_metaclass(context: _Context, i: int) -> None:
    """``__metaclass__ = M`` nel corpo di una classe."""
    if context.tokens[i].string != "__metaclass__":
        return
    context.add(
        _RULES_BY_ID["metaclass-syntax"],
        i,
        "Python 3.0: `__metaclass__` nel corpo della classe e' ignorato, "
        "usare `class C(metaclass=M)`",
    )


def _check_old_class(context: _Context, i: int) -> None:
    """``class C:`` senza base: era una classe vecchia in Python 2.

    Si distingue `class C:` da `class C(Base):` e da `class C:` seguito da una
    clausola di montaggio: conta solo se, dopo il nome, non compare alcuna base
    prima dei due punti.
    """
    if context.tokens[i].string != "class":
        return
    statement_end, _ = _statement_end(context.tokens, i)
    if statement_end is None:
        return
    name_index = _next_code(context.tokens, i)
    if name_index is None or name_index >= statement_end:
        return
    after_name = _next_code(context.tokens, name_index)
    if after_name is None or context.tokens[after_name].string == ":":
        context.add(
            _RULES_BY_ID["classic-classes"],
            i,
            "in Python 2 questa era una 'classic class'; in Python 3 esiste "
            "un solo modello di classe, derivato da `object`",
        )


def _check_has_key(context: _Context, i: int) -> None:
    """``d.has_key(k)``: non risolvibile automaticamente."""
    if context.tokens[i].string != "has_key":
        return
    previous = _prev_code(context.tokens, i)
    if previous is None or context.tokens[previous].string != ".":
        return
    context.add(
        _RULES_BY_ID["has-key"],
        i,
        "Python 3.0: `has_key` non esiste piu', riscrivere come `chiave in dizionario`",
    )


def _check_keys_subscript(context: _Context, i: int) -> None:
    """``d.keys()[0]``: in Python 3 `keys()` restituisce una vista."""
    if context.tokens[i].string not in ("keys", "values", "items"):
        return
    previous = _prev_code(context.tokens, i)
    if previous is None or context.tokens[previous].string != ".":
        return
    opening = _next_code(context.tokens, i)
    if opening is None or context.tokens[opening].string != "(":
        return
    closing = _matching_paren(context.tokens, opening)
    if closing is None:
        return
    following = _next_code(context.tokens, closing)
    if following is None or context.tokens[following].string != "[":
        return
    context.add(
        _RULES_BY_ID["iteritems"],
        i,
        "in Python 3 `keys()`/`values()`/`items()` restituiscono viste non "
        "indicizzabili: usare `list(d.keys())` o `sorted(d)`",
    )


# -- 4. Sintassi moderna: quale versione di Python richiede ------------------


def _check_walrus(context: _Context, i: int) -> None:
    """L'operatore di assegnazione ``:=`` (Python 3.8)."""
    if context.tokens[i].string != ":=":
        return
    context.add(
        _RULES_BY_ID["modern-walrus"],
        i,
        "Python 3.8: l'operatore `:=` permette di assegnare e usare il valore "
        "nella stessa espressione",
    )


def _check_match(context: _Context, i: int) -> None:
    """Il pattern matching con ``match``/``case`` (Python 3.10).

    `match` resta un nome legittimo, quindi la regola pretende che sia
    seguito da un soggetto e che la riga si chiuda con i due punti di un
    blocco: `match = 3`, `match(x)` e `d.match` non vengono toccati.
    """
    if context.tokens[i].type != token_module.NAME or context.tokens[i].string != "match":
        return
    following = _next_code(context.tokens, i)
    if following is None:
        return
    if context.tokens[following].string in ("(", "=", "."):
        return
    if context.tokens[following].type not in (
        token_module.NAME,
        token_module.STRING,
        token_module.NUMBER,
    ):
        return
    statement_end, depth = _statement_end(context.tokens, i)
    if statement_end is None or depth != 0:
        return
    if context.tokens[statement_end].string != ":":
        return
    context.add(
        _RULES_BY_ID["modern-pattern-matching"],
        i,
        "Python 3.10: `match`/`case` sostituisce lunghe catene di `if`/`elif`",
    )


def _check_type_params(context: _Context, i: int) -> None:
    """I type parameter nella definizione, ``def f[T](...)`` (Python 3.12)."""
    if context.tokens[i].string != "def":
        return
    statement_end, depth = _statement_end(context.tokens, i)
    if statement_end is None or depth != 0:
        return
    after_name = _next_code(context.tokens, i)
    if after_name is None or after_name >= statement_end:
        return
    opening = _next_code(context.tokens, after_name)
    if opening is None or context.tokens[opening].string != "[":
        return
    context.add(
        _RULES_BY_ID["modern-type-params"],
        i,
        "Python 3.12: i type parameter si dichiarano nella definizione (PEP 695)",
    )


def _check_positional_only(context: _Context, i: int) -> None:
    """Il separatore ``/`` dei parametri positional-only (Python 3.8)."""
    if context.tokens[i].string != "/":
        return
    statement_end, depth = _statement_end(context.tokens, i)
    if statement_end is None or depth != 0:
        return
    if i < statement_end and context.tokens[i - 1].string == "=":
        return  # `a /= 2` e' un assegnamento, non un separatore
    for j in range(i, statement_end):
        if context.tokens[j].type == token_module.NAME and context.tokens[j].string == "def":
            context.add(
                _RULES_BY_ID["modern-positional-only"],
                i,
                "Python 3.8: `/` nella firma dichiara i parametri positional-only",
            )
            return


def _check_async(context: _Context, i: int) -> None:
    """``async`` e ``await`` (Python 3.5)."""
    if context.tokens[i].type != token_module.NAME:
        return
    if context.tokens[i].string not in ("async", "await"):
        return
    previous = _prev_code(context.tokens, i)
    if previous is not None and context.tokens[previous].string in (".", "def"):
        # `d.async` non esiste, ma `def async_...` e `x.await` vanno ignorati
        if context.tokens[previous].string == ".":
            return
    context.add(
        _RULES_BY_ID["modern-async"],
        i,
        "Python 3.5: `async`/`await` definiscono la coroutines; in Python 2 "
        "si usavano i generatori con `@asyncio.coroutine`",
    )


def _check_yield_from(context: _Context, i: int) -> None:
    """``yield from`` (Python 3.3)."""
    if context.tokens[i].string != "yield":
        return
    following = _next_code(context.tokens, i)
    if following is None or context.tokens[following].string != "from":
        return
    context.add(
        _RULES_BY_ID["modern-yield-from"],
        i,
        "Python 3.3: `yield from` delega a un altro generatore",
    )


def _check_except_star(context: _Context, i: int) -> None:
    """``except*`` (Python 3.11)."""
    if context.tokens[i].string != "except":
        return
    following = _next_code(context.tokens, i)
    if following is None or context.tokens[following].string != "*":
        return
    context.add(
        _RULES_BY_ID["modern-except-star"],
        i,
        "Python 3.11: `except*` raggruppa piu' eccezioni contemporanee",
    )


def _check_fstring(context: _Context, i: int) -> None:
    """Le stringhe con interpolazione, per calcolare la versione minima.

    Qui non si suggerisce nulla: il codice usa gia' la sintassi moderna, quindi
    l'unica informazione utile e' *quale* versione richiede. Segnalare una
    f-string come "prova a usare una f-string" sarebbe un falso positivo.

    Le regole che *suggeriscono* la f-string sono altre e guardano il punto in
    cui la stringa viene composta: `_check_percent_format` per `%` e
    `_check_format_method` per `.format()`.

    Dal 3.12 il tokenizer di Python non produce un unico token per un letterale
    con interpolazione, ma tre: ``FSTRING_START``, ``FSTRING_MIDDLE`` e
    ``FSTRING_END`` (gli equivalenti ``TSTRING_*`` per i template). Per
    compatibilita' con i tokenizer piu' vecchi la regola esamina anche i
    normali letterali ``STRING`` che portano il prefisso ``f`` o ``t``.
    """
    tok = context.tokens[i]
    if tok.type == getattr(tokenize, "FSTRING_START", -1):
        context.add(
            _RULES_BY_ID["modern-fstring-syntax"],
            i,
            "Python 3.6: il codice usa una f-string, quindi richiede almeno la 3.6",
        )
        return
    if tok.type == getattr(tokenize, "TSTRING_START", -1):
        context.add(
            _RULES_BY_ID["modern-t-string"],
            i,
            "Python 3.14: il codice usa una t-string, quindi richiede almeno la 3.14",
        )
        return
    if tok.type != token_module.STRING:
        return
    quote_positions = [tok.string.find(char) for char in "\"'"]
    quote_positions = [pos for pos in quote_positions if pos >= 0]
    if not quote_positions:
        return
    prefix = tok.string[: min(quote_positions)].lower()
    if "f" in prefix:
        context.add(
            _RULES_BY_ID["modern-fstring-syntax"],
            i,
            "Python 3.6: il codice usa una f-string, quindi richiede almeno la 3.6",
        )
    elif "t" in prefix:
        context.add(
            _RULES_BY_ID["modern-t-string"],
            i,
            "Python 3.14: il codice usa una t-string, quindi richiede almeno la 3.14",
        )


def _check_builtin_generics(context: _Context, i: int) -> None:
    """``list[str]`` e simili: i generici integrati in Python 3.9."""
    if context.tokens[i].type != token_module.NAME:
        return
    if context.tokens[i].string not in ("list", "dict", "set", "frozenset", "tuple", "type"):
        return
    following = _next_code(context.tokens, i)
    if following is None or context.tokens[following].string != "[":
        return
    previous = _prev_code(context.tokens, i)
    if previous is not None and context.tokens[previous].string == ".":
        return  # `d.list[...]` non e' il builtin
    context.add(
        _RULES_BY_ID["modern-builtin-generics"],
        i,
        "Python 3.9: `list[str]` indica i tipo con il builtin, senza `typing.List`",
    )


def _check_union_types(context: _Context, i: int) -> None:
    """``X | Y`` fra nomi di tipo: le unioni della PEP 604, da Python 3.10.

    La regola e' volutamente stretta: il token ``|`` indica anche l'unione fra
    dizionari (3.9), fra insiemi e l'OR bit a bit. Segnalare tutto produrrebbe
    falsi positivi su codice corretto, quindi si richiede che almeno un
    operando sia ``None`` o un nome che inizia per maiuscola, che e' la
    convenzione per i tipi.
    """
    if context.tokens[i].string != "|":
        return
    precedente = _prev_code(context.tokens, i)
    successivo = _next_code(context.tokens, i)
    if precedente is None or successivo is None:
        return
    if not _is_typename(context.tokens[precedente]) and not _is_typename(
        context.tokens[successivo]
    ):
        return
    # `dict | dict` e `set | set` sono operatori sui valori, non annotazioni.
    if _is_typename(context.tokens[precedente]) and _is_typename(context.tokens[successivo]):
        return
    context.add(
        _RULES_BY_ID["modern-union-types"],
        i,
        "Python 3.10: `X | Y` e' l'unione di tipo della PEP 604, "
        "al posto di `Optional[X]` e `Union[X, Y]`",
    )


def _is_typename(tok: TokenInfo) -> bool:
    """Distingue un nome che indica un tipo da un valore."""
    if tok.type == token_module.NAME and tok.string == "None":
        return True
    if tok.type not in (token_module.NAME, token_module.STRING):
        return False
    return bool(tok.string[:1].isupper())


# -- 5. Consigli di stile moderno --------------------------------------------


def _check_super(context: _Context, i: int) -> None:
    """``super(Classe, self)``."""
    if context.tokens[i].string != "super":
        return
    following = _next_code(context.tokens, i)
    if following is None or context.tokens[following].string != "(":
        return
    closing = _matching_paren(context.tokens, following)
    if closing is None:
        return
    # gli argomenti sono i token a profondita' zero, ignorando le virgole
    argomenti = [
        context.tokens[j]
        for j in range(following + 1, closing)
        if _is_code(context.tokens[j]) and context.tokens[j].string != ","
    ]
    if len(argomenti) == 2:
        context.add(
            _RULES_BY_ID["modern-super"],
            i,
            "da Python 3: `super()` senza argomenti funziona in ogni metodo di classe",
        )


def _check_os_path_join(context: _Context, i: int) -> None:
    """``os.path.join(...)``: da Python 3.4 esiste `pathlib`."""
    if context.tokens[i].string != "join":
        return
    previous = _prev_code(context.tokens, i)
    if previous is None or context.tokens[previous].string != ".":
        return
    path_attr = _prev_code(context.tokens, previous)
    if path_attr is None or context.tokens[path_attr].string != "path":
        return
    os_attr = _prev_code(context.tokens, path_attr)
    if os_attr is None or context.tokens[os_attr].string != "os":
        return
    context.add(
        _RULES_BY_ID["modern-pathlib"],
        i,
        "da Python 3.4: `Path(\"a\") / \"b\"` e' piu' leggibile di `os.path.join`",
    )


def _check_percent_format(context: _Context, i: int) -> None:
    """``"..." % valore``: da Python 3.6 conviene la f-string."""
    tok = context.tokens[i]
    if tok.type != token_module.OP or tok.string != "%":
        return
    previous = _prev_code(context.tokens, i)
    if previous is None or context.tokens[previous].type != token_module.STRING:
        return
    following = _next_code(context.tokens, i)
    if following is None:
        return
    if context.tokens[following].string in ("(", "["):
        return  # il `%` e' un operatore aritmetico su altro
    context.add(
        _RULES_BY_ID["modern-fstring"],
        i,
        "da Python 3.6: la f-string rende esplicito quali valori vengono interpolati",
    )


def _check_format_method(context: _Context, i: int) -> None:
    """``"...".format(...)``: da Python 3.6 conviene la f-string."""
    if context.tokens[i].string != "format" or context.tokens[i].type != token_module.NAME:
        return
    previous = _prev_code(context.tokens, i)
    if previous is None:
        return
    if context.tokens[previous].string == ".":
        # `"...".format(...)`: il letterale sta immediatamente prima del punto
        letterale = _prev_code(context.tokens, previous)
    elif context.tokens[previous].string in (")", "]", "}"):
        # `"...".format(...).altro(...)`: risalgo fino al letterale di partenza
        opener = _matching_open(context.tokens, previous)
        if opener is None:
            return
        letterale = _prev_code(context.tokens, opener)
    else:
        return
    if letterale is None or context.tokens[letterale].type != token_module.STRING:
        return
    context.add(
        _RULES_BY_ID["modern-fstring"],
        i,
        "da Python 3.6: `.format(...)` puo' diventare una f-string",
    )


# ---------------------------------------------------------------------------
# Navigazione fra token
# ---------------------------------------------------------------------------


def _next_code(tokens: Sequence[tokenize.TokenInfo], index: int) -> Optional[int]:
    """Indice del prossimo token di codice, se esiste."""
    for j in range(index + 1, len(tokens)):
        if _is_code(tokens[j]):
            return j
    return None


def _prev_code(tokens: Sequence[tokenize.TokenInfo], index: int) -> Optional[int]:
    """Indice del token di codice precedente, se esiste."""
    for j in range(index - 1, -1, -1):
        if _is_code(tokens[j]):
            return j
    return None


def _statement_end(tokens: Sequence[tokenize.TokenInfo], start: int) -> Tuple[Optional[int], int]:
    """Trova l'ultimo token della dichiarazione che inizia in ``start``.

    Restituisce ``(indice_ultimo_token, profondità_aperta)``. La profondita' e'
    utile per capire se ci sono parentesi aperte non chiuse, cioe' una
    dichiarazione che continua su un'altra riga.
    """
    depth = 0
    last = start
    for j in range(start, len(tokens)):
        tok = tokens[j]
        if tok.type in (token_module.NEWLINE, token_module.ENDMARKER):
            return (last if last > start else None, depth)
        if tok.type in (token_module.INDENT, token_module.DEDENT):
            continue
        if tok.type == token_module.OP:
            if tok.string in "([{":
                depth += 1
            elif tok.string in ")]}":
                depth -= 1
        last = j
    return (last if last > start else None, depth)


def _depth_at(tokens: Sequence[tokenize.TokenInfo], start: int, stop: int) -> int:
    """Profondita' di parentesi raggiunta immediatamente prima di ``stop``."""
    depth = 0
    for j in range(start, stop):
        text = tokens[j].string
        if tokens[j].type == token_module.OP:
            if text in "([{":
                depth += 1
            elif text in ")]}":
                depth -= 1
    return depth


def _matching_paren(tokens: Sequence[tokenize.TokenInfo], opening: int) -> Optional[int]:
    """Indice della parentesi chiusa che corrisponde a quella di apertura."""
    depth = 0
    for j in range(opening, len(tokens)):
        if tokens[j].type != token_module.OP:
            continue
        if tokens[j].string in "([{":
            depth += 1
        elif tokens[j].string in ")]}":
            depth -= 1
            if depth == 0:
                return j
    return None


def _matching_open(tokens: Sequence[tokenize.TokenInfo], closing: int) -> Optional[int]:
    """Indice della parentesi di apertura che corrisponde a quella di chiusura."""
    depth = 0
    for j in range(closing, -1, -1):
        if tokens[j].type != token_module.OP:
            continue
        if tokens[j].string in ")]}":
            depth += 1
        elif tokens[j].string in "([{":
            depth -= 1
            if depth == 0:
                return j
    return None


def _rename_edit(context: _Context, i: int, new_name: str) -> TextEdit:
    """Costruisce l'edizione che rinomina un singolo token."""
    tok = context.tokens[i]
    return TextEdit(
        start=context.source.offset(*tok.start),
        end=context.source.offset(*tok.end),
        replacement=new_name,
    )


# ---------------------------------------------------------------------------
# Tabella delle regole
# ---------------------------------------------------------------------------


_RULES: Tuple[_Rule, ...] = (
    _Rule(
        id="print-statement",
        title="print come istruzione",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="print-statement",
        check=_check_print,
    ),
    _Rule(
        id="raw-input",
        title="raw_input()",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="raw-input",
        check=_check_renamed_call,
    ),
    _Rule(
        id="xrange",
        title="xrange()",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="xrange",
        check=_check_renamed_call,
    ),
    _Rule(
        id="unicode-type",
        title="unicode, long, basestring e prefissi correlati",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="unicode-type",
        check=_check_renamed_call,
    ),
    _Rule(
        id="iteritems",
        title="iteritems() e viste dei dizionari",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="iteritems",
        check=_check_dict_view,
    ),
    _Rule(
        id="has-key",
        title="dict.has_key()",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="has-key",
        check=_check_has_key,
    ),
    _Rule(
        id="true-division",
        title="divisione intera con /",
        severity=Severity.WARNING,
        introduced=_V30,
        feature_id="true-division",
        check=_check_old_division,
    ),
    _Rule(
        id="backtick-repr",
        title="backtick al posto di repr()",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="backtick-repr",
        check=_check_backtick,
    ),
    _Rule(
        id="angle-comparison",
        title="operatore <>",
        severity=Severity.ERROR,
        removed=_V30,
        check=_check_angle_comparison,
    ),
    _Rule(
        id="except-comma",
        title="except E, e:",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="except-comma",
        check=_check_except_comma,
    ),
    _Rule(
        id="raise-old-form",
        title="raise E, value, tb",
        severity=Severity.ERROR,
        removed=_V30,
        check=_check_old_raise,
    ),
    _Rule(
        id="metaclass-syntax",
        title="__metaclass__ nel corpo della classe",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="metaclass-syntax",
        check=_check_metaclass,
    ),
    _Rule(
        id="reduce-moved",
        title="reduce() e reload() spostati",
        severity=Severity.ERROR,
        removed=_V30,
        feature_id="reduce-moved",
    ),
    _Rule(
        id="modern-async",
        title="async e await",
        severity=Severity.ADVICE,
        introduced=Version(3, 5),
    ),
    _Rule(
        id="modern-yield-from",
        title="yield from",
        severity=Severity.ADVICE,
        introduced=Version(3, 3),
    ),
    _Rule(
        id="modern-fstring-syntax",
        title="f-string",
        severity=Severity.ADVICE,
        introduced=Version(3, 6),
        feature_id="f-string",
    ),
    _Rule(
        id="modern-walrus",
        title="operatore walrus",
        severity=Severity.ADVICE,
        introduced=Version(3, 8),
        feature_id="walrus",
    ),
    _Rule(
        id="modern-positional-only",
        title="parametri positional-only",
        severity=Severity.ADVICE,
        introduced=Version(3, 8),
        feature_id="positional-only",
    ),
    _Rule(
        id="modern-builtin-generics",
        title="generici integrati (list[str])",
        severity=Severity.ADVICE,
        introduced=Version(3, 9),
        feature_id="builtin-generics",
    ),
    _Rule(
        id="modern-union-types",
        title="unioni di tipo (X | Y)",
        severity=Severity.ADVICE,
        introduced=Version(3, 10),
        feature_id="union-types",
    ),
    _Rule(
        id="modern-pattern-matching",
        title="pattern matching (match/case)",
        severity=Severity.ADVICE,
        introduced=Version(3, 10),
        feature_id="structural-pattern-matching",
    ),
    _Rule(
        id="modern-except-star",
        title="except*",
        severity=Severity.ADVICE,
        introduced=Version(3, 11),
        feature_id="except-star",
    ),
    _Rule(
        id="modern-type-params",
        title="type parameter (PEP 695)",
        severity=Severity.ADVICE,
        introduced=Version(3, 12),
        feature_id="type-params",
    ),
    _Rule(
        id="modern-t-string",
        title="t-string",
        severity=Severity.ADVICE,
        introduced=Version(3, 14),
        feature_id="t-string",
    ),
    _Rule(
        id="classic-classes",
        title="classe senza base (classic class)",
        severity=Severity.ADVICE,
        removed=_V30,
        feature_id="classic-classes",
        check=_check_old_class,
    ),
    _Rule(
        id="legacy-removed-call",
        title="API rimossa in Python 3.0",
        severity=Severity.ERROR,
        removed=_V30,
        check=_check_renamed_name,
    ),
    _Rule(
        id="long-literal-suffix",
        title="suffisso L sui letterali",
        severity=Severity.ERROR,
        removed=_V30,
        check=_check_long_suffix,
    ),
    _Rule(
        id="unicode-literal-prefix",
        title="prefisso u sui letterali",
        severity=Severity.ERROR,
        removed=_V30,
        check=_check_unicode_prefix,
    ),
    _Rule(
        id="sys-maxint",
        title="sys.maxint",
        severity=Severity.ERROR,
        removed=_V30,
        check=_check_sys_maxint,
    ),
    _Rule(
        id="dict-view-subscript",
        title="indicizzazione di keys()/values()/items()",
        severity=Severity.ERROR,
        removed=_V30,
        check=_check_keys_subscript,
    ),
    _Rule(
        id="modern-super",
        title="super(Classe, self)",
        severity=Severity.ADVICE,
        introduced=_V30,
        feature_id="classic-classes",
        check=_check_super,
    ),
    _Rule(
        id="modern-pathlib",
        title="os.path.join",
        severity=Severity.ADVICE,
        introduced=Version(3, 4),
        feature_id="pathlib",
        check=_check_os_path_join,
    ),
    _Rule(
        id="modern-fstring",
        title="formattazione con % o .format()",
        severity=Severity.ADVICE,
        introduced=Version(3, 6),
        feature_id="f-string",
        check=_check_percent_format,
    ),
    _Rule(
        id="modern-fstring-format",
        title=".format()",
        severity=Severity.ADVICE,
        introduced=Version(3, 6),
        feature_id="f-string",
        check=_check_format_method,
    ),
)

_RULES_BY_ID: Dict[str, _Rule] = {rule.id: rule for rule in _RULES}


def rules() -> Tuple[_Rule, ...]:
    """Restituisce tutte le regole di rilevamento."""
    return _RULES


#: Regole attive per ciascun token. La tabella e' costruita da
#: :func:`_build_checks` al termine della definizione della funzione.


def _build_checks() -> Mapping[str, Tuple[Callable[["_Context", int], None], ...]]:
    """Associa a ogni testo di token le regole che lo esaminano.

    La tabella evita di eseguire ogni regola su ogni token: il rilevamento resta
    lineare anche su file di grandi dimensioni.
    """
    table: Dict[str, List[Callable[["_Context", int], None]]] = {}

    def register(names: Sequence[str], check: Callable[["_Context", int], None]) -> None:
        for name in names:
            table.setdefault(name, []).append(check)

    register(["print"], _check_print)
    register([name for name, _, _, _ in _RENAMED_CALLS], _check_renamed_call)
    register(list(_DICT_VIEW_METHODS), _check_dict_view)
    register([name for name, _, _, _ in _RENAMED_NAMES if name != "sys.maxint"], _check_renamed_name)
    register(["maxint"], _check_sys_maxint)
    register(["`"], _check_backtick)
    register(["<>"], _check_angle_comparison)
    register(["/"], _check_old_division)
    register(["except"], _check_except_comma)
    register(["raise"], _check_old_raise)
    register(["__metaclass__"], _check_metaclass)
    register(["class"], _check_old_class)
    register(["has_key"], _check_has_key)
    register(["keys", "values", "items"], _check_keys_subscript)
    register(["super"], _check_super)
    register(["join"], _check_os_path_join)
    register(["%"], _check_percent_format)
    register(["format"], _check_format_method)
    register([":="], _check_walrus)
    register(["match"], _check_match)
    register(["def"], _check_type_params)
    register(["/"], _check_positional_only)
    register(["async", "await"], _check_async)
    register(["yield"], _check_yield_from)
    register(["except"], _check_except_star)
    register(["list", "dict", "set", "frozenset", "tuple", "type"], _check_builtin_generics)
    register(["|"], _check_union_types)
    return {name: tuple(checks) for name, checks in table.items()}


def _check_literals(context: "_Context", i: int) -> None:
    """Regole valide per qualunque token: letterali numerici e stringa.

    Queste regole non possono essere indicizzate per testo del token, perche'
    il testo e' diverso a ogni occorrenza.
    """
    _check_long_suffix(context, i)
    _check_unicode_prefix(context, i)
    _check_fstring(context, i)


#: Regole eseguite su ogni token, indipendentemente dal suo testo.
_ALWAYS_CHECKS: Tuple[Callable[["_Context", int], None], ...] = (_check_literals,)


def _run_checks(context: "_Context", i: int) -> None:
    """Esegue tutte le regole che si applicano al token in posizione ``i``."""
    tok = context.tokens[i]
    for check in _CHECKS_BY_TOKEN.get(tok.string, ()):
        check(context, i)
    for check in _ALWAYS_CHECKS:
        check(context, i)


def _token_key(tok: tokenize.TokenInfo) -> str:
    """Chiave di ricerca nella tabella delle regole."""
    return tok.string


#: Tabella associata al testo del token. Costruita qui, dopo la definizione
#: della funzione, perche' dipende da tutte le regole registrate sopra.
_CHECKS_BY_TOKEN: Mapping[str, Tuple[Callable[["_Context", int], None], ...]] = _build_checks()


def detect(source: str) -> Tuple[Finding, ...]:
    """Analizza il sorgente e restituisce i ritrovamenti, dal piu' grave al meno.

    Il codice viene tokenizzato, non interpretato: per questo l'analisi funziona
    anche su sorgenti Python 2 che non potrebbero essere compilati da Python 3.

    Args:
        source: il codice da analizzare.

    Returns:
        I ritrovamenti, ordinati per gravita' e poi per posizione.

    Example:
        >>> [f.rule for f in detect("print x\\n")]
        ['print-statement']
    """
    built = _Source.build(source)
    context = _Context(source=built, tokens=built.tokens)
    for i, _ in enumerate(built.tokens):
        _run_checks(context, i)
    order = {severity: rank for rank, severity in enumerate(_SEVERITY_ORDER)}
    return tuple(
        sorted(context.findings, key=lambda f: (order[f.severity], f.line, f.column, f.rule))
    )


def modernize(source: str) -> ModernizeResult:
    """Applica al sorgente le riscritture deterministiche.

    Le modifiche che si sovrappongono vengono scartate: e' preferibile lasciare
    un frammento invariato e segnalarlo, invece di produrre codice scorretto.

    Args:
        source: il codice da modernizzare.

    Returns:
        Un :class:`ModernizeResult` con il sorgente nuovo e l'elenco delle
        modifiche applicate o scartate.
    """
    built = _Source.build(source)
    context = _Context(source=built, tokens=built.tokens)
    for i, _ in enumerate(built.tokens):
        _run_checks(context, i)

    applied: List[TextEdit] = []
    skipped: List[Tuple[str, str]] = []
    for edit in sorted(context.edits, key=lambda e: (e.start, e.end)):
        if any(edit.start < other.end and other.start < edit.end for other in applied):
            continue
        skipped.append(
            (built.text[edit.start : edit.end], f"modifica sovrapposta ignorata @{edit.start}")
        )
        applied.append(edit)

    # la ricostruzione procede a ritroso sugli offset assoluti: ogni modifica
    # parte dalla copia normalizzata del sorgente, non dall'originale
    pieces: List[str] = []
    cursor = 0
    for edit in sorted(applied, key=lambda e: e.start):
        pieces.append(built.text[cursor : edit.start])
        pieces.append(edit.replacement)
        cursor = edit.end
    pieces.append(built.text[cursor:])

    findings = tuple(
        sorted(context.findings, key=lambda f: (f.line, f.column, f.rule))
    )
    return ModernizeResult(
        source="".join(pieces),
        original=source,
        findings=findings,
        applied=len(applied),
        skipped=tuple(skipped),
    )


def minimum_version(source: str, *, modernize_first: bool = True) -> str:
    """Calcola la versione minima di Python necessaria per eseguire il codice.

    L'algoritmo e' semplice e verificabile: si parte da Python 3.0 (il primo
    interprete che puo' eseguire il risultato della modernizzazione) e si
    prende il massimo fra le versioni che hanno introdotto le funzionalita'
    richieste dal codice. Ogni richiesta e' una regola di :func:`detect` che
    porta con se' la versione di introduzione.

    Non e' un analizzatore di dipendenze: non legge gli import e non controlla
    le librerie esterne. Risponde solo a "quale interprete serve per *questa*
    sintassi e per queste API", ed e' esattamente la domanda che si pone chi
    deve decidere se un progetto puo' scendere a Python 3.8.

    Args:
        source: il codice da valutare.
        modernize_first: se ``True`` (predefinito) valuta il codice dopo la
            modernizzazione, altrimenti il sorgente originale.

    Returns:
        La versione minima in formato ``"major.minor"``.

    Example:
        >>> minimum_version("if (n := 10) > 5:\\n    pass\\n")
        '3.8'
    """
    candidate = modernize(source).source if modernize_first else source

    required = _V30
    for finding in detect(candidate):
        if finding.removed is not None:
            # funzionalita' rimossa: il codice va riscritto, non si tratta di
            # un requisito di versione
            continue
        if finding.introduced is not None and finding.introduced > required:
            required = finding.introduced
    return str(required)


def summarize(findings: Iterable[Finding]) -> str:
    """Restituisce un riepilogo compatto dei ritrovamenti.

    Args:
        findings: i ritrovamenti da riassumere.

    Returns:
        Una tabella Markdown con il conteggio per regola.
    """
    counter: Dict[str, Tuple[Finding, int]] = {}
    for finding in findings:
        previous = counter.get(finding.rule)
        counter[finding.rule] = (finding, (previous[1] if previous else 0) + 1)

    if not counter:
        return "Nessun ritrovamento: il codice non mostra costrutti legacy."

    lines = ["| Regola | Gravita' | Occorrenze | Versione |", "|---|---|---|---|"]
    for rule, (finding, count) in sorted(
        counter.items(), key=lambda item: (_SEVERITY_ORDER.index(item[1][0].severity), item[0])
    ):
        version = f"rimossa in {finding.removed}" if finding.removed else f"da {finding.introduced}"
        lines.append(
            f"| `{rule}` | {finding.severity} | {count} | {version} |"
        )
    return "\n".join(lines)


def report(source: str) -> str:
    """Restituisce il rapporto testuale completo per un sorgente."""
    findings = detect(source)
    header = [
        f"Rilevati {len(findings)} problemi.",
        "",
        summarize(findings),
        "",
        "Dettaglio:",
    ]
    header.extend(finding.as_line() for finding in findings)
    return "\n".join(header)