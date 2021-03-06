#!/usr/bin/env python
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

import sys, os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view
from trytond.backend.sqlite.database import Database as SQLiteDatabase

class TimesheetInvoiceTestCase(unittest.TestCase):
    '''
    Test timesheet_invoice module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('timesheet_invoice')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('timesheet_invoice')


def doctest_dropdb(test):
    '''
    Remote sqlite memory database
    '''
    database = SQLiteDatabase().connect()
    cursor = database.cursor(autocommit=True)
    try:
        database.drop(cursor, ':memory:')
        cursor.commit()
    finally:
        cursor.close()

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        TimesheetInvoiceTestCase))
    suite.addTest(doctest.DocFileSuite('scenario_timesheet_invoice.rst',
                                      setUp=doctest_dropdb,
                                      tearDown=doctest_dropdb,
                                      encoding='utf-8'))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
