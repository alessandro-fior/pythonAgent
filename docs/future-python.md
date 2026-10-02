# Cosa viene dopo: Python 3.15, 3.16 e oltre

Le versioni future non sono speculazione: sono il risultato di PEP accettate,
calendari pubblici e decisioni di design già prese. Questa pagina separa cio'
che e' pianificato da cio' che e' solo un'idea.

## Il calendario ufficiale

| Versione | Stato | Rilascio previsto | PEP |
| --- | --- | --- | --- |
| 3.15 | prerelease | 2026-10-01 | PEP 790 |
| 3.16 | feature | 2027-10-06 | PEP TBD |
| 3.17 | planned | 2028 | PEP TBD |

Le date sono quelle annunciate; possono slittare. Lo stato "feature" per 3.16
significa che le PEP che ne faranno parte sono ancora in discussione.

## Python 3.15 (PEP 790)

Le feature accettate per 3.15 al momento:

| Feature | PEP | Cosa cambia |
| --- | --- | --- |
| `frozendict` builtin | 814 | Dizionario immutabile e hashabile; prima serviva `MappingProxyType` |
| Import lazy dichiarativi | 810 | `import deferred module` invece di trucchetti runtime |

Non tutte le PEP accettate per una release entrano nel rilascio finale; il
catalogo le segna con `status="planned"` finche' non sono nel ramo
stabile.

## Python 3.16 (in fase di discussione)

Le PEP in stato "accepted" o "provisional" per 3.16:

| Feature | PEP | Stato | Nota |
| --- | --- | --- | --- |
| Tipi parametrizzati generici migliorati | 695+ | accepted | estende i `type parameter` del 3.12 |
| Pattern matching su type | TBD | draft | `match x: case int: ...` |
| `except*` con binding multipli | TBD | draft | estende il 3.11 |

Queste sono fonti ufficiali consultate periodicamente:
- <https://peps.python.org/topic/typing/>
- <https://peps.python.org/topic/stdlib/>
- <https://devguide.python.org/versions/>

## Python 4: non e' rilasciato

Il progetto dichiara esplicitamente:

```python
>>> from pme.version import PYTHON4_RELEASED
>>> PYTHON4_RELEASED
False
```

Non esiste una PEP per Python 4, non esiste una roadmap pubblica che lo
preveda, e la numerazione continuerà con 3.x finché non ci sarà una ragione
architetturale per cambiare. Speculare su Python 4 distoglie l'attenzione da
cose concrete che arrivano in 3.15 e 3.16.

## Come usare queste informazioni

1. **Per decidere la versione minima**: `python -m pme features --status planned`
   elenca solo le feature `planned`; se il tuo codice non ne usa nessuna, la
   versione minima non cambia.
2. **Per prepararsi alle rimozioni**: le feature con `kind=DEPRECATION` e
   `removed` impostato indicano quando una deprecazione diventa errore.
3. **Per non essere sorpresi**: la scheda `versions/future.md` e'
   generata dal catalogo e cita le PEP; si rigenera con
   `python -m pme generate`.

```bash
python -m pme features --status planned
python -m pme features --removed-in 3.16
python -m pme versions | grep -E "3\.(15|16)"
```

## La differenza tra "pianificato" e "speculativo"

Una feature e' **pianificata** se:
- ha una PEP accettata (`Status: Accepted`);
- ha un milestione assegnato in una versione futura;
- e' nel calendario ufficiale.

Una feature e' **speculativa** se:
- e' solo una discussione su `python-dev` o `discuss.python.org`;
- non ha PEP o la PEP e' `Draft`;
- non c'e' un calendario.

Il catalogo include solo le pianificate. Le speculative non hanno una scheda,
perche' non hanno una fonte verificabile.