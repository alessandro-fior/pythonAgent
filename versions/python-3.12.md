# Python 3.12

Stato al momento della ricerca: **security**, rilasciata il 2023-10-02, fine supporto 2028-10-01

Prima release senza distutils nella standard library.

Calendario di rilascio: PEP 693

## Nuova sintassi
### Sintassi dei type parameter (PEP 695) (PEP 695)

I parametri di tipo si dichiarano con `def f[T]` e `class C[T]`.

**Perche'**: Il `TypeVar` globale creava conflitti di nome fra moduli e rendeva la dichiarazione lontana dalla funzione che la usa.

```python
def primo[T](items: list[T]) -> T:
    return items[0]

class Scatola[T]:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.12.html


## Miglioramento del linguaggio
### f-string multilinea e riutilizzo delle quote (PEP 701)

Le f-string possono contenere a capo, commenti e gli stessi delimitatori.

**Perche'**: Prima la grammatica vieta-va le stesse virgolette all'interno della f-string e le sequenze di escape andavano raddoppiate.

```python
sql = f"""SELECT *
FROM utenti
WHERE attivo = {1}
"""
```

Fonte: https://docs.python.org/3/whatsnew/3.12.html

### GIL per interprete (PEP 684)

Ogni interprete secondario puo' avere il proprio GIL.

**Perche'**: Apre la strada agli interpreti indipendenti nella standard library.

```python
import _testcapi

id = _testcapi.make_gil_switching_interpreter()
```

Fonte: https://docs.python.org/3/whatsnew/3.12.html


## Nuove API
### `sys.monitoring` (PEP 669)

API di monitoraggio a basso impatto per strumenti come profiler e debugger.

**Perche'**: `sys.settrace` e' invasivo e lento; questa API usa un meccanismo distinto.

```python
import sys

def profilo(code, offset):
    ...

sys.monitoring.register_callback(sys.monitoring.PROFILE, profilo)
sys.monitoring.set_events(sys.monitoring.PROFILE)
```

Fonte: https://docs.python.org/3/whatsnew/3.12.html

### Decoratore `typing.override` (PEP 698)

Segnala che un metodo sovrascrive un metodo della classe base.

**Perche'**: Un errore di battitura nel nome del metodo non veniva segnalato da nessun strumento.

```python
from typing import override

class Base:
    def salva(self) -> None: ...

class Derivata(Base):
    @override
    def salva(self) -> None: ...
```

Fonte: https://docs.python.org/3/whatsnew/3.12.html


## Miglioramenti delle performance
### Inlining delle comprensioni (PEP 709)

Le comprensioni sono state trasformate in codice inline, senza chiamata di funzione.

**Perche'**: Le comprensioni hanno un proprio scope: l'inlining elimina il costo della funzione.

Fonte: https://docs.python.org/3/whatsnew/3.12.html


## Rimozioni
### `distutils` rimosso dalla standard library (PEP 632)

Il modulo di packaging storico e' stato rimosso dopo la deprecazione annunciata in Python 3.10.

**Perche'**: Duplicava `setuptools` e dipendeva da `imp`, rimosso nella stessa release.

```python
from setuptools import setup

setup(name='mio', version='1.0')
```

Fonte: https://docs.python.org/3/whatsnew/3.12.html


Fonte del rilascio: https://devguide.python.org/versions/
