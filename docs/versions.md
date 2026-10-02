# Le versioni di Python nel tempo

Questa pagina e' la mappa di orientamento: dice quando e' uscita ogni versione,
quanto e' durato il suo supporto e quali sono le novita' che la definiscono. Per
il dettaglio di una singola versione si veda la scheda in `versions/`, che e'
generata dal catalogo e quindi non puo' divergere dai dati.

## Come leggere il calendario

Il progetto Python usa un modello di rilascio con cadenza annuale: ogni anno
nasce una nuova versione, ogni versione riceve correzioni per circa cinque anni.
Lo stato di ogni ramo e' definito in modo formale dalla PEP 602.

| Stato | Significato |
| --- | --- |
| `end-of-life` | non riceve piu' nulla, nemmeno correzioni di sicurezza |
| `security` | riceve solo correzioni di vulnerabilita' |
| `bugfix` | riceve correzioni di bug, ed e' la versione stabile corrente |
| `prerelease` | esiste ma non e' ancora una versione installabile come stabile |
| `feature` | in sviluppo, le novita' non sono ancora decise |

Una distinzione che il calendario rende esplicita e che spesso viene confusa:
una versione in prerelease riceve correzioni, ma non e' un rilascio che si puo'
installare come stabile. Per questo nel progetto `supported_releases()`
 distingue "supportato" da "rilasciato".

## Il calendario

| Versione | Rilascio | Stato | Fine supporto |
| --- | --- | --- | --- |
| 2.7 | 2020-04-20 | end-of-life (EOL) | - |
| 3.0 | 2008-12-03 | end-of-life | 2009-06-27 |
| 3.1 | 2009-06-27 | end-of-life | - |
| 3.2 | 2011-02-20 | end-of-life | - |
| 3.3 | 2012-09-29 | end-of-life | - |
| 3.4 | 2014-03-16 | end-of-life | - |
| 3.5 | 2015-09-13 | end-of-life | - |
| 3.6 | 2016-12-23 | end-of-life | - |
| 3.7 | 2018-06-27 | end-of-life | - |
| 3.8 | 2019-10-14 | end-of-life | - |
| 3.9 | 2020-10-05 | end-of-life | 2025-10-31 |
| 3.10 | 2021-10-04 | end-of-life | 2026-10-01 |
| 3.11 | 2022-10-24 | security | 2027-10-01 |
| 3.12 | 2023-10-02 | security | 2028-10-01 |
| 3.13 | 2024-10-07 | security | 2029-10-01 |
| 3.14 | 2025-10-07 | bugfix | 2030-10-01 |
| 3.15 | 2026-10-01 | prerelease | 2031-10-01 |
| 3.16 | 2027-10-06 | feature | 2032-10-01 |

La tabella e' anche disponibile come dati interrogabili:

```bash
python -m pme versions
python -m pme versions --markdown
```

```python
>>> from pme import latest_stable, supported_releases
>>> latest_stable().version
Version(major=3, minor=14)
>>> [str(r.version) for r in supported_releases()]
['3.11', '3.12', '3.13', '3.14']
```

## Le quattro versioni che contano

Non tutte le versioni hanno la stessa importanza per chi scrive codice. Queste
quattro spiegano la maggior parte delle differenze che si incontrano working
today:

* **3.0 (2008)** — la rottura con Python 2: `print` diventa funzione, `/`
  cambia significato, le stringhe diventano Unicode per default. E' la versione
  che spiega la maggior parte degli errori di migrazione.
* **3.6 (2016)** — le f-string, e con esse la fine del `%` e di `.format()` per
  il testo interpolato. E' anche la versione in cui i type hint diventano
  ufficiale (PEP 484).
* **3.10 (2021)** — il pattern matching con `match`/`case`, e il parser PEG che
  rende possibile tutta la sintassi successiva.
* **3.14 (2025)** — le t-string, l'esecuzione differita delle annotazioni e il
  supporto ufficiale del JIT.

## Lettura per obiettivi

* **Se parti da codice Python 2**: leggi prima `python2.md`, poi
  `migration-python2-python3.md`.
* **Se vuoi capire cosa e' cambiato rispetto a quello che usi**:
  `changed_between(versione_mia, latest_stable())`.
* **Se vuoi scrivere codice nuovo**: `modern-python.md`.
* **Se ti interessa cosa viene dopo**: `future-python.md`.

```python
>>> from pme import changed_between
>>> from pme.version import Version
>>> sommario = changed_between(Version(3, 8), Version(3, 14))
>>> sorted(sommario)
['cambiate', 'deprecate', 'introdotte', 'rimosse']
```

Le quattro chiavi rispondono a quattro fatti distinti, e la distinzione conta:
una scheda di rimozione con `introduced` al 3.0 e' un cambiamento del 3.0, non
una novita' del 3.0.
