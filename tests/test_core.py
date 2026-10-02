"""Test del nucleo documentale: versioni, catalogo, sonde e runtime.

I dati che questi test mettono alla prova provengono da fonti esterne
(ufficio), quindi non sono verificabili dagli stessi test. Qui si controlla
che siano *internamente coerenti* e che le funzioni pubbliche si comportino
come la documentazione promette: e' il massimo che un test puo' garantire su
un dato esterno, ed e' comunque essenziale perche' un errore di coerenza
(riga vuota, versione invertita, riferimento pendente) indica un refuso, non
un dubbio sul dato.
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from pme import features as F
from pme import probes as P
from pme import runtime as R
from pme import version as V


class VersionTest(unittest.TestCase):
    """Confronto e ordinamento delle versioni.

    Le versioni sono ``major.minor`` senza il numero di patch: il progetto
    ragiona per rilasci (``3.14``), non per micro versioni.
    """

    def test_parse_simple(self) -> None:
        self.assertEqual(V.Version.parse("3.10"), V.Version(3, 10))

    def test_parse_ignores_the_patch_level(self) -> None:
        self.assertEqual(V.Version.parse("3.14.5"), V.Version(3, 14))

    def test_numeric_comparison_not_lexicographic(self) -> None:
        self.assertGreater(V.Version.parse("3.10"), V.Version.parse("3.9"))

    def test_ordering_chain(self) -> None:
        self.assertLess(
            V.Version.parse("3.9"),
            V.Version.parse("3.10"),
        )
        self.assertLess(V.Version.parse("3.10"), V.Version.parse("3.11"))

    def test_equality_and_hash(self) -> None:
        self.assertEqual(V.Version.parse("3.12"), V.Version(3, 12))
        self.assertEqual(len({V.Version(3, 12), V.Version(3, 12)}), 1)

    def test_str_roundtrip(self) -> None:
        self.assertEqual(str(V.Version.parse("3.14.2")), "3.14")

    def test_rejects_non_numeric(self) -> None:
        for text in ("", "tre", "3.x", "abc.def"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                V.Version.parse(text)


class ReleaseCatalogueTest(unittest.TestCase):
    """Il calendario delle release."""

    def test_releases_are_sorted(self) -> None:
        versions = [release.version for release in V.iter_releases()]
        self.assertEqual(versions, sorted(versions))

    def test_no_duplicate_versions(self) -> None:
        versions = [release.version for release in V.iter_releases()]
        self.assertEqual(len(versions), len(set(versions)))

    def test_release_dates_are_in_the_past(self) -> None:
        for release in V.iter_releases():
            if not release.is_released:
                continue
            with self.subTest(version=str(release.version)):
                self.assertLessEqual(release.released, date.today())

    def test_eol_is_after_release(self) -> None:
        for release in V.iter_releases():
            if release.eol is None:
                continue
            with self.subTest(version=str(release.version)):
                self.assertGreater(release.eol, release.released)

    def test_prereleases_are_not_released(self) -> None:
        for release in V.iter_releases():
            if release.lifecycle in (V.Lifecycle.FEATURE, V.Lifecycle.PRERELEASE):
                with self.subTest(version=str(release.version)):
                    self.assertFalse(release.is_released)
                    self.assertFalse(release.supported)

    def test_supported_releases_exclude_prerelease(self) -> None:
        supported = V.supported_releases()
        self.assertTrue(supported)
        for release in supported:
            self.assertTrue(release.is_released)
            self.assertIsNot(release.lifecycle, V.Lifecycle.END_OF_LIFE)

    def test_latest_stable_is_not_a_prerelease(self) -> None:
        latest = V.latest_stable()
        self.assertTrue(latest.is_released)
        self.assertIsNot(latest.lifecycle, V.Lifecycle.END_OF_LIFE)

    def test_latest_stable_is_the_maximum(self) -> None:
        self.assertGreaterEqual(
            V.latest_stable().version,
            max(r.version for r in V.supported_releases()),
        )

    def test_python2_releases_are_eol(self) -> None:
        for release in V.iter_releases():
            if release.version.major == 2:
                with self.subTest(version=str(release.version)):
                    self.assertIs(release.lifecycle, V.Lifecycle.END_OF_LIFE)

    def test_python4_is_not_released(self) -> None:
        self.assertFalse(V.PYTHON4_RELEASED)
        self.assertTrue(V.PYTHON4_NOTE)

    def test_every_release_has_a_source(self) -> None:
        for release in V.iter_releases():
            with self.subTest(version=str(release.version)):
                self.assertTrue(release.source.startswith("https://"))

    def test_by_version_and_get_agree(self) -> None:
        for release in V.iter_releases():
            with self.subTest(version=str(release.version)):
                self.assertEqual(V.by_version(release.version).version, release.version)
                self.assertEqual(V.get(str(release.version)).version, release.version)

    def test_next_version_follows_the_catalogue(self) -> None:
        self.assertEqual(
            V.next_version(V.Version(3, 13)), V.Version(3, 14)
        )

    def test_next_version_of_last_is_none(self) -> None:
        last = max(r.version for r in V.iter_releases())
        self.assertIsNone(V.next_version(last))

    def test_timeline_rows_are_complete(self) -> None:
        rows = V.timeline_rows()
        releases = list(V.iter_releases())
        self.assertEqual(len(rows), len(releases))
        for row in rows:
            self.assertEqual(len(row), 4)

    def test_release_dates_table_is_markdown(self) -> None:
        table = V.release_dates_table()
        self.assertIn("|", table)
        self.assertIn("3.14", table)


class FeatureCatalogueTest(unittest.TestCase):
    """Il catalogo delle funzionalita'."""

    def test_ids_are_unique(self) -> None:
        ids = [feature.id for feature in F.iter_features()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ids_are_kebab_case(self) -> None:
        for feature in F.iter_features():
            with self.subTest(feature=feature.id):
                self.assertRegex(feature.id, r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def test_every_feature_has_a_summary(self) -> None:
        for feature in F.iter_features():
            with self.subTest(feature=feature.id):
                self.assertTrue(feature.summary.strip())

    def test_every_feature_explains_why(self) -> None:
        """`agent.md` chiede la motivazione: e' un campo obbligatorio."""
        for feature in F.iter_features():
            with self.subTest(feature=feature.id):
                self.assertTrue(feature.reason.strip())

    def test_every_feature_has_an_official_source(self) -> None:
        for feature in F.iter_features():
            with self.subTest(feature=feature.id):
                self.assertTrue(feature.source.startswith("https://"))

    def test_after_snippets_compile(self) -> None:
        """Il codice "come si usa oggi" deve essere Python valido.

        I frammenti ``before`` non sono invece controllati: descrivono il
        Python precedente e sono spesso sintatticamente non validi, ed e'
        esattamente cio' che vogliono mostrare.
        """
        for feature in F.iter_features():
            if not feature.after:
                continue
            with self.subTest(feature=feature.id):
                compile(feature.after, f"<{feature.id}:after>", "exec")

    def test_removal_features_date_the_removal(self) -> None:
        """Per una rimozione, ``introduced`` e' la versione che ha rimosso.

        E' la convenzione del catalogo: una scheda di tipo ``Rimozioni``
        descrive un costrutto che *non esiste piu'* dalla versione indicata,
        quindi la data della rimozione e' quella di introduzione della scheda.
        """
        for feature in F.iter_features():
            if feature.kind is not F.Kind.REMOVAL:
                continue
            with self.subTest(feature=feature.id):
                self.assertGreaterEqual(feature.introduced, V.PY3_0)
                self.assertTrue(feature.before, "manca il codice di partenza")

    def test_deprecated_features_have_a_deprecation_version(self) -> None:
        for feature in F.iter_features():
            if feature.kind is F.Kind.DEPRECATION:
                with self.subTest(feature=feature.id):
                    self.assertIsNotNone(feature.deprecated)

    def test_a_removal_may_be_deprecated_before_it_is_removed(self) -> None:
        """`2to3` e' stato annunciato nel 3.11 e rimosso nel 3.13.

        E' il caso che distingue "rimosso" da "introdotto": la scheda descrive
        una rimozione, quindi non puo' essere contata come novita'.
        """
        feature = F.get("deprecated-2to3-removed")
        self.assertEqual(feature.deprecated, V.Version(3, 11))
        self.assertEqual(feature.removed, V.Version(3, 13))
        annunciata = F.changed_between(V.Version(3, 10), V.Version(3, 11))
        self.assertIn(feature, annunciata["deprecate"])
        self.assertNotIn(feature, annunciata["rimosse"])
        eseguita = F.changed_between(V.Version(3, 12), V.Version(3, 13))
        self.assertIn(feature, eseguita["rimosse"])
        self.assertNotIn(feature, eseguita["introdotte"])

    def test_a_deprecation_is_not_a_removal_until_it_is_scheduled(self) -> None:
        feature = F.get("typeddict-fields-deprecation")
        self.assertEqual(feature.deprecated, V.Version(3, 13))
        self.assertEqual(feature.removed, V.Version(3, 16))
        annunciata = F.changed_between(V.Version(3, 12), V.Version(3, 14))
        self.assertIn(feature, annunciata["deprecate"])
        self.assertNotIn(feature, annunciata["rimosse"])
        eseguita = F.changed_between(V.Version(3, 15), V.Version(3, 16))
        self.assertIn(feature, eseguita["rimosse"])
        self.assertNotIn(feature, eseguita["deprecate"])

    def test_removals_are_reported_as_removed_not_as_new(self) -> None:
        window = F.changed_between(V.Version(3, 11), V.Version(3, 14))
        for feature in F.iter_features():
            if feature.kind is not F.Kind.REMOVAL:
                continue
            if not V.Version(3, 11) < feature.introduced <= V.Version(3, 14):
                continue
            with self.subTest(feature=feature.id):
                self.assertIn(feature, window["rimosse"])
                self.assertNotIn(feature, window["introdotte"])

    def test_every_feature_explains_why_and_cites_a_source(self) -> None:
        for feature in F.iter_features():
            with self.subTest(feature=feature.id):
                self.assertTrue(feature.reason.strip())
                self.assertTrue(feature.source.startswith("https://"))

    def test_versions_are_ordered(self) -> None:
        for feature in F.iter_features():
            if feature.deprecated and feature.removed:
                with self.subTest(feature=feature.id):
                    self.assertLess(feature.deprecated, feature.removed)

    def test_by_id_and_get_agree(self) -> None:
        for feature in F.iter_features():
            with self.subTest(feature=feature.id):
                self.assertEqual(F.by_id(feature.id).id, feature.id)
                self.assertEqual(F.get(feature.id).id, feature.id)

    def test_unknown_ids_raise_with_the_available_ones(self) -> None:
        with self.assertRaises(KeyError) as ctx:
            F.by_id("non-esiste")
        self.assertIn("non-esiste", str(ctx.exception))

    def test_get_raises_a_helpful_error(self) -> None:
        with self.assertRaises(KeyError) as ctx:
            F.get("non-esiste")
        self.assertIn("disponibili", str(ctx.exception))

    def test_introduced_in_groups_by_version(self) -> None:
        found = F.introduced_in(V.Version(3, 8))
        for feature in found:
            self.assertEqual(feature.introduced, V.Version(3, 8))

    def test_introduced_in_covers_every_version(self) -> None:
        for release in V.iter_releases():
            if not release.is_released:
                continue
            found = F.introduced_in(release.version)
            with self.subTest(version=str(release.version)):
                self.assertTrue(
                    found, f"nessuna scheda per {release.version}"
                )

    def test_removed_in_groups_by_version(self) -> None:
        for feature in F.removed_in(V.Version(3, 0)):
            self.assertEqual(feature.removed, V.Version(3, 0))

    def test_headline_features_limited(self) -> None:
        for release in V.iter_releases():
            found = F.headline_features(release.version, limit=3)
            with self.subTest(version=str(release.version)):
                self.assertLessEqual(len(found), 3)

    def test_headline_features_are_marked(self) -> None:
        for release in V.iter_releases():
            for feature in F.headline_features(release.version):
                with self.subTest(version=str(release.version), feature=feature.id):
                    self.assertTrue(feature.headline)

    def test_changed_between_rejects_an_inverted_window(self) -> None:
        with self.assertRaises(ValueError):
            F.changed_between(V.Version(3, 1), V.Version(3, 0))

    def test_changed_between_same_version_is_empty(self) -> None:
        window = F.changed_between(V.Version(3, 5), V.Version(3, 5))
        for group in window.values():
            self.assertEqual(group, ())

    def test_changed_between_groups(self) -> None:
        window = F.changed_between(V.Version(3, 0), V.Version(3, 14))
        self.assertTrue(window["introdotte"])
        self.assertTrue(window["rimosse"])

    def test_requires_matches_introduced(self) -> None:
        for feature in F.iter_features():
            if feature.removed is not None:
                continue
            with self.subTest(feature=feature.id):
                self.assertEqual(F.requires(feature.id), feature.introduced)

    def test_the_parenthesised_with_probe_uses_the_310_syntax(self) -> None:
        """La sonda deve contenere le parentesi, non la forma gia' valida dal 3.1."""
        probe = P.get_probe("parenthesized-with-items")
        self.assertEqual(probe.since, V.Version(3, 10))
        self.assertIn("with (", probe.source)
        self.assertIn("\n):", probe.source)

    def test_topical_index_covers_everything(self) -> None:
        indexed = [f for group in F.topical_index().values() for f in group]
        self.assertEqual(len(indexed), len(list(F.iter_features())))

    def test_probe_references_resolve(self) -> None:
        """Le sonde che dichiarano una funzionalita' devono trovarla."""
        for probe in P.probe_syntax():
            if probe.feature_id is None:
                continue
            with self.subTest(probe=probe.id):
                self.assertEqual(F.by_id(probe.feature_id).id, probe.feature_id)

    def test_probe_versions_agree_with_the_catalogue(self) -> None:
        """La versione della sonda coincide con quella della scheda."""
        for probe in P.probe_syntax():
            if probe.feature_id is None:
                continue
            card = F.by_id(probe.feature_id)
            with self.subTest(probe=probe.id):
                self.assertEqual(probe.since, card.introduced)


class ProbeTest(unittest.TestCase):
    """Le sonde sintattiche."""

    def test_ids_are_unique(self) -> None:
        ids = [probe.id for probe in P.probe_syntax()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_probe_has_a_description(self) -> None:
        for probe in P.probe_syntax():
            with self.subTest(probe=probe.id):
                self.assertTrue(probe.description.strip())

    def test_every_probe_compiles_on_this_interpreter(self) -> None:
        """Le sonde devono riflettere l'interprete su cui girano."""
        for probe in P.probe_syntax():
            with self.subTest(probe=probe.id):
                self.assertTrue(probe.available(), probe.description)

    def test_since_is_a_released_version(self) -> None:
        released = {r.version for r in V.iter_releases() if r.is_released}
        for probe in P.probe_syntax():
            with self.subTest(probe=probe.id):
                self.assertIn(probe.since, released)

    def test_get_probe(self) -> None:
        first = next(P.probe_syntax())
        self.assertEqual(P.get_probe(first.id).id, first.id)
        self.assertIsNone(P.get_probe("non-esiste"))

    def test_check_reports_false_on_failure(self) -> None:
        self.assertFalse(P.check(lambda: 1 / 0))


class RuntimeTest(unittest.TestCase):
    """La fotografia dell'interprete.

    ``pme.runtime.runtime_info`` e' un'istantia già calcolata, non una
    funzione: rilevare l'ambiente costa e il risultato non cambia durante
    l'esecuzione.
    """

    def setUp(self) -> None:
        self.info = R.runtime_info

    def test_runtime_info_is_a_singleton_instance(self) -> None:
        self.assertIsInstance(R.runtime_info, R.RuntimeInfo)

    def test_module_exposes_a_frozen_dataclass(self) -> None:
        with self.assertRaises(Exception):
            R.runtime_info.version = V.Version(3, 0)  # type: ignore[misc]

    def test_version_matches_the_interpreter(self) -> None:
        import sys

        self.assertEqual(self.info.version, V.current_runtime_version())
        self.assertEqual(self.info.version_string, sys.version.split()[0])

    def test_syntax_map_matches_probes(self) -> None:
        expected = {probe.id for probe in P.probe_syntax()}
        self.assertEqual(set(self.info.syntax), expected)

    def test_all_probes_available_here(self) -> None:
        for probe_id, ok in self.info.syntax.items():
            with self.subTest(probe=probe_id):
                self.assertTrue(ok)

    def test_maps_are_read_only(self) -> None:
        with self.assertRaises(TypeError):
            self.info.syntax["match"] = False  # type: ignore[index]
        with self.assertRaises(TypeError):
            self.info.capabilities["t-string"] = True  # type: ignore[index]

    def test_as_table_is_read_only(self) -> None:
        with self.assertRaises(TypeError):
            self.info.as_table()["versione"] = "0"  # type: ignore[index]

    def test_supports_version_uses_numeric_order(self) -> None:
        self.assertTrue(self.info.supports_version("3.0"))
        self.assertFalse(self.info.supports_version("99.0"))

    def test_missing_requirements_is_empty_for_low_versions(self) -> None:
        self.assertEqual(self.info.missing_version_requirements("3.0"), ())

    def test_missing_requirements_is_empty_for_current(self) -> None:
        self.assertEqual(self.info.missing_version_requirements("3.0.0"), ())

    def test_module_supports_reflects_the_interpreter(self) -> None:
        self.assertTrue(R.supports("3.0"))
        self.assertFalse(R.supports("99.0"))

    def test_require_raises_for_the_future(self) -> None:
        with self.assertRaises(RuntimeError):
            R.require("99.0")

    def test_require_is_silent_for_supported(self) -> None:
        self.assertIsNone(R.require("3.0"))

    def test_supports_also_asks_the_parser(self) -> None:
        """La versione non basta: conta anche la sintassi realmente supportata.

        Si simula un interprete con la versione giusta ma senza una capacita'
        sintattica, il caso delle build particolari descritte in
        :mod:`pme.runtime`.
        """
        probe = next(p for p in P.probe_syntax() if p.since > V.Version(3, 0))
        sintassi = dict(self.info.syntax)
        sintassi[probe.id] = False
        finto = R.RuntimeInfo(
            implementation=self.info.implementation,
            version=self.info.version,
            version_string=self.info.version_string,
            releaselevel=self.info.releaselevel,
            gil_enabled=self.info.gil_enabled,
            jit_available=self.info.jit_available,
            sys_builtin_module_names=self.info.sys_builtin_module_names,
            syntax=sintassi,
            capabilities=self.info.capabilities,
        )
        with mock.patch.object(R, "runtime_info", finto):
            self.assertTrue(R.supports(probe.since))
            self.assertEqual(R.runtime_info.missing_version_requirements("3.0"), (probe.id,))
            with self.assertRaises(RuntimeError) as ctx:
                R.require("3.0")
        self.assertIn(probe.id, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()