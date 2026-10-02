# Python 2: la base storica

Python 2 e' la base di partenza della maggior parte del codice ancora in
produzione. Non e' una versione "vecchia e basta": e' un linguaggio con regole
precise, e quasi ogni problema di miguzione nasce da una differenza concreta
fra due regole. Questa pagina elenca le differenze; la procedura e' in
[`migration-python2-python3.md`](migration-python2-python3.md).

## Le tre differenze silenziose

Le modifiche piu' costose non sono quelle che fanno fallire l'import: sono
quelle che lasciano girare il programma con risultati sbagliati.

### `/` non e' piu' la divisione intera

```python
# Python 2
resto = 7 / 2          # 3, intero

# Python 3
resto = 7 / 2          # 3.5, float
resto = 7 // 2         # 3, intero
```

In Python 3 `/` restituisce sempre un `float`. Il codice che faceva conti su
numeri interi con `/` continua a girare e restituisce numeri diversi: e' il caso
peggiore, perche' nessun errore segnala il problema. Vale anche per i confronti
e per la formattazione di risultati che vengono scritti su file o inviati a un
servizio esterno.

Lo strumento automatico e' semplice: l'analizzatore di questo progetto segnala
ogni `/` fra due literal interi come `true-division`, con la correzione suggerita
`//`.

### Le stringhe sono byte, e `unicode` e' un tipo diverso

```python
# Python 2
s = "testo"
len(s)          # 5 byte
u = u"testo"    # 5 caratteri, codice Unicode

# Python 3
s = "testo"
len(s)          # 5 caratteri
```

In Python 3 esiste un solo tipo di testo, `str`, e i byte sono un tipo
separato (`bytes`). Questo elimina la classe di bug piu' insidiosa della
migrazione: quelli che si manifestano solo con caratteri non ASCII, cioe'
esattamente quelli che la macchina di test non riproduce.

Le conseguenze pratiche sono tre:

1. `open(f)` restituisce byte: va indicato `encoding="utf-8"` esplicitamente;
2. `dict.keys()` restituiva una lista, ora una vista: `list(d)` per copiare;
3. gli identificatori sono `str`, e le stringhe `unicode` sono scomparse.

### `print` era un'istruzione

```python
# Python 2
print "ciao", nome
print >>sys.stderr, "errore"

# Python 3
print("ciao", nome)
print("errore", file=sys.stderr)
```

La forma Python 2 non e' convertibile automaticamente in tutti i casi: con piu'
argomenti e con la redirezione la riscrittura meccanica produce codice che
compila ma non fa quello che voleva. Va riscritta a mano.

## Le API che sono scomparse

Non tutte le rimozioni hanno un sostituto drop-in. Le piu' frequenti:

| Python 2 | Python 3 | Nota |
| --- | --- | --- |
| `raw_input()` | `input()` | la funzione era gia' quella giusta |
| `xrange()` | `range()` | `range` e' lazy dalla 3.0 |
| `dict.iteritems()` | `d.items()` | la vista e' lazy e dinamica |
| `dict.has_key(k)` | `k in d` | con `.get(k)` se serve il default |
| `unicode(x)` | `str(x)` | e `basestring` -> `str` |
| `long(x)` | `int(x)` | in Python 3 esiste un solo intero |
| `cmp(a, b)` | `(a > b) - (a < b)` | nessun sostituto leggibile |
| `reduce` | `from functools import reduce` | spostato, non rimosso |
| `reload` | `from importlib import reload` | idem |
| ConfigParser, httplib, xmlrpclib | `configparser`, `http.client`, `xmlrpc.client` | rinominati, i nomi con underscore erano lo standard |
| `filter`/`map` restituiscono liste | iteratori | in Python 3 |

Le classi `str`/`unicode` e la gerarchia `int`/`long` non hanno un semplice
"dopo": in Python 3 la distinzione e' scomparsa e con lei una parte dei modi in
cui era possibile sbagliare.

## Il modello delle classi

```python
# Python 2: classe vecchia, non discende da object
class Vecchio:
    def __init__(self):
        self.x = 1

# Python 3: un solo modello, tutto discende da object
class Moderno(object):
    def __init__(self):
        self.x = 1
```

In Python 3 `class Foo:` e `class Foo(object):` sono la stessa cosa. Le
differenze residue riguardano i metaclassi (`__metaclass__` diventa
`metaclass=` nella definizione) e i descrittori, che in Python 2 avevano una
semantica propria.

## Il modulo `__future__`

```python
from __future__ import division, print_function, unicode_literals
```

Era il meccanismo che permetteva di preparare la migrazione. Sono tutte
diventate permanenti: `division`, `print_function`, `unicode_literals`,
`absolute_import`, `generator_stop`, `nested_scopes`, `with_statement`. In
Python 3 sono no-op e l'importazione genera un `DeprecationWarning` quando il
futuro non esiste.

Il fatto che esistessero e' la prova che la rottura era nota e voluta: Python 3
non e' nato per sostituire Python 2, e' nato per poter rimuovere quello che non
reggeva piu'.

## Come il progetto verifica questi dati

Il catalogo in `pme/features.py` contiene una scheda per ciascuna di queste
differenze, con la fonte (`docs.python.org/3/whatsnew/3.0.html`) e con il
codice "prima" e "dopo". L'analizzatore in `pme/legacy.py` applica le stesse
regole a codice reale:

```bash
python -m pme check examples/python2/legacy_report.py
```

Un esempio completo e commentato e' in `examples/python2/legacy_report.py`: e'
Python 2 vero e non viene importato dai test, che lo leggono come testo.
