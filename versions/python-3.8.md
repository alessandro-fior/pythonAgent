# Python 3.8

Stato al momento della ricerca: **end-of-life**, rilasciata il 2019-10-14

Ultima release a supportare Windows 7.

## Nuova sintassi
### Specificatore `=` nelle f-string

`f'{x=}'` scrive il testo dell'espressione insieme al suo valore.

**Perche'**: Il formato piu' comune del debugging era ripetere il nome della variabile due volte, con il rischio di scrivere due nomi diversi.

```python
print(f'x={x}')
print(f'{risultato=}')  # risultato = 42
```

Fonte: https://docs.python.org/3/whatsnew/3.8.html

### Parametri positional-only con `/` (PEP 570)

I parametri prima di `/` non possono essere passati per nome.

**Perche'**: Permette di rinominare un parametro interno senza rompere i chiamanti, e di accettare che un parametro si chiami come un altro nella chiamata.

```python
def confronta(a, b, /, chiave=None):
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.8.html

### Operatore walrus (`:=`) (PEP 572)

Assegnazione dentro un'espressione.

**Perche'**: Evita la variabile temporanea quando il valore serve sia per il test sia per l'uso.

```python
def cerca(d: dict[str, int]) -> int | None:
    if (risultato := d.get('a')) is not None:
        return risultato
    return None
```

Fonte: https://docs.python.org/3/whatsnew/3.8.html


## Nuove API
### `functools.cached_property`

Proprieta' calcolata una volta sola e memorizzata nell'istanza.

**Perche'**: Prima serviva un decoratore di terze parti o il trucco con `self._cache`.

```python
from functools import cached_property

class Relazione:
    @cached_property
    def righe(self) -> list[str]:
        return self._carica_righe()
```

Fonte: https://docs.python.org/3/whatsnew/3.8.html

### `TypedDict`, `Literal`, `Final`, `Protocol` in `typing` (PEP 589)

Tipizzazione di dizionari, valori letterali, costanti e protocolli strutturali.

**Perche'**: Permette di descrivere tipi che non sono classi: dizionari e protocolli.

```python
from typing import Literal, Protocol, TypedDict

class Config(TypedDict):
    host: str

class SupportaLen(Protocol):
    def __len__(self) -> int: ...
```

Fonte: https://docs.python.org/3/whatsnew/3.8.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.8.html
