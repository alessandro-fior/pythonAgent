# Python 3.3

Stato al momento della ricerca: **end-of-life**, rilasciata il 2012-09-29

Ultima release a supportare Windows XP e Mac OS X 10.5.

## Nuova sintassi
### `yield from` per la delegazione fra generatori (PEP 380)

Un generatore puo' delegare a un altro e riceverne il valore di ritorno.

**Perche'**: Semplifica la composizione di generatori e rende possibile il ritorno di un valore.

```python
def wrapper(seq):
    return (yield from seq)
```

Fonte: https://docs.python.org/3/whatsnew/3.3.html


## Miglioramento del linguaggio
### Pacchetti namespace senza `__init__.py` (PEP 420)

Una directory puo' diventare un pacchetto senza `__init__.py`.

**Perche'**: Permette di dividere un pacchetto fra piu' distribuzioni.

Fonte: https://docs.python.org/3/whatsnew/3.3.html

### Gerarchia delle eccezioni di sistema ridefinita (PEP 3151)

`IOError` e `EnvironmentError` sono alias di `OSError`; le nuove sottoclassi distinguono i casi.

**Perche'**: `except IOError:` era troppo generico per gestire gli errori reali.

```python
# Python 3.3+
try:
    apri()
except FileNotFoundError:
    ...
except PermissionError:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.3.html


## Nuove API
### `time.monotonic()` e orologi robusti (PEP 418)

Sostituisce `time.clock()` con un orologio immune ai cambi di ora di sistema.

**Perche'**: `time.clock()` misurava il tempo di CPU su Unix e il tempo di parete su Windows.

```python
inizio = time.monotonic()
elapsed = time.monotonic() - inizio
```

Fonte: https://docs.python.org/3/whatsnew/3.3.html

### Modulo `unittest.mock`

Basi in stdlib per il mocking, senza dipendenze esterne.

**Perche'**: Il mocking era disponibile solo tramite librerie di terze parti.

```python
from unittest.mock import patch

with patch('modulo.servizio') as servizio:
    servizio.restituisce.return_value = 42
```

Fonte: https://docs.python.org/3/whatsnew/3.3.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.3.html
