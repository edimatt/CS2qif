import argparse
import csv
import json
import logging
import os
import re
from datetime import datetime
from io import open

import chardet

__all__ = ["QifConverter", "processCsv"]


class QifConverter:
    def __init__(
        self,
        file_name_inp,
        file_name_out,
        cc=False,
        start_dt=datetime(1900, 1, 1),
        log_level="ERROR",
    ):
        logging.basicConfig()
        self._mlogger = logging.getLogger(__name__)
        self._mlogger.setLevel(log_level)

        self.__file_name_inp = file_name_inp
        self.__file_name_out = file_name_out
        with open(self.__file_name_inp, "rb") as inp:
            self.__encoding = chardet.detect(inp.read())["encoding"] or "iso-8859-1"
        self.cc = cc
        self.start_dt = start_dt
        self.transactions = []
        self.categories = {}

        _cf = os.path.join(
            os.environ.get("HOME"), ".config", "cs2qif", "categories.json"
        )
        if os.path.isfile(_cf):
            self._mlogger.info("Reading categories from %s", _cf)
            with open(_cf, "r") as cat:
                self.categories = json.load(cat)
        else:
            self._mlogger.warning("Categories file does not exist: %s.", _cf)
            self.categories = {}

        self._mlogger.info(
            "Run parameters: %s, %s, %s, %s",
            self.__file_name_inp,
            self.__file_name_out,
            self.cc,
            self.start_dt,
        )

    def __enter__(self):
        self._mlogger.debug("Opening " + self.__file_name_inp)
        self.__file_handler_inp = open(
            self.__file_name_inp, "r", encoding=self.__encoding
        )
        self._mlogger.debug("Opening " + self.__file_name_out)
        self.__file_handler_out = open(
            self.__file_name_out, "w", encoding=self.__encoding
        )
        return self

    def __exit__(self, type, value, traceback):
        self._mlogger.debug("Closing " + self.__file_name_inp)
        self.__file_handler_inp.close()
        self._mlogger.debug("Closing " + self.__file_name_out)
        self.__file_handler_out.close()
        return False

    def convertCsv(self):
        row_to_process = 0
        account_name = None
        account_type = None

        for line in csv.reader(self.__file_handler_inp):
            row_to_process = row_to_process + 1
            CC_LINE = 4 if self.cc else 3
            CC_STOP = 6 if self.cc else 5

            if row_to_process == CC_LINE:
                account_type = (
                    "CCard"
                    if re.search("Carta di credito", line[0], re.IGNORECASE) is not None
                    else "Bank"
                )
                account_name = line[1]
                self._mlogger.info("Processing: " + account_name)

            if row_to_process == CC_STOP:
                break

        self.__file_handler_out.write(u"!Account\n")
        self.__file_handler_out.write(u"N" + account_name + "\n")
        self.__file_handler_out.write(u"T" + account_type + "\n^\n")
        self.__file_handler_out.write(u"!Type:" + account_type + "\n")

        csv.register_dialect(
            "CREDIT_SUISSE",
            delimiter=",",
            doublequote=True,
            escapechar="\\",
            quotechar='"',
            lineterminator="\n",
        )
        csv.register_dialect(
            "QIF",
            delimiter="\n",
            quoting=csv.QUOTE_NONE,
            doublequote=True,
            escapechar="",
            quotechar="",
            lineterminator="\n^\n",
        )
        csfile = csv.DictReader(self.__file_handler_inp, dialect="CREDIT_SUISSE")
        qcsfile = csv.DictWriter(
            self.__file_handler_out,
            dialect="QIF",
            fieldnames=[
                "Data di registrazione",
                "Addebito",
                "Categoria",
                "Testo",
                "Payee",
            ],
        )

        data = "Data di transazione" if self.cc else "Data di registrazione"
        addebito = "Addebito"
        accredito = "Accredito"
        if self.cc:
            addebito = addebito + " CHF"
            accredito = accredito + " CHF"

        skipped = False

        for row in csfile:
            # Skip account name
            if self.cc and not skipped:
                skipped = True
                continue

            # Skip trailer
            if (
                row[data].lower() == "totale della colonna"
                or row[data].lower() == "registrazione provv."
                or row[data] == "Totale"
            ):
                continue

            # Set up registration date
            try:
                d = datetime.strptime(row[data], "%d.%m.%Y")
                if d < self.start_dt:
                    continue
            except ValueError:
                d = datetime.now()

            # Set up transaction amount
            amount = "-" + row[addebito] if len(row[addebito]) != 0 else row[accredito]

            # Identify categories
            cat = None
            payee = None

            try:
                text = row["Testo"]
            except KeyError:
                text = row["Descrizione"]

            while cat is None:
                for c, expr in self.categories.items():
                    m = re.search(expr, text, re.IGNORECASE)
                    if m is not None:
                        self._mlogger.debug("Match for %s found", m.group(0))
                        cat = c
                        payee = m.group(0)
                        break

                if cat is None:
                    cat = "Other"

            # Write the row
            outrow = {
                "Data di registrazione": "D" + d.strftime("%d-%m-%y"),
                "Addebito": "T" + amount,
                "Categoria": "L" + cat,
                "Testo": "M" + text,
            }
            if payee is not None:
                outrow["Payee"] = "P" + payee.upper()

            self.transactions.append(outrow)
            qcsfile.writerow(outrow)
        self._mlogger.info("{0} transactions converted.".format(len(self.transactions)))


def processCsv(file_name_inp, file_name_out, cc, start_dt, log_level):
    with QifConverter(file_name_inp, file_name_out, cc, start_dt, log_level) as qif:
        qif.convertCsv()


def main():
    parser = argparse.ArgumentParser(
        description="Credit Suisse online banking csv to qif format."
    )
    parser.add_argument(
        "--filein",
        default="export.csv",
        required=True,
        help="Input csv containing the CS transactions.",
    )
    parser.add_argument(
        "--fileout", default="export.qif", help="Output file in the QIF format."
    )
    parser.add_argument(
        "--cc", action="store_true", help="The file to convert is a credit card."
    )
    parser.add_argument(
        "--start_dt",
        default=datetime(datetime.today().year, datetime.today().month, 1),
        type=lambda s: datetime.strptime(s, "%Y%m%d"),
        help="Start date for analysis. Format YYYYMMDD.",
    )
    parser.add_argument(
        "--log-level", dest="log_level", default=logging.ERROR, help="Logging level"
    )
    args = parser.parse_args()
    processCsv(args.filein, args.fileout, args.cc, args.start_dt, args.log_level)


if __name__ == "__main__":
    main()
