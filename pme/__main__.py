"""Permette di eseguire il pacchetto con ``python -m pme``.

L'eseguibile e' sottinteso: il progetto e' una raccolta di dati verificabili, e
i suoi programmi devono poter girare senza installazione, dalla cartella del
repository.
"""

from __future__ import annotations

import sys

from pme.cli import main

if __name__ == "__main__":
    sys.exit(main())
