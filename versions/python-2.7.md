# Python 2.7 (ultima versione: 2.7.18)

Stato al momento della ricerca: **end-of-life**, rilasciata il 2020-04-20

Ultima release di Python 2 (2.7.18). Fine supporto: 2020-01-01.

## Miglioramento del linguaggio
### Python 2.7, l'ultima versione della serie 2

La base di partenza di quasi ogni migrazione: stringhe byte per default, `print` come istruzione, divisione intera con `/`.

**Perche'**: Python 2.7 ha segnato la fine del ramo 2: dal 1 gennaio 2020 riceve solo correzioni di sicurezza. E' la versione da cui si migra e il riferimento per capire cosa e' cambiato.

```python
# Python 3
import configparser
valori = open('dati.txt', encoding='utf-8').read()
print(len(valori) // 2)
```

Fonte: https://docs.python.org/3/whatsnew/2.7.html


Fonte del rilascio: https://www.python.org/downloads/release/python-2718/
