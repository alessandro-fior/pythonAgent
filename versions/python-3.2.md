# Python 3.2

Stato al momento della ricerca: **end-of-life**, rilasciata il 2011-02-20

Ultima release a supportare Python 2.5 e precedenti.

## Miglioramento del linguaggio
### Cache dei bytecode in `__pycache__` (PEP 3147)

I file `.pyc` non stanno piu' accanto ai sorgenti.

**Perche'**: I `.pyc` accanto ai sorgenti rendevano impossibile il backup incrementale.

```python
import mio_modulo  # crea __pycache__/mio_modulo.cpython-312.pyc
```

Fonte: https://docs.python.org/3/whatsnew/3.2.html


## Nuove API
### `concurrent.futures` (PEP 3148)

Esecuzione parallela con pool di thread e di processi, pensata per codice di lunga durata.

**Perche'**: Prima si usavano `threading` e `multiprocessing` con API diverse e parallele.

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor() as pool:
    risultati = list(pool.map(analizza, record))
```

Fonte: https://docs.python.org/3/whatsnew/3.2.html

### `functools.lru_cache`

Memoizzazione con limite di dimensione.

**Perche'**: Rende il pattern cache-delle-funzionalita' di alto livello, senza scrivere una classe.

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def lento(x: int) -> int:
    return x * x
```

Fonte: https://docs.python.org/3/whatsnew/3.2.html


## Miglioramenti delle performance
### Il GIL e' stato riscritto

Semaforo e condizioni aggiornate, con intervallo di commutazione esplicito e configurabile.

**Perche'**: Meno contention sul lock e un comportamento di commutazione prevedibile.

```python
import sys

sys.setswitchinterval(0.005)
```

Fonte: https://docs.python.org/3/whatsnew/3.2.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.2.html
