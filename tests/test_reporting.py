"""Test di dimostrazioni, report Markdown e CLI.

Questi moduli producono i file che finiscono nel repository e l'interfaccia
che l'utente usa per interrogarli. Il rischio tipico qui non e' un valore
sbagliato, ma una divergenza fra cio' che il codice promette e cio' che il file
generato contiene: percio' i test scrivono su disco, rileggono e confrontano.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from pme import cli, demos, report
from pme.features import by_id, iter_features
from pme.version import Version, current_runtime_version, iter_releases

RADICE = Path(__file__).resolve().parent.parent
ESEMPIO_PY2 = RADICE / "examples" / "python2" / "legacy_report.py"


class DemoTest(unittest.TestCase):
    """Le dimostrazioni devono essere eseguibili e produrre il risultato atteso."""

    def test_ids_are_unique(self) -> None:
        ids = [demo.id for demo in demos.DEMOS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_feature_references_resolve(self) -> None:
        for demo in demos.DEMOS:
            if demo.feature_id is None:
                continue
            with self.subTest(demo=demo.id):
                self.assertEqual(by_id(demo.feature_id).id, demo.feature_id)

    def test_every_demo_assigns_a_result(self) -> None:
        for demo in demos.DEMOS:
            with self.subTest(demo=demo.id):
                self.assertIn("risultato =", demo.source)

    def test_runnable_demos_produce_the_expected_value(self) -> None:
        """Il cuore del progetto: ogni demo deve dare esattamente quel valore.

        Il confronto e' fatto a runtime e non con un valore scritto due volte:
        se una demo produce qualcos'altro, il fallimento dice esattamente cosa.
        """
        for demo in demos.DEMOS:
            if demo.since > current_runtime_version():
                continue
            with self.subTest(demo=demo.id):
                self.assertEqual(demo.result(), demo.expected)

    def test_available_matches_the_result(self) -> None:
        for demo in demos.DEMOS:
            with self.subTest(demo=demo.id):
                atteso = demo.since <= current_runtime_version()
                self.assertEqual(demo.available(), atteso)

    def test_render_produces_a_markdown_block(self) -> None:
        testo = report_text = demos.render(demos.get_demo("f-string"))
        self.assertTrue(testo.startswith("### "))
        self.assertIn("```python", testo)
        self.assertIn(demos.get_demo("f-string").source, testo)
        self.assertEqual(report_text, testo)

    def test_get_demo_raises_with_the_available_ids(self) -> None:
        with self.assertRaises(KeyError) as ctx:
            demos.get_demo("non-esiste")
        self.assertIn("f-string", str(ctx.exception))

    def test_run_available_yields_pairs(self) -> None:
        coppie = list(demos.run_available())
        self.assertTrue(coppie)
        for demo, esito in coppie:
            self.assertEqual(esito, demo.expected)

    def test_supported_ids_are_a_subset(self) -> None:
        for demo_id in demos.supported_ids():
            self.assertIn(demo_id, demos.demo_ids())


class ReportTest(unittest.TestCase):
    """Il Markdown generato deve contenere cio' che il catalogo afferma."""

    def test_render_feature_has_title_reason_and_source(self) -> None:
        testo = report.render_feature(by_id("pattern-matching"))
        self.assertTrue(testo.startswith("# "))
        self.assertIn("## Perche'", testo)
        self.assertIn("Fonte: https://", testo)

    def test_render_feature_shows_only_what_exists(self) -> None:
        testo = report.render_feature(by_id("print-statement"))
        self.assertIn("Come era", testo)
        self.assertIn("Come si usa oggi", testo)

    def test_render_feature_marks_removals(self) -> None:
        testo = report.render_feature(by_id("distutils-removed"))
        self.assertIn("rimossa in", testo)

    def test_render_version_card_lists_the_features(self) -> None:
        testo = report.render_version_card(Version(3, 12))
        self.assertTrue(testo.startswith("# Python 3.12"))
        for feature in iter_features():
            if feature.introduced != Version(3, 12):
                continue
            with self.subTest(feature=feature.id):
                self.assertIn(feature.title, testo)

    def test_render_version_card_mentions_removals(self) -> None:
        testo = report.render_version_card(Version(3, 12))
        self.assertIn("distutils", testo)

    def test_render_version_card_rejects_unknown_versions(self) -> None:
        with self.assertRaises(KeyError) as ctx:
            report.render_version_card(Version(9, 9))
        self.assertIn("9.9", str(ctx.exception))

    def test_render_timeline_has_a_row_per_release(self) -> None:
        testo = report.render_timeline()
        self.assertTrue(testo.startswith("# Calendario dei rilasci"))
        righe = [r for r in testo.splitlines() if r.startswith("| ")]
        # intestazione, separatore e una riga per rilascio
        self.assertEqual(len(righe), len(tuple(iter_releases())) + 2)

    def test_render_feature_index_covers_everything(self) -> None:
        testo = report.render_feature_index()
        for feature in iter_features():
            with self.subTest(feature=feature.id):
                self.assertIn(feature.title, testo)

    def test_write_version_cards_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cartella = Path(tmp)
            scritti = report.write_version_cards(cartella)
            self.assertEqual(len(scritti), len(report.version_card_names()))
            for percorso in scritti:
                self.assertTrue(percorso.exists())
            self.assertEqual(report.write_version_cards(cartella), [])
            self.assertEqual(
                (cartella / "python-3.12.md").read_text(encoding="utf-8"),
                report.render_version_card(Version(3, 12)),
            )

    def test_render_catalog_contains_every_card(self) -> None:
        testo = report.render_catalog()
        for feature in iter_features():
            with self.subTest(feature=feature.id):
                self.assertIn(feature.title, testo)

    def test_future_card_declares_what_is_not_released(self) -> None:
        testo = report.render_future()
        self.assertIn("future", testo.splitlines()[0].lower())
        for release in iter_releases():
            if release.is_released:
                continue
            with self.subTest(release=str(release.version)):
                self.assertIn(f"## Python {release.version}", testo)

    def test_write_future_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            percorso = report.write_future_card(Path(tmp))
            self.assertEqual(percorso.name, "future.md")
            self.assertEqual(percorso.read_text(encoding="utf-8"), report.render_future())


class CommandLineTest(unittest.TestCase):
    """La CLI deve rispondere e usare codici di uscita coerenti."""

    def esegui(self, argv: list[str]) -> tuple[int, str]:
        """Esegue la CLI e restituisce codice di uscita e testo prodotto."""
        flusso = io.StringIO()
        codice = cli.main(argv, flusso)
        return codice, flusso.getvalue()

    def test_versions_prints_every_release(self) -> None:
        codice, testo = self.esegui(["versions"])
        self.assertEqual(codice, 0)
        for release in iter_releases():
            self.assertIn(str(release.version), testo)

    def test_versions_markdown(self) -> None:
        codice, testo = self.esegui(["versions", "--markdown"])
        self.assertEqual(codice, 0)
        self.assertTrue(testo.startswith("# Calendario dei rilasci"))

    def test_features_by_id(self) -> None:
        codice, testo = self.esegui(["features", "--id", "f-string"])
        self.assertEqual(codice, 0)
        self.assertTrue(testo.startswith("# "))

    def test_features_filtered_by_version(self) -> None:
        codice, testo = self.esegui(["features", "--version", "3.10", "--markdown"])
        self.assertEqual(codice, 0)
        self.assertIn("pattern-matching", testo)
        self.assertNotIn("t-string", testo)

    def test_unknown_id_is_an_error_not_a_traceback(self) -> None:
        codice, testo = self.esegui(["features", "--id", "non-esiste"])
        self.assertEqual(codice, cli.EXIT_FINDINGS)
        self.assertIn("non-esiste", testo)

    def test_runtime_and_probes(self) -> None:
        codice, testo = self.esegui(["runtime", "--probes"])
        self.assertEqual(codice, 0)
        self.assertIn("implementazione", testo)
        self.assertIn("walrus", testo)

    def test_check_reports_findings_with_positions(self) -> None:
        codice, testo = self.esegui(["check", str(ESEMPIO_PY2)])
        self.assertEqual(codice, cli.EXIT_FINDINGS)
        self.assertIn(f"{ESEMPIO_PY2}:", testo)
        self.assertIn(" errore: ", testo)

    def test_check_is_silent_on_modern_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            percorso = Path(tmp) / "moderno.py"
            percorso.write_text("totale = somma(1, 2)\nprint(totale, file=errore)\n", encoding="utf-8")
            codice, testo = self.esegui(["check", str(percorso)])
        self.assertEqual(codice, 0)
        self.assertIn("nessun problema", testo)

    def test_check_reports_the_minimum_version_of_a_file(self) -> None:
        """Una f-string non e' un problema: e' un requisito di versione."""
        with tempfile.TemporaryDirectory() as tmp:
            percorso = Path(tmp) / "fstring.py"
            percorso.write_text("testo = f'{nome}'\n", encoding="utf-8")
            codice, testo = self.esegui(["check", str(percorso)])
        self.assertEqual(codice, cli.EXIT_FINDINGS)
        self.assertIn("richiede almeno la 3.6", testo)

    def test_check_reports_a_missing_file(self) -> None:
        codice, testo = self.esegui(["check", "file-che-non-esiste.py"])
        self.assertEqual(codice, cli.EXIT_FINDINGS)
        self.assertIn("errore", testo)

    def test_modernize_diff(self) -> None:
        codice, testo = self.esegui(["modernize", str(ESEMPIO_PY2), "--diff"])
        self.assertEqual(codice, 0)
        self.assertIn("originale", testo)

    def test_modernize_prints_the_new_source(self) -> None:
        codice, testo = self.esegui(["modernize", str(ESEMPIO_PY2)])
        self.assertEqual(codice, 0)
        self.assertIn("print(", testo)

    def test_demo_runs_one(self) -> None:
        codice, testo = self.esegui(["demo", "--id", "pattern-matching"])
        self.assertEqual(codice, 0)
        self.assertIn("risultato:", testo)

    def test_demo_rejects_unknown_id(self) -> None:
        codice, testo = self.esegui(["demo", "--id", "non-esiste"])
        self.assertEqual(codice, cli.EXIT_FINDINGS)
        self.assertIn("non-esiste", testo)

    def test_demo_lists_all(self) -> None:
        codice, testo = self.esegui(["demo"])
        self.assertEqual(codice, 0)
        for demo_id in demos.demo_ids():
            self.assertIn(demo_id, testo)

    def test_generate_writes_and_then_reports_up_to_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cartella = Path(tmp) / "versions"
            codice, _ = self.esegui(["generate", "--versions-dir", str(cartella)])
            self.assertEqual(codice, 0)
            self.assertTrue((cartella / "python-3.14.md").exists())
            codice, testo = self.esegui(["generate", "--versions-dir", str(cartella)])
        self.assertEqual(codice, 0)
        self.assertIn("aggiornato", testo)

    def test_parser_requires_a_command(self) -> None:
        with self.assertRaises(SystemExit):
            cli.build_parser().parse_args([])


if __name__ == "__main__":
    unittest.main()
