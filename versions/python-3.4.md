# Python 3.4

Stato al momento della ricerca: **end-of-life**, rilasciata il 2014-03-16

Prima release con asyncio ed ensurepip.

## Nuove API
### Modulo `asyncio` (PEP 3156)

Prima API standard per l'I/O asincrono.

**Perche'**: Prima esistevano solo soluzioni di terze parti con API diverse.

```python
import asyncio

async def attendi() -> None:
    await asyncio.sleep(1)
```

Fonte: https://docs.python.org/3/whatsnew/3.4.html

### Modulo `enum` (PEP 435)

Tipi enumerati con metodo `name`/`value`.

**Perche'**: Le costanti a stringa spariscono in favore di un tipo controllabile.

```python
from enum import Enum

class Stato(Enum):
    ATTIVO = 'attivo'
    SPENTO = 'spento'
```

Fonte: https://docs.python.org/3/whatsnew/3.4.html

### `pathlib`: percorsi come oggetti (PEP 428)

Percorsi manipolabili con gli operatori e con i metodi.

**Perche'**: `os.path` e' una raccolta di funzioni che non compone, senza stato ne' oggetti.

```python
from pathlib import Path

percorso = Path("dati") / "file.txt"
if percorso.exists():
    dati = percorso.read_text(encoding="utf-8")
```

Fonte: https://docs.python.org/3/whatsnew/3.4.html

### `functools.singledispatch` (PEP 443)

Dispatch generico basato sul tipo del primo argomento.

**Perche'**: Alternativa leggibile all'overloading per tipo.

```python
from functools import singledispatch

@singledispatch
def mostra(oggetto: object) -> str:
    return str(oggetto)
```

Fonte: https://docs.python.org/3/whatsnew/3.4.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.4.html
