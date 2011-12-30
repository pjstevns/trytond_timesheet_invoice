#!/usr/bin/python
# -*- coding: utf-8 -*-

from z3c.rml import pagetemplate
from decimal import Decimal
import datetime

company = dict(
    name = 'NFG Net Facilities Group BV',
    currency = dict(
        name='Euro',
        symbol=u'€',
        code='EUR',
        rounding=Decimal('0.01'),
        mon_grouping='[3, 3, 0]',
        mon_decimal_point=',',
    ),
    vat_country = 'NL',
    vat_number = '811863761B01',
    addresses = [
        dict(
            street='PO 24105',
            zip='3502 MC',
            city = 'Utrecht',
            country = dict (
                code='NL'
            ),
        )
    ],
    website='www.nfg.nl',
    email='info@nfg.nl',
    phone='+31.(0)85.877.99.97',
    fax='+31.(0)85.877.99.96',

)

address = (
    """Paul J Stevens
Oeral 144
3524 DZ Utrecht
NETHERLANDS"""
)

timesheet_lines = [
    dict(
        employee=dict(name='Paul Stevens'),
        date=datetime.date.today(),
        hours=1.5,
        work='MyTask',
        description='some work done',
    ),
]

lineset = [ 
    dict(
        type='line',
        quantity=Decimal('5.5'),
        description="""MyProject/MyTask timespent""",
        unit_price=Decimal('100.00'),
        amount=Decimal('550.00'),
        timesheet_lines = 15 * timesheet_lines,

    ), 
    dict(
        type='line',
        quantity=Decimal('10.0'),
        description="""MyProject/MyOtherTask timespent""",
        unit_price=Decimal('100.00'),
        amount=Decimal('1000.00'),
        timesheet_lines = 30 * timesheet_lines,
    ), 
    dict(
        type='subtotal',
        description="""Sub-total""",
        amount=Decimal('1550.00'),
    ), 
]


invoice = dict(
    type = 'out_invoice',
    party = dict(
        full_name='Whatever Inc',
        code='123000022'
    ),
    invoice_address = dict(
        full_address=address,
        country = dict(
            code = 'NL',
        ),
    ),
    description="Timesheet Bill",
    invoice_date=datetime.date.today(),
    number='20100001',
    lines = lineset,
    untaxed_amount=Decimal('1550.00'),
    tax_amount=Decimal('294.5'),
    total_amount=Decimal('1844.5'),
    state = 'open',
    reference = 'PO:2011010212',
)

data = dict(
    invoice=invoice,
    company=company,
)

templatefile = pagetemplate.RMLPageTemplateFile('invoice-report.pt')
open('/tmp/test-report.pdf','w').write(templatefile(**data))
