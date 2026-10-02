# Versioni future

**Python 4 non e' stato rilasciato.** Python 4 - not released. Status: no Python 4 release currently documented by the official Python documentation. Action: continue tracking https://devguide.python.org/versions/ and https://www.python.org/downloads/.

Quello che segue e' pianificato, non rilasciato: le date sono quelle annunciate dal progetto e possono cambiare.

## Python 3.15

- stato: **prerelease**
- calendario: PEP 790
- fonte: https://peps.python.org/pep-0790/

Data pianificata da PEP 790; da rivedere al rilascio effettivo. Lo stato prerelease proviene da devguide.python.org/versions/.

### Tipo built-in `frozendict` (PEP 814)

Un dizionario immutabile e hashabile nella standard library.

**Perche'**: Era disponibile solo come `types.MappingProxyType`, che non e' confrontabile.

### Import espliciti lazy (PEP 810)

Gli import rimandati diventano dichiarativi.

**Perche'**: Riduce il costo di avvio senza rinunciare alla chiarezza del codice.

### UTF-8 come encoding predefinito (PEP 686)

Le operazioni di I/O senza `encoding` esplicito usano UTF-8, indipendentemente dall'impostazione di sistema.

**Perche'**: I default dipendenti dalla locale rendevano il comportamento non portabile.


## Python 3.16

- stato: **feature**
- calendario: PEP 826
- fonte: https://devguide.python.org/versions/

Ramo 'main': unico ad accettare nuove funzionalita'. Data pianificata.
