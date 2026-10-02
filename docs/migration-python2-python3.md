# Da Python 2 a Python 3: come si migura

Questa e' la pagina operativa: presuppone che il codice esista, e descrive
l'ordine in cui conviene affrontare i problemi. L'elenco delle differenze e' in
[`python2.md`](python2.md); qui l'ordine di lavoro.

## Step 1: misurare prima di toccare

Il primo errore da evitare e' iniziare dalla sintassi. Un programma che non
importa puo' avere problemi di compatibilita' non syntactic, che sono piu'
costosi: stringhe e divisione. Conviene quindi partire dai dati.

```bash
python -m pme check examples/python2/legacy_report.py
```

L'output e' una lista di posizioni con gravita':

```text
examples\python2\legacy_report.py:19:12: errore: Python 3.0: il suffisso `L` sui letterali interi non esiste piu' [long-literal-suffix]
examples\python2\legacy_report.py:48:42: errore: Python 3.0: `iteritems()` e' stato rimosso, usare `items()` [iteritems]
examples\python2\legacy_report.py:61:29: errore: Python 3.0: `has_key` non esiste piu', riscrivere come `chiave in dizionario` [has-key]
...
```

Il formato e' `file:line:colonna: gravita': versione: messaggio [regola]`, e la
regola fra parentesi quadre e' quella che si puo' usare per filtrare o per
cercare la corrispondenza nel catalogo.

Le tre gravita' hanno un significato operativo:

* **errore**: in Python 3 il codice non esiste piu', va riscritto;
* **avvertenza**: il codice esiste ma si comporta diversamente, va deciso;
* **suggerimento**: il codice funziona, ma c'e' una forma moderna.

Da questo comando si ottiene anche la versione minima richiesta:

```bash
python -m pme modernize file.py --diff
```

## Step 2: la riscrittura automatica, e dove si ferma

Lo strumento automatico e' utile ma non sufficiente, ed e' importante sapere
perche'. `pme.legacy.modernize` applica solo trasformazioni **deterministiche**:
quelle in cui il risultato e' lo stesso per ogni input possibile.

| Applicata automaticamente | Perche' si puo' |
| --- | --- |
| `x.has_key(k)` -> `k in x` | la semantica e' definita per ogni dizionario |
| `d.iteritems()` -> `d.items()` | lista e vista si usano nello stesso modo nel `for` |
| `print "x"` -> `print("x")` | se non c'e' redirezione ne' argomenti multipli |
| `except E, e` -> `except E as e` | la nuova forma accetta la stessa variabile |
| `u"x"` -> `"x"` | con l'encoding dichiarato esplicitamente |
| `10L` -> `10` | i letterali interi non hanno piu' suffisso |

| Segnalata ma non applicata | Perche' no |
| --- | --- |
| `/` -> `//` | serve sapere se il risultato deve essere intero |
| `print >>f, x` | la redirezione ha piu' forme possibili |
| backtick `` `x` `` | `repr()` cambia il tipo, non solo il testo |
| `2to3` sul file intero | la riscrittura non capisce il significato |

Il punto di fondo e' noto da decenni e ufficialmente riconosciuto: nel 2025
Python 3.13 ha rimosso `2to3` e `lib2to3` proprio perche' mantenere uno
strumento che riscrive senza capire costa piu' di quanto rende. La scheda
`deprecated-2to3-removed` del catalogo lo registra, con la fonte.

## Step 3: stringhe e I/O, in ordine

La causa piu' frequente di errori dopo l'import e' `open()` senza `encoding`.

```python
# Python 2
testo = open("dati.txt").read()          # byte

# Python 3
testo = open("dati.txt", encoding="utf-8").read()   # caratteri
```

Regole pratiche:

1. ogni `open()` per file di testo dichiara `encoding`;
2. ogni operazione fra `str` e `bytes` e' un errore in Python 3, ed e' il
   momento in cui il bug diventa visibile: risolvere qui, non con `encode()` a
   caso;
3. la codice di default e' UTF-8; dichiararlo lo rende esplicito e indipendente
   dalle impostazioni della macchina.

## Step 4: divisione e confronto

Sostituire `/` con `//` solo dove il risultato deve essere intero. Nei calcoli
in virgola mobile il comportamento e' gia' quello giusto.

```python
# media di interi: in Python 2 il risultato era un intero, ora un float
media = somma / n
```

Se il valore deve essere intero, la domanda da porsi e' *arrotondare o
troncare*: `//` tronca verso l'infinito negativo, `int()` tronca verso zero.
Per numeri negativi i due risultati differiscono.

## Step 5: la verifica finale

```python
>>> from pme.legacy import detect, minimum_version
>>> sorgente = open("mio_modulo.py", encoding="utf-8").read()
>>> minimum_version(sorgente)
'3.6'
>>> bloccanti = [f for f in detect(sorgente) if f.severity.value == "errore"]
>>> len(bloccanti) > 0
True
```

Il risultato non e' sempre la versione che causa l'errore bloccante: per
l'esempio in `examples/python2/legacy_report.py` la versione minima e' **3.6**,
non 3.0. Il motivo e' che la `%`-formattazione non e' un errore ma un
suggerimento di modernizzazione, e la versione minima include anche i
suggerimenti, perche' descrive la versione che l'applicazione dovrebbe
dichiarare *per poter usare le forme consigliate*.

La stessa separazione e' quella che usa la CLI: `check` distingue cio' che
*blocca* da cio' che *suggerisce*, e le due risposte non vanno confuse.

Un codice davvero portato non deve piu' produrre errori con `check`: restano, al
massimo, suggerimenti.

## Le quattro regole che rendono il lavoro durevole

1. **Niente codice nuovo in Python 2.** Ogni correzione a un ramo Python 2 e'
   un lavoro che va rifatto.
2. **Prima i test.** Un codice senza test che funziona in Python 2 ha un
   comportamento documentato solo per il caso che i test coprono.
3. **Una versione minima esplicita.** Dichiarare `requires-python` nel packaging
   e farlo derivare dai dati, non dalla memoria.
4. **Il catalogo come riferimento.** `python -m pme features --version 3.x`
   risponde piu' in fretta di una ricerca, e cita la fonte.
