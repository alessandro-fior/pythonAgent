# Python 3.13

Stato al momento della ricerca: **security**, rilasciata il 2024-10-07, fine supporto 2029-10-01

Prima release con build free-threaded (sperimentale).

Calendario di rilascio: PEP 719

## Miglioramento del linguaggio
### JIT sperimentale (PEP 744)

Un compilatore just-in-time opzionale, attivato in compilazione.

**Perche'**: Dopo anni di ottimizzazioni statiche, la compilazione a runtime diventa praticabile.

```python
import sys

if hasattr(sys, '_jit'):
    attivo = sys._jit.is_available()
```

Fonte: https://docs.python.org/3/whatsnew/3.13.html

### Build free-threaded sperimentale (PEP 703)

CPython puo' essere compilato senza GIL.

**Perche'**: Il GIL e' il limite principale all'uso di piu' core per codice puro Python.

```python
import sys

if not sys._is_gil_enabled():
    print('esecuzione senza GIL')
```

Fonte: https://docs.python.org/3/whatsnew/3.13.html


## Nuove API
### `copy.replace()` e il protocollo `__replace__`

Copia modificando campi, con supporto per dataclassi, namedtuple e oggetti immutabili.

**Perche'**: Prima si usava `dataclasses.replace` o si ricostruiva l'oggetto a mano.

```python
import copy

from dataclasses import dataclass

@dataclass(frozen=True)
class Utente:
    nome: str
    admin: bool

u2 = copy.replace(u1, admin=True)
```

Fonte: https://docs.python.org/3/whatsnew/3.13.html

### `warnings.deprecated` (PEP 702)

Decoratore che segnala l'uso di un'API deprecata e informa i type checker.

**Perche'**: Unificare il deprecamento fra runtime e analisi statica.

```python
from warnings import deprecated

@deprecated('usare parse_v2()')
def parse_v1(testo: str) -> dict:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.13.html


## Deprecazioni
### L'argomento `fields` di `TypedDict`

Non passare `None` (o omettere i campi) alla forma funzionale di `TypedDict`: dal 3.13 e' deprecato e dal 3.16 solleva `ValueError`.

**Perche'**: `TypedDict('Film')` non poteva essere costruito in modo coerente: la forma funzionale accettava un nome senza campi, mentre l'API di subscript richiede una lista di campi. La deprecazione chiude il caso ambiguo a favore della sintassi con classe o con dizionario esplicito.

```python
from typing import TypedDict

Film = TypedDict('Film', {})  # nessun campo

class Regista(TypedDict):
    nome: str
```

Fonte: https://docs.python.org/3/deprecations/index.html


## Rimozioni
### Rimossi 19 moduli "dead batteries" (PEP 594)

Moduli rimossi dopo PEP 594: `cgi`, `telnetlib`, `nntplib`, `imghdr`, `audioop`, `crypt`, `mailcap`, `pipes`, `uu`, `xdrlib` e altri.

**Perche'**: Moduli senza manutentori, con problemi di sicurezza noti e sostituiti.

```python
import email

messaggio = email.message_from_binary_file(stream)
valori = dict(messaggio)
```

Fonte: https://docs.python.org/3/whatsnew/3.13.html

### Rimossi `2to3` e `lib2to3`

Lo strumento che automatizzava la conversione da Python 2 e' stato rimosso, insieme al modulo `lib2to3` su cui si basava.

**Perche'**: `2to3` riscriveva il codice senza capire il significato: produceva risultati che a volte compilavano e a volte no, e la correzione manuale restava necessaria. Mantenerlo in mantenimento era un costo che il progetto ha deciso di non pagare.

```python
# Python 3.13: il percorso di migrazione e' leggere il codice,
# capire cosa e' cambiato e riscrivere a mano
```

Fonte: https://docs.python.org/3/whatsnew/3.13.html


## Deprecazioni introdotte

- L'argomento `fields` di `TypedDict` (rimossa in 3.16) - https://docs.python.org/3/deprecations/index.html

## Rimozioni

- Rimossi `2to3` e `lib2to3` (rimossa in 3.13) - https://docs.python.org/3/whatsnew/3.13.html

Fonte del rilascio: https://devguide.python.org/versions/
