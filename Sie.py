
# -*- coding: utf-8 -*-

import collections
import io
import logging
import ntpath
import os
import re
import sys
import main

# SIE format
# http://www.sie.se/?page_id=12
# PC 8 encoding https://en.wikipedia.org/wiki/Code_page_437

class SieProperties:
    _program   = None
    _org_num   = None
    _company   = None
    _format    = None
    _sie_type  = None
    _kp_type   = None
    _generated = None
    _flag      = None

    """ Program 'Bokio' 1.0 """
    def set_program(self, program):
        self._program = program

    def get_program(self):
        return self._program

    """ #ORGNR 5566778899 """
    def set_org_num(self, org_num):
        self._org_num = org_num

    def get_org_num(self):
        return self._org_num

    """ #FNAMN 'Company name AB' """
    def set_company(self, company):
        self._company = company

    def get_company(self):
        return self._company

    """ #FORMAT PC8 """
    def set_format(self, format):
        self._format = format

    def get_format(self):
        return self._format

    """ #SIETYP 4 """
    def set_sie_type(self, sie_type):
        self._sie_type = sie_type

    def get_sie_type(self):
        return self._sie_type

    """ #KPTYP BAS2014 """
    def set_kp_type(self, kp_type):
        self._kp_type = kp_type

    def get_kp_type(self):
        return self._kp_type

    """ #GEN 20190413 """
    def set_generated(self, gen):
        self._gen = gen

    def get_generated(self):
        return self._gen

    """ #FLAGGA 0 """
    def set_flag(self, flag):
        self._flag = flag

    def get_flag(self):
        return self._flag

    program   = property(get_program,   set_program)
    org_num   = property(get_org_num,   set_org_num)
    company   = property(get_company,   set_company)
    format    = property(get_format,    set_format)
    sie_type  = property(get_sie_type,  set_sie_type)
    kp_type   = property(get_kp_type,   set_kp_type)
    generated = property(get_generated, set_generated)
    flag      = property(get_flag,      set_flag)

class Sie:
    """ Handler for ignored sie fields """
    def not_implemented(self, line):
        pass

    """
    #RAR 0 20180101 20181231
    #RAR -1 20170101 20171231
    """
    def handle_rars(self, line):
        d = line.split()
        self.rars[d[1]] = "{} - {}".format(d[2], d[3])

    """ #KONTO 1010 "Utvecklingsutgifter" """
    def handle_konto(self, line):
        m = re.match(r"#KONTO\s+(\d+)\s+\"(.*)\"", line)
        account = m.group(1)
        description = m.group(2)
        self.baskonto[account] = description

    """
    #IB 0 1010 0.00
    #IB -2 1011 289634.00
    """
    def handle_ib(self, line):
        (_, year, account, value) = line.split()

        if year in self.ibs:
            self.ibs[year][account] = value
        else:
            self.ibs[year] = {}
            self.ibs[year][account] = value

    """
    #UB -1 1510 301438.00
    #UB 0 1510 181875.00
    """
    def handle_ub(self, line):
        (_, year, account, value) = line.split()

        if year in self.ubs:
            self.ubs[year][account] = value
        else:
            self.ubs[year] = {}
            self.ubs[year][account] = value

    """
    #RES -1 5011 18000.00
    #RES 0 5011 18000.00
    """
    def handle_res(self, line):
        (_, year, account, value) = line.split()

        if year in self.res:
            self.res[year][account] = value
        else:
            self.res[year] = {}
            self.res[year][account] = value

    """ #SRU 5011 7513 """
    def handle_sru(self, line):
        sru = line.split()
        if sru[2] in self.sru_table:
            self.sru_table[sru[2]].append(sru[1])
        else:
            self.sru_table[sru[2]] = []
            self.sru_table[sru[2]].append(sru[1])

    def handle_property(self, line):
        descriptor = line.split()[0]

        if descriptor == "#FLAGGA":
            self.properties.flag = line.split()[1]
        elif descriptor == "#PROGRAM":
            self.properties.flag = line.split(" ", 1)[1]
        elif descriptor == "#FORMAT":
            self.properties.format = line.split()[1]
        elif descriptor == "#GEN":
            self.properties.gen = line.split()[1]
        elif descriptor == "#SIETYP":
            self.properties.sie_type = line.split()[1]
        elif descriptor == "#ORGNR":
            self.properties.org_num = line.split()[1]
        elif descriptor == "#FNAMN":
            self.properties.company = line.split(" ", 1)[1]
            self.properties.company = self.properties.company.replace('"', '')
        elif descriptor == "#KPTYP":
            self.properties.kp_type = line.split()[1]
        elif descriptor == "#RAR":
            self.properties.rars = line.split()
        else:
            print("Unhandled descriptor {}".format(descriptor))

    handlers = {
        # Mandatory posts per SIE format 4
        '#FLAGGA'  : handle_property,
        '#PROGRAM' : handle_property,
        '#FORMAT'  : handle_property,
        '#GEN'     : handle_property,
        '#SIETYP'  : handle_property,
        '#FNAMN'   : handle_property,
        '#RAR'     : handle_rars,
        '#KONTO'   : handle_konto,
        '#IB'      : handle_ib,
        '#UB'      : handle_ub,
        '#RES'     : handle_res,

        # Additional posts of interests
        '#SRU'      : handle_sru,
        '#FTYP'     : handle_property,
        '#ORGNR'    : handle_property,
        '#KPTYP'    : handle_property,
        '#VER'      : not_implemented,
        '#TRANS'    : not_implemented,

        # Handler for non handled posts
        'OTHERS'    : not_implemented,
    }

    def __init__(self, sie_file, ink2r_file):
        self.rars       = {}
        self.baskonto   = {}
        self.ibs        = {}
        self.ubs        = {}
        self.res        = {}
        self.sru_table  = {}
        self.sie_file   = sie_file
        self.ink2r_file = ink2r_file
        self.properties = SieProperties()
        self.ink2r      = Ink2r(ink2r_file)
        self._parse_sie(self.sie_file)

        # Determine log file name (based on input sie file) and setup logger
        head, tail = ntpath.split(sie_file)
        file_name = tail or ntpath.basename(head)
        self.log_file_name = '{}-ink2r.txt'.format(file_name)
        with open(self.log_file_name, "w") as fh:
            fh.close()

        self._setup_logger(self.log_file_name)

    """ Setup a basic logger to log output data to file system """
    def _setup_logger(self, log_file_name):
        handler = logging.FileHandler(log_file_name, mode='w')
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger = logging.getLogger(log_file_name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

    """
    Reads sie file line by line and call appropriate handler.
    Some tags, such as #VER is stretching multiple lines, not
    necessarily starting with '#'. For the sake of generating
    an INK2-R, these are not required and thus we can safely
    ignore them.
    """
    def _parse_sie(self, file):
        lines = ""
        with open(file, 'r') as fh:
            lines = fh.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                descriptor = line.split()[0]
                try:
                    self.handlers[descriptor](self, line)
                except:
                    self.handlers['OTHERS'](self, line)

    """
    Log the fields and values in the constructed INK2R table
    Each item in the table corresponds to an entry in the INK2R form and is keyed by
    the table entry number. Below is an example of a 2.26 entry

    "2.26" : {
        'desc'         : "Kassa och bank Kassa, bank och redovisningsmedel"
        'accounts'     : ['1910', '1911', '1912', '1913', '1914', '1920', '1930' ...  '1941', '1942', '1945']
        'contributors' : ['1930', '1940', '1941', '1942', '1945'],
        'sru'          : '7281',
        "total"        : 550000,
            },

    'accounts'     is a list of accounts that is includes in the 2.26 fields of the INK2R.
    'contributors' is a list of the accounts that existed in your books (parsed SIE file)

    From this data structure the function logs the calculated results as,

    2.26 Kassa och bank Kassa, bank och redovisningsmedel
    Sum of ['1910', '1911', '1912', '1913', '1914', '1920', '1930', ...  '1941', '1942', '1945']
    account 1910:             0.00 (Kassa)
    account 1930:             0.00 (Företagskonto / affärskonto)
    account 1940:             0.00 (Övriga bankkonton)
    account 1941:        250000.00 ()
    account 1942:             0.00 ()
    account 1945:        300000.00 ()
    TOTAL:                 550000 SEK
    """
    def _log_ink2r_table(self, table):
        self.logger.debug("{} ({}) INK2R data as derived from external sources '{}' and '{}'" \
            .format(self.properties.company, self.properties.org_num, self.sie_file, self.ink2r_file))
        for code, _ in table.items():
            self.logger.debug("\n{} {}\nSum of {}".format(code, table[code]['desc'], table[code]['accounts']))
            for contrib in table[code]['contributors']:
                account     = contrib.items()[0][0]
                value       = contrib.items()[0][1]
                description = self.baskonto[account]
                self.logger.debug("account {0}: {1: >16} ({2})".format(account, value, description))

            if 'total' in table[code]:
                self.logger.debug("TOTAL: {0: > 23} SEK".format(table[code]['total']))

        print("\nWrote INK2R to '{}'".format(self.log_file_name))

    """
    Each INK2R field (e.g. 2.26) has a list of associated accounts (e.g. 1930). Given these accounts, this
    function returns a list of key/value pairs (account/value) actually present in the sie file
    """
    def _get_contributing_accounts(self, accounts):
        contributors = []

        if len(accounts) == 0:
            return contributors

        active_accounts = []

        if int(accounts[0]) < 3000:
            active_accounts = self.ubs['0']
        else:
            active_accounts = self.res['0']

        for account in accounts:
            if account in active_accounts:
                contributors.append({account:active_accounts[account]})

        return contributors

    """ Simple summarize the vales of all contributing key/value pairs """
    def _summarize_contributing_accounts(self, contributors):
        sum = 0
        for contributor in contributors:
            sum += float(contributor.items()[0][1])
        return sum

    """ Calculate and log the result based on parsed sie and ink2 r files """
    def Process(self):
        sru_warnings = []

        # Fetch the INK2R table as generated from parsing the external file, supplied by IRS
        ink2r_table = self.ink2r.get_ink2r_table()

        # Add all associated accounts to the SRU code defined in the to the ink2r table
        # This is the very foundation upon which we calculate the result
        for code, _ in ink2r_table.items():
            sru = ink2r_table[code]['sru']
            ink2r_table[code]['contributors'] = []
            if sru in self.sru_table:
                ink2r_table[code]['accounts'] = self.sru_table[sru]
                ink2r_table[code]['contributors'] = self._get_contributing_accounts(ink2r_table[code]['accounts'])
                ink2r_table[code]['total'] = int(float(self._summarize_contributing_accounts(ink2r_table[code]['contributors'])))

            else:
                ink2r_table[code]['accounts'] = []
                sru_warnings.append(sru)

        # Log table (corresponding to your INK2R) to file
        self._log_ink2r_table(ink2r_table)

"""
Class representation of a IRS supplied SRU to INK2R mapping
https://www.skatteverket.se/foretagochorganisationer/sjalvservice/blanketterbroschyrer/broschyrer/info/269.4.39f16f103821c58f680007305.html
"""
class Ink2r:
    def __init__(self, file):
        self.table = collections.OrderedDict()
        self.sru_to_code = {}
        self._import_ink2r(file)

    def _import_ink2r(self, file):
        with open(file, 'r') as fh:
            for line in fh.readlines():
                (sru, code, desc)     = [x.strip() for x in line.split(';')]
                self.table[code]      = {'sru':sru, 'desc':desc}
                self.sru_to_code[sru] = code

    def get_ink2r_table(self):
        return self.table
