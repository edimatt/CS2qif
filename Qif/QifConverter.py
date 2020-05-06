from datetime import datetime
import logging.config
from io import open
import argparse
import chardet
import json
import csv
import re
import os

__all__ = ['QifConverter', 'processCsv']

logging.basicConfig(level=logging.DEBUG)
mlogger = logging.getLogger(__name__)


class QifConverter:
    def __init__(self, file_name_inp, file_name_out, cc=False,
                 start_dt=datetime(1900, 1, 1)):
        self.__file_name_inp = file_name_inp
        self.__file_name_out = file_name_out
        self.__encoding = chardet.detect(open(self.__file_name_inp, 'rb')
                                         .read())['encoding'] or 'iso-8859-1'
        self.cc = cc
        self.start_dt = start_dt

        _cf = os.path.join(os.environ.get('HOME'),
                           '.config',
                           'cs2qif',
                           'categories.json')
        if os.path.isfile(_cf):
            mlogger.info('Reading categories from %s', _cf)
            self.categories = json.load(open(_cf, 'r'))
        else:
            mlogger.warning('Categories file does not exist: %s.', _cf)
            self.categories = {}

    def __enter__(self):
        mlogger.debug("Opening " + self.__file_name_inp)
        self.__file_handler_inp = open(self.__file_name_inp, "r",
                                       encoding=self.__encoding)
        mlogger.debug("Opening " + self.__file_name_out)
        self.__file_handler_out = open(self.__file_name_out, "w",
                                       encoding=self.__encoding)
        return self

    def __exit__(self, type, value, traceback):
        mlogger.debug("Closing " + self.__file_name_inp)
        self.__file_handler_inp.close()
        mlogger.debug("Closing " + self.__file_name_out)
        self.__file_handler_out.close()
        return False

    def convertCsv(self):
        row_to_process = 0
        account_name = None
        account_type = None

        for line in csv.reader(self.__file_handler_inp):
            row_to_process = row_to_process+1
            CC_LINE = 4 if self.cc else 3
            CC_STOP = 6 if self.cc else 5

            if row_to_process == CC_LINE:
                account_type = 'CCard' if re.search(
                    'Carta di credito',
                    line[0],
                    re.IGNORECASE) is not None else 'Bank'
                account_name = line[1]
                mlogger.info("Processing: " + account_name)

            if row_to_process == CC_STOP:
                break

        self.__file_handler_out.write(u"!Account\n")
        self.__file_handler_out.write(u"N" + account_name + "\n")
        self.__file_handler_out.write(u"T" + account_type + "\n^\n")
        self.__file_handler_out.write(u"!Type:" + account_type + "\n")

        csv.register_dialect("CREDIT_SUISSE",
                             delimiter=',',
                             doublequote=True,
                             escapechar='\\',
                             quotechar='"',
                             lineterminator="\n")
        csv.register_dialect("QIF",
                             delimiter='\n',
                             quoting=csv.QUOTE_NONE,
                             doublequote=True,
                             escapechar='',
                             quotechar='',
                             lineterminator="\n^\n")
        csfile = csv.DictReader(self.__file_handler_inp,
                                dialect="CREDIT_SUISSE")
        qcsfile = csv.DictWriter(self.__file_handler_out,
                                 dialect="QIF",
                                 fieldnames=['Data di registrazione',
                                             'Addebito',
                                             'Categoria',
                                             'Testo',
                                             'Payee'])

        data = 'Data di transazione' if self.cc else 'Data di registrazione'
        addebito = 'Addebito'
        accredito = 'Accredito'
        if self.cc:
            addebito = addebito + ' CHF'
            accredito = accredito + ' CHF'

        skipped = False

        for row in csfile:
            # Skip account name
            if self.cc and not skipped:
                skipped = True
                continue

            # Skip trailer
            if row[data].lower() == 'totale della colonna' or \
               row[data].lower() == 'registrazione provv.' or \
               row[data] == 'Totale':
                continue

            # Set up registration date
            try:
                d = datetime.strptime(row[data], '%d.%m.%Y')
                if d < self.start_dt:
                    continue
            except ValueError:
                d = datetime.now()

            # Set up transaction amount
            amount = '-' + row[addebito] \
                if len(row[addebito]) != 0 \
                else row[accredito]

            # Identify categories
            cat = None
            payee = None

            try:
                text = row['Testo']
            except KeyError:
                text = row['Descrizione']

            while cat is None:
                for c, expr in self.categories.items():
                    m = re.search(expr, text, re.IGNORECASE)
                    if m is not None:
                        mlogger.debug('Match for %s found', m.group(0))
                        cat = c
                        payee = m.group(0)
                        break

                if cat is None:
                    cat = 'Other'

            # Write the row
            outrow = {'Data di registrazione': 'D' + d.strftime('%d-%m-%y'),
                      'Addebito': 'T' + amount,
                      'Categoria': 'L' + cat,
                      'Testo': 'M' + text}
            if payee is not None:
                outrow['Payee'] = 'P' + payee.upper()

            qcsfile.writerow(outrow)


def processCsv(file_name_inp, file_name_out, cc, start_dt):
    mlogger.info("Run parameters: %s, %s, %s, %s",
                 file_name_inp,
                 file_name_out,
                 cc, start_dt)
    with QifConverter(file_name_inp, file_name_out, cc, start_dt) as qif:
        qif.convertCsv()


def parseargs():
    parser = argparse.ArgumentParser(
        description="Credit Suisse online banking csv to qif format.")
    parser.add_argument("--filein", default='export.csv', required=True,
                        help='Input csv containing the CS transactions.')
    parser.add_argument("--fileout", default='export.qif',
                        help='Output file in the QIF format.')
    parser.add_argument("--cc", action='store_true',
                        help='The file to convert is a credit card.')
    parser.add_argument('--start_dt',
                        default=datetime(datetime.today().year,
                                         datetime.today().month, 1),
                        type=lambda s: datetime.strptime(s, '%Y%m%d'),
                        help='Start date for analysis. Format YYYYMMDD.')
    args = parser.parse_args()
    processCsv(args.filein, args.fileout, args.cc, args.start_dt)


if __name__ == "__main__":
    parseargs()
