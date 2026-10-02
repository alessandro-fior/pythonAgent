# Python 3.14

Stato al momento della ricerca: **bugfix**, rilasciata il 2025-10-07, fine supporto 2030-10-01

Prima release con annotazioni a valutazione differita (PEP 649).

Calendario di rilascio: PEP 745

## Nuova sintassi
### `except E1, E2:` senza parentesi (PEP 758)

La clausola `except` (e `except*`) puo' elencare piu' eccezioni senza le parentesi.

**Perche'**: Le parentesi erano necessarie solo per un motivo grammaticale ormai risolto.

```python
try:
    carica()
except FileNotFoundError, PermissionError:
    log.error('risorsa non disponibile')
```

Fonte: https://docs.python.org/3/whatsnew/3.14.html

### t-string (stringhe template) (PEP 750)

Come le f-string, ma il risultato e' un `Template` con i valori esposti come metadati, non ancora serializzati.

**Perche'**: Le f-string rendono impossibile distinguere il codice dal dato: una SQL costruita con f-string e' un rischio di iniezione.

```python
from string.templatelib import Template

sql = t"SELECT * FROM utenti WHERE nome = {nome!r}"
# Template con .strings e .interpolations: si puo' ispezionare e validare
```

Fonte: https://docs.python.org/3/whatsnew/3.14.html


## Miglioramento del linguaggio
### Valutazione differita delle annotazioni (PEP 649) (PEP 649)

Le annotazioni vengono valutate solo quando servono, tramite descrittori; `annotationlib` permette di forzarne la valutazione.

**Perche'**: In 3.10-3.13 le annotazioni erano valutate alla definizione, il che costringeva a usare stringhe per i riferimenti in avanti.

```python
def somma(a: int, b: int) -> int:
    return a + b

# forward reference senza stringhe
e = somma(1, 2)
assert 'somma' in annotationlib.get_annotations(somma)
```

Fonte: https://docs.python.org/3/whatsnew/3.14.html

### `return`/`break`/`continue` vietati nel `finally` (PEP 765)

Uscire da un blocco `finally` con un salto di controllo produce una `SyntaxWarning`: il codice viene eseguito ma il flusso era ambiguo.

**Perche'**: Il salto nel `finally` scartava silenziosamente eccezioni in volo.

```python
def chiudi(risorsa):
    try:
        usa(risorsa)
    finally:
        risorsa.chiedi_chiusura()
        # niente return: il finally deve chiudere, non restituire
```

Fonte: https://docs.python.org/3/whatsnew/3.14.html

### Interfaccia di debug remoto sicura (PEP 768)

`sys.remote_exec()` permette a un debugger esterno di eseguire codice, con protezioni e disattivazione esplicita.

**Perche'**: Il debug da remoto era legato a meccanismi non sicuri.

Fonte: https://docs.python.org/3/whatsnew/3.14.html


## Nuove API
### `concurrent.interpreters` (PEP 734)

Interpreti Python indipendenti nella standard library, ognuno con il proprio GIL.

**Perche'**: Il lavoro parallelo su piu' core senza thread era possibile solo con processi, con il costo della serializzazione.

```python
from concurrent.futures import InterpreterPoolExecutor

with InterpreterPoolExecutor() as pool:
    risultati = list(pool.submit(analizza, riga).result() for riga in righe)
```

Fonte: https://docs.python.org/3/whatsnew/3.14.html

### Modulo `compression.zstd` (PEP 784)

Supporto Zstandard nella standard library.

**Perche'**: `bz2`, `lzma` e `gzip` non coprono il formato comunemente usato come Zstandard.

```python
from compression import zstd

dati = zstd.compress(grezzo)
```

Fonte: https://docs.python.org/3/whatsnew/3.14.html


Fonte del rilascio: https://devguide.python.org/versions/
