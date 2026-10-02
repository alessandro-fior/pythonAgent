# Python 3.15

Stato al momento della ricerca: **prerelease**, rilasciata il 2026-10-01, fine supporto 2031-10-01

Data pianificata da PEP 790; da rivedere al rilascio effettivo. Lo stato prerelease proviene da devguide.python.org/versions/.

Calendario di rilascio: PEP 790

## Miglioramento del linguaggio
### Import espliciti lazy (PEP 810)

Gli import rimandati diventano dichiarativi.

**Perche'**: Riduce il costo di avvio senza rinunciare alla chiarezza del codice.

Fonte: https://docs.python.org/3/whatsnew/3.15.html

### UTF-8 come encoding predefinito (PEP 686)

Le operazioni di I/O senza `encoding` esplicito usano UTF-8, indipendentemente dall'impostazione di sistema.

**Perche'**: I default dipendenti dalla locale rendevano il comportamento non portabile.

```python
# 3.15: sempre UTF-8
with open('dati.txt', encoding='utf-8') as f:
    ...
```

Fonte: https://docs.python.org/3/whatsnew/3.15.html


## Nuove API
### Tipo built-in `frozendict` (PEP 814)

Un dizionario immutabile e hashabile nella standard library.

**Perche'**: Era disponibile solo come `types.MappingProxyType`, che non e' confrontabile.

Fonte: https://docs.python.org/3/whatsnew/3.15.html


Fonte del rilascio: https://peps.python.org/pep-0790/
