from datetime import datetime
import logging.config
from io import open
import argparse
import csv
import re

logging.basicConfig(level=logging.DEBUG)
mlogger = logging.getLogger(__name__)

class QifConverter:
    def __init__(self, file_name_inp, file_name_out):
        self.__file_name_inp = file_name_inp
        self.__file_name_out = file_name_out
        self.__encoding = 'iso-8859-1'

    def __enter__(self):
        mlogger.debug("Opening " +self.__file_name_inp)
        self.__file_handler_inp = open(self.__file_name_inp, "r", encoding=self.__encoding)
        mlogger.debug("Opening " +self.__file_name_out)
        self.__file_handler_out = open(self.__file_name_out, "w", encoding=self.__encoding)
        return self

    def __exit__(self, type, value, traceback):
        mlogger.debug("Closing " +self.__file_name_inp)
        self.__file_handler_inp.close()
        mlogger.debug("Closing " +self.__file_name_out)
        self.__file_handler_out.close()
        return False

    def convertCsv(self):
        row_to_process=0
        account_name=None
        account_type=None

        for line in csv.reader(self.__file_handler_inp):
            row_to_process=row_to_process+1

            if row_to_process == 3:
                print(line)
                account_type = 'CCard' if re.search('Carta di credito', line[0], re.IGNORECASE) is not None else 'Bank'
                account_name = line[1]
                mlogger.info ("Processing: " +account_name)

            if row_to_process == 5:
                break

        self.__file_handler_out.write(u"!Account\n")
        self.__file_handler_out.write(u"N" +account_name +"\n")
        self.__file_handler_out.write(u"T" +account_type +"\n^\n")
        self.__file_handler_out.write(u"!Type:" +account_type +"\n")

        csv.register_dialect("CREDIT_SUISSE", delimiter=',', doublequote=True, escapechar='\\', quotechar='"', lineterminator="\n")
        csv.register_dialect("QIF", delimiter='\n', quoting=csv.QUOTE_NONE, doublequote=True, escapechar='', quotechar='', lineterminator="\n^\n")
        csfile = csv.DictReader(self.__file_handler_inp, dialect="CREDIT_SUISSE")
        qcsfile = csv.DictWriter(self.__file_handler_out, dialect="QIF", fieldnames=['Data di registrazione','Addebito','Categoria','Testo','Payee'])

        for row in csfile:

            # Skip trailer
            if row['Data di registrazione'].lower() == 'totale della colonna' or row['Data di registrazione'].lower() == 'registrazione provv.':
                continue

            # Set up registration date
            try:
                d=datetime.strptime(row['Data di registrazione'], '%d.%m.%Y')
            except ValueError:
                #d=datetime(9999,12,31)
                d=datetime.now()

            # Set up transaction amount
            try:
                amount='-' +row['Addebito'] if len(row['Addebito'])!=0  else row['Accredito']
            except KeyError:
                amount='-' +row['Addebito CHF'] if len(row['Addebito CHF'])!=0  else row['Accredito CHF']

            # Identify categories
            cat=None
            payee=None

            try:
                text=row['Testo']
            except KeyError:
                text=row['Descrizione']

            while cat is None:
                m = re.search('NESPRESSO|COOP|Manor|LIDL|MIGROS [A-Z][^R]|ALDI|PLATANERA|LEE TRADING|CONFISERIE SPRUNGLI', text, re.IGNORECASE)
                if m is not None:
                    cat='Groceries'
                    payee=m.group(0)
                    break

                m = re.search('MIGROS MR|NORDSEE|SUBWAY|MITARBEITERRE|RESTAURANT|RISTORANTE|BURGER KING|FOOD COURT 51|Mc Donald|HOLY COW|TRES AMIGOS|STARBUCKS|HOTEL ADLER|ROSSOPOMODORO|CONDITOREI|BRASSERIE FEDERAL|HOOTERS', text, re.IGNORECASE)
                if m is not None:
                    cat='Dining Out'
                    payee=m.group(0)
                    break

                m = re.search('VERKEHRSB|VBZ|SBB|BILLETT|BUNDESBAHN', text)
                if m is not None:
                    cat='Public transport'
                    payee='SBB'
                    break

                m = re.search('Miete|Wolfgang Strebel', text)
                if m is not None:
                    cat='Bills:Rent'
                    break

                m = re.search('Andrea|ANDREATIPS|LUTHY|AMSLER SPIELWAREN|Pagamento all\'estero', text)
                if m is not None:
                    cat='Gifts'
                    payee=m.group(0) if m.group(0) != 'Pagamento all\'estero' else ''
                    break

                m = re.search('SWISSCARD', text)
                if m is not None:
                    cat='Credit Card'
                    payee=m.group(0)
                    break

                m = re.search('Kauf C4 Aircross', text)
                if m is not None:
                    cat='Automobile'
                    payee='CITROEN'
                    break

                m = re.search('Adam Touring GmbH', text)
                if m is not None:
                    cat='Automobile:Maintenance'
                    payee=m.group(0)
                    break

                m = re.search('SOCAR MANEGG|Eni Coldrerio SN', text)
                if m is not None:
                    cat='Automobile:Gasoline'
                    payee=m.group(0)
                    break

                m = re.search('STRASSENVERKEHRSAMT|BASLER VERSICHERUNG', text)
                if m is not None:
                    cat='Automobile:Taxes'
                    payee=m.group(0)
                    break

                m = re.search('Parking|UBER', text, re.IGNORECASE)
                if m is not None:
                    cat='Automobile:Parking'
                    break

                m = re.search("IKEA|INTERIO|MIGROS MICASA|Jumbo-Markt|Maisons.*Monde|TOPTIP|TIGER|GLOBUS|CONFORAMA", text, re.IGNORECASE)
                if m is not None:
                    cat='Household:Furnishing'
                    payee=m.group(0)
                    break

                m = re.search('MULLER|MUELLER|KIEHL|Rituals|THE BODY SHOP|YVES ROCHER', text)
                if m is not None:
                    cat='Personal Care'
                    payee=m.group(0)
                    break

                m = re.search('Apotheke', text, re.IGNORECASE)
                if m is not None:
                    cat='Health Care:Medicine'
                    break

                m = re.search('TOYS.*US|BABYWALZ|PRO BABY|BOESNER|zumstein|Orell F', text, re.IGNORECASE)
                if m is not None:
                    cat='Hobbies/Leisure'
                    payee=m.group(0)
                    break

                m = re.search('ESPRIT|DOSENBACH|CHICOREE|NEW YORKER|ZARA|H & M|C&A|PRIMARK', text, re.IGNORECASE)
                if m is not None:
                    cat='Personal Care:Clothing'
                    payee=m.group(0)
                    break

                m = re.search('ELEKTRIZITAETSWERK', text, re.IGNORECASE)
                if m is not None:
                    cat='Bills:Electricity'
                    payee=m.group(0)
                    break

                m = re.search('UPC|NETFLIX', text, re.IGNORECASE)
                if m is not None:
                    cat='Bills:Internet & TV'
                    payee=m.group(0)
                    break

                m = re.search('kiosk', text)
                if m is not None:
                    cat='Bills:Cell Phone'
                    payee=m.group(0)
                    break

                m = re.search('Pearl Schweiz GmbH|Media Markt|CONRAD|MELECTRONICS|INTERDISCOUNT|FUST', text, re.IGNORECASE)
                if m is not None:
                    cat='Household:Electronics'
                    payee=m.group(0)
                    break

                m = re.search('Trasferimento da un conto all', text)
                if m is not None:
                    cat='Savings'
                    break

                m = re.search('Prelevamento', text)
                if m is not None:
                    cat='Cash'
                    break

                m = re.search('DEUTSCHSCHULE', text, re.IGNORECASE)
                if m is not None:
                    cat='Education'
                    break

                m = re.search('ROLF BOLLINGER', text, re.IGNORECASE)
                if m is not None:
                    cat='Taxes'
                    payee=m.group(0)
                    break

                m = re.search('BONVIVA', text, re.IGNORECASE)
                if m is not None:
                    cat='Taxes:Bank Fees'
                    payee='Credit Suisse'
                    break

                m = re.search('BILLAG', text, re.IGNORECASE)
                if m is not None:
                    cat='Taxes:TV'
                    payee=m.group(0)
                    break

                m = re.search('Bauman Koelliker AG', text, re.IGNORECASE)
                if m is not None:
                    cat='Maintenance'
                    payee=m.group(0)
                    break

                if cat is None:
                    cat='Other'

            # Write the row
            outrow={'Data di registrazione' : 'D' +d.strftime('%d-%m-%y'),
                    'Addebito'              : 'T' +amount,
                    'Categoria'             : 'L' +cat,
                    'Testo'                 : 'M' +text
            }
            if payee is not None:
                outrow['Payee'] = 'P' +payee.upper()

            qcsfile.writerow(outrow)


def processCsv(file_name_inp, file_name_out):
    with QifConverter(file_name_inp, file_name_out) as qif:
        qif.convertCsv()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CREDIT SUISSE csv to qif format")
    parser.add_argument("--filein", default='export.csv', help='Input csv containing the CS transactions')
    parser.add_argument("--fileout", default='export.qif', help='Output file in the QIF format')
    args = parser.parse_args()
    processCsv(args.filein, args.fileout)
