# Python 3.7

Stato al momento della ricerca: **end-of-life**, rilasciata il 2018-06-27

Introdotte le dataclass; async/await diventano parole chiave.

## Nuova sintassi
### `from __future__ import annotations` (PEP 563)

Le annotazioni diventano stringhe, quindi i riferimenti in avanti non richiedono le virgolette.

**Perche'**: I riferimenti in avanti costringevano a scrivere stringhe ovunque.

```python
from __future__ import annotations

def crea(nome: Utente | None = None) -> Utente | None:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.7.html


## Miglioramento del linguaggio
### L'ordine dei dizionari diventa parte del linguaggio

L'ordine di inserimento e' garantito dalla specifica, non piu' solo dall'implementazione.

**Perche'**: Dipendere da un dettaglio dell'implementazione non e' un contratto sostenibile.

```python
# 3.7+: ordine di inserimento garantito
for k in d:
    print(k)  # ordine di inserimento
```

Fonte: https://docs.python.org/3/whatsnew/3.7.html


## Nuove API
### Modulo `dataclasses` (PEP 557)

Il decoratore `@dataclass` genera `__init__`, `__repr__`, `__eq__` e `__hash__` a partire dalle annotazioni.

**Perche'**: Il codice di boilerplate per i semplici contenitori di dati era ripetuto ovunque.

```python
from dataclasses import dataclass

@dataclass
class Persona:
    nome: str
    eta: int
```

Fonte: https://docs.python.org/3/whatsnew/3.7.html


## Rimozioni
### `async` e `await` sono parole chiave riservate

Non sono piu' usabili come nomi di variabili o funzioni.

**Perche'**: Le parole chiave esplicite rendono il codice asincrono riconoscibile a colpo d'occhio.

```python
def attendi(x):
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.7.html


Fonte del rilascio: https://docs.python.org/3/whatsnew/3.7.html
