\# Python Modern Evolution — AGENT.md



\## 1. Obiettivo del progetto



Creare una repository GitHub dedicata all'evoluzione del linguaggio \*\*Python\*\*, partendo da \*\*Python 2\*\* e arrivando alle versioni moderne di \*\*Python 3.x\*\*.



Il progetto deve permettere a uno sviluppatore di capire:



\- cosa è cambiato tra Python 2 e Python 3;

\- quali funzionalità sono state introdotte nelle principali versioni Python 3.x;

\- quali funzionalità sono oggi moderne e consigliate;

\- quali funzionalità sono obsolete/deprecate;

\- come è cambiato lo stile di programmazione Python;

\- come aggiornare codice Python legacy;

\- quali caratteristiche distinguono Python moderno dal vecchio Python 2;

\- verificare nel tempo l'eventuale arrivo di \*\*Python 4\*\*.



> \*\*Situazione attuale:\*\* Python 4 non è stato rilasciato.  

> Il progetto deve quindi considerare Python 3.x come linea evolutiva principale fino a quando la documentazione ufficiale non stabilirà diversamente.



\---



\# 2. Regola fondamentale dell'agente



L'agente deve distinguere sempre:



```text

Python 2

&#x20;  ↓

Python 3.0

&#x20;  ↓

Python 3.1

&#x20;  ↓

...

Python 3.7

&#x20;  ↓

Python 3.8

&#x20;  ↓

Python 3.9

&#x20;  ↓

Python 3.10

&#x20;  ↓

Python 3.11

&#x20;  ↓

Python 3.12

&#x20;  ↓

Python 3.13

&#x20;  ↓

Python 3.14

&#x20;  ↓

future Python 3.x

&#x20;  ↓

eventuale Python 4

```



Non deve inventare una versione Python 4.



Quando vengono richieste informazioni sulle versioni più recenti, verificare sempre la documentazione ufficiale Python.



\---



\# 3. Fonti



Preferire:



1\. documentazione ufficiale Python;

2\. Python Enhancement Proposals (PEP);

3\. Python Developer's Guide;

4\. documentazione delle singole versioni;

5\. Python Packaging Authority (PyPA).



Evitare di utilizzare blog o articoli non ufficiali come fonte primaria quando è disponibile la documentazione ufficiale.



\---



\# 4. Struttura della repository



Creare una struttura simile:



```text

PythonModernEvolution\_AGENT/

│

├── README.md

├── AGENT.md

├── LICENSE

│

├── docs/

│   ├── python2.md

│   ├── python3.md

│   ├── versions.md

│   ├── migration-python2-python3.md

│   ├── modern-python.md

│   └── future-python.md

│

├── versions/

│   ├── python-2.md

│   ├── python-3.0.md

│   ├── python-3.1.md

│   ├── python-3.2.md

│   ├── python-3.3.md

│   ├── python-3.4.md

│   ├── python-3.5.md

│   ├── python-3.6.md

│   ├── python-3.7.md

│   ├── python-3.8.md

│   ├── python-3.9.md

│   ├── python-3.10.md

│   ├── python-3.11.md

│   ├── python-3.12.md

│   ├── python-3.13.md

│   ├── python-3.14.md

│   └── future.md

│

├── examples/

│   ├── python2/

│   ├── python3/

│   ├── python-modern/

│   └── migration/

│

├── exercises/

│   ├── 01-syntax/

│   ├── 02-types/

│   ├── 03-functions/

│   ├── 04-oop/

│   ├── 05-generators/

│   ├── 06-decorators/

│   ├── 07-typing/

│   ├── 08-async/

│   └── 09-modern-python/

│

└── tests/

```



\---



\# 5. Python 2



Documentare Python 2 come base storica.



Argomenti minimi:



\- `print` statement;

\- `unicode` e `str`;

\- divisione tra interi;

\- `xrange`;

\- `raw\_input`;

\- vecchio modello delle classi;

\- `dict.iteritems()`;

\- eccezioni;

\- metaclassi;

\- `\_\_future\_\_`;

\- differenze Python 2 / Python 3.



Esempio:



```python

\# Python 2

print "Hello"



name = raw\_input("Name: ")



for i in xrange(10):

&#x20;   print i

```



Confrontarlo con Python moderno:



```python

\# Python 3

print("Hello")



name = input("Name: ")



for i in range(10):

&#x20;   print(i)

```



\---



\# 6. Python 3.0



Documentare Python 3 come grande rottura rispetto a Python 2.



Evidenziare:



\- `print()` come funzione;

\- Unicode come comportamento standard delle stringhe;

\- `input()`;

\- `range()`;

\- nuove regole per la divisione;

\- `bytes`;

\- annotazioni;

\- eccezioni;

\- iteratori;

\- eliminazione di numerose API Python 2.



Il confronto Python 2 → Python 3 deve essere uno dei capitoli principali del progetto.



\---



\# 7. Evoluzione Python 3.x



Per ogni versione creare una scheda con questa struttura:



```markdown

\# Python X.Y



\## Data



\## Stato



\## Novità principali



\## Nuova sintassi



\## Nuove API



\## Miglioramenti del linguaggio



\## Miglioramenti delle performance



\## Deprecazioni



\## Rimozioni



\## Esempio



\## Prima / Dopo



\## Impatto sul codice esistente



\## PEP importanti



\## Compatibilità

```



\---



\# 8. Argomenti da tracciare



L'agente deve classificare le novità almeno nelle seguenti categorie:



\### Sintassi



Esempi:



\- f-string;

\- walrus operator;

\- pattern matching;

\- nuove forme di `except`;

\- nuove sintassi per type hints.



\### Tipi



Seguire l'evoluzione di:



```python

str

bytes

list

tuple

dict

set

frozenset

```



e delle API collegate.



\### Funzioni



Documentare:



\- positional-only arguments;

\- keyword-only arguments;

\- default arguments;

\- `\*args`;

\- `\*\*kwargs`;

\- annotations.



\### OOP



Seguire:



\- classi;

\- dataclass;

\- metaclassi;

\- protocolli;

\- abstract base classes;

\- `\_\_slots\_\_`;

\- properties;

\- descriptors.



\### Iteratori e generatori



Documentare:



```python

yield

yield from

generator expressions

iterators

async generators

```



\### Decoratori



Mostrare esempi progressivi:



```python

@decorator

def function():

&#x20;   ...

```



\### Type hints



Seguire l'evoluzione:



```python

List\[str]

Dict\[str, int]

Optional\[str]

Union\[int, str]

```



verso:



```python

list\[str]

dict\[str, int]

str | None

int | str

```



e documentare:



\- `typing`;

\- generics;

\- `TypeVar`;

\- `Protocol`;

\- `TypedDict`;

\- `Literal`;

\- `TypeAlias`;

\- `Self`;

\- `TypeGuard`;

\- type parameter syntax.



\---



\# 9. Dataclasses



Creare una sezione dedicata alle `dataclasses`.



Esempio:



```python

from dataclasses import dataclass





@dataclass

class Person:

&#x20;   name: str

&#x20;   age: int

```



Confrontarla con una classe tradizionale:



```python

class Person:



&#x20;   def \_\_init\_\_(self, name, age):

&#x20;       self.name = name

&#x20;       self.age = age

```



Spiegare quando utilizzare ciascun approccio.



\---



\# 10. Pattern Matching



Documentare il pattern matching introdotto in Python 3.10.



Esempio:



```python

match command:

&#x20;   case "start":

&#x20;       start()

&#x20;   case "stop":

&#x20;       stop()

&#x20;   case \_:

&#x20;       unknown()

```



Mostrare anche pattern strutturali.



\---



\# 11. Async Python



Creare una sezione dedicata alla programmazione asincrona.



Seguire l'evoluzione:



```text

generator

&#x20;   ↓

coroutine

&#x20;   ↓

async / await

&#x20;   ↓

asyncio

&#x20;   ↓

async context manager

&#x20;   ↓

async iterator

```



Esempio moderno:



```python

import asyncio





async def main():

&#x20;   print("Hello")

&#x20;   await asyncio.sleep(1)

&#x20;   print("World")





asyncio.run(main())

```



\---



\# 12. Modern Python



Creare una pagina:



```text

docs/modern-python.md

```



che descriva lo stile Python moderno.



Esempio:



```python

from dataclasses import dataclass





@dataclass

class User:

&#x20;   name: str

&#x20;   age: int





def adults(users: list\[User]) -> list\[User]:

&#x20;   return \[user for user in users if user.age >= 18]

```



Utilizzare, quando appropriato:



\- type hints;

\- dataclasses;

\- f-string;

\- comprehensions;

\- context manager;

\- pathlib;

\- `enum`;

\- `match`;

\- `async/await`;

\- pattern moderni delle standard library.



\---



\# 13. pathlib



Confrontare il vecchio approccio:



```python

import os



path = os.path.join("data", "file.txt")

```



con:



```python

from pathlib import Path



path = Path("data") / "file.txt"

```



Spiegare vantaggi e compatibilità.



\---



\# 14. Gestione degli errori



Documentare l'evoluzione delle eccezioni.



Esempio:



```python

try:

&#x20;   value = int(text)

except ValueError as exc:

&#x20;   raise RuntimeError("Invalid value") from exc

```



Includere:



\- `try`;

\- `except`;

\- `else`;

\- `finally`;

\- exception chaining;

\- custom exceptions;

\- `ExceptionGroup`;

\- `except\*`.



\---



\# 15. Context manager



Documentare:



```python

with open("file.txt") as file:

&#x20;   data = file.read()

```



e la creazione di context manager personalizzati:



```python

from contextlib import contextmanager

```



\---



\# 16. Packaging



Creare una sezione dedicata all'evoluzione del packaging Python.



Documentare:



```text

setup.py

setup.cfg

pyproject.toml

pip

venv

virtualenv

wheel

sdist

build

```



e spiegare il ruolo di:



```text

PEP 517

PEP 518

PEP 621

```



\---



\# 17. Ambiente virtuale



Preferire gli strumenti moderni della standard library quando appropriato:



```bash

python -m venv .venv

```



Attivazione Windows:



```powershell

.venv\\Scripts\\Activate.ps1

```



Linux/macOS:



```bash

source .venv/bin/activate

```



\---



\# 18. Testing



Documentare almeno:



```text

unittest

pytest

doctest

```



e mostrare un test moderno:



```python

def add(a: int, b: int) -> int:

&#x20;   return a + b





def test\_add():

&#x20;   assert add(2, 3) == 5

```



\---



\# 19. Migrazione Python 2 → Python 3



Creare una guida specifica:



```text

docs/migration-python2-python3.md

```



La guida deve affrontare almeno:



| Python 2 | Python 3 |

|---|---|

| `print "x"` | `print("x")` |

| `raw\_input()` | `input()` |

| `xrange()` | `range()` |

| `unicode` | `str` |

| `str` bytes-oriented | `bytes` |

| `dict.iteritems()` | `dict.items()` |

| `/` integer division legacy | `/` true division |

| vecchie eccezioni | nuove exception semantics |



Aggiungere esempi reali di refactoring.



\---



\# 20. Esempio di progetto legacy



Creare:



```text

examples/migration/legacy\_app.py

```



con codice volutamente simile a un'applicazione Python 2.



Poi creare:



```text

examples/migration/modern\_app.py

```



con la versione Python moderna.



L'obiettivo è mostrare concretamente la trasformazione.



\---



\# 21. Tabella cronologica



Creare una tabella centrale:



```markdown

| Versione | Periodo | Novità principali |

|---|---|---|

| Python 2.x | storico | sintassi legacy |

| Python 3.0 | 2008 | grande transizione |

| Python 3.5 | 2015 | async/await |

| Python 3.6 | 2016 | f-string |

| Python 3.7 | 2018 | dataclasses |

| Python 3.8 | 2019 | walrus operator |

| Python 3.9 | 2020 | built-in generics |

| Python 3.10 | 2021 | pattern matching |

| Python 3.11 | 2022 | performance, ExceptionGroup |

| Python 3.12 | 2023 | typing e sintassi |

| Python 3.13 | 2024 | evoluzione interpreter |

| Python 3.14 | 2025 | verificare novità ufficiali |

| Python 4 | futuro | da verificare |

```



Le date e le novità devono essere verificate sulle fonti ufficiali prima di essere considerate definitive.



\---



\# 22. Regola per le nuove versioni



Quando viene rilasciata una nuova versione Python:



1\. creare `versions/python-X.Y.md`;

2\. aggiornare `versions.md`;

3\. aggiornare `README.md`;

4\. documentare le nuove feature;

5\. documentare deprecazioni e rimozioni;

6\. aggiungere almeno un esempio;

7\. aggiornare gli esempi moderni;

8\. verificare compatibilità;

9\. indicare la data di rilascio;

10\. indicare la versione precedente;

11\. indicare eventuali PEP rilevanti.



\---



\# 23. Python 4



Creare:



```text

versions/future.md

docs/future-python.md

```



Il contenuto deve essere prudente.



Non affermare:



```text

Python 4 uscirà nel XXXX

```



a meno che tale informazione sia stata ufficialmente annunciata.



Utilizzare invece:



```text

Python 4 — not released



Status:

No Python 4 release currently documented.



Action:

Continue tracking the official Python release documentation.

```



\---



\# 24. Confronto con altri linguaggi



Se utile, creare una sezione comparativa:



```text

Python

Java

C#

Ruby

```



ma senza trasformare il progetto in una documentazione generica sui linguaggi.



Il focus deve rimanere:



> evoluzione del linguaggio Python.



\---



\# 25. Regola per gli esempi



Ogni esempio deve indicare chiaramente:



```python

\# Python 3.10+

```



oppure:



```python

\# Python 3.12+

```



quando una determinata funzionalità richiede una versione specifica.



Non utilizzare accidentalmente feature moderne in esempi destinati a versioni precedenti.



\---



\# 26. Compatibilità



Quando una feature viene documentata, indicare:



```text

Introduced: Python X.Y

Requires: Python X.Y+

```



Se una feature è stata deprecata:



```text

Deprecated: Python X.Y

```



Se è stata rimossa:



```text

Removed: Python X.Y

```



\---



\# 27. Qualità del codice



Gli esempi devono seguire lo stile Python moderno.



Quando appropriato utilizzare:



```text

PEP 8

PEP 257

type hints

docstrings

f-strings

pathlib

dataclasses

context managers

```



Non introdurre complessità solo per dimostrare una feature.



\---



\# 28. Obiettivo didattico



Il progetto deve permettere a un programmatore che conosce Python legacy di arrivare progressivamente a:



```text

Python 2

&#x20;  ↓

Python 3 fundamentals

&#x20;  ↓

Python 3 modern syntax

&#x20;  ↓

Type hints

&#x20;  ↓

Dataclasses

&#x20;  ↓

Iterators / Generators

&#x20;  ↓

Decorators

&#x20;  ↓

Pattern Matching

&#x20;  ↓

Async / Await

&#x20;  ↓

Modern Standard Library

&#x20;  ↓

Packaging

&#x20;  ↓

Testing

&#x20;  ↓

Modern Python architecture

```



\---



\# 29. Checklist dell'agente



Prima di considerare completata una versione:



\- \[ ] versione verificata;

\- \[ ] data verificata;

\- \[ ] novità principali documentate;

\- \[ ] sintassi nuova documentata;

\- \[ ] API nuove documentate;

\- \[ ] deprecazioni documentate;

\- \[ ] rimozioni documentate;

\- \[ ] PEP importanti indicati;

\- \[ ] esempio funzionante aggiunto;

\- \[ ] compatibilità indicata;

\- \[ ] README aggiornato;

\- \[ ] indice aggiornato;

\- \[ ] test aggiornati.



\---



\# 30. Regola finale



Questo progetto deve essere una \*\*timeline viva dell'evoluzione di Python\*\*.



Non limitarsi a descrivere cosa esiste oggi.



Per ogni caratteristica importante cercare di mostrare:



```text

COME ERA

&#x20;  ↓

COSA È CAMBIATO

&#x20;  ↓

PERCHÉ È CAMBIATO

&#x20;  ↓

COME SI USA OGGI

&#x20;  ↓

COSA È DEPRECATO

```



L'obiettivo finale è permettere a uno sviluppatore di prendere codice Python vecchio e capire:



```text

"Da quale epoca arriva?"

"Quali problemi di compatibilità presenta?"

"Come lo trasformo in Python moderno?"

"Quale versione minima di Python devo utilizzare?"

```

