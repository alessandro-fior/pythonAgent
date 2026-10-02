# Python 3.1

Stato al momento della ricerca: **end-of-life**, rilasciata il 2009-06-27

Ultima 3.x con supporto per Python 2.6/2.7 tramite 2to3 come default.

## Miglioramento del linguaggio
### `repr()` dei float usa la forma piu' corta che fa riscontro esatto

`repr(1.1)` restituisce `'1.1'` invece di 17 cifre.

**Perche'**: Mantiene il valore leggibile senza perdere la precisione della conversione.

```python
# Python 3.1+
repr(1.1)   # '1.1'
```

Fonte: https://docs.python.org/3/whatsnew/3.1.html


## Nuove API
### `collections.OrderedDict` (PEP 372)

Dizionario che conserva l'ordine di inserimento.

**Perche'**: Prima l'ordine di un dizionario era un dettaglio dell'implementazione, non un contratto.

```python
from collections import OrderedDict

d = OrderedDict([('b', 1), ('a', 2)])
```

Fonte: https://docs.python.org/3/whatsnew/3.1.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.1.html
