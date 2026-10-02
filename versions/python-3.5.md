# Python 3.5

Stato al momento della ricerca: **end-of-life**, rilasciata il 2015-09-13

Introdotte le coroutine con async/await e il modulo typing.

Calendario di rilascio: PEP 478

## Nuova sintassi
### Coroutine con `async` e `await` (PEP 492)

Parole chiave per scrivere codice asincrono, con ciclo di vita esplicito.

**Perche'**: I generatori decorati erano indistinguibili da quelli normali: gli errori di runtime erano frequenti e il debugging impossibile.

```python
async def attendi() -> None:
    await asyncio.sleep(1)
```

Fonte: https://docs.python.org/3/whatsnew/3.5.html

### Generalizzazione dell'unpacking con `*` e `**` (PEP 448)

Piu' di un `*` nelle chiamate, piu' di un `**`, e piu' elementi spreads nei display di lista, set e dizionario.

**Perche'**: Compositione di liste e chiamate senza costruire liste intermedie.

```python
def f(a, b, c):
    ...

lista = [1, 2, *[3, 4]]
args = [1, 2]
f(*args, 3)
```

Fonte: https://docs.python.org/3/whatsnew/3.5.html


## Nuove API
### Modulo `typing` (PEP 484)

Annotazioni di tipo con strutture parametriche: `List`, `Dict`, `Optional`, `Union`.

**Perche'**: Nessun controllo a runtime, ma uno strumento statico comune (mypy, pyright, IDE).

```python
from typing import Optional

def somma(a: int, b: int) -> int:
    return a + b
```

Fonte: https://docs.python.org/3/whatsnew/3.5.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.5.html
