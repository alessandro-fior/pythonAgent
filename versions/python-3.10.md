# Python 3.10 (ultima versione: 3.10.22)

Stato al momento della ricerca: **end-of-life**, rilasciata il 2021-10-04, fine supporto 2026-10-01

Ultima release a supportare macOS 10.9/10.10/10.11.

Calendario di rilascio: PEP 619

## Nuova sintassi
### Context manager tra parentesi

Gli elementi di un `with` possono essere racchiusi fra parentesi e suddivisi su piu' righe.

**Perche'**: La continuazione con barra rovesciata era scomoda e fragile; il parser PEG rende possibile la grammatica con parentesi.

```python
with (
    open('a.txt') as a,
    open('b.txt') as b,
):
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.10.html

### Structural pattern matching (`match` / `case`) (PEP 634)

`match` e `case` sono parole chiave morbide: funzionano come identificatori se non sono usati in posizione di pattern.

**Perche'**: I confronti annidati su tipo e forma richiedevano catene di `if` e controlli ripetuti sullo stesso valore.

```python
def esegui(comando):
    match comando:
        case 'start':
            return start()
        case 'stop':
            return stop()
        case [primo, *resto]:
            return [primo, *[esegui(c) for c in resto]]
        case str() as testo:
            raise ValueError(testo)
        case _:
            raise ValueError(f'comando non gestito: {comando!r}')
```

Fonte: https://docs.python.org/3/whatsnew/3.10.html

### Unioni di tipo con `X | Y` (PEP 604)

Le unioni si scrivono con l'operatore `|`, anche a runtime.

**Perche'**: `Optional[X]` era zucchero per `Union[X, None]`: due modi per lo stesso tipo.

```python
def cerca(id: int | str | None = None) -> int | None:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.10.html


## Nuove API
### `dataclasses`: `slots=True` e `kw_only=True`

Le dataclassi possono occupare gli slot e imporre argomenti per nome.

**Perche'**: Gli slot riducono il consumo di memoria e l'attrito sugli attributi.

```python
from dataclasses import dataclass

@dataclass(slots=True)
class Punto:
    x: float
    y: float
```

Fonte: https://docs.python.org/3/whatsnew/3.10.html

### `zip(strict=True)` (PEP 618)

Lo zip segnala un errore se le sequenze hanno lunghezza diversa.

**Perche'**: Lo zip silenziosamente troncava, nascondendo un bug di allineamento dei dati.

```python
for a, b in zip(seq_a, seq_b, strict=True):
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.10.html


Fonte del rilascio: https://devguide.python.org/versions/
