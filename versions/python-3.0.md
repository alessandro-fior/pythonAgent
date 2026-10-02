# Python 3.0

Stato al momento della ricerca: **end-of-life**, rilasciata il 2008-12-03, fine supporto 2009-06-27

Prima release incompatibile con Python 2. python.org e la pagina 'What's New in Python 3.0' concordano sul 3 dicembre 2008.

Calendario di rilascio: PEP 3000

## Nuova sintassi
### Comprensioni per dizionari e set

Python 3 aggiunge le comprensioni di dizionari e di set.

**Perche'**: Uniforma la sintassi: le comprensioni di lista esistevano gia' in 2.0.

```python
# Python 3
quadrati = {x: x * x for x in range(10)}
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### Annotazioni di funzione (PEP 3107)

Annotazioni su parametri e valore di ritorno, introspecabili a runtime.

**Perche'**: Danno un punto di aggancio a strumenti di verifica e documentazione.

```python
def somma(a: int, b: int) -> int:
    return a + b
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### Argomenti keyword-only (PEP 3102)

I parametri che seguono un `*` possono essere passati solo per nome.

**Perche'**: Permette di aggiungere opzioni senza rompere le chiamate posizionali esistenti: e' il modo standard per proteggere l'API dalla crescita.

```python
def connetti(host, /, *, timeout=10, retries=3):
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `nonlocal` per le variabili di funzioni annidate (PEP 3104)

Assegnazione diretta a un nome appartenente a uno scope esterno ma non globale.

**Perche'**: Prima serviva passare la variabile in una lista mutabile per aggirare la regola.

```python
def esterna():
    x = 1
    def interna():
        nonlocal x
        x += 1
        return x
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `print()` come funzione (PEP 3105)

L'istruzione `print` e' diventata una funzione con parole chiave `sep`, `end`, `file`, `flush`.

**Perche'**: Rende `print` utilizzabile come valore e uniforma le chiamate.

```python
print("trovati", n, "record", sep=", ", end="\n", file=sys.stderr)
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html


## Miglioramento del linguaggio
### Concatenamento esplicito delle eccezioni (PEP 3134)

`raise ... from ...` collega esplicitamente un errore a quello che lo ha causato.

**Perche'**: In Python 2 la nuova eccezione nascondeva completamente la causa originale; il traceback mostrava solo il sintomo.

```python
try:
    valore = int(testo)
except ValueError as exc:
    raise ValueError('valore non valido') from exc
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### Sintassi nuova per le metaclassi (PEP 3115)

La metaclassi si indica nella intestazione della classe.

**Perche'**: La variabile `__metaclass__` nel corpo della classe era ignorata in molti casi.

```python
class Base(metaclass=Meta):
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### Testo e dati binari non si mescolano piu'

Python 3 distingue `str` (testo) da `bytes` (dati); concatenarli e' un `TypeError`, non una coercizione silenziosa.

**Perche'**: In Python 2 la somma tra `str` e `unicode` riusciva solo se i byte erano ASCII: il fallimento dipendeva dal contenuto del dato.

```python
risultato = "ciao " + "mondo"   # Python 3: str + str = testo + testo
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `/` e' divisione reale, `//` e' divisione intera

In Python 2 `/` fra due interi troncava verso zero. In Python 3 `/` restituisce sempre un `float`.

**Perche'**: La divisione che tronca e' stata spostata su un operatore esplicito (`//`), eliminando la classe di bug silenziosi piu' insidiosi del mondo Python 2.

```python
# Python 3
media = (3 + 4) / 2      # 3.5
quota = 7 // 2         # 3
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html


## Rimozioni
### Le parentesi acute per il repr sono state rimosse

Il backtick restituiva la rappresentazione testuale di un valore.

**Perche'**: La sintassi coincideva con il carattere di sostituzione in vari linguaggi.

```python
testo = repr(valore)
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### Le classi vecchie sono sparite

In Python 2 esistevano due modelli di classe, selezionati da `__metaclass__`; in Python 3 esiste solo il modello nuovo.

**Perche'**: I due modelli avevano regole diverse per descrittori, proprietà e MRO.

```python
# Python 3: un solo modello, derivato da object
class Nuova:
    pass
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `except E, e:` rimosso in favore di `except E as e:` (PEP 3110)

La variabile della clausola `except` veniva eliminata automaticamente.

**Perche'**: La forma con virgola era ambigua con la tupla di eccezioni in Python 3.

```python
try:
    ...
except ValueError as exc:
    print(exc)
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `dict.has_key()` rimosso

Membro esistenziale del dizionario come metodo.

**Perche'**: `in` funziona su ogni tipo di contenitore, non solo sui dizionari.

```python
if "nome" in d:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `dict.iteritems()` e amici rimossi

I metodi `iterkeys`, `itervalues`, `iteritems` producevano iteratori; `keys`, `values`, `items` restituivano liste.

**Perche'**: `keys()`, `values()` e `items()` restituiscono ora viste, che sono iterabili, efficienti e permettono di evitare la copia della lista.

```python
for chiave, valore in d.items():
    print(chiave, valore)
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `print` era un'istruzione, non una funzione

In Python 2 `print` e' una dichiarazione con sintassi propria, con argomenti separati da virgole e redirezione via `>>`.

**Perche'**: Una dichiarazione speciale impediva di usare `print` come valore prima di chiamata, non aveva `sep`/`end` e non si poteva redirigere senza una sintassi separata. La funzione risolve tutti e tre i punti.

```python
print("ciao", nome)
print("errore", file=sys.stderr)
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `raw_input()` rinominato in `input()`

Python 2 aveva due funzioni di lettura: `input()` valutava l'espressione letta (pericoloso), `raw_input()` restituiva la stringa.

**Perche'**: Avere una sola funzione di lettura evita che `input()` valuti codice arbitrario: in Python 3 `input()` non esegue nulla.

```python
nome = input("Nome: ")
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `reduce()` non e' piu' un builtin

La funzione e' stata spostata in `functools` dove non era in conflitto con concetti non correlati.

**Perche'**: Era una delle pochissime funzioni non intuitive fra i builtin.

```python
from functools import reduce

risultato = reduce(lambda a, b: a + b, [1, 2, 3])
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `unicode` rimosso: `str` e' gia' testo Unicode

In Python 2 `str` conteneva byte e `unicode` conteneva caratteri. In Python 3 esiste un solo tipo per il testo.

**Perche'**: La distinzione obbligava a decodificare in modo esplicito e produceva la maggior parte dei bug di codifica.

```python
def f(s: str) -> str:
    return "testo" + s
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html

### `xrange()` sostituito da `range()`

In Python 2 `range()` costruiva una lista; `xrange()` restituiva un generatore di interi.

**Perche'**: Due funzioni con lo stesso nome e comportamento diverso era una trappola frequente. `range()` e' diventata pigra e Accepta anche numeri arbitrariamente grandi.

```python
for i in range(10):
    print(i)
```

Fonte: https://docs.python.org/3/whatsnew/3.0.html


Fonte del rilascio: https://www.python.org/downloads/release/python-300/
