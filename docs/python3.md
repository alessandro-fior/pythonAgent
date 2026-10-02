# Python 3: la base attuale

Questa pagina e' il quadro di insieme di Python 3. Per il dettaglio di una
singola novita' si veda la scheda in `versions/`, che e' generata dal catalogo
e cita la fonte ufficiale.

## Tre decenni in quattro passaggi

**3.0 (2008) — la rottura.** `print` diventa funzione, `/` restituisce un
float, le stringhe diventano Unicode per default, `dict.keys()` diventa una
vista. Il progetto si dichiara incompatibile e la PEP 240 descrive il metodo di
portabilita' (`2to3`, poi rimosso nel 3.13).

**3.6 (2016) — la comodita' quotidiana.** Le f-string (PEP 498) e i type hint
(PEP 484). Da qui in poi la sintassi incorporate l'espressioni con il metodo che
si usa adesso, e il codice diventa progressivamente piu' breve da leggere.

**3.10 (2021) — il linguaggio piu' espressivo.** Il pattern matching
(PEP 634) e il parser PEG (PEP 617), che abilita tutta la sintassi successiva.
Le parentesi attorno a una lista di contestatori diventano opzionali.

**3.14 (2025) — il passo oltre.** Le t-string (PEP 750), l'esecuzione differita
delle annotazioni (PEP 649) e il supporto ufficiale del JIT su Linux e macOS.

## Come orientarsi fra le novita'

Il catalogo distingue quattro fatti, non uno:

* **introdotta** in una versione: la scheda vale da quel momento;
* **deprecata** in una versione: funziona ancora, ma va evitata;
* **rimossa** in una versione: non esiste piu', e la versione di rimozione e'
  il dato che conta per la compatibilita';
* **cambiata**: esiste in entrambe le versioni, con comportamento diverso.

```bash
python -m pme features --version 3.12      # introdotte e deprecate
python -m pme features --id pattern-matching   # una scheda
python -m pme features --introduced-in 3.13  # come data di introduzione
python -m pme features --removed-in 3.12     # cio' che e' sparito, e quando
```

```python
>>> from pme import changed_between
>>> from pme.version import Version
>>> changed_between(Version(3, 10), Version(3, 14))["rimosse"]
['dead-batteries-removed', 'deprecated-2to3-removed', 'distutils-removed']
```

## Le sintassi che si vedono piu' spesso

Ogni costrutto e' dimostrato da un programma che gira e che dichiara il
risultato atteso:

```bash
python -m pme demo --id f-string
python -m pme demo --id walrus
python -m pme demo --id pattern-matching
python -m pme demo --id except-star
python -m pme demo --id type-parameters
python -m pme demo --id t-string
```

`python -m pme demo --list` mostra tutte le dimostrazioni e indica per quale
versione servono, quindi la stessa suite puo' girare su un solo interprete
saltando cio' che non e' ancora supportato.

## Le cose che sono andate via

Il catalogo copre in dettaglio le rimozioni piu' importanti; l'elenco completo
e' in `versions/` e si interroga anche a runtime.

| Rimossa | Da | Al posto |
| --- | --- | --- |
| backtick e `raw_input`, `xrange`, `has_key`, `iteritems` | 3.0 | `repr`, `input`, `range`, `in`, `items()` |
| classi "vecchie", `print` come istruzione, `unicode`, `reduce` dal namespace | 3.0 | `class X(object)`, funzione, `str`, `functools.reduce` |
| keyword `async`/`await` come identificatori | 3.7 | nomi diversi |
| `distutils` | 3.12 | `setuptools`, `pyproject.toml` |
| `dead batteries` (PEP 594) | 3.13 | `urllib`, `email`, `http`, `ssl` |
| `2to3` e `lib2to3` | 3.13 | riscrittura manuale o strumenti esterni |
| `typing.io`, `typing.re`, `locale.resetlocale` | 3.13 | i moduli reali |
| il campo `fields` di `TypedDict` | 3.16 (gia' deprecato nel 3.13) | keyword `fields=` |

Due righe di questa tabella valgono una precisazione, perche' mostrano come il
catalogo distingue i casi:

* **`distutils`** e' una rimozione "pura": non c'e' stato un periodo di
  deprecazione, quindi la scheda non ha `deprecated`. In Python 3.10 ne era stata
  annunciata la fine, ma la rimozione vera e' avvenuta nel 3.12.
* **`2to3`** ha invece una deprecazione esplicita nel 3.11 e la rimozione nel
  3.13: due eventi distinti, entrambi presenti nella scheda.

Una rimozione non e' mai una sorpresa se il catalogo e' aggiornato: ogni scheda
di rimozione registra la versione che l'ha rimossa e, quando esiste, quella che
l'aveva prima deprecata, cosi' si puo' risalire alla versione minima che un
progetto deve dichiarare.

## Come tenere il conto

```bash
python -m pme versions     # stato del supporto
python -m pme runtime     # l'interprete in esecuzione
```

`pme runtime` e' utile per controllare cosa e' supportato *qui* adesso, che non
e' la stessa cosa di cio' che esiste in una versione futura: include sonde
sintattiche che compilano davvero il costrutto, non solo un confronto di
numeri.
