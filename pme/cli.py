"""Interfaccia a riga di comando del progetto.

La CLI non contiene logica propria: ogni sotto-comando chiama le funzioni di
:mod:`pme.features`, :mod:`pme.probes`, :mod:`pme.runtime`, :mod:`pme.legacy` e
:mod:`pme.report`. Serve a due scopi:

* controllare il catalogo dalla shell, per esempio ``pme features --version 3.12``;
* generare i file di ``versions/`` a partire dagli stessi dati che la
  documentazione consulta, cosi' il repository non può divergere dal codice.

Esempi::

    $ python -m pme versions
    $ python -m pme features --kind "Nuova sintassi"
    $ python -m pme check esempi/legacy.py
    $ python -m pme generate --versions-dir versions
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import List, Optional, Sequence, TextIO

from pme import demos, report
from pme.features import Category, Kind, by_id, iter_features
from pme.legacy import detect, minimum_version, modernize
from pme.probes import probe_syntax
from pme.runtime import runtime_info
from pme.version import Version, iter_releases

__all__ = ["build_parser", "main"]

#: Codice di uscita quando l'analisi trova qualcosa da correggere.
EXIT_FINDINGS = 1


def build_parser() -> argparse.ArgumentParser:
    """Costruisce il parser degli argomenti.

    Returns:
        Parser pronto per :func:`main`.
    """
    parser = argparse.ArgumentParser(
        prog="pme",
        description="Documentazione eseguibile dell'evoluzione di Python.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + _package_version(),
    )
    sottocomandi = parser.add_subparsers(dest="comando", required=True)

    sotto = sottocomandi.add_parser("versions", help="calendario dei rilasci")
    sotto.add_argument("--markdown", action="store_true", help="esce in tabella Markdown")

    sotto = sottocomandi.add_parser("features", help="catalogo delle funzionalita'")
    sotto.add_argument("--id", dest="feature_id", help="mostra una sola scheda")
    sotto.add_argument("--version", dest="versione", help="filtra per versione (3.12)")
    sotto.add_argument("--category", choices=[str(c) for c in Category])
    sotto.add_argument("--kind", choices=[str(k) for k in Kind])
    sotto.add_argument("--status", choices=["stable", "planned", "deprecated", "removed"],
                       help="filtra per stato della scheda")
    sotto.add_argument("--removed-in", dest="removed_in",
                       help="filtra per versione di rimozione (3.16)")
    sotto.add_argument("--markdown", action="store_true", help="esce in Markdown")

    sotto = sottocomandi.add_parser("runtime", help="interprete in esecuzione")
    sotto.add_argument("--probes", action="store_true", help="elenca le sonde sintattiche")

    sotto = sottocomandi.add_parser("check", help="analizza codice Python 2")
    sotto.add_argument("file", type=Path, help="file da analizzare")

    sotto = sottocomandi.add_parser("modernize", help="riscrive un file Python 2")
    sotto.add_argument("file", type=Path, help="file da riscrivere")
    sotto.add_argument("--diff", action="store_true", help="mostra solo le differenze")

    sotto = sottocomandi.add_parser("demo", help="esegue le dimostrazioni")
    sotto.add_argument(
        "--list",
        dest="demo_list",
        action="store_true",
        help="elenca le dimostrazioni senza eseguirle",
    )
    sotto.add_argument("--id", dest="demo_id", help="esegue una sola dimostrazione")

    sotto = sottocomandi.add_parser("generate", help="genera le version card")
    sotto.add_argument(
        "--versions-dir",
        type=Path,
        default=Path("versions"),
        help="cartella delle version card (default: versions)",
    )
    return parser


def _package_version() -> str:
    """Legge la versione del pacchetto senza importarlo ricorsivamente."""
    from pme import __version__

    return __version__


def _comando_versions(args: argparse.Namespace, out: TextIO) -> int:
    """Stampa il calendario dei rilasci."""
    if args.markdown:
        out.write(report.render_timeline())
        return 0
    for release in iter_releases():
        fine = release.eol.isoformat() if release.eol else "-"
        out.write(
            f"{str(release.version):<8} {release.released.isoformat()}  "
            f"{str(release.lifecycle):<12} eol={fine}\n"
        )
    return 0


def _comando_features(args: argparse.Namespace, out: TextIO) -> int:
    """Stampa il catalogo, filtrato come richiesto."""
    if args.feature_id:
        out.write(report.render_feature(by_id(args.feature_id)))
        return 0
    schede = list(iter_features())
    if args.versione:
        versione = Version.parse(args.versione)
        schede = [f for f in schede if f.introduced == versione]
    if args.category:
        schede = [f for f in schede if str(f.category) == args.category]
    if args.kind:
        schede = [f for f in schede if str(f.kind) == args.kind]
    if args.status:
        schede = [f for f in schede if f.status == args.status]
    if args.removed_in:
        versione = Version.parse(args.removed_in)
        schede = [f for f in schede if f.removed == versione]
    if args.markdown:
        out.write(report.render_feature_index(schede))
        return 0
    for feature in schede:
        stato = ""
        if feature.removed is not None:
            stato = f" [rimossa in {feature.removed}]"
        elif feature.deprecated is not None:
            stato = f" [deprecata in {feature.deprecated}]"
        out.write(f"{str(feature.introduced):<8} {feature.id:<28} {feature.title}{stato}\n")
    return 0


def _comando_runtime(args: argparse.Namespace, out: TextIO) -> int:
    """Stampa le informazioni sull'interprete in esecuzione."""
    for chiave, valore in runtime_info.as_table().items():
        out.write(f"{chiave}: {valore}\n")
    if not args.probes:
        return 0
    for probe in probe_syntax():
        stato = "ok" if probe.available() else "non supportata"
        out.write(f"  {str(probe.since):<8} {probe.id:<28} {stato}\n")
    return 0


def _comando_check(args: argparse.Namespace, out: TextIO) -> int:
    """Analizza un file e ne elenca i problemi."""
    sorgente = args.file.read_text(encoding="utf-8", errors="replace")
    ritrovamenti = detect(sorgente)
    for ritrovamento in ritrovamenti:
        out.write(
            f"{args.file}:{ritrovamento.line}:{ritrovamento.column}: "
            f"{ritrovamento.severity.value}: {ritrovamento.message} "
            f"[{ritrovamento.rule}]\n"
        )
    if not ritrovamenti:
        out.write(f"{args.file}: nessun problema rilevato\n")
        return 0
    out.write(f"\n{len(ritrovamenti)} ritrovamenti\n")
    return EXIT_FINDINGS


def _comando_modernize(args: argparse.Namespace, out: TextIO) -> int:
    """Mostra il risultato della riscrittura, o le sue differenze."""
    sorgente = args.file.read_text(encoding="utf-8", errors="replace")
    esito = modernize(sorgente)
    if args.diff:
        righe = difflib.unified_diff(
            sorgente.splitlines(keepends=True),
            esito.source.splitlines(keepends=True),
            fromfile=f"{args.file} (originale)",
            tofile=f"{args.file} (modernizzato)",
        )
        out.writelines(righe)
    else:
        out.write(esito.source)
    richiesta = minimum_version(sorgente)
    if richiesta is not None:
        out.write(f"\n# versione minima richiesta: {richiesta}\n")
    return 0


def _comando_demo(args: argparse.Namespace, out: TextIO) -> int:
    """Esegue una dimostrazione o le elenca."""
    if args.demo_id:
        try:
            demo = demos.get_demo(args.demo_id)
        except KeyError as err:
            out.write(f"{err}\n")
            return EXIT_FINDINGS
        try:
            esito = demo.result()
        except RuntimeError as err:
            out.write(f"{err}\n")
            return EXIT_FINDINGS
        out.write(f"{demo.title} (Python {demo.since})\n")
        out.write(f"{demo.description}\n")
        out.write(f"risultato: {esito!r}\n")
        return 0
    for demo in demos.DEMOS:
        stato = "eseguibile" if demo.available() else "non eseguibile qui"
        out.write(f"{str(demo.since):<8} {demo.id:<20} {stato}\n")
    return 0


def _comando_generate(args: argparse.Namespace, out: TextIO) -> int:
    """Scrive le version card su disco."""
    scritti = report.write_version_cards(args.versions_dir)
    report.write_future_card(args.versions_dir)
    if not scritti:
        out.write(f"{args.versions_dir}: gia' aggiornato\n")
        return 0
    for percorso in scritti:
        out.write(f"scritto {percorso}\n")
    return 0


_COMANDI = {
    "versions": _comando_versions,
    "features": _comando_features,
    "runtime": _comando_runtime,
    "check": _comando_check,
    "modernize": _comando_modernize,
    "demo": _comando_demo,
    "generate": _comando_generate,
}


def main(argv: Optional[Sequence[str]] = None, out: Optional[TextIO] = None) -> int:
    """Punto d'ingresso della CLI.

    Args:
        argv: argomenti da riga di comando; se omessi usa ``sys.argv[1:]``.
        out: flusso di uscita; se omesso usa ``sys.stdout``.

    Returns:
        Il codice di uscita: ``0`` se tutto bene, ``1`` se ci sono ritrovamenti.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    flusso: TextIO = out if out is not None else sys.stdout
    comando = _COMANDI[args.comando]
    try:
        return comando(args, flusso)
    except KeyError as err:
        # gli identificativi arrivano dalla tastiera: un errore leggibile vale
        # piu' di una traceback
        flusso.write(f"errore: {err.args[0] if err.args else err}\n")
        return EXIT_FINDINGS
    except OSError as err:
        flusso.write(f"errore: {err.strerror or err} ({getattr(err, 'filename', '')})\n")
        return EXIT_FINDINGS
