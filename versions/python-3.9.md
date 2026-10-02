# Python 3.9

Stato al momento della ricerca: **end-of-life**, rilasciata il 2020-10-05, fine supporto 2025-10-31

Ultima release a supportare CentOS 7 e macOS 10.9.

Calendario di rilascio: PEP 596

## Nuova sintassi
### Generics sulle raccolte standard (`list[str]`) (PEP 585)

Le raccolte standard accettano parametri di tipo direttamente.

**Perche'**: `typing.List` era una copia necessaria perche' `list` non era sottoscrivibile.

```python
def carica(ids: list[int]) -> dict[int, str]:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.9.html

### Unione di dizionari con `|` (PEP 584)

L'unione e l'aggiornamento tra dizionari diventano operatori.

**Perche'**: Tre righe di copia e mutazione diventano una, e la copia e' esplicita.

```python
default = base | extra
default |= {'debug': True}
```

Fonte: https://docs.python.org/3/whatsnew/3.9.html


## Miglioramento del linguaggio
### Nuovo parser PEG (PEP 617)

Il parser basato su PEG sostituisce quello LL(1).

**Perche'**: La grammatica era frammentata fra parser e compilatore; il PEG consente una singola fonte e una diagnostica migliore.

Fonte: https://docs.python.org/3/whatsnew/3.9.html


## Nuove API
### `str.removeprefix()` e `str.removesuffix()` (PEP 616)

Rimozione controllata di un prefisso o suffisso.

**Perche'**: Si evita il test `startswith()` seguito da `len()` e slicing.

```python
percorso = '/srv/app/utenti.txt'
relativo = percorso.removeprefix('/srv/')
```

Fonte: https://docs.python.org/3/whatsnew/3.9.html


Fonte del rilascio: https://devguide.python.org/versions/
