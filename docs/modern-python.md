# Scrivere Python moderno

Le novita' di Python non sono curiosita': quasi tutte risolvono un problema
che si incontra scrivendo codice di tutti i giorni. Questa pagina le raggruppa
per problema, non per versione.

## Il testo: f-string e t-string

```python
# prima: % e .format() hanno ordini di argomenti e quoting da ricordare
msg = "%s ha %d anni" % (nome, eta)
msg = "{0} ha {1} anni".format(nome, eta)

# da 3.6: l'espressione resta un'espressione
msg = f"{nome} ha {eta} anni"
```

Le f-string si formattano in tempo di compilazione, quindi sono piu' veloci dei
due metodi precedenti; il vantaggio principale e' la leggibilita'. Attenzione
perche' l'espressione viene valutata per intero: `f"{utente['nome']}"` non
funziona con le virgolette doppie identiche.

Dalla 3.14 esistono le t-string, che producono un oggetto template invece di
una stringa:

```python
risposta = t"ciao {utente}, benvenuto"
invio(risposta)     # il destinatario puo' applicare policy o traduzione
```

Non sostituiscono le f-string ovunque: sono per messaggi che passano da un
confine, dove la localizzazione non deve essere anticipata.

## I confronti: `match`

```python
# prima
if tipo == "click" and isinstance(azione, tuple):
    x, y = azione[1], azione[2]

# da 3.10
match tipo:
    case "click" if isinstance(azione, tuple):
        x, y = azione[1], azione[2]
    case _:
        ...
```

Il vantaggio non e' la brevita': e' che ogni caso e' dichiarato come una forma
possibile della struttura dati, e i binding sono visibili nel ramo. Le parentesi
attorno alla lista di casi sono opzionali dal 3.10, cosa resa possibile dal
parser PEG (PEP 617).

## La concorrenza: `asyncio`

| Prima | Da 3.5 |
| --- | --- |
| `@asyncio.coroutine` | `async def` |
| `yield from` | `await` |
| `loop.run_until_complete` | `asyncio.run` |
| `asyncio.ensure_future` | `asyncio.create_task` |

In Python 3 le coroutine sono distinte dai generatori: una funzione `async def`
non puo' essere usata come un generatore e viceversa. `await` esprime
esplicitamente la sospensione, il che rende leggibile dove l'esecuzione
cambia thread e dove no.

Dal 3.11 `asyncio.TaskGroup` gestisce un insieme di task e garantisce che, se uno
fallisce, gli altri vengano cancellati: e' il modo corretto di lanciare lavoro
concorrente con un solo errore.

## I tipi

```python
# da 3.9
def conta(v: list[str]) -> dict[str, int]: ...

# da 3.10: anche la barra verticale
def somma(a: int | float) -> int | float: ...

# da 3.12
type Risultato = list[tuple[str, int]]   # alias con type statement

# da 3.12
class Archivio[T]:
    def __init__(self, elementi: list[T]) -> None:
        self.elementi = elementi

# da 3.14
def carica(dati: list[str]) -> Path | None: ...
```

I type parameter (PEP 695) eliminano le classi `Generic` e i protocolli di
sola forma: la classe dichiara il parametro dove si usa. Le annotazioni sono ormai
valutate in modo differito (PEP 649, 3.14), quindi un'annotazione che richiede
un import non costa piu' all'avvio.

## Gli errori: `except*`

```python
# prima
try:
    elaborate(gruppo)
except ErroreA:
    ...
except ErroreB:
    ...

# da 3.11
try:
    elaborate(gruppo)
except* ErroreA:
    ...
except* ErroreB:
    ...
```

`except` termina il `try` al primo errore, quindi nel ramo `ErroreB` gli
elementi restanti non sono elaborati. `except*` divide il gruppo e lascia
intatti gli elementi non coperti dal ramo, che arrivano al ramo successivo o
risalgono a chi chiama.

## I dati: `copy.replace`, `itertools.batched`

```python
# da 3.13: copia immutabile con un campo cambiato
import copy
punto = copy.replace(punto, y=0)

# da 3.12: gruppi di n elementi
for batch in itertools.batched(dati, 100):
    salva(batch)
```

## Cosa usare, in sintesi

| Problema | Scrivere |
| --- | --- |
| testo con valori | f-string |
| testo localizzabile | t-string |
| strutture con forme note | `match` |
| lavoro concorrente | `asyncio.run`, `TaskGroup` |
| errori per gruppo | `except*` |
| firme pubbliche | annotazioni moderne |
| collezioni generiche | sintassi `class C[T]` |
| divisione intera esplicita | `//` |

Le versioni richieste da queste scelte si dichiarano in `pyproject.toml` con
`requires-python`, e nel caso di questo progetto il valore si puo' ricavare dai
dati invece di indovinarlo:

```python
>>> from pme.legacy import minimum_version
>>> minimum_version("def conta(dati: list[str] | None) -> None: ...")
'3.10'
```

## Cosa non fare

* non usare `2to3` su codice che si vuole capire: e' stato rimosso nel 3.13
  perche' riscriveva senza capire;
* non lasciare `/` dove serve un intero: non e' un errore, e' un risultato
  sbagliato;
* non usare `lambda` in tutti i posti in cui si usa `def`: solo dove serve, e
  con un nome quando il nome aiuta;
* non introdurre una sintassi nuova solo perche' e' nuova: il vantaggio e'
  leggibilita', e la leggibilita' si misura su chi legge.

## Il metodo che funziona

`python -m pme features --introduced-in 3.12` per sapere cosa e' entrato,
`python -m pme demo --id walrus` per vedere un esempio funzionante, e i test
per decidere se una riscrittura ha mantenuto il comportamento. La regola di
`agent.md` resta la piu' utile: per ogni caratteristica importante, mostrare
come era, cosa e' cambiato, perche', e cosa e' stato deprecato.
