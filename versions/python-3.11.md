# Python 3.11

Stato al momento della ricerca: **security**, rilasciata il 2022-10-24, fine supporto 2027-10-01

Ultima release a supportare Windows 8.1 e macOS 10.13.

Calendario di rilascio: PEP 664

## Nuova sintassi
### `ExceptionGroup` e `except*` (PEP 654)

Permette di propagare piu' eccezioni indipendenti insieme.

**Perche'**: Accumulare gli errori in una lista dentro l'eccezione perdi informazione: non si distingue piu' quale operazione e' fallita.

```python
def carica_tutto(risorse):
    risultati = []
    for risorsa in risorse:
        risultati.append(elabora(risorsa))  # solleva da sola

async def carica_insieme(rs):
    try:
        async with asyncio.TaskGroup() as gruppo:
            for r in rs:
                gruppo.create_task(elabora(r))
    except* ErroreDominio as gruppo_errori:
        log.error('falliti: %s', gruppo_errori.exceptions)
```

Fonte: https://docs.python.org/3/whatsnew/3.11.html


## Miglioramento del linguaggio
### Posizioni di errore fini nel traceback (PEP 657)

Il traceback indica colonna e fine riga oltre che il numero di riga.

**Perche'**: Su una riga sola l'indicazione della riga non basta a individuare l'errore.

```python
def calcola(totale, divisore):
    # il traceback del 3.11 indica anche colonna e fine riga
    return totale / divisore
```

Fonte: https://docs.python.org/3/whatsnew/3.11.html


## Nuove API
### `BaseException.add_note()` (PEP 678)

Aggiunge righe di contesto mostrate nel traceback.

**Perche'**: Arricchire il traceback senza perdere il tipo dell'eccezione originale.

```python
def recupera(utente: str) -> None:
    try:
        carica(utente)
    except KeyError as exc:
        exc.add_note(f'utente richiesto: {utente!r}')
        raise
```

Fonte: https://docs.python.org/3/whatsnew/3.11.html

### `typing.Self` (PEP 673)

Annota un metodo che restituisce il tipo dell'istanza, non della classe.

**Perche'**: Prima si usava un TypeVar, verboso e non sempre corretto con l'ereditarieta'.

```python
from typing import Self

class Fabbrica:
    def nuovo(self) -> Self:
        return type(self)()
```

Fonte: https://docs.python.org/3/whatsnew/3.11.html

### Modulo `tomllib` (PEP 680)

Lettore TOML nella standard library, in sola lettura.

**Perche'**: TOML e' il formato di `pyproject.toml`: leggero in stdlib evita una dipendenza.

```python
import tomllib

with open('pyproject.toml', 'rb') as f:
    config = tomllib.load(f)
```

Fonte: https://docs.python.org/3/whatsnew/3.11.html


## Miglioramenti delle performance
### Interprete adattivo con specializzazione (PEP 659)

CPython 3.11 specializza i bytecode sulla situazione osservata a runtime.

**Perche'**: Permette di ottimizzare i percorsi caldi senza costi per i percorsi freddi.

Fonte: https://docs.python.org/3/whatsnew/3.11.html


## Deprecazioni introdotte

- Rimossi `2to3` e `lib2to3` (rimossa in 3.13) - https://docs.python.org/3/whatsnew/3.13.html

Fonte del rilascio: https://devguide.python.org/versions/
