#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name': 'Invoicing of Timesheets',
    'version': '1.9.0',
    'author': 'NFG',
    'email': 'info@nfg.nl',
    'website': 'http://www.nfg.nl/',
    'description': '''Support creation of invoices based on timesheets.
''',
    'xml': [
        'line.xml',
        'work.xml',
        'invoice.xml',
        'configuration.xml',
        'report.xml',
    ],
    'depends': [
        'account',
        'account_invoice',
        'product',
        'company',
        'currency',
        'timesheet',
        'project',
        'project_revenue',
    ],
}
