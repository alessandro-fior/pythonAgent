"""Test di :mod:`pme.legacy`.

Il file di esempio ``examples/python2/legacy_report.py`` contiene sintassi
Python 2 che Python 3 non sa compilare: non viene mai importato, solo letto
come testo. E' esattamente il modo in cui un analizzatore di codice legacy
deve comportarsi.
"""

from __future__ import annotations

import io
import re
import tokenize
import unittest
from pathlib import Path

from pme.legacy import Severity, detect, minimum_version, modernize, rules, summarize

ROOT = Path(__file__).resolve().parents[1]
LEGACY_EXAMPLE = ROOT / "examples" / "python2" / "legacy_report.py"


def read_legacy_example() -> str:
    """Legge l'esempio Python 2 come testo."""
    return LEGACY_EXAMPLE.read_text(encoding="utf-8")


class TokenizerAcceptsPython2Test(unittest.TestCase):
    """Verifica la premessa del modulo: il tokenizer accetta il Python 2."""

    def test_example_is_not_valid_python3(self) -> None:
        source = read_legacy_example()
        with self.assertRaises(SyntaxError):
            compile(source, str(LEGACY_EXAMPLE), "exec")

    def test_tokenizer_accepts_python2(self) -> None:
        source = read_legacy_example()
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        self.assertTrue(tokens)
        self.assertIn("print", {tok.string for tok in tokens})


class DetectRulesTest(unittest.TestCase):
    """Ogni regola deve scattare su un frammento minimale."""

    def _rules_of(self, source: str) -> set:
        return {finding.rule for finding in detect(source)}

    def test_print_statement(self) -> None:
        findings = detect("print x\n")
        self.assertEqual([f.rule for f in findings], ["print-statement"])
        self.assertIs(findings[0].severity, Severity.ERROR)
        self.assertEqual(str(findings[0].removed), "3.0")

    def test_print_call_is_not_flagged(self) -> None:
        self.assertNotIn("print-statement", self._rules_of("print(x)\n"))

    def test_raw_input(self) -> None:
        self.assertIn("raw-input", self._rules_of("x = raw_input()\n"))

    def test_xrange(self) -> None:
        self.assertIn("xrange", self._rules_of("for i in xrange(3):\n    pass\n"))

    def test_iteritems(self) -> None:
        self.assertIn("iteritems", self._rules_of("d.iteritems()\n"))

    def test_has_key(self) -> None:
        self.assertIn("has-key", self._rules_of("d.has_key('a')\n"))

    def test_angle_comparison(self) -> None:
        self.assertIn("angle-comparison", self._rules_of("if a <> b:\n    pass\n"))

    def test_backtick(self) -> None:
        self.assertIn("backtick-repr", self._rules_of("x = `a`\n"))

    def test_except_comma(self) -> None:
        self.assertIn("except-comma", self._rules_of("try:\n    pass\nexcept E, e:\n    pass\n"))

    def test_except_tuple_is_not_flagged(self) -> None:
        source = "try:\n    pass\nexcept (A, B):\n    pass\n"
        self.assertNotIn("except-comma", self._rules_of(source))

    def test_except_as_is_not_flagged(self) -> None:
        source = "try:\n    pass\nexcept E as e:\n    pass\n"
        self.assertNotIn("except-comma", self._rules_of(source))

    def test_true_division_is_a_warning(self) -> None:
        findings = detect("x = 7 / 2\n")
        self.assertEqual([f.rule for f in findings], ["true-division"])
        self.assertIs(findings[0].severity, Severity.WARNING)

    def test_true_division_ignores_non_integers(self) -> None:
        self.assertNotIn("true-division", self._rules_of("x = a / b\n"))
        self.assertNotIn("true-division", self._rules_of("x = 1.5 / 2\n"))

    def test_unicode_prefix(self) -> None:
        self.assertIn("unicode-literal-prefix", self._rules_of('x = u"a"\n'))
        self.assertNotIn("unicode-literal-prefix", self._rules_of('x = "a"\n'))
        self.assertNotIn("unicode-literal-prefix", self._rules_of('x = r"a"\n'))

    def test_long_suffix(self) -> None:
        self.assertIn("long-literal-suffix", self._rules_of("x = 10L\n"))
        self.assertNotIn("long-literal-suffix", self._rules_of("x = 10\n"))

    def test_sys_maxint(self) -> None:
        self.assertIn("sys-maxint", self._rules_of("x = sys.maxint\n"))

    def test_method_with_legacy_name_is_ignored(self) -> None:
        # un metodo omonimo non e' la funzione rimossa
        self.assertEqual(self._rules_of("d.reduce()\n"), set())

    def test_definition_shadowing_is_ignored(self) -> None:
        source = "def cmp(a, b):\n    return a\n"
        self.assertEqual(self._rules_of(source), set())

    def test_class_without_base(self) -> None:
        self.assertIn("classic-classes", self._rules_of("class C:\n    pass\n"))

    def test_class_with_base_is_not_flagged(self) -> None:
        source = "class C(object):\n    pass\n"
        self.assertNotIn("classic-classes", self._rules_of(source))

    def test_metaclass(self) -> None:
        source = "class C(object):\n    __metaclass__ = type\n"
        self.assertIn("metaclass-syntax", self._rules_of(source))

    def test_super_with_arguments(self) -> None:
        source = "class C(Base):\n    def m(self):\n        super(C, self).m()\n"
        self.assertIn("modern-super", self._rules_of(source))

    def test_percent_formatting(self) -> None:
        self.assertIn("modern-fstring", self._rules_of('x = "ciao %s" % nome\n'))

    def test_clean_modern_code_has_no_findings(self) -> None:
        source = (
            "import os\n"
            "\n"
            "def somma(valori):\n"
            "    totale = 0\n"
            "    for valore in valori:\n"
            "        totale = totale + valore\n"
            "    return totale\n"
            "\n"
            "def percorso(base, nome):\n"
            "    return os.path.join(base, nome)\n"
        )
        self.assertEqual(detect(source), ())


class SeverityTest(unittest.TestCase):
    """Gravita' e ordinamento dei ritrovamenti."""

    def test_findings_sorted_by_severity(self) -> None:
        source = 'x = 7 / 2\nprint y\nd.iteritems()\n' + 'z = "a %s" % 1\n'
        findings = detect(source)
        severities = [f.severity for f in findings]
        self.assertEqual(severities, sorted(severities, key=lambda s: [Severity.ERROR, Severity.WARNING, Severity.ADVICE].index(s)))

    def test_is_blocking(self) -> None:
        errors = [f for f in detect("print x\n") if f.is_blocking]
        self.assertEqual(len(errors), 1)

    def test_location_and_line(self) -> None:
        finding = detect("a = 1\nprint b\n")[0]
        self.assertEqual(finding.line, 2)
        self.assertEqual(finding.location(), "2:0")

    def test_as_line_contains_rule(self) -> None:
        finding = detect("print x\n")[0]
        self.assertIn("print-statement", finding.as_line())


class ModernizeTest(unittest.TestCase):
    """Le riscritture deterministiche."""

    def assertModernizes(self, source: str, expected: str) -> None:
        result = modernize(source)
        self.assertEqual(result.source, expected)
        self.assertTrue(result.changed)
        compile(result.source, "<modernized>", "exec")

    def test_print_simple(self) -> None:
        self.assertModernizes("print 'ciao'\n", "print('ciao')\n")

    def test_print_expression(self) -> None:
        self.assertModernizes("print 1 + 2\n", "print(1 + 2)\n")

    def test_print_alone(self) -> None:
        self.assertModernizes("print\n", "print()\n")

    def test_print_bare_statement_with_tuple(self) -> None:
        # Python 2: `print x, y` stampa due elementi separati da uno spazio
        self.assertModernizes("print x, y\n", "print(x, y)\n")

    def test_print_trailing_comma(self) -> None:
        # Python 2: `print x,` non andava a capo
        self.assertModernizes("print x,\n", "print(x, end=' ')\n")

    def test_print_redirect_is_reported_not_applied(self) -> None:
        source = "print >>sys.stderr, 'errore'\n"
        result = modernize(source)
        self.assertEqual(result.source, source)
        self.assertIn("print-statement", {f.rule for f in result.findings})

    def test_renamed_calls(self) -> None:
        self.assertModernizes("x = xrange(3)\n", "x = range(3)\n")
        self.assertModernizes("x = raw_input()\n", "x = input()\n")
        self.assertModernizes("x = unicode(y)\n", "x = str(y)\n")
        self.assertModernizes("x = unichr(65)\n", "x = chr(65)\n")

    def test_dict_view_methods(self) -> None:
        self.assertModernizes("a = d.iteritems()\n", "a = d.items()\n")
        self.assertModernizes("a = d.iterkeys()\n", "a = d.keys()\n")
        self.assertModernizes("a = d.itervalues()\n", "a = d.values()\n")

    def test_operator_and_literals(self) -> None:
        self.assertModernizes("if a <> b:\n    pass\n", "if a != b:\n    pass\n")
        self.assertModernizes("x = 10L\n", "x = 10\n")
        self.assertModernizes('x = u"a"\n', 'x = "a"\n')

    def test_except_comma(self) -> None:
        source = "try:\n    pass\nexcept E, err:\n    pass\n"
        self.assertModernizes(source, "try:\n    pass\nexcept E as err:\n    pass\n")

    def test_modernize_keeps_unchanged_source(self) -> None:
        source = "try:\n    pass\nexcept (A, B):\n    pass\n"
        result = modernize(source)
        self.assertEqual(result.source, source)
        self.assertFalse(result.changed)
        self.assertEqual(result.applied, 0)

    def test_has_key_is_reported_but_not_fixed(self) -> None:
        source = "d.has_key('a')\n"
        result = modernize(source)
        self.assertEqual(result.source, source)
        self.assertIn("has-key", {f.rule for f in result.findings})

    def test_sys_maxint(self) -> None:
        self.assertModernizes("x = sys.maxint\n", "x = sys.maxsize\n")

    def test_imported_legacy_module_is_reported(self) -> None:
        source = "from StringIO import StringIO\n"
        result = modernize(source)
        self.assertEqual(result.source, source)
        self.assertIn("legacy-removed-call", {f.rule for f in result.findings})

    def test_reduce_suggests_import(self) -> None:
        source = "x = reduce(f, seq)\n"
        result = modernize(source)
        self.assertEqual(result.source, source)
        self.assertIn("reduce-moved", {f.rule for f in result.findings})

    def test_modern_code_unchanged(self) -> None:
        source = "print(f'{x!r}')\n"
        result = modernize(source)
        self.assertEqual(result.source, source)
        self.assertFalse(result.changed)
        self.assertEqual(result.applied, 0)

    def test_multiple_fixes_in_one_file(self) -> None:
        source = "d = {}\nfor k, v in d.iteritems():\n    print k\n"
        expected = "d = {}\nfor k, v in d.items():\n    print(k)\n"
        self.assertModernizes(source, expected)

    def test_overlapping_fixes_are_skipped(self) -> None:
        # `print unicode(x)` richiede due modifiche vicine ma non sovrapposte;
        # il risultato deve restare compilabile
        result = modernize("print unicode(x)\n")
        compile(result.source, "<modernized>", "exec")
        self.assertEqual(result.source, "print(str(x))\n")

    def test_findings_sorted_by_position(self) -> None:
        source = "d.iteritems()\nprint x\n"
        findings = modernize(source).findings
        positions = [(f.line, f.column) for f in findings]
        self.assertEqual(positions, sorted(positions))


#: Regole che il modulo segnala ma non corregge: la riscrittura richiederebbe
#: di modificare la struttura dell'espressione, non solo i suoi token.
NON_AUTOMATIZZABILI = frozenset(
    {
        "backtick-repr",
        "has-key",
        "true-division",
        "classic-classes",
        "modern-fstring",
        "modern-super",
        "modern-pathlib",
        "reduce-moved",
        "metaclass-syntax",
        "raise-old-form",
    }
)


class ExampleFileTest(unittest.TestCase):
    """L'esempio reale viene analizzato per intero."""

    def setUp(self) -> None:
        self.source = read_legacy_example()
        self.findings = detect(self.source)

    def test_finds_many_problems(self) -> None:
        self.assertGreaterEqual(len(self.findings), 20)

    def test_no_duplicate_findings(self) -> None:
        """Due regole diverse non devono colpire lo stesso token.

        Un doppione gonfierebbe il conteggio e suggerirebbe al lettore due
        problemi distinti dove ce n'e' uno solo.
        """
        posizioni = [(f.rule, f.line, f.column) for f in self.findings]
        self.assertEqual(len(posizioni), len(set(posizioni)))

    def test_expected_rules_present(self) -> None:
        rules_found = {f.rule for f in self.findings}
        for expected in (
            "print-statement",
            "iteritems",
            "has-key",
            "true-division",
            "except-comma",
            "raw-input",
            "unicode-type",
            "unicode-literal-prefix",
            "long-literal-suffix",
            "backtick-repr",
            "angle-comparison",
            "modern-fstring",
            "classic-classes",
        ):
            self.assertIn(expected, rules_found)

    def test_every_finding_has_a_position(self) -> None:
        for finding in self.findings:
            self.assertGreaterEqual(finding.line, 1)
            self.assertGreaterEqual(finding.column, 0)

    def test_modernization_fixes_everything_it_claims(self) -> None:
        """Dopo la modernizzazione restano solo problemi non automatizzabili."""
        result = modernize(self.source)
        leftover = {f.rule for f in detect(result.source)}
        self.assertEqual(leftover - NON_AUTOMATIZZABILI, set())

    def test_modernization_removes_print_statements(self) -> None:
        result = modernize(self.source)
        leftover = [f.rule for f in detect(result.source) if f.rule == "print-statement"]
        self.assertEqual(leftover, [])

    def test_modernized_output_compiles_once_backticks_are_fixed(self) -> None:
        """Dopo la correzione manuale del backtick, il file e' Python 3 valido.

        Il backtick e' l'esempio del limite dichiarato del modulo: viene
        segnalato ma non riscritto, perche' la trasformazione da ``x`` a
        ``repr(x)`` richiede di sapere dove finisce l'espressione. Qui la
        correzione viene simulata a mano, come farebbe uno sviluppatore.
        """
        result = modernize(self.source)
        corretto = re.sub(r"`([^`]*)`", r"repr('\1')", result.source)
        compile(corretto, "<modernized-example>", "exec")

    def test_summary_is_markdown_table(self) -> None:
        text = summarize(self.findings)
        self.assertIn("| Regola |", text)
        self.assertIn("iteritems", text)

    def test_summary_of_nothing(self) -> None:
        self.assertIn("Nessun ritrovamento", summarize(()))


class MinimumVersionTest(unittest.TestCase):
    """La versione minima richiesta dal codice."""

    def test_empty_code(self) -> None:
        self.assertEqual(minimum_version(""), "3.0")

    def test_python2_code_after_modernization(self) -> None:
        source = "for i in xrange(3):\n    print i\n"
        self.assertEqual(minimum_version(source), "3.0")

    def test_match_statement_requires_310(self) -> None:
        source = (
            "def f(x):\n"
            "    match x:\n"
            "        case 1:\n"
            "            return 'uno'\n"
            "        case _:\n"
            "            return 'altro'\n"
        )
        self.assertEqual(minimum_version(source), "3.10")

    def test_walrus_requires_38(self) -> None:
        source = "def f(d):\n    if (n := len(d)) > 2:\n        return n\n"
        self.assertEqual(minimum_version(source), "3.8")

    def test_fstring_requires_36(self) -> None:
        self.assertEqual(minimum_version("x = f'{a}'\n"), "3.6")

    def test_original_python2_needs_modernization_first(self) -> None:
        self.assertEqual(minimum_version("print 10L\n"), "3.0")

    def test_without_modernization_reports_removed_api(self) -> None:
        # senza modernizzare, `xrange` viene comunque segnalato ma non
        # determina un requisito: resta la base 3.0
        self.assertEqual(minimum_version("for i in xrange(3):\n    pass\n", modernize_first=False), "3.0")


class RuleTableTest(unittest.TestCase):
    """La tabella delle regole deve restare coerente."""

    def test_rules_have_unique_ids(self) -> None:
        identifiers = [rule.id for rule in rules()]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_rule_ids_are_kebab_or_snake_case(self) -> None:
        for rule in rules():
            self.assertRegex(rule.id, r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def test_every_rule_has_a_title_and_severity(self) -> None:
        for rule in rules():
            self.assertTrue(rule.title)
            self.assertIsInstance(rule.severity, Severity)

    def test_rules_that_remove_something_target_30(self) -> None:
        for rule in rules():
            if rule.removed is not None:
                self.assertEqual(str(rule.removed), "3.0", rule.id)


if __name__ == "__main__":
    unittest.main()