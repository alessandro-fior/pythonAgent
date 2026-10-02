"""Report di vendite scritto in Python 2.

Questo file e' un esempio reale di codice legacy: **non deve essere importato**
e non deve essere compilato da Python 3. I test lo leggono come testo e lo
sottopongono a :mod:`pme.legacy`, che sa analizzarlo perche' lavora a livello
di token e non di sintassi.

Ogni costrutto qui presente e' annotato con la versione che l'ha introdotto o
rimossa, cosche' il file si legga come una scheda tecnica.

Prima versione: Python 2.4
Versione minima per eseguirlo oggi, dopo la modernizzazione: 3.0
"""

import sys

#: Limite di righe elaborabili. Il suffisso `L` sui letterali interi e' sparito
#: in Python 3.0: in Python 2 serviva a distinguerli dai numeri in virgola.
MAX_ITEMS = 10L


class Report(object):
    """Report di vendite: in Python 2 le classi esplicitamente derivate da
    ``object`` erano gia' "new style", quindi la modernizzazione e' indolore.
    """

    def __init__(self, rows):
        self.rows = rows

    def total(self):
        """Sommatoria delle quantita'.

        Nota: ``/`` fra interi troncava in Python 2 (``3 / 2 == 1``); in
        Python 3 restituisce ``1.5``. Per una divisione intera serve ``//``.
        """
        somma = 0
        for row in self.rows:
            somma = somma + row["qty"]
        return somma

    def by_product(self):
        """Raggruppa le righe per prodotto.

        ``iteritems()`` e' stato rimosso in Python 3.0 e sostituito da
        ``items()``, che restituisce una vista iterabile.
        """
        totali = {}
        for product, qty in self.totals().iteritems():
            totali[product] = totali.get(product, 0) + qty
        return totali

    def totals(self):
        """Restituisce le coppie (prodotto, quantita')."""
        coppie = []
        for row in self.rows:
            coppie.append((row["product"], row["qty"]))
        return coppie

    def has_product(self, nome):
        """`has_key` e' sparito in Python 3.0: si scrive `nome in dizionario`."""
        return self.totals().has_key(nome)

    def __repr__(self):
        # tre costrutti Python 2 in una riga: il backtick (che restituiva la
        # repr), il prefisso `u` sui letterali e la formattazione con `%`
        return u"<Report con %d righe>" % len(self.rows)


class Ledger:
    """Classe "vecchia" di Python 2: nessuna base esplicita.

    In Python 2 era una *classic class*, con regole di risoluzione dei metodi
    diverse da quelle delle *new style class*. In Python 3 il modello e' uno
    solo e la classe qui e' gia'derivata da `object`.
    """

    def __init__(self):
        self.entrate = 0
        self.uscite = 0

    def saldo(self):
        return self.entrate - self.uscite

    def __repr__(self):
        # in Python 2 il backtick produceva la repr() dell'espressione
        return `<Ledger: entrate %d, uscite %d>` % (self.entrate, self.uscite)


def ask_name():
    """Chiede un nome all'utente.

    ``raw_input`` e' sparito in Python 3.0: li' si chiama ``input``, che
    restituisce sempre una stringa (mentre ``raw_input`` in Python 2 restituiva
    byte).
    """
    nome = raw_input("Nome cliente: ")
    return unicode(nome)


def old_division(a, b):
    """Mostra la differenza di `/` fra interi (Python 3.0)."""
    return 7 / 2


def check(value):
    """`except E, err:` (Python 2) contro `except E as err:` (Python 3.0)."""
    try:
        if value <> 0:
            raise ValueError, "non zero"
    except (ValueError, TypeError), err:
        print "errore:", err
        return None
    return value


def main(argv):
    righe = [
        {"product": "tastiera", "qty": 2},
        {"product": "mouse", "qty": 5},
    ]
    report = Report(righe)
    print report
    print "righe:", len(righe)
    for product, qty in report.by_product().items():
        print "-", product, qty
    if report.has_product("mouse"):
        print "trovato"
    print "check:", check(3)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))