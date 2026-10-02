# Python 3.6

Stato al momento della ricerca: **end-of-life**, rilasciata il 2016-12-23

Introdotte le f-string.

Calendario di rilascio: PEP 494

## Nuova sintassi
### Comprensioni asincrone (PEP 530)

`async for` e `await` sono ammessi dentro le comprensioni.

**Perche'**: In 3.5 le comprensioni non potevano contenere `await` o `async for`.

```python
async def raccogli(stream):
    return [x async for x in stream]
```

Fonte: https://docs.python.org/3/whatsnew/3.6.html

### Generatori asincroni (PEP 525)

`yield` dentro `async def` produce un generatore asincrono.

**Perche'**: In 3.5 non si poteva produrre uno stream asincrono con un generatore.

```python
async def stream():
    yield 1
```

Fonte: https://docs.python.org/3/whatsnew/3.6.html

### f-string (PEP 498)

Stringhe formattate letterali, valutate a runtime come una normale espressione.

**Perche'**: `%` e `.format()` hanno sintassi diverse fra loro e non sono sicuri: un campo sbagliato fallisce tardi e lontano dal punto di errore.

```python
nome = "Ada"
eta = 36
messaggio = f"{nome} ha {eta} anni"
```

Fonte: https://docs.python.org/3/whatsnew/3.6.html

### Separatori `_` nei letterali numerici (PEP 515)

Il carattere `_` puo' separare le cifre di letterali interi, float e esadecimali.

**Perche'**: Legibilita' dei numeri grandi senza perdere la precisione.

```python
budget = 1_000_000
maschera = 0xFF_FF_FF
piccolo = 1_0.5
```

Fonte: https://docs.python.org/3/whatsnew/3.6.html

### Annotazioni di variabile (PEP 526)

Annotazioni su variabili locali, di istanza e di classe.

**Perche'**: I tipi delle strutture dati non erano esprimibili senza una dichiarazione a runtime.

```python
class Utente:
    nome: str

    def __init__(self, nome: str) -> None:
        self.nome = nome
```

Fonte: https://docs.python.org/3/whatsnew/3.6.html


## Nuove API
### Protocollo `os.PathLike` (PEP 519)

Gli oggetti percorso sono accettati da `open()` e dalle funzioni di `os`.

**Perche'**: Le API di sistema accettavano solo `str`, quindi `pathlib` era scomodo da usare.

```python
from pathlib import Path

with open(Path('dati') / 'x.txt') as f:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.6.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.6.html
